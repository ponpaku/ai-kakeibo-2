from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal
from app.database import get_db
from app.models.user import User
from app.models.expense import Expense
from app.models.category import Category
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["ダッシュボード"])


@router.get("/summary")
def get_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """サマリー情報を取得"""
    # デフォルトは今月
    if not start_date:
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = datetime.now()

    # 総支出
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).scalar() or Decimal(0)

    # 出費件数
    expense_count = db.query(func.count(Expense.id)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).scalar() or 0

    # カテゴリ別集計
    category_breakdown = db.query(
        Category.id,
        Category.name,
        Category.color,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).join(Expense, Expense.category_id == Category.id).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(Category.id, Category.name, Category.color).all()

    # 日別集計（グラフ用）
    daily_expenses = db.query(
        func.date(Expense.expense_date).label('date'),
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(func.date(Expense.expense_date)).order_by('date').all()

    # 前月比較
    prev_month_start = (start_date - timedelta(days=30)).replace(day=1)
    prev_month_end = start_date - timedelta(days=1)
    prev_month_total = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= prev_month_start,
        Expense.expense_date <= prev_month_end
    ).scalar() or Decimal(0)

    change_from_prev = float(total_expenses) - float(prev_month_total)
    change_percent = (change_from_prev / float(prev_month_total) * 100) if prev_month_total > 0 else 0

    return {
        "total_expenses": float(total_expenses),
        "expense_count": expense_count,
        "average_expense": float(total_expenses / expense_count) if expense_count > 0 else 0,
        "category_breakdown": [
            {
                "category_id": cat.id,
                "category_name": cat.name,
                "color": cat.color,
                "total": float(cat.total),
                "count": cat.count,
                "percentage": float(cat.total / total_expenses * 100) if total_expenses > 0 else 0
            }
            for cat in category_breakdown
        ],
        "daily_expenses": [
            {
                "date": str(day.date),
                "total": float(day.total)
            }
            for day in daily_expenses
        ],
        "comparison": {
            "previous_month_total": float(prev_month_total),
            "change_amount": change_from_prev,
            "change_percent": change_percent
        },
        "period": {
            "start_date": str(start_date),
            "end_date": str(end_date)
        }
    }


@router.get("/recent-expenses")
def get_recent_expenses(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """最近の出費を取得"""
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.expense_date.desc()).limit(limit).all()

    result = []
    for expense in expenses:
        category_name = None
        if expense.category_id:
            category = db.query(Category).filter(Category.id == expense.category_id).first()
            if category:
                category_name = category.name

        result.append({
            "id": expense.id,
            "amount": float(expense.amount),
            "expense_date": expense.expense_date,
            "store_name": expense.store_name,
            "description": expense.description,
            "category_name": category_name,
            "status": expense.status
        })

    return result
