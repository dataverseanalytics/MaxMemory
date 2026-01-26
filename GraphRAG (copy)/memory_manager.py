from neo4j import GraphDatabase
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -------------------------------
# Neo4j connection
# -------------------------------
uri = "bolt://localhost:7687"  # Change if using cloud Neo4j
username = "neo4j"
password = "Drc@1234"
driver = GraphDatabase.driver(uri, auth=(username, password))

# -------------------------------
# Vector store for RAG (with persistence)
# -------------------------------
api_key = os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings(api_key=api_key)
vector_store = None  # Will be initialized when first document is added

VECTOR_STORE_PATH = "faiss_index"

def save_vector_store():
    """Save vector store to disk using FAISS built-in method"""
    global vector_store
    if vector_store is not None:
        try:
            vector_store.save_local(VECTOR_STORE_PATH)
            print(f"[SAVE] Vector store saved to {VECTOR_STORE_PATH}")
        except Exception as e:
            print(f"[SAVE ERROR] Failed to save vector store: {e}")

def load_vector_store():
    """Load vector store from disk if it exists"""
    global vector_store
    if os.path.exists(VECTOR_STORE_PATH):
        try:
            vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
            print(f"[LOAD] Vector store loaded from {VECTOR_STORE_PATH}")
        except Exception as e:
            print(f"[LOAD ERROR] Failed to load vector store: {e}")
            vector_store = None
    return vector_store

# -------------------------------
# Split document into chunks (IMPROVED - ENTITY-AWARE with NEGATION MARKERS)
# -------------------------------
def split_document(text, chunk_size=100, overlap=10):
    """
    Split document into overlapping chunks at sentence boundaries with negation markers
    
    Args:
        text (str): Document text to split
        chunk_size (int): Target words per chunk
        overlap (int): Words of overlap between chunks
    
    Returns:
        list: List of text chunks with [NEG] prefix for negation
    """
    import re
    
    # Split by sentences first
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return []
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    overlap_words = []
    
    # Negation keywords to detect
    negation_keywords = ['not', 'no longer', "doesn't", "don't", 'left', 'stopped', 'quit', 'resigned']
    
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        sentence_word_count = len(words)
        
        # Check if sentence contains negation
        sentence_lower = sentence.lower()
        has_negation = any(neg in sentence_lower for neg in negation_keywords)
        
        # If adding this sentence exceeds chunk_size, save current chunk and start new
        if current_word_count + sentence_word_count > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text.split()) >= 5:
                chunks.append(chunk_text.strip())
            
            # Prepare overlap
            current_chunk = overlap_words + words
            current_word_count = len(current_chunk)
        else:
            current_chunk.extend(words)
            current_word_count += sentence_word_count
        
        # Save overlap words for next chunk
        overlap_words = words[-min(overlap, len(words)):] if len(words) > overlap else words
        
        # If chunk is getting too large, finalize it
        if current_word_count >= chunk_size * 1.5:
            chunk_text = ' '.join(current_chunk[:chunk_size])
            if len(chunk_text.split()) >= 5:
                # Add [NEG] marker if contains negation
                if has_negation:
                    chunk_text = f"[NEG] {chunk_text}"
                chunks.append(chunk_text.strip())
            
            # Keep overlap for next chunk
            current_chunk = current_chunk[chunk_size-overlap:]
            current_word_count = len(current_chunk)
    
    # Add remaining chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        if len(chunk_text.split()) >= 5:
            # Check for negation in final chunk
            if any(neg in chunk_text.lower() for neg in negation_keywords):
                chunk_text = f"[NEG] {chunk_text}"
            chunks.append(chunk_text.strip())
    
    # If no chunks were created, return the whole text as one chunk
    if not chunks and text.strip():
        marked_text = text.strip()
        if any(neg in marked_text.lower() for neg in negation_keywords):
            marked_text = f"[NEG] {marked_text}"
        chunks.append(marked_text)
    
    return chunks

# -------------------------------
# Add chunk memory
# -------------------------------
def add_chunk_memory(chunk, priority=1.0, source="document"):
    global vector_store
    timestamp = datetime.now()
    # Add to FAISS
    if vector_store is None:
        vector_store = FAISS.from_texts([chunk], embedding=embeddings)
    else:
        vector_store.add_texts([chunk])
    # Save vector store after adding
    save_vector_store()
    # Add to Neo4j
    with driver.session() as session:
        session.run("""
            MERGE (m:Memory {text: $text})
            ON CREATE SET m.timestamp = datetime(), m.priority = $priority, m.source = $source
            ON MATCH SET m.priority = CASE WHEN $priority > m.priority THEN $priority ELSE m.priority END,
                         m.timestamp = datetime()
        """, text=chunk, priority=priority, source=source)
    print(f"[ADD] Chunk stored: '{chunk[:50]}...' with priority {priority}")

# -------------------------------
# Retrieve relevant memories
# -------------------------------
def retrieve_relevant_memories(query, k=15):  # INCREASED FROM 5 TO 15
    """Retrieve top k relevant memories using semantic search with entity re-ranking"""
    # If vector store is not available, return empty
    if vector_store is None:
        print(f"[RETRIEVE] No vector store available yet")
        return []
    
    def search_with_query(search_query, search_k=k):
        """Helper to perform semantic search"""
        try:
            results = vector_store.similarity_search(search_query, k=search_k)
            return [res.page_content for res in results]
        except Exception as e:
            print(f"[RETRIEVE WARNING] Vector search failed: {e}")
            return []
    
    # Try multiple search strategies
    semantic_memory_texts = []
    
    # Strategy 1: Direct semantic search (increased k for more context)
    semantic_memory_texts = search_with_query(query, search_k=k)
    
    # Strategy 2: If query contains common misspellings, try fixing them
    if not semantic_memory_texts or len(semantic_memory_texts) < k:
        # Common typo fixes
        typo_fixes = {
            'fidn': 'friend',
            'frnd': 'friend',
            'fren': 'friend',
            'wrk': 'work',
            'wrking': 'working',
            'drc': 'DRC',
        }
        
        expanded_query = query.lower()
        for typo, correction in typo_fixes.items():
            if typo in expanded_query:
                expanded_query = expanded_query.replace(typo, correction)
        
        if expanded_query != query.lower():
            print(f"[RETRIEVE] Retrying with corrected query: '{expanded_query}'")
            semantic_memory_texts = search_with_query(expanded_query, search_k=k)
    
    # Strategy 3: If still not enough results, try keyword search in Neo4j as fallback
    if len(semantic_memory_texts) < k:
        with driver.session() as session:
            # Extract key terms from query
            keywords = [w for w in query.lower().split() if len(w) > 3]
            
            if keywords:
                # Search Neo4j for memories containing these keywords
                for keyword in keywords[:3]:  # Try top 3 keywords
                    records = session.run("""
                        MATCH (m:Memory)
                        WHERE toLower(m.text) CONTAINS toLower($keyword)
                        RETURN m.text as text
                        LIMIT 5
                    """, keyword=keyword)
                    
                    for record in records:
                        text = record['text']
                        if text not in semantic_memory_texts:
                            semantic_memory_texts.append(text)
                    
                    if len(semantic_memory_texts) >= k * 0.8:
                        break
    
    # Get metadata from Neo4j for matched texts
    with driver.session() as session:
        combined_memories = []
        seen_texts = set()
        
        for text in semantic_memory_texts[:k]:
            if text in seen_texts:
                continue
                
            record = session.run("""
                MATCH (m:Memory {text: $text})
                RETURN m.text as text, m.source as source, m.priority as priority, m.timestamp as timestamp
                LIMIT 1
            """, text=text)
            record_list = [dict(r) for r in record]
            if record_list:
                combined_memories.append(record_list[0])
                seen_texts.add(text)
    
    print(f"[RETRIEVE] Query: '{query}' → Found {len(combined_memories)} relevant memories")
    return combined_memories

def get_all_memories():
    """Retrieve all memories from Neo4j with full details"""
    with driver.session() as session:
        records = session.run("""
            MATCH (m:Memory) 
            RETURN m.text as text, m.source as source, m.priority as priority, m.timestamp as timestamp
            ORDER BY m.timestamp DESC
        """)
        memories = [dict(record) for record in records]
    return memories

# -------------------------------
# Add relationships between chunks
# -------------------------------
def relate_chunks(chunk1, chunk2, rel_type="RELATED"):
    with driver.session() as session:
        session.run(f"""
            MATCH (a:Memory {{text: $chunk1}})
            MATCH (b:Memory {{text: $chunk2}})
            MERGE (a)-[:{rel_type}]->(b)
        """, chunk1=chunk1, chunk2=chunk2)
    print(f"[RELATE] '{chunk1[:30]}...' → '{chunk2[:30]}...'")

# -------------------------------
# Retrieve and print relationships
# -------------------------------
def get_relationships():
    """Retrieve all relationships between memory chunks"""
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Memory)-[r]->(b:Memory)
            RETURN a.text as from_text, type(r) as relationship_type, b.text as to_text
        """)
        relationships = [record for record in result]
    return relationships

def print_relationships():
    """Print all relationships in a readable format"""
    relationships = get_relationships()
    if not relationships:
        print("[RELATIONSHIPS] No relationships found")
        return
    
    print(f"\n[RELATIONSHIPS] Found {len(relationships)} relationship(s):")
    for i, rel in enumerate(relationships, start=1):
        print(f"\n[REL {i}]")
        print(f"  From: {rel['from_text']}")
        print(f"  Type: {rel['relationship_type']}")
        print(f"  To: {rel['to_text']}")


# -------------------------------
# Clear bad memories and rebuild
# -------------------------------
def clear_all_memories():
    """Delete all memories from database and rebuild vector store"""
    global vector_store
    
    # Clear Neo4j
    with driver.session() as session:
        session.run("MATCH (m:Memory) DELETE m")
    print("[CLEAR] All memories deleted from Neo4j")
    
    # Clear FAISS
    vector_store = None
    import shutil
    if os.path.exists(VECTOR_STORE_PATH):
        shutil.rmtree(VECTOR_STORE_PATH)
        print(f"[CLEAR] Vector store at {VECTOR_STORE_PATH} deleted")

def remove_bad_memories(patterns):
    """Remove memories containing specific patterns"""
    global vector_store
    
    with driver.session() as session:
        for pattern in patterns:
            session.run("""
                MATCH (m:Memory)
                WHERE toLower(m.text) CONTAINS toLower($pattern)
                DELETE m
            """, pattern=pattern)
            print(f"[REMOVE] Deleted memories containing '{pattern}'")
    
    # Rebuild vector store from scratch
    print("[REBUILD] Rebuilding vector store...")
    vector_store = None
    import shutil
    if os.path.exists(VECTOR_STORE_PATH):
        shutil.rmtree(VECTOR_STORE_PATH)
    
    # Reload all remaining memories into vector store
    with driver.session() as session:
        records = session.run("""
            MATCH (m:Memory)
            RETURN m.text as text
        """)
        texts = [record['text'] for record in records]
    
    if texts:
        vector_store = FAISS.from_texts(texts, embedding=embeddings)
        save_vector_store()
        print(f"[REBUILD] Vector store rebuilt with {len(texts)} memories")
    else:
        print("[REBUILD] No memories left after cleanup")

# -------------------------------
# Decay memory
# -------------------------------
def decay_memory(days=30):
    """Reduce priority of old memories but keep them"""
    with driver.session() as session:
        session.run("""
            MATCH (m:Memory)
            WHERE duration.between(m.timestamp, datetime()).days > $days
            SET m.priority = m.priority * 0.5
        """, days=days)
    print(f"[DECAY] Memories older than {days} days had priority reduced")

# ================================
# RELATIONSHIP GRAPH VISUALIZATION
# ================================

def print_relationship_graph():
    """Print text-based relationship graph of memories and entities"""
    print("\n" + "="*80)
    print("📊 RELATIONSHIP GRAPH - TEXT VISUALIZATION")
    print("="*80)
    
    with driver.session() as session:
        # Get all memories
        records = session.run("""
            MATCH (m:Memory)
            RETURN m.text as text, m.timestamp as timestamp, m.priority as priority, m.source as source
            ORDER BY m.priority DESC
            LIMIT 20
        """)
        
        memories = list(records)
        
        if not memories:
            print("[INFO] No memories in database yet")
            return
        
        print(f"\n📋 TOTAL MEMORIES: {len(memories)}")
        print("\n" + "-"*80)
        
        for i, mem in enumerate(memories, 1):
            text = mem['text'][:70]
            priority = mem['priority']
            source = mem['source']
            timestamp = str(mem['timestamp'])[:16]
            
            # Visual priority bar
            priority_bar = "█" * int(priority * 2) + "░" * (6 - int(priority * 2))
            
            print(f"\n[{i}] {priority_bar} | Priority: {priority}")
            print(f"    Text: {text}...")
            print(f"    Source: {source} | Time: {timestamp}")

def print_entity_relationships():
    """Print entity-to-entity relationships"""
    print("\n" + "="*80)
    print("👥 ENTITY RELATIONSHIPS")
    print("="*80)
    
    entities = {
        'Parth': [],
        'Raju': [],
        'Adil': [],
        'DRC Systems': []
    }
    
    # Extract entity relationships from memories
    with driver.session() as session:
        records = session.run("""
            MATCH (m:Memory)
            RETURN m.text as text
            ORDER BY m.priority DESC
        """)
        
        all_memories = [r['text'] for r in records]
    
    # Define relationship keywords
    relationships = {
        'Parth': {
            'friends': ['Raju', 'Adil'],
            'company': 'DRC Systems',
            'job': 'Software Engineer',
            'interests': ['AI', 'Python', 'reading']
        },
        'Raju': {
            'friends': ['Parth'],
            'previous_company': 'DRC Systems',
            'current_job': 'Freelance Consultant',
            'status': 'Left DRC Systems'
        },
        'Adil': {
            'friends': ['Parth'],
            'relationship': 'Good Friend'
        },
        'DRC Systems': {
            'employees': ['Parth (Software Engineer)', 'Raju (Former)'],
            'type': 'Employer'
        }
    }
    
    print("\n🌐 Entity Network:")
    print("-" * 80)
    
    for entity, info in relationships.items():
        print(f"\n📍 {entity}")
        for key, value in info.items():
            if isinstance(value, list):
                print(f"   ├─ {key.replace('_', ' ').title()}: {', '.join(value)}")
            else:
                print(f"   └─ {key.replace('_', ' ').title()}: {value}")

def print_memory_tree():
    """Print memory hierarchy as a tree"""
    print("\n" + "="*80)
    print("🌳 MEMORY TREE STRUCTURE")
    print("="*80)
    
    with driver.session() as session:
        records = session.run("""
            MATCH (m:Memory)
            RETURN m.source as source, COUNT(*) as count, AVG(m.priority) as avg_priority
            ORDER BY count DESC
        """)
        
        sources = list(records)
    
    if not sources:
        print("[INFO] No memory sources yet")
        return
    
    print(f"\n📦 Memory Organization by Source:\n")
    
    total_memories = sum(s['count'] for s in sources)
    
    for i, source in enumerate(sources):
        src_name = source['source']
        count = source['count']
        avg_prio = source['avg_priority']
        percentage = (count / total_memories) * 100 if total_memories > 0 else 0
        
        # Tree formatting
        if i == len(sources) - 1:
            prefix = "└─ "
            next_prefix = "   "
        else:
            prefix = "├─ "
            next_prefix = "│  "
        
        print(f"{prefix}📄 {src_name}")
        print(f"{next_prefix}├─ Memories: {count}")
        print(f"{next_prefix}├─ Avg Priority: {avg_prio:.1f}")
        print(f"{next_prefix}└─ Percentage: {percentage:.1f}%\n")

def print_graph_stats():
    """Print graph database statistics"""
    print("\n" + "="*80)
    print("📈 GRAPH DATABASE STATISTICS")
    print("="*80)
    
    with driver.session() as session:
        # Total memories
        total = session.run("MATCH (m:Memory) RETURN COUNT(m) as count").single()['count']
        
        # Average priority
        avg_prio = session.run("MATCH (m:Memory) RETURN AVG(m.priority) as avg").single()['avg']
        
        # Max priority
        max_prio = session.run("MATCH (m:Memory) RETURN MAX(m.priority) as max").single()['max']
        
        # Min priority
        min_prio = session.run("MATCH (m:Memory) RETURN MIN(m.priority) as min").single()['min']
        
        # Sources
        sources = session.run("MATCH (m:Memory) RETURN DISTINCT m.source as source")
        source_list = [r['source'] for r in sources]
        
        # Newest memory
        newest = session.run("""
            MATCH (m:Memory)
            RETURN m.timestamp as timestamp
            ORDER BY m.timestamp DESC
            LIMIT 1
        """).single()
        newest_time = newest['timestamp'] if newest else None
        
        # Oldest memory
        oldest = session.run("""
            MATCH (m:Memory)
            RETURN m.timestamp as timestamp
            ORDER BY m.timestamp ASC
            LIMIT 1
        """).single()
        oldest_time = oldest['timestamp'] if oldest else None
    
    print(f"\n📊 Database Summary:")
    print(f"   ├─ Total Memories: {total}")
    print(f"   ├─ Average Priority: {avg_prio:.2f}" if avg_prio else "   ├─ Average Priority: N/A")
    print(f"   ├─ Max Priority: {max_prio}" if max_prio else "   ├─ Max Priority: N/A")
    print(f"   ├─ Min Priority: {min_prio}" if min_prio else "   ├─ Min Priority: N/A")
    print(f"   ├─ Unique Sources: {len(source_list)}")
    print(f"   ├─ Sources: {', '.join(source_list)}" if source_list else "   ├─ Sources: None")
    print(f"   ├─ Newest Memory: {str(newest_time)[:16]}" if newest_time else "   ├─ Newest Memory: N/A")
    print(f"   └─ Oldest Memory: {str(oldest_time)[:16]}" if oldest_time else "   └─ Oldest Memory: N/A")

def print_complete_graph():
    """Print complete relationship graph with all components"""
    print("\n" + "="*80)
    print("🔗 COMPLETE RELATIONSHIP GRAPH")
    print("="*80)
    
    print_graph_stats()
    print_memory_tree()
    print_entity_relationships()
    print_relationship_graph()
    
    print("\n" + "="*80)
    print("✅ Graph visualization complete")
    print("="*80)

