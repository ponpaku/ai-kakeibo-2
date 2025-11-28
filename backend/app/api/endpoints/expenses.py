from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.expense import Expense, ExpenseStatus
from app.models.category import Category
from app.schemas.expense import (
    Expense as ExpenseSchema,
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseWithReceipt,
    ExpenseListResponse,
    ManualExpenseCreate
)
from app.api.deps import get_current_user
from app.tasks.ai_tasks import classify_expense_task

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
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if status:
        query = query.filter(Expense.status == status)

    total = query.count()
    expenses = query.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()

    # カテゴリ名を付与
    result_expenses = []
    for expense in expenses:
        expense_dict = ExpenseWithReceipt.model_validate(expense)
        if expense.category_id:
            category = db.query(Category).filter(Category.id == expense.category_id).first()
            if category:
                expense_dict.category_name = category.name
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
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="出費が見つかりません")

    expense_dict = ExpenseWithReceipt.model_validate(expense)
    if expense.category_id:
        category = db.query(Category).filter(Category.id == expense.category_id).first()
        if category:
            expense_dict.category_name = category.name

    return expense_dict


@router.post("/manual", response_model=ExpenseSchema)
def create_manual_expense(
    expense_in: ManualExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手入力で出費を登録"""
    expense = Expense(
        user_id=current_user.id,
        amount=expense_in.amount,
        expense_date=expense_in.expense_date,
        store_name=expense_in.store_name,
        description=expense_in.description,
        note=expense_in.note,
        category_id=expense_in.category_id,
        status=ExpenseStatus.PENDING
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    # AI分類を実行（カテゴリが指定されていない、かつスキップフラグがFalseの場合）
    if not expense_in.category_id and not expense_in.skip_ai_classification:
        classify_expense_task.delay(expense.id)
    elif expense_in.category_id:
        expense.status = ExpenseStatus.COMPLETED
        db.commit()
        db.refresh(expense)

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

    db.delete(expense)
    db.commit()
    return {"message": "出費を削除しました"}


@router.post("/{expense_id}/reclassify")
def reclassify_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """出費を再分類"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="出費が見つかりません")

    # AI分類タスクを実行
    classify_expense_task.delay(expense.id)

    return {"message": "再分類を開始しました"}
