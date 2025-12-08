from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ExpenseItem（商品明細）スキーマ
class ExpenseItemBase(BaseModel):
    product_name: str
    quantity: Optional[Decimal] = None
    unit_price: Optional[int] = None
    line_total: int
    tax_rate: Optional[Decimal] = None  # 税率（%）
    tax_included: Optional[bool] = None  # 税込みか
    tax_amount: Optional[int] = None  # 税額（円）
    category_id: Optional[int] = None


class ExpenseItemCreate(ExpenseItemBase):
    pass


class ExpenseItem(ExpenseItemBase):
    id: int
    expense_id: int
    position: int
    category_source: Optional[str] = None
    ai_confidence: Optional[Decimal] = None

    class Config:
        from_attributes = True


class ExpenseItemWithCategory(ExpenseItem):
    category_name: Optional[str] = None


class ExpenseItemUpdate(BaseModel):
    """ExpenseItem更新用スキーマ"""
    product_name: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[int] = None
    line_total: Optional[int] = None
    tax_rate: Optional[Decimal] = None
    tax_included: Optional[bool] = None
    tax_amount: Optional[int] = None
    category_id: Optional[int] = None


# Expense（決済ヘッダ）スキーマ
class ExpenseBase(BaseModel):
    occurred_at: datetime  # 発生日時
    merchant_name: Optional[str] = None  # 店舗名/加盟店名
    title: Optional[str] = None  # 決済のタイトル
    total_amount: int  # 合計金額（円）
    currency: str = "JPY"  # 通貨コード
    payment_method: Optional[str] = None  # 支払い方法
    card_brand: Optional[str] = None  # カードブランド
    card_last4: Optional[str] = None  # カード下4桁
    points_used: Optional[int] = None  # 使用ポイント
    points_earned: Optional[int] = None  # 獲得ポイント
    points_program: Optional[str] = None  # ポイントプログラム名
    description: Optional[str] = None  # 説明
    note: Optional[str] = None  # 備考


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    occurred_at: Optional[datetime] = None
    merchant_name: Optional[str] = None
    title: Optional[str] = None
    total_amount: Optional[int] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    points_used: Optional[int] = None
    points_earned: Optional[int] = None
    points_program: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None


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
    status: str
    ai_confidence: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExpenseWithReceipt(Expense):
    receipt: Optional[Receipt] = None
    items: List[ExpenseItemWithCategory] = []


class ExpenseListResponse(BaseModel):
    total: int
    expenses: List[ExpenseWithReceipt]


class ManualExpenseCreate(BaseModel):
    """手入力用のスキーマ"""
    occurred_at: datetime  # 発生日時
    merchant_name: Optional[str] = None  # 店舗名/加盟店名
    total_amount: int  # 合計金額（円）
    product_name: Optional[str] = None  # 商品名（単一商品の場合）
    description: Optional[str] = None  # 説明（任意）
    note: Optional[str] = None  # 備考（任意）
    category_id: Optional[int] = None  # 手入力の場合は指定可能
    skip_ai_classification: bool = False  # AI分類をスキップするか
    payment_method: Optional[str] = None  # 支払い方法
