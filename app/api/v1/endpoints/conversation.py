from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.chat import Conversation, Message
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate, 
    ConversationResponse, 
    ConversationDetail,
    ChatSessionRequest,
    ChatSessionResponse
)
from app.core.dependencies import get_current_user
from app.services.chat_service import chat_service
from app.services.memory_service import memory_service

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation session"""
    
    # Generate default title if not provided
    title = conv_data.title or "New Conversation"
    if conv_data.initial_message:
        title = conv_data.initial_message[:30] + "..."
        
    conversation = Conversation(
        user_id=current_user.id,
        project_id=conv_data.project_id,
        title=title
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation

@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all conversations for a project"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.project_id == project_id,
        Conversation.is_active == True
    ).order_by(Conversation.updated_at.desc()).all()
    
    return conversations

@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation details and messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    return conversation

@router.post("/{conversation_id}/chat", response_model=ChatSessionResponse)
async def chat_in_conversation(
    conversation_id: int,
    request: ChatSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to a conversation and get response"""
    
    # 1. Verify ownership
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # 1.5 Check Credits
    from app.services.credit_service import credit_service
    if not credit_service.check_balance(current_user.id, db):
        raise HTTPException(
            status_code=402, 
            detail="Insufficient credits. Please top up to continue chatting."
        )

    # 2. Save User Message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.query
    )
    db.add(user_msg)
    
    # Update conversation title if it's the first message and default title
    if conversation.title == "New Conversation":
        conversation.title = request.query[:30] + "..."
        
    db.commit()
    
    # 3. Retrieve Context (RAG) using existing memory service
    memories = memory_service.query_memories(
        query=request.query, 
        user_id=str(current_user.id), 
        project_id=str(conversation.project_id)
    )
    
    # 4. Generate Response
    # We might want to pass recent chat history context here too in future
    response = await chat_service.generate_response(
        request.query,
        request.model,
        memories
    )
    
    answer_text = response["answer"]
    token_usage = response.get("usage", {})
    
    # 5. Save Assistant Message
    bot_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer_text
    )
    db.add(bot_msg)
    
    # Update timestamp
    conversation.updated_at = func.now()
    
    db.commit()
    db.refresh(bot_msg)
    
    # 6. Save Validated Interaction to Memory
    memory_service.add_chat_memory(
        query=request.query, 
        answer=answer_text, 
        user_id=str(current_user.id), 
        project_id=str(conversation.project_id)
    )
    
    # 7. Deduct Credits
    credit_result = credit_service.deduct_credits(current_user.id, token_usage, db)
    
    return ChatSessionResponse(
        answer=answer_text,
        conversation_id=conversation.id,
        message_id=bot_msg.id,
        credit_cost=credit_result.get("cost", 0.0),
        remaining_credits=credit_result.get("balance_remaining", 0.0)
    )

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    db.delete(conversation)
    db.commit()
    return
