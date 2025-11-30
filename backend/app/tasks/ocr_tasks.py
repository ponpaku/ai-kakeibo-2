from datetime import datetime
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.expense import Expense, ExpenseStatus
from app.models.receipt import Receipt
from app.services.ocr_service import OCRService
from app.services.image_service import ImageService
from app.tasks.ai_tasks import classify_expense_task


@celery_app.task(name="process_receipt_ocr")
def process_receipt_ocr(expense_id: int, skip_ai: bool = False):
    """レシートのOCR処理タスク"""
    db = SessionLocal()
    try:
        # ExpenseとReceiptを取得
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            return {"success": False, "error": "Expense not found"}

        receipt = db.query(Receipt).filter(Receipt.expense_id == expense_id).first()
        if not receipt:
            return {"success": False, "error": "Receipt not found"}

        # OCR開始時刻を記録
        receipt.ocr_started_at = datetime.utcnow()
        db.commit()

        # 画像パスを取得
        image_path = ImageService.get_full_path(receipt.file_path)

        # OCR実行
        ocr_result = OCRService.process_receipt(image_path)

        if not ocr_result.get("success"):
            expense.status = ExpenseStatus.FAILED
            db.commit()
            return {"success": False, "error": ocr_result.get("error")}

        # OCR結果をExpenseに保存
        expense.ocr_raw_text = ocr_result.get("raw_text")

        # 解析されたデータを取得
        parsed_data = ocr_result.get("parsed_data", {})
        if parsed_data.get("store_name"):
            expense.store_name = parsed_data["store_name"]
        if parsed_data.get("total_amount"):
            expense.amount = parsed_data["total_amount"]
        if parsed_data.get("product_name"):
            expense.product_name = parsed_data["product_name"]

        # OCR完了時刻を記録
        receipt.ocr_processed = True
        receipt.ocr_completed_at = datetime.utcnow()

        db.commit()

        # AI分類タスクを実行（skip_aiがFalseの場合）
        if not skip_ai:
            classify_expense_task.delay(expense_id)

        return {
            "success": True,
            "expense_id": expense_id,
            "ocr_result": parsed_data
        }

    except Exception as e:
        if expense:
            expense.status = ExpenseStatus.FAILED
            db.commit()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
