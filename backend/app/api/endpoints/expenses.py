from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.expense import Expense, ExpenseStatus
from app.models.expense_item import ExpenseItem, CategorySource
from app.models.category import Category
from app.schemas.expense import (
    Expense as ExpenseSchema,
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseWithReceipt,
    ExpenseListResponse,
    ManualExpenseCreate,
    ExpenseItemWithCategory
)
from app.api.deps import get_current_user
from app.tasks.ai_tasks import classify_expense_task, classify_expense_item_task

router = APIRouter(prefix="/expenses", tags=["出費管理"])


@router.get("/", response_model=ExpenseListResponse)
def list_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category_id: Optional[int] = None,
    status: Optional[ExpenseStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """出費一覧を取得"""
    query = db.query(Expense).filter(Expense.user_id == current_user.id)

    if start_date:
        query = query.filter(Expense.occurred_at >= start_date)
    if end_date:
        query = query.filter(Expense.occurred_at <= end_date)
    if status:
        query = query.filter(Expense.status == status)

    # カテゴリIDでフィルタする場合、ExpenseItemsを介してフィルタ
    if category_id:
        query = query.join(ExpenseItem).filter(ExpenseItem.category_id == category_id)

    total = query.count()
    expenses = query.options(joinedload(Expense.items), joinedload(Expense.receipt))\
                    .order_by(Expense.occurred_at.desc())\
                    .offset(skip)\
                    .limit(limit)\
                    .all()

    # カテゴリIDのマップを一括取得（N+1問題の回避）
    all_category_ids = set()
    for expense in expenses:
        for item in expense.items:
            if item.category_id:
                all_category_ids.add(item.category_id)

    category_map = {}
    if all_category_ids:
        categories = db.query(Category).filter(Category.id.in_(all_category_ids)).all()
        category_map = {cat.id: cat.name for cat in categories}

    # ExpenseItemsにカテゴリ名を付与
    result_expenses = []
    for expense in expenses:
        expense_dict = ExpenseWithReceipt.model_validate(expense)

        # ItemsにCategory名を付与
        items_with_category = []
        for item in expense.items:
            item_dict = ExpenseItemWithCategory.model_validate(item)
            if item.category_id and item.category_id in category_map:
                item_dict.category_name = category_map[item.category_id]
            items_with_category.append(item_dict)

        expense_dict.items = items_with_category
        result_expenses.append(expense_dict)

    return ExpenseListResponse(total=total, expenses=result_expenses)


@router.get("/{expense_id}", response_model=ExpenseWithReceipt)
def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """出費詳細を取得"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).options(joinedload(Expense.items), joinedload(Expense.receipt)).first()

    if not expense:
        raise HTTPException(status_code=404, detail="出費が見つかりません")

    expense_dict = ExpenseWithReceipt.model_validate(expense)

    # カテゴリIDのマップを一括取得（N+1問題の回避）
    category_ids = {item.category_id for item in expense.items if item.category_id}
    category_map = {}
    if category_ids:
        categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
        category_map = {cat.id: cat.name for cat in categories}

    # ItemsにCategory名を付与
    items_with_category = []
    for item in expense.items:
        item_dict = ExpenseItemWithCategory.model_validate(item)
        if item.category_id and item.category_id in category_map:
            item_dict.category_name = category_map[item.category_id]
        items_with_category.append(item_dict)

    expense_dict.items = items_with_category
    return expense_dict


@router.post("/manual", response_model=ExpenseSchema)
def create_manual_expense(
    expense_in: ManualExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手入力で出費を登録（ExpenseItem自動作成）"""
    # ステータスを事前に決定
    if expense_in.category_id or expense_in.skip_ai_classification:
        initial_status = ExpenseStatus.COMPLETED
    else:
        initial_status = ExpenseStatus.PROCESSING

    # Expense（決済ヘッダ）作成
    expense = Expense(
        user_id=current_user.id,
        occurred_at=expense_in.occurred_at,
        merchant_name=expense_in.merchant_name,
        title=expense_in.merchant_name or expense_in.product_name or "手入力",
        total_amount=expense_in.total_amount,
        payment_method=expense_in.payment_method,
        description=expense_in.description,
        note=expense_in.note,
        status=initial_status
    )

    db.add(expense)
    db.flush()  # IDを取得

    # ExpenseItem作成（最低1つ）
    product_name = expense_in.product_name or expense_in.note or expense_in.merchant_name or "購入品"
    expense_item = ExpenseItem(
        expense_id=expense.id,
        position=0,
        product_name=product_name,
        line_total=expense_in.total_amount,
        category_id=expense_in.category_id,
        category_source=CategorySource.MANUAL if expense_in.category_id else None
    )
    db.add(expense_item)
    db.commit()
    db.refresh(expense)

    # AI分類が必要な場合のみタスク起動
    if initial_status == ExpenseStatus.PROCESSING:
        classify_expense_item_task.delay(expense_item.id)

    return expense


@router.put("/{expense_id}", response_model=ExpenseSchema)
def update_expense(
    expense_id: int,
    expense_in: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """出費情報を更新"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="出費が見つかりません")

    update_data = expense_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """出費を削除"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="出費が見つかりません")

    # レシート画像も削除
    if expense.receipt:
        from app.services.image_service import ImageService
        ImageService.delete_image(ImageService.get_full_path(expense.receipt.file_path))

    # ExpenseItemsもカスケード削除される
    db.delete(expense)
    db.commit()
    return {"message": "出費を削除しました"}


@router.post("/{expense_id}/reclassify")
def reclassify_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """出費のExpenseItemsを再分類"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="出費が見つかりません")

    # 全ExpenseItemsを再分類
    items = db.query(ExpenseItem).filter(ExpenseItem.expense_id == expense_id).all()

    if not items:
        return {"message": "再分類する商品がありません"}

    # 各ItemのAI分類タスクを起動
    for item in items:
        # カテゴリをクリアしてAI分類対象にする
        item.category_id = None
        item.category_source = None
        item.ai_confidence = None
        classify_expense_item_task.delay(item.id)

    expense.status = ExpenseStatus.PROCESSING
    db.commit()

    return {"message": f"{len(items)}個の商品の再分類を開始しました"}
