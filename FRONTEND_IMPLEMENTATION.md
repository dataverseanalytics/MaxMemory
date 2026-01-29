# Frontend Implementation Guide - Chat UI Flow

Based on the screenshot, here's how to implement the complete chat interface with the backend.

## UI Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌──────────────┐  ┌────────────────────────────────────────┐  │
│  │   SIDEBAR    │  │        MAIN CHAT AREA                  │  │
│  │              │  │                                        │  │
│  │ Projects ▼   │  │ ┌────────────────────────────────────┐ │  │
│  │ Marketing... │  │ Marketing Campaign | Gemini 2.5 Pro  │ │  │
│  │              │  │ ┌────────────────────────────────────┐ │  │
│  │ + New Chat   │  │ │ You: Help me plan the marketing...│ │  │
│  │              │  │ │                             10:33PM │ │  │
│  │ Search ....  │  │ ├────────────────────────────────────┤ │  │
│  │              │  │ │ MaxMemory AI: Let's create a...   │ │  │
│  │ TODAY        │  │ │                             10:33PM │ │  │
│  │ • Campaign.. │  │ └────────────────────────────────────┘ │  │
│  │ • Brand Gu.. │  │ [Attachment] [+] [Voice] [Send] ► │ │  │
│  │ YESTERDAY    │  │ Message MaxMemory...                  │ │  │
│  │              │  └────────────────────────────────────────┘  │  │
│  └──────────────┘  │   ┌───────────────────────────────────┐  │
│                    │   │ Documents (1 docs • 4 memories) ◄─┤  │
│                    │   │ Search memories...                 │  │
│                    │   ├───────────────────────────────────┤  │
│                    │   │ ┌─────────┐ ┌─────────┐ ┌─────────┐│  │
│                    │   │ │Executive│ │Key      │ │Technical││  │
│                    │   │ │Summary  │ │Findings │ │Require..││  │
│                    │   │ │ 89% ✓   │ │ 80% ✓   │ │ 65% ✓   ││  │
│                    │   │ └─────────┘ └─────────┘ └─────────┘│  │
│                    │   └───────────────────────────────────┘  │
│                    └────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Structure

```
App.tsx
├── Sidebar.tsx
│   ├── ProjectSelector.tsx
│   ├── NewChatButton.tsx
│   ├── SearchHistory.tsx
│   └── ChatList.tsx
│       └── ChatItem.tsx
├── MainChat.tsx
│   ├── ChatHeader.tsx
│   │   ├── ProjectName
│   │   └── ModelSelector
│   ├── MessageList.tsx
│   │   └── MessageBubble.tsx
│   ├── MessageInput.tsx
│   │   ├── FileUploadButton
│   │   └── SendButton
│   └── MemoriesPanel.tsx
│       ├── DocumentStats
│       ├── SearchMemories
│       └── MemoryCards.tsx
│           └── MemoryCard.tsx
```

---

## State Management (React Context / Redux)

### Global State Structure
```javascript
{
  auth: {
    user: { id, name, email, credits },
    token: "jwt_token"
  },
  projects: {
    currentProjectId: 1,
    list: [{ id, name, description }],
    loading: false
  },
  conversations: {
    currentConversationId: 100,
    list: [{ id, title, project_id, created_at }],
    loading: false
  },
  messages: {
    items: [{ id, role, content, created_at, memory_refs }],
    loading: false
  },
  memories: {
    total: 150,
    documents: [
      { doc_id, source, memory_count, preview }
    ],
    recentMemories: [{ text, source, timestamp, match_percentage }],
    loading: false
  },
  files: {
    uploadStatus: "idle|pending|success|error",
    uploadProgress: 0
  }
}
```

---

## API Integration Flow

### 1. Initialize App (Page Load)
```javascript
async function initializeApp() {
  try {
    // 1. Get current user (from token)
    const user = await GET("/auth/me");
    dispatch(setUser(user));
    
    // 2. Get user's projects
    const projects = await GET("/projects");
    dispatch(setProjects(projects));
    
    // 3. If user has last project, switch to it
    if (user.lastProjectId) {
      switchProject(user.lastProjectId);
    }
  } catch (error) {
    handleAuthError(error);
  }
}
```

### 2. Switch Project
```javascript
async function switchProject(projectId) {
  dispatch(setCurrentProject(projectId));
  
  // Get conversations in this project
  const conversations = await GET(`/conversations?project_id=${projectId}`);
  dispatch(setConversations(conversations));
  
  // Get project memories
  const memoryData = await GET(`/memory/memories?project_id=${projectId}`);
  dispatch(setMemories(memoryData));
  
  // If user selects a specific chat, load it
}
```

### 3. Create New Chat
```javascript
async function createNewChat() {
  const newConversation = await POST("/conversations", {
    project_id: currentProjectId,
    title: "New Conversation",
    initial_message: null
  });
  
  dispatch(addConversation(newConversation));
  switchConversation(newConversation.id);
}

function switchConversation(conversationId) {
  dispatch(setCurrentConversation(conversationId));
  
  // Load chat history
  const conversation = await GET(`/conversations/${conversationId}`);
  dispatch(setMessages(conversation.messages));
  
  // Auto-scroll to latest message
}
```

### 4. Upload Document
```javascript
async function uploadDocument(file) {
  dispatch(setUploadStatus("pending"));
  
  const formData = new FormData();
  formData.append("file", file);
  formData.append("project_id", currentProjectId);
  // Optional: formData.append("conversation_id", currentConversationId);
  
  try {
    const response = await POST("/memory/upload", formData, {
      onUploadProgress: (progress) => {
        dispatch(setUploadProgress(progress.loaded / progress.total * 100));
      }
    });
    
    dispatch(setUploadStatus("success"));
    dispatch(addDocument(response));
    
    // Refresh memories
    const memoryData = await GET(`/memory/memories?project_id=${currentProjectId}`);
    dispatch(setMemories(memoryData));
    
    // Show success toast
    showToast("Document uploaded successfully!");
    
  } catch (error) {
    dispatch(setUploadStatus("error"));
    showToast(`Upload failed: ${error.message}`, "error");
  }
}
```

### 5. Send Message (Most Important)
```javascript
async function sendMessage(userQuery) {
  // 1. Add user message to UI immediately
  const userMsg = {
    id: Date.now(),
    role: "user",
    content: userQuery,
    created_at: new Date()
  };
  dispatch(addMessage(userMsg));
  
  // Clear input
  setInputValue("");
  
  // Show loading state for bot message
  dispatch(setMessagesLoading(true));
  
  try {
    // 2. Call backend to get response
    const response = await POST(
      `/conversations/${currentConversationId}/chat`,
      {
        query: userQuery,
        model: selectedModel // "gpt-4o-mini" or user selection
      }
    );
    
    // 3. Add bot message to UI
    const botMsg = {
      id: response.message_id,
      role: "assistant",
      content: response.answer,
      created_at: new Date(),
      memory_refs: response.memories_used // Store which memories were used
    };
    dispatch(addMessage(botMsg));
    
    // 4. Update credits
    dispatch(updateCredits(response.remaining_credits));
    
    // 5. Refresh memories to show updated stats
    const memoryData = await GET(`/memory/memories?project_id=${currentProjectId}`);
    dispatch(setMemories(memoryData));
    
    // 6. Auto-scroll to latest message
    scrollToBottom();
    
  } catch (error) {
    if (error.status === 402) {
      showToast("Insufficient credits. Please top up.", "error");
      navigateTo("/credits");
    } else {
      showToast(`Error: ${error.message}`, "error");
    }
  } finally {
    dispatch(setMessagesLoading(false));
  }
}
```

### 6. Search Memories
```javascript
async function searchMemories(query) {
  dispatch(setMemoriesLoading(true));
  
  try {
    const results = await POST(`/memory/search?project_id=${currentProjectId}`, {
      query: query,
      model: selectedModel
    });
    
    // Update memories list without changing chat
    dispatch(setSearchResults(results));
    
  } catch (error) {
    showToast(`Search failed: ${error.message}`, "error");
  } finally {
    dispatch(setMemoriesLoading(false));
  }
}
```

---

## Component Implementation Examples

### Sidebar.tsx
```typescript
export function Sidebar() {
  const { currentProjectId } = useAppState();
  const { projects } = useAppState();
  
  return (
    <div className="sidebar">
      <ProjectSelector projects={projects} />
      
      <button className="new-chat-btn" onClick={createNewChat}>
        + New Chat
      </button>
      
      <SearchHistory />
      
      <ChatList />
    </div>
  );
}
```

### MainChat.tsx
```typescript
export function MainChat() {
  const { currentConversationId, messages, memories } = useAppState();
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [inputValue, setInputValue] = useState("");
  
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    await sendMessage(inputValue);
  };
  
  return (
    <div className="main-chat">
      <ChatHeader selectedModel={selectedModel} setSelectedModel={setSelectedModel} />
      
      <div className="messages-and-memories">
        <div className="messages-section">
          <MessageList messages={messages} />
          <MessageInput 
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSendMessage}
            onFileUpload={uploadDocument}
          />
        </div>
        
        <MemoriesPanel 
          total={memories.total}
          documents={memories.documents}
          recentMemories={memories.recentMemories}
          onSearch={searchMemories}
        />
      </div>
    </div>
  );
}
```

### MemoriesPanel.tsx
```typescript
export function MemoriesPanel({ total, documents, recentMemories, onSearch }) {
  const [searchQuery, setSearchQuery] = useState("");
  
  const handleSearch = () => {
    if (searchQuery.trim()) {
      onSearch(searchQuery);
    }
  };
  
  return (
    <div className="memories-panel">
      <div className="memories-header">
        <h3>Documents</h3>
        <badge>{documents.length} docs • {total} memories</badge>
      </div>
      
      <SearchInput 
        placeholder="Search memories..."
        value={searchQuery}
        onChange={setSearchQuery}
        onSearch={handleSearch}
      />
      
      <div className="document-cards">
        {documents.map(doc => (
          <MemoryCard 
            key={doc.doc_id}
            source={doc.source}
            preview={doc.preview}
            memoryCount={doc.memory_count}
          />
        ))}
      </div>
      
      <div className="recent-memories">
        {recentMemories.map(memory => (
          <MemoryItem 
            key={memory.id}
            text={memory.text}
            source={memory.source}
            matchPercentage={memory.match_percentage}
          />
        ))}
      </div>
    </div>
  );
}
```

### MessageBubble.tsx
```typescript
export function MessageBubble({ message }) {
  const isUser = message.role === "user";
  
  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-content">
        {message.content}
      </div>
      <div className="message-footer">
        {message.created_at && (
          <span className="timestamp">
            {formatTime(message.created_at)}
          </span>
        )}
        {message.memory_refs && (
          <span className="memory-badge">
            {message.memory_refs.length} sources
          </span>
        )}
      </div>
    </div>
  );
}
```

---

## Complete User Flow

### Step 1: User Opens App
```
1. Load stored JWT token from localStorage
2. GET /auth/me → Get user profile
3. GET /projects → Get all projects
4. Display projects in sidebar
5. Auto-load last viewed project
```

### Step 2: User Selects/Creates Project
```
1. Click project in sidebar
   OR
   Click "+ New Chat"
2. GET /conversations?project_id=X → Get chats
3. GET /memory/memories?project_id=X → Get memory stats
4. Display chat list + memory panel
```

### Step 3: User Selects/Creates Chat
```
1. Click existing chat
   OR
   Click "+ New Chat" button
2. POST /conversations → Create new chat
3. GET /conversations/{id} → Load messages
4. Display empty chat with input field
```

### Step 4: User Uploads Document
```
1. Click attachment icon
2. Select file (PDF/TXT/DOCX)
3. POST /memory/upload (multipart/form-data)
   - file: [binary]
   - project_id: X
4. Show upload progress
5. GET /memory/memories → Refresh stats
6. Show success toast
```

### Step 5: User Sends Message
```
1. Type message in input
2. Click send or press Enter
3. Immediately show user message
4. POST /conversations/{id}/chat
   - query: "user text"
   - model: "gpt-4o-mini"
5. Receive bot response
6. Add to message list
7. Update memory stats
8. Update credits
9. Show bot message with timestamp
```

### Step 6: View Chat History
```
1. GET /conversations/{id}
2. Render all messages chronologically
3. Each message shows:
   - Content
   - Timestamp
   - Who sent it (role)
   - Memory references (optional)
```

### Step 7: Search Memories
```
1. Type in "Search memories..." input
2. POST /memory/search
   - query: "search text"
   - project_id: X
3. Display matching memory cards
4. Show relevance percentage (match_score)
```

---

## Key Implementation Details

### Auto-Scrolling
```typescript
const messagesEndRef = useRef(null);

useEffect(() => {
  // Scroll to bottom when new message arrives
  messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
}, [messages]);
```

### Loading States
```typescript
// Show typing indicator while bot responds
{isLoading && (
  <div className="typing-indicator">
    <span></span><span></span><span></span>
  </div>
)}
```

### Error Handling
```typescript
if (error.status === 401) {
  // Redirect to login
  navigateTo("/login");
} else if (error.status === 402) {
  // Show credit topup
  navigateTo("/credits");
} else if (error.status === 404) {
  // Chat not found - refresh
  window.location.reload();
}
```

### Real-time Updates (Optional)
```typescript
// WebSocket for real-time message updates
useEffect(() => {
  const ws = new WebSocket(`wss://api.example.com/ws/conversation/${conversationId}`);
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    dispatch(addMessage(message));
  };
  
  return () => ws.close();
}, [conversationId]);
```

---

## Summary

The complete flow works like this:

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND                                 BACKEND               │
├─────────────────────────────────────────────────────────────────┤
│
│  1. Load Projects ──────────────→ GET /projects
│                    ←────────────── [projects list]
│
│  2. Select Project ─────────────→ GET /conversations?project_id=X
│                    ←────────────── [chats, memory stats]
│
│  3. Create Chat ────────────────→ POST /conversations
│                    ←────────────── [new conversation]
│
│  4. Upload File ────────────────→ POST /memory/upload
│                    ←────────────── [doc_id, chunks]
│
│  5. Send Message ───────────────→ POST /conversations/X/chat
│                    ←────────────── [response, memories_used]
│
│  6. Show Chat History ─────────→ GET /conversations/X
│                    ←────────────── [all messages]
│
│  7. Search Memories ───────────→ POST /memory/search
│                    ←────────────── [matching memories]
│
└─────────────────────────────────────────────────────────────────┘
```

This matches the screenshot UI perfectly with:
- Project selector (left sidebar)
- Chat list (left sidebar)
- Message list (center)
- Memory panel (right) showing document counts and recent memories
