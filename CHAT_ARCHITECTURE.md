# Project-wise Chat Architecture

## Overview
The system is structured to support **Project → Chat → Documents → Memories** hierarchy with chat history tracking.

## Database Structure

### Relationships
```
User
├── Projects
│   └── Conversation (Chat Sessions)
│       ├── Messages (Chat History)
│       └── Documents (Chat-specific uploads)
│           └── Memories (Vector embeddings in Neo4j)
└── Credits (for API usage)
```

### Current SQL Models

#### 1. **User** → Projects
- User creates projects to organize work
- Each project scopes all data (chats, documents, memories)

#### 2. **Project** (app/models/project.py)
- `id`: Primary key
- `user_id`: Owner
- `name`: Project name
- `description`: Optional description
- `created_at`, `updated_at`: Timestamps

#### 3. **Conversation** (app/models/chat.py)
- Represents a **single chat session** within a project
- `id`: Primary key
- `user_id`: Owner (redundant but for quick filtering)
- `project_id`: Foreign key to Project
- `title`: Auto-generated from first message
- `created_at`, `updated_at`: Timestamps
- **Relationships**: Has many `Message` records

#### 4. **Message** (app/models/chat.py)
- Individual messages within a conversation
- `id`: Primary key
- `conversation_id`: Foreign key to Conversation
- `role`: "user" or "assistant"
- `content`: Message text
- `created_at`: Timestamp
- **Ordered by**: `created_at` (chat history order)

### Neo4j Graph (Vector Memory)

#### Nodes & Relationships
```
Document {id, source, user_id, project_id, timestamp}
  ↓
  CONTAINS
  ↓
Memory {text, user_id, project_id, timestamp, chunk_index}
  ↓
  EMBEDDED_IN (FAISS vector)
```

**Key Metadata on Memory nodes:**
- `user_id`: Scoped to user
- `project_id`: Scoped to project
- `source`: Document source (filename or "chat_memory")
- `timestamp`: When memory was created
- `chunk_index`: Position in chunked text

---

## Data Flow

### 1️⃣ CREATE PROJECT
```
POST /projects
├── Input: name, description
├── Create: Project record (user_id from token)
└── Output: Project ID
```

### 2️⃣ CREATE CHAT IN PROJECT
```
POST /conversations
├── Input: project_id, title (optional), initial_message (optional)
├── Create: Conversation record (user_id, project_id)
└── Output: Conversation ID
```

### 3️⃣ UPLOAD DOCUMENT TO CHAT
```
POST /memory/upload?project_id=X
├── Input: PDF/TXT/DOCX file
├── Process:
│   ├── Extract text from file
│   ├── Create Document node in Neo4j
│   ├── Chunk text into Memory nodes
│   ├── Generate embeddings for chunks
│   ├── Store in FAISS vector index
│   └── Tag all with: user_id, project_id, chat_id (optional)
└── Output: doc_id, chunks_count
```

### 4️⃣ SEND CHAT MESSAGE
```
POST /conversations/{conversation_id}/chat
├── Input: query, model_name
├── Process:
│   ├── Save user message to Messages table
│   ├── Query memories (FAISS) with question
│   │   └── Retrieves relevant document chunks from this project
│   ├── Pass query + memories to LLM
│   ├── Get response from LLM
│   ├── Save assistant message to Messages table
│   ├── Save interaction as Memory (chat_memory node)
│   └── Deduct credits
└── Output: answer, conversation_id, message_id, remaining_credits
```

### 5️⃣ GET CHAT HISTORY
```
GET /conversations/{conversation_id}
├── Query: SELECT * FROM messages WHERE conversation_id=X
├── Order: By created_at (chronological)
└── Output: All messages with roles and timestamps
```

### 6️⃣ GET MEMORIES FOR CHAT
```
GET /memory/memories?project_id=X
├── Query Neo4j:
│   ├── Count total memories for project
│   ├── Get document counts (memories per document)
│   └── Get recent memories
└── Output:
{
  "total_memory_count": 450,
  "document_counts": [
    {"source": "report.pdf", "doc_id": "doc_1", "memory_count": 200},
    {"source": "article.txt", "doc_id": "doc_2", "memory_count": 250}
  ],
  "memory_list": [
    {"text": "...", "source": "report.pdf", "timestamp": "..."},
    ...
  ]
}
```

---

## API Endpoints Summary

### Projects
```
POST   /projects                          - Create project
GET    /projects                          - List user's projects
GET    /projects/{project_id}             - Get project details
DELETE /projects/{project_id}             - Delete project
```

### Conversations (Chats)
```
POST   /conversations                     - Create new chat in project
GET    /conversations?project_id=X        - List chats in project
GET    /conversations/{conv_id}           - Get chat details + all messages (HISTORY)
DELETE /conversations/{conv_id}           - Delete chat
```

### Chat Message Exchange
```
POST   /conversations/{conv_id}/chat      - Send message, get response, save to history
```

### Memory Management
```
POST   /memory/upload                     - Upload document to project
GET    /memory/documents                  - Get documents with counts
GET    /memory/memories                   - Get total count + document counts + recent memories
POST   /memory/search                     - Search memories without chatting
DELETE /memory                            - Clear all memories
```

---

## How Chat-Wise Document Upload Works

### Option 1: Global Document (Current Implementation)
- Documents are uploaded at **project level**
- All chats in the project can access those documents
- Memories are tagged with `project_id` only

### Option 2: Chat-Specific Document (To Implement)
For chat-specific documents, you need to:

#### A. Extend Database Schema
```sql
ALTER TABLE documents ADD COLUMN conversation_id INT;
-- Make it optional (NULL = project-level document)
-- If conversation_id != NULL, it's chat-specific
```

#### B. Tag Memory Nodes
```cypher
CREATE (m:Memory {
  user_id: "user_1",
  project_id: "proj_1", 
  conversation_id: "conv_1",  -- NEW: Chat scope
  source: "report.pdf",
  text: "...",
  timestamp: datetime()
})
```

#### C. Modify Memory Queries
```cypher
-- Get memories for specific chat
MATCH (m:Memory {
  user_id: $user_id,
  project_id: $project_id,
  conversation_id: $conversation_id  -- Filter by chat
})

-- Or get project-level + chat-level
MATCH (m:Memory {user_id: $user_id, project_id: $project_id})
WHERE m.conversation_id IS NULL OR m.conversation_id = $conversation_id
```

---

## Implementation Checklist

### ✅ Already Implemented
- [x] User authentication & projects
- [x] Create conversations (chats)
- [x] Save messages to database (chat history)
- [x] Send messages with RAG retrieval
- [x] Get conversation details (with message history)
- [x] Upload documents to project
- [x] Track document counts and total memories
- [x] Search memories

### 🔄 To Implement (Optional Enhancements)

#### 1. **Chat-Specific Document Uploads**
```python
# In memory endpoint
@router.post("/upload/{conversation_id}")
async def upload_to_chat(conversation_id: int, file: UploadFile, ...):
    # Tag document and memories with conversation_id
    # Only this chat retrieves these memories
```

#### 2. **Document Access Control per Chat**
```python
@router.get("/documents/{conversation_id}")
async def get_chat_documents(conversation_id: int, ...):
    # Return documents available to this specific chat
    # Include project-level + chat-specific documents
```

#### 3. **Chat-Scoped Memory Statistics**
```python
@router.get("/memories/{conversation_id}")
async def get_chat_memories(conversation_id: int, ...):
    # Total memories for THIS chat
    # Documents used in THIS chat
    # Memory list from THIS chat
```

#### 4. **Prevent Memory Leakage Between Chats**
```python
# In memory_service.query_memories()
# When searching, filter by conversation_id
# Ensure user can only access their own chats' memories
```

#### 5. **Export Chat History**
```python
@router.get("/conversations/{conversation_id}/export")
async def export_chat(conversation_id: int, format: str = "json"):
    # Export all messages with documents and memories used
    # Format: JSON, TXT, PDF
```

---

## Example Workflow

### Step 1: User Creates Project
```bash
POST /projects
{
  "name": "Legal Case Review",
  "description": "Review documents for case #12345"
}
→ Response: {id: 1, user_id: 42, created_at: "2026-01-30T..."}
```

### Step 2: User Creates Chat in Project
```bash
POST /conversations
{
  "project_id": 1,
  "title": "Evidence Discussion",
  "initial_message": "Analyze the evidence"
}
→ Response: {id: 100, project_id: 1, created_at: "..."}
```

### Step 3: User Uploads Document to Project
```bash
POST /memory/upload?project_id=1
[File: evidence.pdf]
→ Response: {
  doc_id: "doc_abc123",
  chunks: 45,
  status: "success"
}
```

### Step 4: User Sends Message in Chat
```bash
POST /conversations/100/chat
{
  "query": "What are the key findings in the evidence?",
  "model": "gpt-4o"
}
→ Response: {
  answer: "The key findings are...",
  conversation_id: 100,
  message_id: 500,
  remaining_credits: 95.50
}
```

**What happened internally:**
1. User message saved to `messages` table with `conversation_id=100`
2. Query searched Neo4j for memories matching question
3. Found relevant chunks from `evidence.pdf` (project-scoped)
4. Sent to GPT-4o with context
5. Response saved to `messages` table with `conversation_id=100`
6. Interaction saved as Memory node in Neo4j
7. Credits deducted

### Step 5: User Views Chat History
```bash
GET /conversations/100
→ Response: {
  id: 100,
  title: "Evidence Discussion",
  messages: [
    {id: 1, role: "user", content: "Analyze the evidence", created_at: "..."},
    {id: 2, role: "assistant", content: "The key findings are...", created_at: "..."},
    {id: 3, role: "user", content: "What are the key findings...", created_at: "..."},
    {id: 4, role: "assistant", content: "The key findings are...", created_at: "..."}
  ]
}
```

### Step 6: User Views Memory Statistics
```bash
GET /memory/memories?project_id=1
→ Response: {
  total_memory_count: 150,
  document_counts: [
    {source: "evidence.pdf", doc_id: "doc_abc123", memory_count: 45},
    {source: "chat_interactions", doc_id: "chat_memory_1", memory_count: 105}
  ],
  memory_list: [
    {text: "What are the key findings...", source: "chat_interactions", timestamp: "..."},
    ...
  ]
}
```

---

## Key Concepts

### 🔐 Data Scoping
- **User-level**: All data belongs to a user (via auth token)
- **Project-level**: Documents and memories are scoped to projects
- **Chat-level**: Messages are scoped to conversations (ready for chat-specific docs)

### 📚 Memory Types
1. **Document Memory**: Chunks from uploaded PDFs/texts
2. **Chat Memory**: Question-answer pairs from interactions
3. Both stored in Neo4j with user_id, project_id metadata

### 🔍 Retrieval Workflow (RAG)
```
User Query → FAISS Vector Search → Relevant Memory Chunks → LLM → Answer
```

### 💾 Persistence
- **SQL (SQLite/PostgreSQL)**: User, Projects, Conversations, Messages
- **Neo4j**: Documents, Memories (with metadata)
- **FAISS**: Vector embeddings for similarity search

---

## Next Steps

1. **Add chat-specific document uploads** (Option 2 above)
2. **Implement memory filtering** by conversation_id
3. **Add document access control** per chat
4. **Create chat export functionality**
5. **Add memory-to-chat linking** for provenance tracking

