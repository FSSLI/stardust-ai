import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.models import User


class UserService:
    """用户服务"""
    
    @staticmethod
    def generate_session_id() -> str:
        """生成匿名 session_id"""
        return uuid.uuid4().hex[:32]
    
    @staticmethod
    async def get_or_create_user(db: AsyncSession, session_id: str) -> User:
        """
        获取或创建用户
        
        Args:
            db: 数据库会话
            session_id: 用户 session_id
        
        Returns:
            User 对象
        """
        result = await db.execute(
            select(User).where(User.session_id == session_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(session_id=session_id)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_by_session(db: AsyncSession, session_id: str) -> User:
        """通过 session_id 获取用户"""
        result = await db.execute(
            select(User).where(User.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_last_active(db: AsyncSession, user_id: int):
        """更新用户最后活跃时间"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active_at=func.now())
        )
        await db.commit()


# 全局实例
user_service = UserService()