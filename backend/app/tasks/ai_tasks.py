from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.expense import Expense, ExpenseStatus
from app.services.ai_classifier import AIClassifier


@celery_app.task(name="classify_expense_task")
def classify_expense_task(expense_id: int):
    """出費のAI分類タスク"""
    db = SessionLocal()
    try:
        # Expenseを取得
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            return {"success": False, "error": "Expense not found"}

        # 処理中に設定
        expense.status = ExpenseStatus.PROCESSING
        db.commit()

        # AI分類用のデータを準備
        expense_data = {
            "store_name": expense.store_name,
            "description": expense.description,
            "amount": float(expense.amount) if expense.amount else 0,
            "ocr_raw_text": expense.ocr_raw_text or ""
        }

        # AI分類実行
        classification_result = AIClassifier.classify_expense(
            db=db,
            expense_data=expense_data,
            user_id=expense.user_id
        )

        if classification_result.get("success"):
            # 分類結果を保存
            expense.category_id = classification_result.get("category_id")
            expense.ai_confidence = classification_result.get("confidence")
            expense.ai_classification_data = classification_result.get("raw_response")
            expense.status = ExpenseStatus.COMPLETED
        else:
            expense.status = ExpenseStatus.FAILED

        db.commit()

        return {
            "success": classification_result.get("success"),
            "expense_id": expense_id,
            "category_id": classification_result.get("category_id"),
            "confidence": classification_result.get("confidence")
        }

    except Exception as e:
        if expense:
            expense.status = ExpenseStatus.FAILED
            db.commit()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
