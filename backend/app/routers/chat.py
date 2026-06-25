from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.schemas import ChatRequest, EditMessageRequest, ResponseModel
from app.services.user_service import user_service
from app.services.persona_service import persona_service
from app.services.chat_service import chat_service
from app.services.deepseek_service import deepseek_service
from app.services.memory_service import memory_service


router = APIRouter(prefix="/chat", tags=["对话"])


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
    user_message = await chat_service.add_message(
        db, conversation_id, "user", request.message
    )

    # 构建上下文
    context_messages = await chat_service.build_context_messages(
        db, conversation_id, request.message
    )

    # 构建系统提示词（注入记忆）
    memory_context = memory_service.format_memory_context(
        await memory_service.get_latest(db, user.id)
    )
    system_prompt = persona.system_prompt + memory_context

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

            # 发送完成事件（包含用户消息的真实数据库 ID）
            yield f"data: {json.dumps({'type': 'done', 'message_id': message.id, 'user_message_id': user_message.id, 'conversation_id': conversation_id})}\n\n"

            # 检查是否需要生成记忆摘要（流式返回后再处理）
            try:
                if await memory_service.should_summarize(db, user.id):
                    print("[Memory] 触发自动摘要生成...")
                    await memory_service.generate_summary(db, user.id)
            except Exception as e:
                print(f"[Memory] 摘要生成异常: {e}")

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


@router.post("/regenerate/{conversation_id}")
async def regenerate_response(
    conversation_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    基于当前对话自动生成 AI 回复（不添加新的用户消息）
    用于编辑消息后重新生成回复
    """
    conversation = await chat_service.get_conversation(db, conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    persona = await persona_service.get_persona_by_id(db, conversation.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="人格不存在")

    # 获取最近消息作为上下文（最后一条就是刚编辑的用户消息）
    recent = await chat_service.get_recent_messages(db, conversation_id, 10)
    context_messages = [{"role": m.role, "content": m.content} for m in recent]

    # 注入记忆
    memory_context = memory_service.format_memory_context(
        await memory_service.get_latest(db, user.id)
    )
    system_prompt = persona.system_prompt + memory_context

    async def generate():
        full_response = ""
        yield f"data: {json.dumps({'type': 'start'})}\n\n"

        try:
            async for chunk in deepseek_service.chat_stream(context_messages, system_prompt):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

            message = await chat_service.add_message(
                db, conversation_id, "assistant", full_response
            )
            yield f"data: {json.dumps({'type': 'done', 'message_id': message.id, 'conversation_id': conversation_id})}\n\n"

            # 触发记忆摘要
            try:
                if await memory_service.should_summarize(db, user.id):
                    await memory_service.generate_summary(db, user.id)
            except Exception as e:
                print(f"[Memory] {e}")

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


@router.put("/messages/{message_id}")
async def edit_message(
    message_id: int,
    request: EditMessageRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """编辑消息（会删除该消息之后的所有消息，形成对话分支）"""
    # 找到消息所属对话
    from app.models.models import Message
    msg = await db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    # 验证对话归属
    conversation = await chat_service.get_conversation(db, msg.conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    updated = await chat_service.edit_message(
        db, message_id, msg.conversation_id, request.content
    )
    if not updated:
        raise HTTPException(status_code=500, detail="编辑失败")

    return ResponseModel(
        message="消息已更新",
        data={
            "id": updated.id,
            "content": updated.content
        }
    )