from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal
from app.database import get_db
from app.models.user import User
from app.models.expense import Expense
from app.models.expense_item import ExpenseItem
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
    """サマリー情報を取得（ExpenseItemベース集計）"""
    # デフォルトは今月
    if not start_date:
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = datetime.now()

    # 総支出（ExpenseItemの合計）
    total_expenses = db.query(func.sum(ExpenseItem.line_total)).join(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.occurred_at >= start_date,
        Expense.occurred_at <= end_date
    ).scalar() or 0

    # 出費件数（Expenseの件数）
    expense_count = db.query(func.count(Expense.id)).filter(
        Expense.user_id == current_user.id,
        Expense.occurred_at >= start_date,
        Expense.occurred_at <= end_date
    ).scalar() or 0

    # 商品明細数
    item_count = db.query(func.count(ExpenseItem.id)).join(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.occurred_at >= start_date,
        Expense.occurred_at <= end_date
    ).scalar() or 0

    # カテゴリ別集計（ExpenseItemベース）
    category_breakdown = db.query(
        Category.id,
        Category.name,
        Category.color,
        func.sum(ExpenseItem.line_total).label('total'),
        func.count(ExpenseItem.id).label('count')
    ).join(ExpenseItem, ExpenseItem.category_id == Category.id)\
     .join(Expense, ExpenseItem.expense_id == Expense.id)\
     .filter(
        Expense.user_id == current_user.id,
        Expense.occurred_at >= start_date,
        Expense.occurred_at <= end_date
    ).group_by(Category.id, Category.name, Category.color).all()

    # 日別集計（グラフ用）- Expenseの日付で、ExpenseItemの合計を集計
    daily_expenses = db.query(
        func.date(Expense.occurred_at).label('date'),
        func.sum(ExpenseItem.line_total).label('total')
    ).join(ExpenseItem, ExpenseItem.expense_id == Expense.id)\
     .filter(
        Expense.user_id == current_user.id,
        Expense.occurred_at >= start_date,
        Expense.occurred_at <= end_date
    ).group_by(func.date(Expense.occurred_at)).order_by('date').all()

    # 前月比較
    prev_month_start = (start_date - timedelta(days=30)).replace(day=1)
    prev_month_end = start_date - timedelta(days=1)
    prev_month_total = db.query(func.sum(ExpenseItem.line_total)).join(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.occurred_at >= prev_month_start,
        Expense.occurred_at <= prev_month_end
    ).scalar() or 0

    change_from_prev = float(total_expenses) - float(prev_month_total)
    change_percent = (change_from_prev / float(prev_month_total) * 100) if prev_month_total > 0 else 0

    return {
        "total_expenses": float(total_expenses),
        "expense_count": expense_count,
        "item_count": item_count,
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
    ).options(joinedload(Expense.items), joinedload(Expense.receipt))\
     .order_by(Expense.occurred_at.desc())\
     .limit(limit)\
     .all()

    # 全カテゴリIDのマップを一括取得（N+1問題の回避）
    category_ids = set()
    for expense in expenses:
        for item in expense.items:
            if item.category_id:
                category_ids.add(item.category_id)

    category_map = {}
    if category_ids:
        categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
        category_map = {cat.id: cat.name for cat in categories}

    result = []
    for expense in expenses:
        # ExpenseItemsを全てカテゴリ名付きで返す
        items_with_category = []
        for item in expense.items:
            items_with_category.append({
                "id": item.id,
                "expense_id": item.expense_id,
                "position": item.position,
                "product_name": item.product_name,
                "quantity": float(item.quantity) if item.quantity else None,
                "unit_price": item.unit_price,
                "line_total": item.line_total,
                "category_id": item.category_id,
                "category_source": item.category_source.value if item.category_source else None,
                "ai_confidence": float(item.ai_confidence) if item.ai_confidence else None,
                "category_name": category_map.get(item.category_id) if item.category_id else None
            })

        result.append({
            "id": expense.id,
            "user_id": expense.user_id,
            "total_amount": float(expense.total_amount),
            "occurred_at": expense.occurred_at,
            "merchant_name": expense.merchant_name,
            "title": expense.title,
            "description": expense.description,
            "note": expense.note,
            "currency": expense.currency,
            "payment_method": expense.payment_method,
            "status": expense.status.value if hasattr(expense.status, 'value') else expense.status,
            "created_at": expense.created_at,
            "updated_at": expense.updated_at,
            "items": items_with_category,
            "receipt": {"id": expense.receipt.id, "file_path": expense.receipt.file_path} if expense.receipt else None
        })

    return result
