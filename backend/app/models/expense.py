from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Enum, Index
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
    """
    決済ヘッダ（Expenseは1会計/1レシート単位）

    商品名やカテゴリは持たず、決済情報と合計金額のみを管理。
    個別の購入品はExpenseItemで管理する。
    """
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 決済情報
    occurred_at = Column(DateTime(timezone=True), nullable=False)  # 発生日時
    merchant_name = Column(String(200), nullable=True)  # 店舗名/加盟店名
    title = Column(String(200), nullable=True)  # 決済のタイトル（表示用）
    total_amount = Column(Integer, nullable=False)  # 合計金額（円）
    currency = Column(String(3), nullable=False, default="JPY")  # 通貨コード

    # 決済手段
    payment_method = Column(String(50), nullable=True)  # 支払い方法（cash, credit, debit, etc.）
    card_brand = Column(String(50), nullable=True)  # カードブランド（Visa, Mastercard, etc.）
    card_last4 = Column(String(4), nullable=True)  # カード下4桁

    # ポイント情報
    points_used = Column(Integer, nullable=True)  # 使用ポイント
    points_earned = Column(Integer, nullable=True)  # 獲得ポイント
    points_program = Column(String(100), nullable=True)  # ポイントプログラム名

    # 詳細情報
    description = Column(Text, nullable=True)  # 説明（任意）
    note = Column(Text, nullable=True)  # 備考（任意）

    # AI分類関連（Expense全体に対する分類がある場合）
    ai_classification_data = Column(Text, nullable=True)  # AI分類の詳細データ（JSON）
    ai_confidence = Column(Numeric(3, 2), nullable=True)  # AI分類の信頼度（0.00-1.00）
    status = Column(Enum(ExpenseStatus), default=ExpenseStatus.PENDING)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    user = relationship("User", back_populates="expenses")
    receipt = relationship("Receipt", back_populates="expense", uselist=False, cascade="all, delete-orphan")
    items = relationship("ExpenseItem", back_populates="expense", cascade="all, delete-orphan")

    # 複合インデックス
    __table_args__ = (
        Index('idx_user_occurred', 'user_id', 'occurred_at'),
    )
