from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードの検証"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """パスワードのハッシュ化"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """アクセストークンの作成"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    print(f"🔨 Creating token with:")
    print(f"   - Data: {to_encode}")
    print(f"   - SECRET_KEY (first 20 chars): {settings.SECRET_KEY[:20]}...")
    print(f"   - Algorithm: {settings.ALGORITHM}")

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """アクセストークンのデコード"""
    try:
        print(f"🔍 Decoding token with:")
        print(f"   - SECRET_KEY (first 20 chars): {settings.SECRET_KEY[:20]}...")
        print(f"   - Algorithm: {settings.ALGORITHM}")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"   ✅ Decode successful: {payload}")
        return payload
    except JWTError as e:
        print(f"   ❌ JWT Decode Error: {type(e).__name__}: {str(e)}")
        print(f"   - Token (first 50 chars): {token[:50]}...")
        print(f"   - SECRET_KEY being used (first 20 chars): {settings.SECRET_KEY[:20]}...")
        return None
