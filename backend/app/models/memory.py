from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class MemorySummary(Base):
    """长期记忆摘要表"""
    __tablename__ = "memory_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content_json = Column(Text, nullable=False)  # JSON 格式: {basic_info, preferences, recent_status, plans}
    last_message_id = Column(Integer, nullable=True)  # 最后处理到的 message ID
    message_count = Column(Integer, default=0)  # 处理时的总消息数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
