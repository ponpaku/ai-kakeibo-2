from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.expense import Expense, ExpenseStatus
from app.models.expense_item import ExpenseItem, CategorySource
from app.models.category import Category
from app.models.ai_settings import AISettings
from app.services.codex_service import CodexService
from app.services.category_rule_service import CategoryRuleService
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="classify_expense_item_task")
def classify_expense_item_task(expense_item_id: int):
    """
    ExpenseItemのAI分類タスク（Codex exec使用）

    Args:
        expense_item_id: ExpenseItem ID
    """
    db = SessionLocal()
    try:
        # ExpenseItemを取得
        expense_item = db.query(ExpenseItem).filter(ExpenseItem.id == expense_item_id).first()
        if not expense_item:
            logger.error(f"ExpenseItem not found: {expense_item_id}")
            return {"success": False, "error": "ExpenseItem not found"}

        # 既にカテゴリが設定されている場合はスキップ
        if expense_item.category_id is not None:
            logger.info(f"ExpenseItem {expense_item_id} already has category, skipping")
            return {"success": True, "skipped": True}

        # 関連するExpenseを取得
        expense = db.query(Expense).filter(Expense.id == expense_item.expense_id).first()
        if not expense:
            logger.error(f"Expense not found for ExpenseItem: {expense_item_id}")
            return {"success": False, "error": "Expense not found"}

        # カテゴリ一覧を取得
        categories = db.query(Category).filter(Category.is_active == True).all()
        category_names = [cat.name for cat in categories]
        category_map = {cat.id: cat.name for cat in categories}

        if not category_names:
            logger.warning("No active categories found")
            return {"success": False, "error": "No active categories"}

        matched_rule = CategoryRuleService.find_match(
            db,
            [
                expense_item.product_name,
                expense.merchant_name,
                expense.note,
            ],
        )

        if matched_rule:
            expense_item.category_id = matched_rule.category_id
            expense_item.category_source = CategorySource.RULE
            expense_item.ai_confidence = matched_rule.confidence
            db.commit()

            all_items = db.query(ExpenseItem).filter(ExpenseItem.expense_id == expense.id).all()
            uncategorized_count = sum(1 for item in all_items if item.category_id is None)

            if uncategorized_count == 0:
                expense.status = ExpenseStatus.COMPLETED
                db.commit()
            category_name = category_map.get(matched_rule.category_id)
            logger.info(
                "ルールで分類: item_id=%s, category_id=%s, priority=%s",
                expense_item_id,
                matched_rule.category_id,
                matched_rule.priority,
            )

            return {
                "success": True,
                "expense_item_id": expense_item_id,
                "expense_id": expense.id,
                "category_id": matched_rule.category_id,
                "category_name": category_name,
                "confidence": matched_rule.confidence,
                "source": CategorySource.RULE.value,
                "uncategorized_remaining": uncategorized_count,
            }

        ai_settings = db.query(AISettings).first()
        if not ai_settings:
            ai_settings = AISettings()
            db.add(ai_settings)
            db.commit()
            db.refresh(ai_settings)

        if not ai_settings.classification_enabled:
            logger.info("Classification is disabled in settings")
            return {"success": False, "error": "Classification is disabled"}

        logger.info(
            "AI分類処理開始: expense_item_id=%s, product=%s, model=%s",
            expense_item_id,
            expense_item.product_name,
            ai_settings.classification_model,
        )

        classification_result = CodexService.classify_expense(
            product_name=expense_item.product_name or "",
            store_name=expense.merchant_name,
            amount=float(expense_item.line_total) if expense_item.line_total else 0.0,
            note=expense.note,
            categories=category_names,
            model=ai_settings.classification_model,
            sandbox_mode=ai_settings.sandbox_mode,
            skip_git_repo_check=ai_settings.skip_git_repo_check,
            system_prompt=ai_settings.classification_system_prompt,
        )

        if not classification_result.get("success"):
            logger.error(f"分類失敗: {classification_result.get('error')}")
            return {
                "success": False,
                "error": classification_result.get("error")
            }

        category_name = classification_result.get("category")
        confidence = classification_result.get("confidence", 0.0)

        logger.info(f"分類成功: item_id={expense_item_id}, category={category_name}, confidence={confidence}")

        category_id = None
        if category_name:
            category = db.query(Category).filter(Category.name == category_name).first()
            if category:
                category_id = category.id
            else:
                logger.warning(f"カテゴリが見つかりません: {category_name}")

        expense_item.category_id = category_id
        expense_item.category_source = CategorySource.AI
        expense_item.ai_confidence = confidence

        db.commit()

        all_items = db.query(ExpenseItem).filter(ExpenseItem.expense_id == expense.id).all()
        uncategorized_count = sum(1 for item in all_items if item.category_id is None)

        if uncategorized_count == 0:
            expense.status = ExpenseStatus.COMPLETED
            db.commit()
            logger.info(f"Expense {expense.id} - 全商品の分類が完了しました")
        else:
            logger.info(f"Expense {expense.id} - 残り{uncategorized_count}個の商品が未分類")

        return {
            "success": True,
            "expense_item_id": expense_item_id,
            "expense_id": expense.id,
            "category_id": category_id,
            "category_name": category_name,
            "confidence": confidence,
            "uncategorized_remaining": uncategorized_count
        }

    except Exception as e:
        logger.exception(f"分類処理中にエラーが発生: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


# 旧関数の互換性維持（非推奨）
@celery_app.task(name="classify_expense_task")
def classify_expense_task(expense_id: int):
    """
    （非推奨）後方互換性のためのラッパー
    全ExpenseItemsを分類する
    """
    db = SessionLocal()
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            return {"success": False, "error": "Expense not found"}

        # 全ExpenseItemsを取得
        items = db.query(ExpenseItem).filter(ExpenseItem.expense_id == expense_id).all()

        results = []
        for item in items:
            if item.category_id is None:
                # AI分類タスクを起動
                result = classify_expense_item_task.delay(item.id)
                results.append(result)

        return {
            "success": True,
            "expense_id": expense_id,
            "tasks_started": len(results)
        }
    finally:
        db.close()
