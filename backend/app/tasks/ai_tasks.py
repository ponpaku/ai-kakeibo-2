from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.expense import Expense, ExpenseStatus
from app.models.category import Category
from app.models.ai_settings import AISettings
from app.services.codex_service import CodexService
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="classify_expense_task")
def classify_expense_task(expense_id: int):
    """
    出費のAI分類タスク（Codex exec使用）

    Args:
        expense_id: Expense ID
    """
    db = SessionLocal()
    try:
        # Expenseを取得
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            logger.error(f"Expense not found: {expense_id}")
            return {"success": False, "error": "Expense not found"}

        # AI設定を取得
        ai_settings = db.query(AISettings).first()
        if not ai_settings:
            # デフォルト設定を作成
            ai_settings = AISettings()
            db.add(ai_settings)
            db.commit()
            db.refresh(ai_settings)

        # 分類が無効の場合はスキップ
        if not ai_settings.classification_enabled:
            logger.info("Classification is disabled in settings")
            expense.status = ExpenseStatus.COMPLETED
            db.commit()
            return {"success": False, "error": "Classification is disabled"}

        # 処理中に設定
        expense.status = ExpenseStatus.PROCESSING
        db.commit()

        # カテゴリ一覧を取得
        categories = db.query(Category).filter(Category.is_active == True).all()
        category_names = [cat.name for cat in categories]

        if not category_names:
            logger.warning("No active categories found")
            expense.status = ExpenseStatus.COMPLETED
            db.commit()
            return {"success": False, "error": "No active categories"}

        logger.info(f"AI分類処理開始: expense_id={expense_id}, model={ai_settings.classification_model}")

        # Codex execで分類実行
        classification_result = CodexService.classify_expense(
            product_name=expense.product_name or "",
            store_name=expense.store_name,
            amount=float(expense.amount) if expense.amount else 0.0,
            note=expense.note,
            categories=category_names,
            model=ai_settings.classification_model,
            sandbox_mode=ai_settings.sandbox_mode,
            skip_git_repo_check=ai_settings.skip_git_repo_check
        )

        if not classification_result.get("success"):
            logger.error(f"分類失敗: {classification_result.get('error')}")
            expense.status = ExpenseStatus.FAILED
            db.commit()
            return {
                "success": False,
                "error": classification_result.get("error")
            }

        # 分類結果を取得
        category_name = classification_result.get("category")
        confidence = classification_result.get("confidence", 0.0)

        logger.info(f"分類成功: category={category_name}, confidence={confidence}")

        # カテゴリIDを取得
        category_id = None
        if category_name:
            category = db.query(Category).filter(Category.name == category_name).first()
            if category:
                category_id = category.id
            else:
                logger.warning(f"カテゴリが見つかりません: {category_name}")

        # 分類結果を保存
        expense.category_id = category_id
        expense.ai_confidence = confidence
        expense.ai_classification_data = None  # Codex execの出力は保存しない
        expense.status = ExpenseStatus.COMPLETED

        db.commit()

        return {
            "success": True,
            "expense_id": expense_id,
            "category_id": category_id,
            "category_name": category_name,
            "confidence": confidence
        }

    except Exception as e:
        logger.exception(f"分類処理中にエラーが発生: {str(e)}")
        if expense:
            expense.status = ExpenseStatus.FAILED
            db.commit()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
