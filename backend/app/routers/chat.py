from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from app.core.database import get_db
from app.schemas.schemas import ChatRequest, ResponseModel
from app.services.user_service import user_service
from app.services.persona_service import persona_service
from app.services.chat_service import chat_service
from app.services.deepseek_service import deepseek_service


router = APIRouter(prefix="/chat", tags=["对话"])


async def get_current_user(
    x_session_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户（通过 session_id）"""
    if not x_session_id:
        raise HTTPException(status_code=401, detail="缺少 Session ID")
    
    user = await user_service.get_user_by_session(db, x_session_id)
    if not user:
        raise HTTPException(status_code=401, detail="无效的 Session ID")
    
    return user


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息，SSE 流式返回
    
    请求头需要携带 X-Session-Id
    """
    # 确定人格
    persona_id = request.persona_id or user.current_persona_id
    persona = await persona_service.get_persona_by_id(db, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="人格不存在")
    
    # 确定对话
    conversation_id = request.conversation_id
    if conversation_id:
        # 验证对话归属
        conversation = await chat_service.get_conversation(
            db, conversation_id, user.id
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        # 创建新对话
        conversation = await chat_service.create_conversation(
            db, user.id, persona_id
        )
        conversation_id = conversation.id
    
    # 保存用户消息
    await chat_service.add_message(
        db, conversation_id, "user", request.message
    )
    
    # 构建上下文
    context_messages = await chat_service.build_context_messages(
        db, conversation_id, request.message
    )
    
    # 构建系统提示词
    system_prompt = persona.system_prompt
    
    async def generate():
        """SSE 流式生成器"""
        full_response = ""
        
        # 发送开始事件
        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        
        try:
            async for chunk in deepseek_service.chat_stream(
                context_messages, system_prompt
            ):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            
            # 保存 AI 回复
            message = await chat_service.add_message(
                db, conversation_id, "assistant", full_response
            )
            
            # 如果是新对话，生成标题
            if not request.conversation_id:
                title = await deepseek_service.generate_title(
                    request.message, full_response
                )
                await chat_service.update_conversation_title(
                    db, conversation_id, title
                )
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done', 'message_id': message.id, 'conversation_id': conversation_id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/conversations")
async def get_conversations(
    page: int = 1,
    page_size: int = 20,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取对话列表"""
    conversations, total = await chat_service.get_conversations(
        db, user.id, page, page_size
    )
    
    return ResponseModel(
        data={
            "items": [
                {
                    "id": c.id,
                    "title": c.title,
                    "persona_id": c.persona_id,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None
                }
                for c in conversations
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取对话详情"""
    conversation = await chat_service.get_conversation(
        db, conversation_id, user.id
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    messages = await chat_service.get_messages(db, conversation_id)
    
    return ResponseModel(
        data={
            "id": conversation.id,
            "title": conversation.title,
            "persona_id": conversation.persona_id,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ]
        }
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除对话"""
    success = await chat_service.delete_conversation(
        db, conversation_id, user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return ResponseModel(message="删除成功")