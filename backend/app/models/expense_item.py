from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class CategorySource(str, enum.Enum):
    """カテゴリの決定ソース"""
    OCR = "ocr"        # OCRによる自動分類
    AI = "ai"          # AIによる自動分類
    MANUAL = "manual"  # 手動設定
    RULE = "rule"      # ルールベース


class ExpenseItem(Base):
    """
    購入品明細（ExpenseItemは1購入品/1行）

    カテゴリ集計の正（主語）はこのテーブル。
    1つのExpenseに複数のExpenseItemが紐づく。
    """
    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)

    # 明細情報
    position = Column(Integer, nullable=False, default=0)  # レシート上の順序
    product_name = Column(String(200), nullable=False)     # 商品名（必須）
    quantity = Column(Numeric(10, 3), nullable=True)       # 数量
    unit_price = Column(Integer, nullable=True)            # 単価（円）
    line_total = Column(Integer, nullable=False)           # 行合計（円）

    # カテゴリ（集計の主語）
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    category_source = Column(Enum(CategorySource), nullable=True)  # カテゴリ決定方法
    ai_confidence = Column(Numeric(3, 2), nullable=True)           # AI信頼度（0.00-1.00）

    # 拡張用（税区分、割引等）
    raw = Column(Text, nullable=True)  # JSON形式で将来的な拡張データを格納

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    expense = relationship("Expense", back_populates="items")
    category = relationship("Category")

    # 複合インデックス
    __table_args__ = (
        Index('idx_expense_position', 'expense_id', 'position'),
        Index('idx_expense_category', 'expense_id', 'category_id'),
    )

    def __repr__(self):
        return f"<ExpenseItem(id={self.id}, product={self.product_name}, amount={self.line_total})>"
