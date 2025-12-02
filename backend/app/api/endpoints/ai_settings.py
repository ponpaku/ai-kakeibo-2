from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.ai_settings import AISettings
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/ai-settings", tags=["AI設定"])


class AISettingsSchema(BaseModel):
    """AI設定のスキーマ"""
    ocr_model: str
    ocr_enabled: bool
    classification_model: str
    classification_enabled: bool
    sandbox_mode: str
    skip_git_repo_check: bool
    ocr_system_prompt: Optional[str] = None
    classification_system_prompt: Optional[str] = None


class AISettingsResponse(BaseModel):
    """AI設定のレスポンス"""
    id: int
    ocr_model: str
    ocr_enabled: bool
    classification_model: str
    classification_enabled: bool
    sandbox_mode: str
    skip_git_repo_check: bool
    ocr_system_prompt: Optional[str]
    classification_system_prompt: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=AISettingsResponse)
def get_ai_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI設定を取得

    管理者のみアクセス可能
    """
    # 管理者チェック
    require_admin(current_user)

    # AI設定を取得
    settings = db.query(AISettings).first()

    if not settings:
        # デフォルト設定を作成
        settings = AISettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.put("/", response_model=AISettingsResponse)
def update_ai_settings(
    settings_data: AISettingsSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI設定を更新

    管理者のみアクセス可能
    """
    # 管理者チェック
    require_admin(current_user)

    # AI設定を取得
    settings = db.query(AISettings).first()

    if not settings:
        # 新規作成
        settings = AISettings(**settings_data.model_dump())
        db.add(settings)
    else:
        # 更新
        for key, value in settings_data.model_dump().items():
            setattr(settings, key, value)

    db.commit()
    db.refresh(settings)

    return settings
