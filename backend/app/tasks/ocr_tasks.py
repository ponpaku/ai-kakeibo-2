from datetime import datetime, timezone
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.expense import Expense, ExpenseStatus
from app.models.expense_item import ExpenseItem, CategorySource
from app.models.receipt import Receipt
from app.models.category import Category
from app.models.ai_settings import AISettings
from app.services.codex_service import CodexService
from app.services.image_service import ImageService
from app.tasks.ai_tasks import classify_expense_item_task
from app.constants import OCR_SCHEMA_VERSION
from app.services.category_rule_service import CategoryRuleService
import logging
import json

logger = logging.getLogger(__name__)


@celery_app.task(name="process_receipt_ocr")
def process_receipt_ocr(expense_id: int, skip_ai: bool = False):
    """
    レシートのOCR処理タスク（Codex exec使用）
    ExpenseItem複数作成に対応

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
        receipt.ocr_started_at = datetime.now(timezone.utc)
        expense.status = ExpenseStatus.PROCESSING
        db.commit()

        # 画像パスを取得
        image_path = ImageService.get_full_path(receipt.file_path)

        # カテゴリ一覧を取得
        categories = db.query(Category).filter(Category.is_active == True).all()
        category_names = [cat.name for cat in categories]
        category_map = {cat.name: cat.id for cat in categories}

        logger.info(f"OCR処理開始: expense_id={expense_id}, model={ai_settings.ocr_model}")

        # Codex execでOCR実行
        ocr_result = CodexService.process_receipt_ocr(
            image_path=image_path,
            categories=category_names,
            model=ai_settings.ocr_model,
            sandbox_mode=ai_settings.sandbox_mode,
            skip_git_repo_check=ai_settings.skip_git_repo_check,
            system_prompt=ai_settings.ocr_system_prompt,
        )

        if not ocr_result.get("success"):
            logger.error(f"OCR失敗: {ocr_result.get('error')}")
            expense.status = ExpenseStatus.FAILED
            receipt.ocr_processed = False
            db.commit()
            return {"success": False, "error": ocr_result.get("error")}

        # OCR結果を取得
        data = ocr_result.get("data", {})
        raw_output = ocr_result.get("raw_output", "")
        logger.info(f"OCR成功: store={data.get('store')}, items={len(data.get('items', []))}")

        # Receipt: OCR結果の完全なJSONを保存
        receipt.ocr_raw_output = json.dumps(data, ensure_ascii=False)
        receipt.ocr_engine = "codex"
        receipt.ocr_model = ai_settings.ocr_model
        receipt.schema_version = OCR_SCHEMA_VERSION
        receipt.ocr_processed = True
        receipt.ocr_completed_at = datetime.now(timezone.utc)

        # Expense: 決済ヘッダ情報を設定
        # 日付
        if data.get("date"):
            try:
                from datetime import datetime as dt
                date_str = data["date"]
                for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"]:
                    try:
                        expense.occurred_at = dt.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"日付のパースに失敗: {data.get('date')} - {str(e)}")

        # 店舗名/加盟店名
        expense.merchant_name = data.get("store")

        # タイトル生成
        if expense.merchant_name:
            expense.title = f"{expense.merchant_name}での購入"
        else:
            expense.title = "レシート購入"

        # 決済情報
        payment = data.get("payment", {})
        if isinstance(payment, dict):
            expense.total_amount = payment.get("amount") or 0
            expense.payment_method = payment.get("method")
            expense.card_brand = payment.get("card_brand")
            expense.card_last4 = payment.get("card_last4")
        else:
            expense.total_amount = 0

        # ポイント情報
        points = data.get("points", {})
        if isinstance(points, dict):
            expense.points_used = points.get("used")
            expense.points_earned = points.get("earned")
            expense.points_program = points.get("program")

        # ExpenseItem: 商品明細を作成
        items = data.get("items", [])
        uncategorized_item_ids = []

        if items:
            for position, item_data in enumerate(items):
                product_name = item_data.get("name") or "不明な商品"
                quantity = item_data.get("quantity")
                unit_price = item_data.get("unit_price")
                line_total = item_data.get("line_total") or 0

                # カテゴリ名からIDを取得
                category_name = item_data.get("category")
                category_id = None
                category_source = None
                ai_confidence = None

                if category_name and category_name in category_map:
                    category_id = category_map[category_name]
                    category_source = CategorySource.OCR
                else:
                    matched_rule = CategoryRuleService.find_match(
                        db,
                        [
                            product_name,
                            expense.merchant_name,
                            expense.note,
                        ],
                    )
                    if matched_rule:
                        category_id = matched_rule.category_id
                        category_source = CategorySource.RULE
                        ai_confidence = matched_rule.confidence

                # ExpenseItem作成
                expense_item = ExpenseItem(
                    expense_id=expense_id,
                    position=position,
                    product_name=product_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                    category_id=category_id,
                    category_source=category_source,
                    ai_confidence=ai_confidence,
                    raw=json.dumps(item_data, ensure_ascii=False)
                )
                db.add(expense_item)
                db.flush()  # IDを取得

                # カテゴリ未設定の場合はAI分類対象
                if category_id is None:
                    uncategorized_item_ids.append(expense_item.id)

            # total_amountが未設定の場合は商品合計を使用
            if expense.total_amount == 0:
                expense.total_amount = sum(item.get("line_total", 0) or 0 for item in items)
        else:
            # 商品がない場合でも最低1つのExpenseItemを作成
            fallback_product_name = expense.title or "レシート購入品"
            fallback_category_id = None
            fallback_category_source = None
            fallback_confidence = None

            matched_rule = CategoryRuleService.find_match(
                db,
                [
                    fallback_product_name,
                    expense.merchant_name,
                    expense.note,
                ],
            )
            if matched_rule:
                fallback_category_id = matched_rule.category_id
                fallback_category_source = CategorySource.RULE
                fallback_confidence = matched_rule.confidence

            expense_item = ExpenseItem(
                expense_id=expense_id,
                position=0,
                product_name=fallback_product_name,
                line_total=expense.total_amount or 0,
                category_id=fallback_category_id,
                category_source=fallback_category_source,
                ai_confidence=fallback_confidence
            )
            db.add(expense_item)
            db.flush()
            if expense_item.category_id is None:
                uncategorized_item_ids.append(expense_item.id)

        # ステータス決定: 全てカテゴリ設定済みならCOMPLETED。
        # 未設定がある場合はAI分類の実行可否に応じてPROCESSING/PENDINGを設定する。
        should_queue_ai = not skip_ai and ai_settings.classification_enabled

        if uncategorized_item_ids:
            expense.status = ExpenseStatus.PROCESSING if should_queue_ai else ExpenseStatus.PENDING
        else:
            expense.status = ExpenseStatus.COMPLETED

        db.commit()

        # AI分類タスクを実行（設定で有効かつカテゴリ未設定の商品がある場合）
        if should_queue_ai and uncategorized_item_ids:
            logger.info(f"AI分類タスクを開始: {len(uncategorized_item_ids)}個の商品")
            for item_id in uncategorized_item_ids:
                classify_expense_item_task.delay(item_id)
        elif uncategorized_item_ids:
            logger.info("AI分類が無効のため、未分類のまま保留します")

        return {
            "success": True,
            "expense_id": expense_id,
            "items_created": len(items) if items else 1,
            "uncategorized_items": len(uncategorized_item_ids),
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
