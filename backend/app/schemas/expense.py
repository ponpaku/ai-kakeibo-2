from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class ExpenseBase(BaseModel):
    amount: Decimal
    expense_date: datetime
    product_name: str  # 商品名（必須）
    store_name: Optional[str] = None  # 店舗名（任意）
    description: Optional[str] = None  # 説明（任意）
    note: Optional[str] = None  # 備考（任意）


class ExpenseCreate(ExpenseBase):
    category_id: Optional[int] = None


class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = None
    expense_date: Optional[datetime] = None
    category_id: Optional[int] = None
    product_name: Optional[str] = None  # 商品名
    store_name: Optional[str] = None  # 店舗名
    description: Optional[str] = None  # 説明
    note: Optional[str] = None  # 備考


class Receipt(BaseModel):
    id: int
    original_filename: Optional[str]
    file_path: str
    ocr_processed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Expense(ExpenseBase):
    id: int
    user_id: int
    category_id: Optional[int]
    status: str
    ai_confidence: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExpenseWithReceipt(Expense):
    receipt: Optional[Receipt] = None
    category_name: Optional[str] = None


class ExpenseListResponse(BaseModel):
    total: int
    expenses: List[ExpenseWithReceipt]


class ManualExpenseCreate(BaseModel):
    """手入力用のスキーマ"""
    amount: Decimal
    expense_date: datetime
    product_name: str  # 商品名（必須）
    store_name: Optional[str] = None  # 店舗名（任意）
    description: Optional[str] = None  # 説明（任意）
    note: Optional[str] = None  # 備考（任意）
    category_id: Optional[int] = None  # 手入力の場合は指定可能
    skip_ai_classification: bool = False  # AI分類をスキップするか
