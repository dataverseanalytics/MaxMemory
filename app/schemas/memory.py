
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    query: str
    model: str = "gpt-4o-mini"

class ChatResponse(BaseModel):
    answer: str
    memories_used: List[Dict[str, Any]]

class DocumentResponse(BaseModel):
    doc_id: str
    source: str
    memory_count: int
    preview: str

class UploadResponse(BaseModel):
    filename: str
    doc_id: str
    chunks: int
    status: str
