#!/usr/bin/env python3
"""
Fast Query Demo - Shows metadata display without OpenAI latency
"""

import sys
sys.path.insert(0, '/home/parth/Desktop/Learning/GraphRAG')

from memory_manager import get_all_memories, load_vector_store, retrieve_relevant_memories
from dotenv import load_dotenv

load_dotenv()
load_vector_store()

print("""
╔════════════════════════════════════════════════════════════╗
║    FAST QUERY DEMO - Memory Retrieval & Metadata Display  ║
║                                                            ║
║  Shows how answers retrieve memories with metadata:       ║
║  ✓ Memory source (document name)                          ║
║  ✓ Priority level                                         ║
║  ✓ Timestamp (when added)                                 ║
║  ✓ Formatted display                                      ║
╚════════════════════════════════════════════════════════════╝
""")

test_queries = [
    "What is Parth's job?",
    "Who are Parth's friends?",
    "Where does Parth live?",
    "Does Parth work at TechCorp?",
]

print("\n[AVAILABLE MEMORIES IN DATABASE]")
print("="*60)
all_memories = get_all_memories()
print(f"Total memories stored: {len(all_memories)}\n")

for i, m in enumerate(all_memories[:5], 1):
    text = m.get('text', 'N/A') if isinstance(m, dict) else str(m)
    source = m.get('source', 'unknown') if isinstance(m, dict) else 'unknown'
    priority = m.get('priority', 1.0) if isinstance(m, dict) else 1.0
    print(f"{i}. [{source}] (priority: {priority}) → {text[:50]}...")

print("\n[RUNNING QUERIES - SHOWING METADATA RETRIEVAL]")
print("="*60)

for idx, query in enumerate(test_queries, 1):
    print(f"\n\n[QUERY {idx}] {query}")
    print("-"*60)
    
    # Retrieve memories
    memories = retrieve_relevant_memories(query, k=5)
    
    if memories:
        print(f"Found {len(memories)} relevant memories:\n")
        
        # Display with metadata (like in the updated retrieve.py)
        for mem_idx, m in enumerate(memories, 1):
            text = m.get('text', 'N/A') if isinstance(m, dict) else str(m)
            source = m.get('source', 'unknown') if isinstance(m, dict) else 'unknown'
            priority = m.get('priority', 1.0) if isinstance(m, dict) else 1.0
            timestamp = m.get('timestamp', 'unknown') if isinstance(m, dict) else 'unknown'
            timestamp_str = str(timestamp)[:19] if timestamp != 'unknown' else 'unknown'
            
            # Pretty format like in retrieve.py
            print(f"┌─ [MEMORY {mem_idx}] ─────────────────────────────────────")
            print(f"│ Source: {source}")
            print(f"│ Priority: {priority} | Added: {timestamp_str}")
            print(f"├─ Content:")
            print(f"│ {text[:150]}{'...' if len(text) > 150 else ''}")
            print(f"└{'─'*50}\n")
        
        # Show sources summary
        print("[SOURCES USED IN ANSWER]")
        print("-"*40)
        for i, m in enumerate(memories[:3], 1):
            source = m.get('source', 'unknown') if isinstance(m, dict) else 'unknown'
            timestamp = m.get('timestamp', 'unknown') if isinstance(m, dict) else 'unknown'
            timestamp_str = str(timestamp)[:10] if timestamp != 'unknown' else 'unknown'
            print(f"  Memory {i}: {source} ({timestamp_str})")
    else:
        print("No relevant memories found")

print("\n\n" + "="*60)
print("[DEMO COMPLETE]")
print("="*60)
print("""
KEY IMPROVEMENTS IN ANSWER DISPLAY:
═══════════════════════════════════

✓ BEFORE (old format):
  "YES, Parth is the CTO (from Memory 1)"
  - Generic memory reference
  - No metadata visible
  - Not user-friendly

✓ AFTER (new format):
  "YES, Parth Kumar is the CTO of GraphRAG Corporation"
  
  Sources used:
  - Memory 1: Personal Profile (2025-12-19)
  - Memory 2: Company Info (2025-12-19)
  
  - Clean, professional answer
  - Metadata visible for verification
  - User sees document sources
  - Timestamps for audit trail

HOW IT WORKS:
═════════════

1. Query retrieves memories using semantic search
2. Each memory has metadata:
   ├─ text: The actual content
   ├─ source: Where it came from
   ├─ priority: Importance level
   └─ timestamp: When it was added

3. LLM sees all metadata in context
   └─ Helps generate better answers

4. Answer doesn't mention memory names
   └─ Focuses on content, not references

5. Sources displayed at end
   └─ User knows which documents were used
""")
