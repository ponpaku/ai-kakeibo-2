from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.security import verify_password, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["認証"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = Query(default=False, description="ログイン状態を保存するかどうか"),
    db: Session = Depends(get_db)
):
    """ログイン"""
    print(f"🔐 Login attempt for username: {form_data.username}, remember_me: {remember_me}")
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        print(f"❌ Login failed: Invalid credentials for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        print(f"❌ Login failed: User {form_data.username} is inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ユーザーが無効化されています"
        )

    # remember_meの設定に基づいてトークン有効期限を決定
    if remember_me:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER
        print(f"📌 Remember me enabled: token expires in {expire_minutes} minutes (30 days)")
    else:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        print(f"⏰ Normal login: token expires in {expire_minutes} minutes (1 day)")
    
    access_token_expires = timedelta(minutes=expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires  # JWT仕様: subは文字列
    )

    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin
        }
    }

    print(f"✅ Login successful for user: {user.username} (ID: {user.id})")
    print(f"🎫 Token generated (first 30 chars): {access_token[:30]}...")
    print(f"📤 Response data: {response_data}")

    return response_data
