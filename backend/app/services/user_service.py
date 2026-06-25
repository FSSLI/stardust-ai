import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, delete
from typing import Optional, Tuple
from passlib.context import CryptContext
from app.models.models import User, Message, Conversation, JournalEntry

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """用户服务"""

    @staticmethod
    def hash_password(password: str) -> str:
        """bcrypt 哈希密码"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_session_id() -> str:
        """生成匿名 session_id"""
        return uuid.uuid4().hex[:32]

    @staticmethod
    async def get_or_create_user(db: AsyncSession, session_id: str) -> User:
        """
        获取或创建匿名用户

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
    async def get_user_by_session(db: AsyncSession, session_id: str) -> Optional[User]:
        """通过 session_id 获取用户"""
        result = await db.execute(
            select(User).where(User.session_id == session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """通过 id 获取用户"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """通过 email 获取用户"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def register_user(db: AsyncSession, email: str, password: str) -> Tuple[User, Optional[str]]:
        """
        注册新用户

        Returns:
            (user, error_message) — error_message 为 None 表示成功
        """
        # 检查邮箱是否已注册
        existing = await UserService.get_user_by_email(db, email)
        if existing:
            return None, "该邮箱已被注册"

        user = User(
            email=email,
            password_hash=UserService.hash_password(password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user, None

    @staticmethod
    async def login_user(db: AsyncSession, email: str, password: str) -> Tuple[User, Optional[str]]:
        """
        登录验证

        Returns:
            (user, error_message) — error_message 为 None 表示成功
        """
        user = await UserService.get_user_by_email(db, email)
        if not user:
            return None, "邮箱未注册"
        if not user.password_hash:
            return None, "该账号为匿名账号，请使用匿名登录"

        if not UserService.verify_password(password, user.password_hash):
            return None, "密码错误"

        return user, None

    @staticmethod
    async def update_last_active(db: AsyncSession, user_id: int):
        """更新用户最后活跃时间"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active_at=func.now())
        )
        await db.commit()

    @staticmethod
    async def delete_anonymous_user(db: AsyncSession, user_id: int) -> bool:
        """
        级联删除匿名用户及其所有数据
        仅对匿名用户（无邮箱）生效，注册用户不会被删除

        Returns:
            是否成功删除
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user or user.email:
            # 注册用户不删除
            return False

        # 1. 删除该用户所有对话中的消息
        conversation_ids = await db.execute(
            select(Conversation.id).where(Conversation.user_id == user_id)
        )
        conv_ids = [row[0] for row in conversation_ids.all()]
        if conv_ids:
            await db.execute(
                delete(Message).where(Message.conversation_id.in_(conv_ids))
            )

        # 2. 删除对话
        await db.execute(
            delete(Conversation).where(Conversation.user_id == user_id)
        )

        # 3. 删除手帐记录
        await db.execute(
            delete(JournalEntry).where(JournalEntry.user_id == user_id)
        )

        # 4. 删除用户
        await db.execute(
            delete(User).where(User.id == user_id)
        )

        await db.commit()
        return True


    @staticmethod
    async def cleanup_abandoned_anonymous(db: AsyncSession, hours: int = 24) -> int:
        """
        清理超过指定小时未活跃的匿名用户及其所有数据

        Returns:
            清理的用户数量
        """
        from datetime import datetime, timedelta
        from app.models.models import Message, Conversation, JournalEntry
        from app.models.memory import MemorySummary

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # 找到超时的匿名用户
        result = await db.execute(
            select(User).where(
                User.email == None,
                User.last_active_at < cutoff
            )
        )
        users = result.scalars().all()

        count = 0
        for user in users:
            # 级联删除
            conv_ids = await db.execute(
                select(Conversation.id).where(Conversation.user_id == user.id)
            )
            cids = [r[0] for r in conv_ids.all()]
            if cids:
                await db.execute(delete(Message).where(Message.conversation_id.in_(cids)))
            await db.execute(delete(Conversation).where(Conversation.user_id == user.id))
            await db.execute(delete(JournalEntry).where(JournalEntry.user_id == user.id))
            await db.execute(delete(MemorySummary).where(MemorySummary.user_id == user.id))
            await db.execute(delete(User).where(User.id == user.id))
            count += 1

        if count > 0:
            await db.commit()
        return count


# 全局实例
user_service = UserService()