from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== 通用响应 ==========
class ResponseModel(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


# ========== 用户相关 ==========
class UserCreate(BaseModel):
    session_id: str


class UserResponse(BaseModel):
    id: int
    session_id: str
    current_persona_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 人格相关 ==========
class PersonaResponse(BaseModel):
    id: int
    name: str
    avatar: Optional[str]
    description: Optional[str]
    is_default: bool
    
    class Config:
        from_attributes = True


class PersonaDetail(PersonaResponse):
    system_prompt: str


class PersonaSwitch(BaseModel):
    persona_id: int


# ========== 对话相关 ==========
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    persona_id: Optional[int] = None
    conversation_id: Optional[int] = None


class ChatStreamEvent(BaseModel):
    type: str  # content / done / error
    content: Optional[str] = None
    message_id: Optional[int] = None
    error: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    persona_id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetail(ConversationResponse):
    messages: List[MessageResponse]


# ========== 手帐相关 ==========
class JournalCreate(BaseModel):
    content: str = Field(..., min_length=1)
    entry_type: str = "note"
    tags: Optional[List[str]] = None
    mood_score: Optional[int] = Field(None, ge=1, le=10)


class JournalResponse(BaseModel):
    id: int
    content: str
    entry_type: str
    tags: Optional[str]
    mood_score: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class JournalUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    mood_score: Optional[int] = Field(None, ge=1, le=10)