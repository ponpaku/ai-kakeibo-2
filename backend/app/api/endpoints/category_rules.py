from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db, require_admin
from app.models.category_rule import CategoryRule, MatchType
from app.models.category import Category
from app.models.user import User
from app.services.category_rule_service import CategoryRuleService

router = APIRouter(prefix="/category-rules", tags=["分類ルール"])


class CategoryRuleBase(BaseModel):
    name: Optional[str] = None
    pattern: str = Field(..., max_length=500)
    match_type: MatchType = MatchType.CONTAINS
    category_id: int
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    priority: int = Field(100, ge=0)
    is_active: bool = True


class CategoryRuleCreate(CategoryRuleBase):
    pass


class CategoryRuleUpdate(BaseModel):
    name: Optional[str] = None
    pattern: Optional[str] = Field(None, max_length=500)
    match_type: Optional[MatchType] = None
    category_id: Optional[int] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryRuleResponse(CategoryRuleBase):
    id: int

    class Config:
        from_attributes = True


class CategoryRuleTestRequest(BaseModel):
    text: str = Field(..., min_length=1)


class CategoryRuleTestResponse(BaseModel):
    matched: bool
    rule: Optional[CategoryRuleResponse] = None
    category_name: Optional[str] = None


@router.get("/", response_model=List[CategoryRuleResponse])
def list_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)
    rules = (
        db.query(CategoryRule)
        .order_by(CategoryRule.priority.asc(), CategoryRule.id.asc())
        .all()
    )
    return rules


@router.post("/", response_model=CategoryRuleResponse)
def create_rule(
    rule_in: CategoryRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)
    _validate_rule(db, rule_in.pattern, rule_in.match_type, rule_in.category_id)

    rule = CategoryRule(**rule_in.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=CategoryRuleResponse)
@router.patch("/{rule_id}", response_model=CategoryRuleResponse)
def update_rule(
    rule_id: int,
    rule_in: CategoryRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)
    rule = db.query(CategoryRule).filter(CategoryRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="ルールが見つかりません")

    update_data = rule_in.model_dump(exclude_unset=True)
    if "pattern" in update_data or "match_type" in update_data:
        _validate_rule(
            db,
            update_data.get("pattern", rule.pattern),
            update_data.get("match_type", rule.match_type),
            update_data.get("category_id", rule.category_id),
        )

    for key, value in update_data.items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)
    rule = db.query(CategoryRule).filter(CategoryRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="ルールが見つかりません")

    db.delete(rule)
    db.commit()
    return {"message": "ルールを削除しました"}


@router.post("/test", response_model=CategoryRuleTestResponse)
def test_rule(
    payload: CategoryRuleTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)
    matched_rule = CategoryRuleService.test_rule(db, payload.text)

    if not matched_rule:
        return CategoryRuleTestResponse(matched=False)

    category = db.query(Category).filter(Category.id == matched_rule.category_id).first()
    category_name = category.name if category else None
    return CategoryRuleTestResponse(
        matched=True,
        rule=CategoryRuleResponse.model_validate(matched_rule),
        category_name=category_name,
    )


def _validate_rule(db: Session, pattern: str, match_type: MatchType, category_id: int) -> None:
    if match_type == MatchType.REGEX:
        try:
            CategoryRuleService.validate_regex(pattern)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    category_exists = db.query(Category).filter(Category.id == category_id).first()
    if not category_exists:
        raise HTTPException(status_code=400, detail="指定したカテゴリが存在しません")
