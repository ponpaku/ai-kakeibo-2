from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)

    # ファイル情報
    original_filename = Column(String(255))
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # バイト数
    mime_type = Column(String(50))

    # OCR処理状態
    ocr_processed = Column(Boolean, default=False)
    ocr_started_at = Column(DateTime(timezone=True))
    ocr_completed_at = Column(DateTime(timezone=True))

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション
    expense = relationship("Expense", back_populates="receipt")
