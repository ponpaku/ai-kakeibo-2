from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ExpenseStatus(str, enum.Enum):
    PENDING = "pending"  # 処理待ち
    PROCESSING = "processing"  # AI分類中
    COMPLETED = "completed"  # 完了
    FAILED = "failed"  # 失敗


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # 金額と日付
    amount = Column(Numeric(10, 2), nullable=False)
    expense_date = Column(DateTime(timezone=True), nullable=False)

    # 詳細情報
    product_name = Column(String(200), nullable=False)  # 商品名（必須）
    store_name = Column(String(200))  # 店舗名（任意）
    description = Column(Text)  # 説明（任意）
    note = Column(Text)  # 備考（任意）

    # OCRとAI分類関連
    ocr_raw_text = Column(Text)  # OCRの生データ
    ai_classification_data = Column(Text)  # AI分類の詳細データ（JSON）
    ai_confidence = Column(Numeric(3, 2))  # AI分類の信頼度（0.00-1.00）
    status = Column(Enum(ExpenseStatus), default=ExpenseStatus.PENDING)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
    receipt = relationship("Receipt", back_populates="expense", uselist=False)
