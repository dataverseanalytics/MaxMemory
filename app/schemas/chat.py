from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    project_id: int
    initial_message: Optional[str] = None # Optional: Start with a message

class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ConversationDetail(ConversationResponse):
    messages: List[MessageResponse] = []

class ChatSessionRequest(BaseModel):
    query: str
    model: str = "gpt-4o-mini"
    
class ChatSessionResponse(BaseModel):
    answer: str
    conversation_id: int
    message_id: int
    credit_cost: Optional[float] = 0.0
    remaining_credits: Optional[float] = 0.0
