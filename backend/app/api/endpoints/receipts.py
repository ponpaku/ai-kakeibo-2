from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.expense import Expense, ExpenseStatus
from app.models.receipt import Receipt
from app.api.deps import get_current_user
from app.services.image_service import ImageService
from app.tasks.ocr_tasks import process_receipt_ocr
from app.config import settings
import os

router = APIRouter(prefix="/receipts", tags=["レシート管理"])


@router.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    auto_process: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """レシート画像をアップロード"""
    # ファイルサイズチェック
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="ファイルサイズが大きすぎます")

    # 拡張子チェック
    allowed_exts = settings.ALLOWED_EXTENSIONS.split(",")
    ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="サポートされていないファイル形式です")

    try:
        # 画像を保存
        file_path, relative_path = ImageService.save_receipt_image(contents, file.filename)

        # Expenseレコードを作成
        expense = Expense(
            user_id=current_user.id,
            amount=0,  # OCRで更新される
            expense_date=datetime.now(),
            product_name="処理中",  # OCRで更新される
            status=ExpenseStatus.PENDING
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)

        # Receiptレコードを作成
        receipt = Receipt(
            expense_id=expense.id,
            original_filename=file.filename,
            stored_filename=os.path.basename(file_path),
            file_path=relative_path,
            file_size=len(contents),
            mime_type=file.content_type
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)

        # 自動処理フラグがTrueの場合、OCRタスクを実行
        if auto_process:
            process_receipt_ocr.delay(expense.id, skip_ai=False)

        return {
            "expense_id": expense.id,
            "receipt_id": receipt.id,
            "message": "レシートをアップロードしました" if not auto_process else "レシートをアップロードし、処理を開始しました"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アップロードエラー: {str(e)}")


@router.post("/{expense_id}/process")
def process_receipt(
    expense_id: int,
    skip_ai: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """レシートのOCR処理を開始"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="出費が見つかりません")

    receipt = db.query(Receipt).filter(Receipt.expense_id == expense_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="レシートが見つかりません")

    # OCRタスクを実行
    process_receipt_ocr.delay(expense_id, skip_ai=skip_ai)

    return {"message": "OCR処理を開始しました"}


@router.get("/{receipt_id}/image")
def get_receipt_image(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """レシート画像を取得"""
    receipt = db.query(Receipt).join(Expense).filter(
        Receipt.id == receipt_id,
        Expense.user_id == current_user.id
    ).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="レシートが見つかりません")

    image_path = ImageService.get_full_path(receipt.file_path)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="画像ファイルが見つかりません")

    return FileResponse(
        image_path,
        media_type=receipt.mime_type,
        filename=receipt.original_filename
    )


@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """レシートを削除"""
    receipt = db.query(Receipt).join(Expense).filter(
        Receipt.id == receipt_id,
        Expense.user_id == current_user.id
    ).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="レシートが見つかりません")

    # 画像ファイルを削除
    image_path = ImageService.get_full_path(receipt.file_path)
    ImageService.delete_image(image_path)

    # DBから削除
    db.delete(receipt)
    db.commit()

    return {"message": "レシートを削除しました"}
