from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """現在のユーザーを取得"""
    print(f"🔑 Authenticating with token (first 30 chars): {token[:30]}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証に失敗しました",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        print(f"❌ Token decode failed - invalid or expired token")
        raise credentials_exception

    print(f"✅ Token decoded successfully: {payload}")

    user_id: int = payload.get("sub")
    if user_id is None:
        print(f"❌ 'sub' field missing from token payload")
        raise credentials_exception

    print(f"👤 Looking up user with ID: {user_id}")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"❌ User not found with ID: {user_id}")
        raise credentials_exception

    if not user.is_active:
        print(f"❌ User {user.username} is inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ユーザーが無効化されています"
        )

    print(f"✅ User authenticated: {user.username} (ID: {user.id})")
    return user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """管理者権限を確認"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user
