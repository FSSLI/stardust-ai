from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from app.models.models import Conversation, Message, User
from app.services.deepseek_service import deepseek_service


class ChatService:
    """对话服务"""
    
    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: int,
        persona_id: int,
        title: str = "新对话"
    ) -> Conversation:
        """创建新对话"""
        conversation = Conversation(
            user_id=user_id,
            persona_id=persona_id,
            title=title
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation
    
    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int
    ) -> Optional[Conversation]:
        """获取用户指定对话"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_conversations(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Conversation], int]:
        """获取用户对话列表"""
        # 总数
        count_result = await db.execute(
            select(func.count()).select_from(Conversation)
            .where(Conversation.user_id == user_id)
        )
        total = count_result.scalar()
        
        # 分页查询
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total
    
    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: int,
        limit: int = 100
    ) -> List[Message]:
        """获取对话消息"""
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_recent_messages(
        db: AsyncSession,
        conversation_id: int,
        limit: int = 10
    ) -> List[Message]:
        """获取最近 N 条消息（用于上下文）"""
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.role.in_(["user", "assistant"]))
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = result.scalars().all()
        # 按时间正序返回
        return list(reversed(messages))
    
    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: int,
        role: str,
        content: str
    ) -> Message:
        """添加消息"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message
    
    @staticmethod
    async def update_conversation_title(
        db: AsyncSession,
        conversation_id: int,
        title: str
    ):
        """更新对话标题"""
        conversation = await db.get(Conversation, conversation_id)
        if conversation:
            conversation.title = title
            await db.commit()
    
    @staticmethod
    async def edit_message(
        db: AsyncSession,
        message_id: int,
        conversation_id: int,
        new_content: str
    ) -> Optional[Message]:
        """编辑消息并删除该消息之后的所有消息（实现对话分支）"""
        # 获取要编辑的消息
        message = await db.get(Message, message_id)
        if not message or message.conversation_id != conversation_id:
            return None

        # 更新内容
        message.content = new_content

        # 删除该消息之后的所有消息
        await db.execute(
            Message.__table__.delete()
            .where(Message.conversation_id == conversation_id)
            .where(Message.id > message_id)
        )

        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """删除对话"""
        conversation = await ChatService.get_conversation(
            db, conversation_id, user_id
        )
        if not conversation:
            return False
        
        # 级联删除消息
        await db.execute(
            Message.__table__.delete()
            .where(Message.conversation_id == conversation_id)
        )
        await db.delete(conversation)
        await db.commit()
        return True
    
    @staticmethod
    async def build_context_messages(
        db: AsyncSession,
        conversation_id: int,
        new_message: str,
        limit: int = 10
    ) -> List[dict]:
        """
        构建上下文消息列表，用于调用 DeepSeek
        
        Returns:
            [{"role": "user", "content": "..."}, ...]
        """
        # 获取历史消息
        messages = await ChatService.get_recent_messages(
            db, conversation_id, limit
        )
        
        # 构建上下文
        context = []
        for msg in messages:
            context.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 添加当前消息
        context.append({
            "role": "user",
            "content": new_message
        })
        
        return context


# 全局实例
chat_service = ChatService()