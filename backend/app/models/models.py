from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    current_persona_id = Column(Integer, default=1)


class Persona(Base):
    """人格表"""
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    avatar = Column(String(255))
    system_prompt = Column(Text, nullable=False)
    description = Column(String(255))
    is_default = Column(Boolean, default=False)
    is_system = Column(Boolean, default=True)  # 系统预设 vs 用户定制
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL=系统, 非NULL=用户定制
    config_json = Column(Text)  # JSON 配置


class Conversation(Base):
    """对话表"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False)
    title = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_created", "created_at"),
    )


class JournalEntry(Base):
    """手帐记录表"""
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_type = Column(String(20), default="note")  # note / todo / mood / memory
    content = Column(Text, nullable=False)
    tags = Column(String(255))
    mood_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_journal_user", "user_id"),
        Index("idx_journal_created", "created_at"),
    )