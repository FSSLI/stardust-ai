"""
统一认证模块 — JWT + 匿名 Session 双通道
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.services.user_service import user_service


def create_access_token(user_id: int, email: str) -> str:
    """生成 JWT access token"""
    expire = datetime.utcnow() + timedelta(days=settings.jwt_expire_days)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """解码 JWT token，失败返回 None"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db)
):
    """
    统一认证依赖 — 支持 JWT Bearer Token 和 X-Session-Id 两种方式

    优先级：JWT > Session ID
    两者都没有 → 401
    """
    # 方式 1: JWT Bearer Token
    if authorization:
        token = authorization.replace("Bearer ", "")
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user_id = int(payload["sub"])
            user = await user_service.get_user_by_id(db, user_id)
            if user:
                return user
            raise HTTPException(status_code=401, detail="用户不存在")

    # 方式 2: 匿名 Session ID
    if x_session_id:
        user = await user_service.get_user_by_session(db, x_session_id)
        if user:
            return user
        raise HTTPException(status_code=401, detail="无效的 Session ID")

    # 都没有
    raise HTTPException(status_code=401, detail="请先登录或提供 Session ID")


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db)
):
    """可选认证 — 有认证信息时返回用户，没有时返回 None"""
    if authorization:
        token = authorization.replace("Bearer ", "")
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user_id = int(payload["sub"])
            user = await user_service.get_user_by_id(db, user_id)
            if user:
                return user
    if x_session_id:
        user = await user_service.get_user_by_session(db, x_session_id)
        if user:
            return user
    return None
