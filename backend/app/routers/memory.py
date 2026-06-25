from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.schemas import ResponseModel
from app.services.memory_service import memory_service


router = APIRouter(prefix="/memory", tags=["记忆"])


@router.get("")
async def get_memory(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的记忆摘要"""
    summary = await memory_service.get_latest(db, user.id)

    if not summary:
        return ResponseModel(
            data={
                "has_memory": False,
                "content": None,
                "message_count": 0
            }
        )

    return ResponseModel(
        data={
            "has_memory": True,
            "content": summary.content_json,
            "message_count": summary.message_count,
            "updated_at": summary.updated_at.isoformat() if summary.updated_at else None
        }
    )


@router.post("/summarize")
async def trigger_summarize(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """手动触发记忆摘要生成"""
    # 检查消息量
    from app.models.models import Message, Conversation
    from sqlalchemy import select, func

    result = await db.execute(
        select(func.count())
        .select_from(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user.id)
        .where(Message.role.in_(["user", "assistant"]))
    )
    total = result.scalar() or 0

    if total < 3:
        raise HTTPException(status_code=400, detail="消息太少，至少需要 3 条消息才能生成摘要")

    summary = await memory_service.generate_summary(db, user.id)

    if not summary:
        raise HTTPException(status_code=500, detail="摘要生成失败")

    return ResponseModel(
        message="记忆摘要已更新",
        data={
            "content": summary.content_json,
            "message_count": summary.message_count
        }
    )
