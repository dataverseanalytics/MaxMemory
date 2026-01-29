# Chat-Specific Document Upload Implementation

## Overview
This guide shows how to implement document uploads that are scoped to a **specific chat conversation** instead of just the project level.

---

## Current Issue
Currently, documents are uploaded at **project-level**:
```
POST /memory/upload?project_id=1
→ All chats in project 1 can access this document
```

## Solution
Allow documents to be uploaded at **chat-level** (conversation-specific):
```
POST /memory/upload?project_id=1&conversation_id=100
→ Only chat 100 can access this document
→ Other chats in project 1 cannot access it
```

---

## Implementation Steps

### Step 1: Update Memory Service Method

**File**: `app/services/memory_service.py`

Add a parameter to `add_document_memory()` to accept `conversation_id`:

```python
def add_document_memory(
    self, 
    text: str, 
    metadata: dict,
    conversation_id: str = None  # NEW PARAMETER
) -> Dict[str, Any]:
    """
    Add document chunks to memory system.
    
    Args:
        text: Document text to chunk
        metadata: Dict with user_id, project_id, source, doc_id
        conversation_id: Optional - if provided, memory is chat-specific
    
    Returns:
        doc_id and chunks count
    """
    chunks = self._chunk_text(text)
    
    with self.driver.session() as session:
        # Create Document node
        result = session.run("""
            CREATE (d:Document {
                id: $doc_id,
                source: $source,
                user_id: $user_id,
                project_id: $project_id,
                conversation_id: $conversation_id,
                timestamp: datetime()
            })
            RETURN d.id as doc_id
        """, 
        doc_id=metadata.get("doc_id"),
        source=metadata.get("source"),
        user_id=metadata.get("user_id"),
        project_id=metadata.get("project_id"),
        conversation_id=conversation_id  # NEW: Pass conversation_id
        )
        
        doc_id = result.single()["doc_id"]
        
        # Create Memory nodes for each chunk
        for idx, chunk in enumerate(chunks):
            session.run("""
                MATCH (d:Document {id: $doc_id})
                CREATE (m:Memory {
                    id: randomUUID(),
                    text: $text,
                    user_id: $user_id,
                    project_id: $project_id,
                    conversation_id: $conversation_id,
                    source: $source,
                    chunk_index: $chunk_index,
                    timestamp: datetime()
                })
                CREATE (d)-[:CONTAINS]->(m)
            """,
            doc_id=doc_id,
            text=chunk,
            user_id=metadata.get("user_id"),
            project_id=metadata.get("project_id"),
            conversation_id=conversation_id,  # NEW: Tag memory with conversation
            source=metadata.get("source"),
            chunk_index=idx
            )
    
    return {
        "doc_id": doc_id,
        "chunks": len(chunks)
    }
```

---

### Step 2: Update Upload Endpoint

**File**: `app/api/v1/endpoints/memory.py`

Add a new endpoint for chat-specific uploads:

```python
@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    conversation_id: int = None,  # NEW PARAMETER
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file to project (project-level) or specific chat (conversation-level).
    
    Query Parameters:
        - project_id: Required
        - conversation_id: Optional - if provided, document is chat-specific
    """
    try:
        # Verify conversation belongs to user and project
        if conversation_id:
            db = next(get_db())
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
            conversation_id=str(conversation_id) if conversation_id else None  # NEW
        )
        
        return UploadResponse(
            filename=file.filename,
            doc_id=result["doc_id"],
            chunks=result["chunks"],
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**API Usage:**

**Project-level upload (all chats can access):**
```bash
POST /memory/upload?project_id=1
[File: document.pdf]
```

**Chat-specific upload (only this chat can access):**
```bash
POST /memory/upload?project_id=1&conversation_id=100
[File: document.pdf]
```

---

### Step 3: Update Memory Query Filtering

**File**: `app/services/memory_service.py`

Modify `query_memories()` to filter by conversation:

```python
def query_memories(
    self, 
    query: str, 
    user_id: str, 
    project_id: str,
    conversation_id: str = None  # NEW PARAMETER
) -> List[Dict]:
    """
    Query memories relevant to user's question.
    
    Retrieves:
    - Project-level memories (all chats can use)
    - Chat-specific memories (only this chat can use)
    """
    if not self.vector_store:
        return []
    
    # Search FAISS index with metadata filter
    if conversation_id:
        # Get memories for this specific chat + project-level memories
        results = self.vector_store.similarity_search_with_score(
            query, 
            k=5,
            filter={
                "user_id": user_id,
                "project_id": project_id,
                # Match: conversation_id matches OR conversation_id is None (project-level)
                "$or": [
                    {"conversation_id": conversation_id},
                    {"conversation_id": None}
                ]
            }
        )
    else:
        # Get only project-level memories (no specific chat)
        results = self.vector_store.similarity_search_with_score(
            query, 
            k=5,
            filter={
                "user_id": user_id,
                "project_id": project_id,
                "conversation_id": None  # Only project-level
            }
        )
    
    memories = []
    for doc, score in results:
        memories.append({
            "text": doc.page_content,
            "source": doc.metadata.get("source"),
            "score": score,
            "match_percentage": min(100, int((1 - score) * 100))
        })
    
    return memories
```

---

### Step 4: Update Chat Message Endpoint

**File**: `app/api/v1/endpoints/conversation.py`

Pass `conversation_id` when querying memories:

```python
@router.post("/{conversation_id}/chat", response_model=ChatSessionResponse)
async def chat_in_conversation(
    conversation_id: int,
    request: ChatSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to a conversation and get response"""
    
    # Verify ownership
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check credits
    if not credit_service.check_balance(current_user.id, db):
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.query
    )
    db.add(user_msg)
    
    # Update conversation title
    if conversation.title == "New Conversation":
        conversation.title = request.query[:30] + "..."
    
    db.commit()
    
    # Retrieve memories - NOW WITH CONVERSATION FILTER
    memories = memory_service.query_memories(
        query=request.query, 
        user_id=str(current_user.id), 
        project_id=str(conversation.project_id),
        conversation_id=str(conversation_id)  # NEW: Pass conversation_id
    )
    
    # Generate response
    response = await chat_service.generate_response(
        request.query,
        request.model,
        memories
    )
    
    answer_text = response["answer"]
    token_usage = response.get("usage", {})
    
    # Save bot message
    bot_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer_text
    )
    db.add(bot_msg)
    conversation.updated_at = func.now()
    db.commit()
    db.refresh(bot_msg)
    
    # Save to memory
    memory_service.add_chat_memory(
        query=request.query, 
        answer=answer_text, 
        user_id=str(current_user.id), 
        project_id=str(conversation.project_id),
        conversation_id=str(conversation_id)  # NEW: Tag chat memory with conversation
    )
    
    # Deduct credits
    credit_result = credit_service.deduct_credits(current_user.id, token_usage, db)
    
    return ChatSessionResponse(
        answer=answer_text,
        conversation_id=conversation.id,
        message_id=bot_msg.id,
        credit_cost=credit_result.get("cost", 0.0),
        remaining_credits=credit_result.get("balance_remaining", 0.0)
    )
```

---

### Step 5: Update Memory Queries (Neo4j)

**File**: `app/services/memory_service.py`

Update helper methods:

```python
def get_memories_by_document(
    self, 
    user_id: str, 
    project_id: str,
    conversation_id: str = None  # NEW
) -> List[Dict]:
    """Get documents grouped by source, filtered by conversation if provided"""
    
    with self.driver.session() as session:
        if conversation_id:
            # Get documents for specific chat + project-level docs
            result = session.run("""
                MATCH (d:Document {user_id: $user_id, project_id: $project_id})
                WHERE d.conversation_id = $conversation_id OR d.conversation_id IS NULL
                MATCH (d)-[:CONTAINS]->(m:Memory)
                RETURN d.source as source, d.id as doc_id, d.timestamp as timestamp, 
                       count(m) as memory_count, collect(m.text)[0..1] as preview
                ORDER BY timestamp DESC
            """, 
            user_id=user_id, 
            project_id=project_id,
            conversation_id=conversation_id
            )
        else:
            # Get only project-level documents
            result = session.run("""
                MATCH (d:Document {
                    user_id: $user_id, 
                    project_id: $project_id,
                    conversation_id: NULL
                })
                MATCH (d)-[:CONTAINS]->(m:Memory)
                RETURN d.source as source, d.id as doc_id, d.timestamp as timestamp, 
                       count(m) as memory_count, collect(m.text)[0..1] as preview
                ORDER BY timestamp DESC
            """, 
            user_id=user_id, 
            project_id=project_id
            )
        
        documents = []
        for record in result:
            documents.append({
                "source": record["source"],
                "doc_id": record["doc_id"],
                "memory_count": record["memory_count"], 
                "preview": record["preview"][0] if record["preview"] else ""
            })
        
        return documents


def get_total_memory_count(
    self, 
    user_id: str, 
    project_id: str,
    conversation_id: str = None  # NEW
) -> int:
    """Get total memory count, filtered by conversation if provided"""
    
    with self.driver.session() as session:
        if conversation_id:
            result = session.run("""
                MATCH (m:Memory {user_id: $user_id, project_id: $project_id})
                WHERE m.conversation_id = $conversation_id OR m.conversation_id IS NULL
                RETURN count(m) as total_count
            """, 
            user_id=user_id, 
            project_id=project_id,
            conversation_id=conversation_id
            )
        else:
            result = session.run("""
                MATCH (m:Memory {
                    user_id: $user_id, 
                    project_id: $project_id,
                    conversation_id: NULL
                })
                RETURN count(m) as total_count
            """, 
            user_id=user_id, 
            project_id=project_id
            )
        
        record = result.single()
        return record["total_count"] if record else 0


def get_recent_memories(
    self, 
    user_id: str, 
    project_id: str, 
    conversation_id: str = None,  # NEW
    limit: int = 10
) -> List[Dict]:
    """Get recent memories, filtered by conversation if provided"""
    
    with self.driver.session() as session:
        if conversation_id:
            result = session.run("""
                MATCH (m:Memory {user_id: $user_id, project_id: $project_id})
                WHERE m.conversation_id = $conversation_id OR m.conversation_id IS NULL
                OPTIONAL MATCH (d:Document)-[:CONTAINS]->(m)
                RETURN m.text as text, m.timestamp as timestamp, 
                       COALESCE(d.source, m.source) as source, m.chunk_index as chunk_index
                ORDER BY m.timestamp DESC
                LIMIT $limit
            """, 
            limit=limit, 
            user_id=user_id, 
            project_id=project_id,
            conversation_id=conversation_id
            )
        else:
            result = session.run("""
                MATCH (m:Memory {
                    user_id: $user_id, 
                    project_id: $project_id,
                    conversation_id: NULL
                })
                OPTIONAL MATCH (d:Document)-[:CONTAINS]->(m)
                RETURN m.text as text, m.timestamp as timestamp, 
                       COALESCE(d.source, m.source) as source, m.chunk_index as chunk_index
                ORDER BY m.timestamp DESC
                LIMIT $limit
            """, 
            limit=limit, 
            user_id=user_id, 
            project_id=project_id
            )
        
        memories = []
        for record in result:
            text = record["text"]
            title = " ".join(text.split()[:5]) + "..."
            memories.append({
                "text": text,
                "title": title,
                "source": record["source"],
                "timestamp": record["timestamp"].isoformat(),
                "match_percentage": None
            })
        
        return memories
```

---

### Step 6: Update Memory Endpoint

**File**: `app/api/v1/endpoints/memory.py`

Update the `/memories` endpoint to accept conversation_id:

```python
@router.get("/memories", response_model=MemoriesListResponse)
async def get_recent_memories(
    project_id: int, 
    conversation_id: int = None,  # NEW PARAMETER
    limit: int = 10, 
    current_user: User = Depends(get_current_user)
):
    """
    Get memories for project or specific chat.
    
    Query Parameters:
        - project_id: Required
        - conversation_id: Optional - filter by chat
        - limit: Default 10
    """
    try:
        # If conversation_id provided, verify it belongs to user/project
        if conversation_id:
            db = next(get_db())
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
```

---

## Complete Workflow - Chat-Specific Documents

### Scenario: Two Chats in Same Project with Different Documents

#### Setup
```
Project: "Legal Case Review" (ID: 1)
├── Chat 1: "Evidence Analysis" (ID: 100)
└── Chat 2: "Witness Interview" (ID: 101)
```

#### Step 1: Upload to Chat 1 Only
```bash
POST /memory/upload?project_id=1&conversation_id=100
[File: evidence.pdf]
→ Document tagged with user_id=42, project_id=1, conversation_id=100
→ Only Chat 1 can access this document
```

#### Step 2: Upload to Chat 2 Only
```bash
POST /memory/upload?project_id=1&conversation_id=101
[File: witness_statement.pdf]
→ Document tagged with user_id=42, project_id=1, conversation_id=101
→ Only Chat 2 can access this document
```

#### Step 3: Send Message in Chat 1
```bash
POST /conversations/100/chat
{
  "query": "What evidence do we have?",
  "model": "gpt-4o"
}
→ Backend searches memories with:
  - user_id=42
  - project_id=1
  - conversation_id=100 (ONLY THIS CHAT)
→ Returns only evidence.pdf chunks
→ Other chats' documents NOT included
```

#### Step 4: Send Message in Chat 2
```bash
POST /conversations/101/chat
{
  "query": "What did the witness say?",
  "model": "gpt-4o"
}
→ Backend searches memories with:
  - user_id=42
  - project_id=1
  - conversation_id=101 (ONLY THIS CHAT)
→ Returns only witness_statement.pdf chunks
→ Other chats' documents NOT included
```

#### Step 5: View Chat 1 Memory Stats
```bash
GET /memory/memories?project_id=1&conversation_id=100
→ Response: {
  "total_memory_count": 45,
  "document_counts": [
    {"source": "evidence.pdf", "doc_id": "doc_123", "memory_count": 45}
  ],
  "memory_list": [...]
}
→ Only shows documents from Chat 1
```

#### Step 6: View Chat 2 Memory Stats
```bash
GET /memory/memories?project_id=1&conversation_id=101
→ Response: {
  "total_memory_count": 60,
  "document_counts": [
    {"source": "witness_statement.pdf", "doc_id": "doc_124", "memory_count": 60}
  ],
  "memory_list": [...]
}
→ Only shows documents from Chat 2
```

---

## Data Model Changes

### Neo4j Document Node
```cypher
// Before
CREATE (d:Document {
  id: "doc_123",
  source: "evidence.pdf",
  user_id: "42",
  project_id: "1",
  timestamp: datetime()
})

// After (with conversation support)
CREATE (d:Document {
  id: "doc_123",
  source: "evidence.pdf",
  user_id: "42",
  project_id: "1",
  conversation_id: "100",  -- NEW: NULL if project-level
  timestamp: datetime()
})
```

### Neo4j Memory Node
```cypher
// Before
CREATE (m:Memory {
  id: "mem_456",
  text: "Evidence shows...",
  user_id: "42",
  project_id: "1",
  source: "evidence.pdf",
  timestamp: datetime()
})

// After (with conversation support)
CREATE (m:Memory {
  id: "mem_456",
  text: "Evidence shows...",
  user_id: "42",
  project_id: "1",
  conversation_id: "100",  -- NEW: NULL if project-level
  source: "evidence.pdf",
  timestamp: datetime()
})
```

---

## Frontend Integration

### Upload Document in Chat
```typescript
async function uploadToChatSpecific(file: File, conversationId: number) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("project_id", currentProjectId);
  formData.append("conversation_id", conversationId);  // NEW
  
  const response = await POST("/memory/upload", formData);
  return response;
}

// Usage
<button onClick={() => uploadToChatSpecific(file, currentConversationId)}>
  Upload to This Chat Only
</button>
```

### Load Chat-Specific Memories
```typescript
async function loadChatMemories() {
  const response = await GET(`/memory/memories`, {
    params: {
      project_id: currentProjectId,
      conversation_id: currentConversationId  // NEW
    }
  });
  dispatch(setMemories(response));
}
```

### Search Chat-Specific Memories
```typescript
async function searchChatMemories(query: string) {
  const response = await POST(`/memory/search`, 
    { query, model: "gpt-4o-mini" },
    {
      params: {
        project_id: currentProjectId,
        conversation_id: currentConversationId  // NEW
      }
    }
  );
  return response;
}
```

---

## Summary

| Feature | Before | After |
|---------|--------|-------|
| **Upload Scope** | Project-level only | Project-level OR Chat-level |
| **Document Access** | All chats share documents | Each chat has isolated docs |
| **Memory Isolation** | No isolation between chats | Memories isolated by chat |
| **Use Case** | General documents for all | Chat-specific research materials |

**Benefits:**
- ✅ Each chat can have separate documents
- ✅ No memory leakage between conversations
- ✅ Relevant context only for each chat
- ✅ Better organization and control
- ✅ Backward compatible (conversation_id = NULL for project-level)
