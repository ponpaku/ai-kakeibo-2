from datetime import datetime
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.expense import Expense, ExpenseStatus
from app.models.receipt import Receipt
from app.models.category import Category
from app.models.ai_settings import AISettings
from app.services.codex_service import CodexService
from app.services.image_service import ImageService
from app.tasks.ai_tasks import classify_expense_task
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="process_receipt_ocr")
def process_receipt_ocr(expense_id: int, skip_ai: bool = False):
    """
    レシートのOCR処理タスク（Codex exec使用）

    Args:
        expense_id: Expense ID
        skip_ai: AI分類をスキップするか
    """
    db = SessionLocal()
    try:
        # ExpenseとReceiptを取得
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            logger.error(f"Expense not found: {expense_id}")
            return {"success": False, "error": "Expense not found"}

        receipt = db.query(Receipt).filter(Receipt.expense_id == expense_id).first()
        if not receipt:
            logger.error(f"Receipt not found for expense: {expense_id}")
            return {"success": False, "error": "Receipt not found"}

        # AI設定を取得
        ai_settings = db.query(AISettings).first()
        if not ai_settings:
            # デフォルト設定を作成
            ai_settings = AISettings()
            db.add(ai_settings)
            db.commit()
            db.refresh(ai_settings)

        # OCRが無効の場合はスキップ
        if not ai_settings.ocr_enabled:
            logger.info("OCR is disabled in settings")
            expense.status = ExpenseStatus.PENDING
            db.commit()
            return {"success": False, "error": "OCR is disabled"}

        # OCR開始時刻を記録
        receipt.ocr_started_at = datetime.utcnow()
        expense.status = ExpenseStatus.PROCESSING
        db.commit()

        # 画像パスを取得
        image_path = ImageService.get_full_path(receipt.file_path)

        # カテゴリ一覧を取得
        categories = db.query(Category).filter(Category.is_active == True).all()
        category_names = [cat.name for cat in categories]

        logger.info(f"OCR処理開始: expense_id={expense_id}, model={ai_settings.ocr_model}")

        # Codex execでOCR実行
        ocr_result = CodexService.process_receipt_ocr(
            image_path=image_path,
            categories=category_names,
            model=ai_settings.ocr_model,
            sandbox_mode=ai_settings.sandbox_mode,
            skip_git_repo_check=ai_settings.skip_git_repo_check
        )

        if not ocr_result.get("success"):
            logger.error(f"OCR失敗: {ocr_result.get('error')}")
            expense.status = ExpenseStatus.FAILED
            receipt.ocr_processed = False
            db.commit()
            return {"success": False, "error": ocr_result.get("error")}

        # OCR結果を取得
        data = ocr_result.get("data", {})
        logger.info(f"OCR成功: store={data.get('store')}, items={len(data.get('items', []))}")

        # OCR結果をExpenseに保存
        expense.ocr_raw_text = ocr_result.get("raw_output")

        # 店舗名
        if data.get("store"):
            expense.store_name = data["store"]

        # 商品名と金額を決定
        items = data.get("items", [])
        if items:
            # 最初の商品をメインとする、または合計金額を使用
            if len(items) == 1:
                expense.product_name = items[0].get("name") or "レシート購入品"
                expense.amount = items[0].get("line_total") or 0
            else:
                # 複数商品の場合は店舗名を使用
                expense.product_name = f"{expense.store_name or ''}での購入"
                # 合計金額を計算
                total = sum(item.get("line_total", 0) or 0 for item in items)
                expense.amount = total if total > 0 else (data.get("payment", {}).get("amount") if isinstance(data.get("payment"), dict) else 0)

            # 最初の商品のカテゴリを使用
            first_item_category = items[0].get("category")
            if first_item_category:
                category = db.query(Category).filter(Category.name == first_item_category).first()
                if category:
                    expense.category_id = category.id
        else:
            # 商品がない場合
            expense.product_name = f"{expense.store_name or 'レシート'}での購入"
            # 支払い金額を使用
            payment = data.get("payment")
            if payment and isinstance(payment, dict):
                expense.amount = payment.get("amount") or 0

        # 日付
        if data.get("date"):
            try:
                # 日付をパース（YYYY/MM/DD, YYYY-MM-DD など）
                from datetime import datetime as dt
                date_str = data["date"]
                # 複数の形式を試す
                for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"]:
                    try:
                        expense.expense_date = dt.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"日付のパースに失敗: {data.get('date')} - {str(e)}")

        # OCR完了時刻を記録
        receipt.ocr_processed = True
        receipt.ocr_completed_at = datetime.utcnow()

        # カテゴリが設定されていれば完了、なければ処理中のまま
        if expense.category_id:
            expense.status = ExpenseStatus.COMPLETED
        else:
            expense.status = ExpenseStatus.PROCESSING

        db.commit()

        # AI分類タスクを実行（skip_aiがFalseかつカテゴリが未設定の場合）
        if not skip_ai and not expense.category_id:
            logger.info(f"AI分類タスクを開始: expense_id={expense_id}")
            classify_expense_task.delay(expense_id)

        return {
            "success": True,
            "expense_id": expense_id,
            "ocr_result": data
        }

    except Exception as e:
        logger.exception(f"OCR処理中にエラーが発生: {str(e)}")
        if expense:
            expense.status = ExpenseStatus.FAILED
            db.commit()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
