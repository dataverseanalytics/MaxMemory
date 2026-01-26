"""
Query Retrieval Module
Handles retrieving memories and generating answers using LLM
"""

from memory_manager import retrieve_relevant_memories, get_all_memories
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))


class QueryRetrieval:
    """Handles query retrieval and answer generation"""
    
    def __init__(self):
        self.queries = []
        self.answers = []
    
    def generate_answer(self, query, memories):
        """
        Generate an answer based on retrieved memories using LLM
        
        Args:
            query (str): The question to answer
            memories (list): List of retrieved memory dictionaries
        
        Returns:
            str: The generated answer
        """
        # Extract text and metadata from memories (handle both dict and object formats)
        def extract_text(m):
            if isinstance(m, dict):
                return m.get('text', str(m))
            return str(m.get('text', m) if hasattr(m, 'get') else m)
        
        def extract_metadata(m):
            if isinstance(m, dict):
                source = m.get('source', 'unknown')
                priority = m.get('priority', 1.0)
                timestamp = m.get('timestamp', 'unknown')
                return {'source': source, 'priority': priority, 'timestamp': timestamp}
            return {'source': 'unknown', 'priority': 1.0, 'timestamp': 'unknown'}
        
        # Format memories with numbering, text, and metadata for reference
        relevant_context = ""
        for idx, m in enumerate(memories, 1):
            text = extract_text(m)
            meta = extract_metadata(m)
            source = meta['source']
            priority = meta['priority']
            timestamp = str(meta['timestamp'])[:19] if meta['timestamp'] != 'unknown' else 'unknown'
            
            relevant_context += f"\n[Memory {idx}] (Source: {source} | Priority: {priority} | Added: {timestamp})\n{text}"
        
        # Create focused prompt that forces explicit answers for YES/NO, handles negation, and lists all items
        prompt = f"""You are a helpful assistant answering questions based on personal memories. Your task is to answer the user's question accurately based ONLY on the provided memories.

CRITICAL INSTRUCTIONS:

1. **YES/NO QUESTIONS**: Answer directly with YES or NO first, then explain
   - Example: "Is Raju your friend?" → "Yes, Raju is my friend because..."

2. **NEGATION HANDLING**: Pay special attention to [NEG] markers and words like "NOT", "no longer", "left", "doesn't"
   - "[NEG] Raju left DRC" means Raju is NOT at DRC anymore
   - Answer "No" if the question asks about a negated fact

3. **MULTIPLE ITEMS**: Always list ALL items mentioned in memories, not just one
   - If 2+ friends are mentioned, list ALL of them: "Raju and Adil"
   - Example: "Who are my friends?" → "Raju and Adil" (not just one)

4. **PERSPECTIVE CLARITY**: 
   - "I" = Parth (the person being described)
   - "You" = Also Parth
   - When memories say "Parth is friends with X", it means X is my friend

5. **FACTS vs INFERENCE**:
   - Only answer based on explicit facts in memories
   - Do NOT infer, assume, or add information

6. **MEMORY CITATION - INCLUDE METADATA**:
   - When citing memories, include source and document info
   - Example: (from Memory 2 - Personal notes) or (from Memory 5 - Uploaded document)
   - Include metadata only if it's relevant to understanding the source

RELEVANT MEMORIES (READ ALL OF THEM COMPLETELY):
{relevant_context}

User Question: {query}

ANSWER:"""
        
        # Generate answer
        response = llm.invoke(prompt)
        return response.content
    
    def ask_question(self, query, k=15):  # INCREASED FROM 5 TO 15
        """
        Ask a question and get an answer
        
        Args:
            query (str): The question to ask
            k (int): Number of top memories to retrieve
        
        Returns:
            dict: Query results including memories and answer
        """
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"{'='*60}")
        
        # Retrieve relevant memories (semantic search only)
        memories = retrieve_relevant_memories(query, k=k)
        
        if not memories:
            print(f"\n[NO MEMORIES FOUND] Unable to find relevant information for this query")
            return {"query": query, "memories_count": 0, "memories": [], "answer": "No relevant information found."}
        
        print(f"\n[RETRIEVED {len(memories)} SEMANTIC MATCHES]")
        for i, m in enumerate(memories, start=1):
            # Extract text and metadata properly
            text = m.get('text', str(m)) if isinstance(m, dict) else str(m)
            source = m.get('source', 'unknown') if isinstance(m, dict) else 'unknown'
            priority = m.get('priority', 1.0) if isinstance(m, dict) else 1.0
            timestamp = m.get('timestamp', 'unknown') if isinstance(m, dict) else 'unknown'
            timestamp_str = str(timestamp)[:19] if timestamp != 'unknown' else 'unknown'
            
            # Pretty print with metadata
            print(f"\n┌─ [MEMORY {i}] ─────────────────────────────────────")
            print(f"│ Source: {source}")
            print(f"│ Priority: {priority} | Added: {timestamp_str}")
            print(f"├─ Content:")
            print(f"│ {text[:150]}{'...' if len(text) > 150 else ''}")
            print(f"└{'─'*50}")
        
        # Generate answer
        print(f"\n[GENERATING ANSWER...]")
        answer = self.generate_answer(query, memories)
        
        # Pretty print answer with metadata references
        print(f"\n{'='*60}")
        print(f"[ANSWER]")
        print(f"{'='*60}")
        print(f"\n{answer}")
        print(f"\n{'='*60}")
        print(f"[SOURCES USED]")
        print(f"{'='*60}")
        for i, m in enumerate(memories[:5], start=1):  # Show top 5 sources
            source = m.get('source', 'unknown') if isinstance(m, dict) else 'unknown'
            timestamp = m.get('timestamp', 'unknown') if isinstance(m, dict) else 'unknown'
            timestamp_str = str(timestamp)[:10] if timestamp != 'unknown' else 'unknown'
            print(f"  Memory {i}: {source} ({timestamp_str})")
        
        # Store query and answer
        query_result = {
            "query": query,
            "memories_count": len(memories),
            "memories": memories,
            "answer": answer
        }
        self.queries.append(query_result)
        self.answers.append(answer)
        
        return query_result
    
    def get_query_history(self):
        """Get all previous queries and answers"""
        print(f"\n{'='*60}")
        print("QUERY HISTORY")
        print(f"{'='*60}")
        
        if not self.queries:
            print("[INFO] No queries made yet")
            return
        
        for i, q in enumerate(self.queries, start=1):
            print(f"\n[QUERY {i}] {q['query'][:60]}...")
            print(f"  Memories Retrieved: {q['memories_count']}")
            print(f"  Answer: {q['answer'][:100]}...")
    
    def clear_query_history(self):
        """Clear query history"""
        self.queries = []
        self.answers = []
        print("[INFO] Query history cleared")
    
    def compare_answers(self, query1, query2):
        """
        Compare answers to two different queries
        
        Args:
            query1 (str): First question
            query2 (str): Second question
        """
        print(f"\n{'='*60}")
        print("COMPARING ANSWERS")
        print(f"{'='*60}")
        
        result1 = self.ask_question(query1)
        result2 = self.ask_question(query2)
        
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}")
        print(f"\nQuery 1: {query1}")
        print(f"Answer 1: {result1['answer'][:150]}...")
        print(f"\nQuery 2: {query2}")
        print(f"Answer 2: {result2['answer'][:150]}...")


# Create a global instance for easy access
retrieval = QueryRetrieval()


def quick_ask(query, k=5):
    """Quick function to ask a question"""
    return retrieval.ask_question(query, k=k)


def get_query_history():
    """Get all previous queries"""
    retrieval.get_query_history()


def clear_history():
    """Clear query history"""
    retrieval.clear_query_history()


def compare_queries(query1, query2):
    """Compare answers to two queries"""
    retrieval.compare_answers(query1, query2)
