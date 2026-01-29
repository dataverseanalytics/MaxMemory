from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Query
from typing import List, Dict, Any
import shutil

from sqlalchemy.orm import Session

from app.schemas.memory import ChatRequest, ChatResponse, DocumentResponse, UploadResponse, MemoriesListResponse
from app.services.file_service import file_service
from app.services.memory_service import memory_service
from app.services.chat_service import chat_service
from app.services.credit_service import credit_service
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.chat import Conversation

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    conversation_id: int = Query(None),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file (PDF, TXT, DOCX), extract text, and ingest into memory.
    
    Query Parameters:
        - project_id: Required
        - conversation_id: Optional - if provided, document is chat-specific
    """
    try:
        # Verify conversation belongs to user and project if provided
        if conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
                Conversation.project_id == project_id
            ).first()
            
            if not conv:
                raise HTTPException(
                    status_code=404, 
                    detail="Conversation not found or doesn't belong to this project"
                )
        
        # Save file
        file_path = await file_service.save_file(file, file.filename)
        
        # Extract text
        text = file_service.extract_text(file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
            
        # Add to memory with conversation_id
        metadata = {
            "source": file.filename, 
            "doc_id": file.filename, 
            "user_id": str(current_user.id),
            "project_id": str(project_id)
        }
        result = memory_service.add_document_memory(
            text, 
            metadata,
            conversation_id=str(conversation_id) if conversation_id else None
        )
        
        return UploadResponse(
            filename=file.filename,
            doc_id=result["doc_id"],
            chunks=result["chunks"],
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(project_id: int, current_user: User = Depends(get_current_user)):
    """
    Get list of ingested documents with memory counts.
    """
    try:
        return memory_service.get_memories_by_document(user_id=str(current_user.id), project_id=str(project_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories", response_model=MemoriesListResponse)
async def get_recent_memories(
    project_id: int, 
    conversation_id: int = Query(None),
    limit: int = 10, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recently added memories with document counts and total memory count.
    
    Query Parameters:
        - project_id: Required
        - conversation_id: Optional - filter by chat
        - limit: Default 10
    
    Returns:
    - total_memory_count: Total number of memories for this user and project
    - document_counts: List of all documents with their memory counts
    - memory_list: Recently added memories (for the dashboard grid)
    """
    try:
        # If conversation_id provided, verify it belongs to user/project
        if conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
                Conversation.project_id == project_id
            ).first()
            
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get total memory count
        total_count = memory_service.get_total_memory_count(
            user_id=str(current_user.id), 
            project_id=str(project_id),
            conversation_id=str(conversation_id) if conversation_id else None
        )
        
        # Get document counts
        document_counts = memory_service.get_memories_by_document(
            user_id=str(current_user.id), 
            project_id=str(project_id),
            conversation_id=str(conversation_id) if conversation_id else None
        )
        
        # Get recent memories
        memory_list = memory_service.get_recent_memories(
            limit=limit, 
            user_id=str(current_user.id), 
            project_id=str(project_id),
            conversation_id=str(conversation_id) if conversation_id else None
        )
        
        return MemoriesListResponse(
            total_memory_count=total_count,
            document_counts=document_counts,
            memory_list=memory_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=List[Dict[str, Any]])
async def search_memories(project_id: int, request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    Search for memories without chatting. Returns memory cards with match scores.
    """
    try:
        return memory_service.query_memories(request.query, user_id=str(current_user.id), project_id=str(project_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(project_id: int, request: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Chat with the memory system using the selected model.
    """
    # 1.5 Check Credits
    if not credit_service.check_balance(current_user.id, db):
        raise HTTPException(
            status_code=402, 
            detail="Insufficient credits. Please top up to continue chatting."
        )

    try:
        # Retrieve relevant memories
        memories = memory_service.query_memories(request.query, user_id=str(current_user.id), project_id=str(project_id))
        
        # Generate response
        response = await chat_service.generate_response(
            request.query, 
            request.model, 
            memories
        )
        
        token_usage = response.get("usage", {})
        
        # Save conversation to memory
        # Run in background to not block response
        # Using background_tasks would be better but we need to change signature
        # For now, just run sync or adding to background_tasks later
        
        # We can just add it here:
        memory_service.add_chat_memory(request.query, response["answer"], user_id=str(current_user.id), project_id=str(project_id))
        
        # Deduct Credits
        credit_service.deduct_credits(current_user.id, token_usage, db)
        
        return ChatResponse(
            answer=response["answer"],
            memories=response["memories_used"]
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/", status_code=204)
async def clear_memory(project_id: int, current_user: User = Depends(get_current_user)):
    """
    Clear all memories and documents.
    """
    try:
        memory_service.clear_all(user_id=str(current_user.id), project_id=str(project_id))
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
