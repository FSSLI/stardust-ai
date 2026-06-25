from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import ResponseModel
from app.services.user_service import user_service


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/anonymous")
async def create_anonymous_user(db: AsyncSession = Depends(get_db)):
    """
    创建匿名用户
    
    返回 session_id，用于后续所有请求的 X-Session-Id 头
    """
    session_id = user_service.generate_session_id()
    user = await user_service.get_or_create_user(db, session_id)
    
    return ResponseModel(
        data={
            "session_id": user.session_id,
            "user_id": user.id,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    )