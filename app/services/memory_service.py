
import os
import shutil
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing long-term memory (Neo4j + FAISS)"""
    
    def __init__(self):
        # Neo4j setup
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        
        # FAISS setup
        self.vector_store_path = "faiss_index"
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vector_store = self._load_vector_store()
        
    def close(self):
        """Close Neo4j driver"""
        self.driver.close()

    def _load_vector_store(self):
        """Load FAISS index from disk"""
        if os.path.exists(self.vector_store_path):
            try:
                # allow_dangerous_deserialization is needed for loading local pickle files
                vs = FAISS.load_local(
                    self.vector_store_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Loaded vector store from {self.vector_store_path}")
                return vs
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
                return None
        return None

    def _save_vector_store(self):
        """Save FAISS index to disk"""
        if self.vector_store:
            self.vector_store.save_local(self.vector_store_path)
            logger.info(f"Saved vector store to {self.vector_store_path}")

    def add_document_memory(self, text: str, metadata: Dict[str, Any]):
        """
        Add a document's text to memory.
        Splits text into chunks, embeds them, and saves to Neo4j + FAISS.
        """
    def _split_document(self, text: str) -> List[str]:
        """
        Splits text into overlapping chunks at sentence boundaries with negation markers
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
        
        chunk_word_limit = 100 # Approx equivalent to 500 chars
        overlap = 10
        
        for sentence in sentences:
            words = sentence.split()
            if not words:
                continue
            sentence_word_count = len(words)
            
            # Check if sentence contains negation
            sentence_lower = sentence.lower()
            has_negation = any(neg in sentence_lower for neg in negation_keywords)
            
            # If adding this sentence exceeds chunk_size, save current chunk and start new
            if current_word_count + sentence_word_count > chunk_word_limit and current_chunk:
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
            if current_word_count >= chunk_word_limit * 1.5:
                chunk_text = ' '.join(current_chunk[:chunk_word_limit])
                if len(chunk_text.split()) >= 5:
                    # Add [NEG] marker if contains negation
                    if has_negation:
                        chunk_text = f"[NEG] {chunk_text}"
                    chunks.append(chunk_text.strip())
                
                # Keep overlap for next chunk
                current_chunk = current_chunk[chunk_word_limit-overlap:]
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

    def add_document_memory(self, text: str, metadata: Dict[str, Any]):
        """
        Add a document's text to memory.
        Splits text into chunks, embeds them, and saves to Neo4j + FAISS.
        """
        chunks = self._split_document(text) # Use the new split method
        
        source = metadata.get("source", "unknown")
        doc_id = metadata.get("doc_id", source) # Simple ID generation
        user_id = metadata.get("user_id", "unknown")
        project_id = metadata.get("project_id", "default")
        
        # Add to FAISS
        vectors = [chunk for chunk in chunks]
        metadatas = [metadata.copy() for _ in chunks]
        
        # Add index to metadata
        for i, meta in enumerate(metadatas):
            meta["chunk_index"] = i
            meta["text"] = chunks[i] # Store text in metadata for retrieval convenience
        
        if self.vector_store is None:
            self.vector_store = FAISS.from_texts(vectors, self.embeddings, metadatas=metadatas)
        else:
            self.vector_store.add_texts(vectors, metadatas=metadatas)
            
        self._save_vector_store()
        
        # Add to Neo4j
        with self.driver.session() as session:
            for i, chunk in enumerate(chunks):
                session.run("""
                    MERGE (d:Document {id: $doc_id})
                    ON CREATE SET d.source = $source, d.timestamp = datetime(), d.user_id = $user_id, d.project_id = $project_id
                    
                    CREATE (m:Memory {text: $text})
                    SET m.chunk_index = $index, 
                        m.timestamp = datetime(),
                        m.priority = 1.0,
                        m.user_id = $user_id,
                        m.project_id = $project_id
                    
                    MERGE (d)-[:CONTAINS]->(m)
                """, doc_id=doc_id, source=source, user_id=user_id, project_id=project_id, text=chunk, index=i)
                
                # Relate previous chunk if exists
                if i > 0:
                    session.run("""
                        MATCH (m1:Memory {text: $prev_text})
                        MATCH (m2:Memory {text: $curr_text})
                        MERGE (m1)-[:NEXT]->(m2)
                    """, prev_text=chunks[i-1], curr_text=chunk)
                    
        logger.info(f"Added document {doc_id} with {len(chunks)} chunks")
        return {"chunks": len(chunks), "doc_id": doc_id}

    def add_chat_memory(self, query: str, answer: str, user_id: str, project_id: str):
        """
        Add a chat interaction to memory.
        """
        # Combine query and answer for better context
        text = f"User: {query}\nAssistant: {answer}"
        
        metadata = {
            "source": "chat",
            "type": "conversation",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "project_id": project_id
        }
        
        # Add to FAISS
        self.vector_store.add_texts([text], metadatas=[metadata])
        self._save_vector_store()
        
        # Add to Neo4j
        with self.driver.session() as session:
            session.run("""
                CREATE (m:Memory {text: $text})
                SET m.source = 'chat',
                    m.type = 'conversation',
                    m.timestamp = datetime(),
                    m.priority = 0.8,
                    m.user_id = $user_id,
                    m.project_id = $project_id
            """, text=text, user_id=user_id, project_id=project_id)
            
        logger.info(f"Added chat memory for user {user_id} in project {project_id}")


    def query_memories(self, query: str, user_id: str, project_id: str, k: int = 5) -> List[Dict]:
        """Retrieve relevant memories using hybrid search (Semantic + Graph) with user and project isolation"""
        if self.vector_store is None:
            return []
            
        def search_with_query(search_query, search_k=k*3): # Fetch more for filtering
            """Helper to perform semantic search"""
            try:
                results = self.vector_store.similarity_search_with_score(search_query, k=search_k)
                
                # Filter by user_id AND project_id
                filtered_results = []
                for doc, score in results:
                    doc_user_id = doc.metadata.get("user_id")
                    doc_project_id = doc.metadata.get("project_id")
                    
                    # Strict isolation: match both user and project
                    if str(doc_user_id) == str(user_id) and str(doc_project_id) == str(project_id): 
                        filtered_results.append((doc, score))
                        
                return filtered_results[:k]
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
                return []
    
        # Strategy 1: Direct semantic search
        results = search_with_query(query)
        
        # Strategy 2: Typo correction (simplified from source)
        if not results or len(results) < k:
            typo_fixes = {
                'fidn': 'friend', 'frnd': 'friend', 'fren': 'friend',
                'wrk': 'work', 'wrking': 'working', 'drc': 'DRC',
            }
            expanded_query = query.lower()
            changed = False
            for typo, correction in typo_fixes.items():
                if typo in expanded_query:
                    expanded_query = expanded_query.replace(typo, correction)
                    changed = True
            
            if changed:
                logger.info(f"Retrying with corrected query: '{expanded_query}'")
                extra_results = search_with_query(expanded_query)
                
                # Merge unique results
                existing_texts = {doc.page_content for doc, _ in results}
                for doc, score in extra_results:
                    if doc.page_content not in existing_texts:
                        results.append((doc, score))
                        existing_texts.add(doc.page_content)
        
        # Strategy 3: Keyword/Entity Search fallback (if still low results)
        if len(results) < k:
            keywords = [w for w in query.lower().split() if len(w) > 3]
            if keywords:
                with self.driver.session() as session:
                    # Simple keyword match in Neo4j
                    for keyword in keywords[:3]:
                        records = session.run("""
                            MATCH (m:Memory)
                            WHERE m.user_id = $user_id AND m.project_id = $project_id AND toLower(m.text) CONTAINS toLower($keyword)
                            RETURN m.text as text, m.timestamp as timestamp, m.source as source
                            LIMIT 3
                        """, keyword=keyword, user_id=user_id, project_id=project_id)
                        
                        existing_texts = {doc.page_content for doc, _ in results}
                        for record in records:
                            text = record["text"]
                            if text not in existing_texts:
                                # Create dummy Document/score for consistency
                                doc = Document(page_content=text, metadata={"source": record.get("source", "unknown"), "timestamp": str(record.get("timestamp", ""))})
                                # Assign a low score (high distance) or neutral
                                score = 0.5 
                                results.append((doc, score))
                                existing_texts.add(text)

        # Truncate to k
        results = results[:k]
        
        memories = []
        for doc, score in results:
            # FAISS L2 distance: lower is better. Convert to approx percentage (0-100)
            similarity = 1 / (1 + score)
            match_percentage = int(similarity * 100)
            
            memories.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
                "match_percentage": match_percentage
            })
            
        return memories

    def get_recent_memories(self, user_id: str, project_id: str, limit: int = 10) -> List[Dict]:
        """Get the most recently added memories across all documents for the valid user and project"""
        # Fetch from Neo4j for metadata, we can't easily sort FAISS by time without metadata index
        # But we assume Neo4j is the source of truth for "Existence"
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Memory {user_id: $user_id, project_id: $project_id})
                OPTIONAL MATCH (d:Document)-[:CONTAINS]->(m)
                RETURN m.text as text, m.timestamp as timestamp, COALESCE(d.source, m.source) as source, m.chunk_index as chunk_index
                ORDER BY m.timestamp DESC
                LIMIT $limit
            """, limit=limit, user_id=user_id, project_id=project_id)
            
            memories = []
            for record in result:
                # Generate a simple title (first 5 words)
                text = record["text"]
                title = " ".join(text.split()[:5]) + "..."
                
                memories.append({
                    "text": text,
                    "title": title,
                    "source": record["source"],
                    "timestamp": record["timestamp"].isoformat(),
                    "match_percentage": None # No query, so no match score
                })
            return memories


    def get_memories_by_document(self, user_id: str, project_id: str) -> List[Dict]:
        """Get all memories grouped by document source for the user and project"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {user_id: $user_id, project_id: $project_id})-[:CONTAINS]->(m:Memory)
                RETURN d.source as source, d.id as doc_id, d.timestamp as timestamp, count(m) as memory_count, collect(m.text)[0..1] as preview
                ORDER BY timestamp DESC
            """, user_id=user_id, project_id=project_id)
            
            documents = []
            for record in result:
                documents.append({
                    "source": record["source"],
                    "doc_id": record["doc_id"],
                    "memory_count": record["memory_count"], 
                    "preview": record["preview"][0] if record["preview"] else ""
                })
                
            return documents
            
    def clear_all(self, user_id: str, project_id: str):
        """Clear all memories for specific user and project"""
        # Clear Neo4j
        with self.driver.session() as session:
            session.run("""
                MATCH (n {user_id: $user_id, project_id: $project_id})
                DETACH DELETE n
            """, user_id=user_id, project_id=project_id)
            
        # Rebuild FAISS (Inefficient but correct for complete isolation without managed vector DB)
        # In production, use Pinecone/Weaviate with metadata filtering instead of FAISS local
        logger.info(f"Cleared memories for user {user_id} project {project_id}. Rebuilding index...")
        
        # NOTE: This part clears the ENTIRE index and rebuilds only from remaining neo4j data
        # This is a heavy operation.
        
        if os.path.exists(self.vector_store_path):
             shutil.rmtree(self.vector_store_path)
             
        # Fetch ALL remaining memories from Neo4j (all users/projects) to rebuild
        with self.driver.session() as session:
            result = session.run("MATCH (m:Memory) RETURN m.text as text, m.user_id as user_id, m.project_id as project_id, m.source as source")
            records = list(result)
            
        if not records:
            self.vector_store = None
            return

        texts = [r["text"] for r in records]
        metadatas = [{"user_id": r["user_id"], "project_id": r.get("project_id", "default"), "source": r["source"]} for r in records]
        
        self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        self._save_vector_store()
        
        logger.info("Cleared project memories and rebuilt index")

    def get_total_memory_count(self, user_id: str, project_id: str) -> int:
        """Get total count of memories for user and project"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Memory {user_id: $user_id, project_id: $project_id})
                RETURN count(m) as total_count
            """, user_id=user_id, project_id=project_id)
            
            record = result.single()
            return record["total_count"] if record else 0

memory_service = MemoryService()
