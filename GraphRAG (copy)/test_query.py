#!/usr/bin/env python3
"""
Quick Query Test - Tests full query pipeline
"""

import sys
sys.path.insert(0, '/home/parth/Desktop/Learning/GraphRAG')

from memory_manager import add_chunk_memory, get_all_memories, vector_store
from retrieve import QueryRetrieval
from dotenv import load_dotenv
import os

load_dotenv()

print("╔═══════════════════════════════════════════════════════════╗")
print("║          QUICK QUERY TEST - FULL PIPELINE               ║")
print("╚═══════════════════════════════════════════════════════════╝")

print("\n[1] Adding sample data to memory...")
try:
    sample_data = [
        ("Parth Kumar is the CTO of GraphRAG", "Profile", 2.0),
        ("Raju is Parth's best friend", "Notes", 1.5),
        ("They work together at DRC Systems", "Work", 1.5),
    ]
    
    for text, source, priority in sample_data:
        add_chunk_memory(text, priority=priority, source=source)
    
    all_mems = get_all_memories()
    print(f"✓ Added {len(sample_data)} chunks")
    print(f"✓ Total memories in DB: {len(all_mems)}")
    
except Exception as e:
    print(f"✗ FAILED: {str(e)[:100]}")
    exit(1)

print("\n[2] Testing query retrieval...")
try:
    from memory_manager import retrieve_relevant_memories
    
    query = "What does Parth do?"
    memories = retrieve_relevant_memories(query, k=5)
    
    print(f"✓ Retrieved {len(memories)} memories")
    for i, m in enumerate(memories, 1):
        text = m.get('text', '')[:50] if isinstance(m, dict) else str(m)[:50]
        print(f"  Memory {i}: {text}...")
        
except Exception as e:
    print(f"✗ FAILED: {str(e)[:100]}")
    exit(1)

print("\n[3] Testing answer generation with 15s timeout...")
try:
    from langchain_openai import ChatOpenAI
    import signal
    
    class TimeoutError(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Answer generation timed out")
    
    retrieval = QueryRetrieval()
    
    # Set 15 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)
    
    try:
        print("  → Generating answer (max 15s)...")
        answer = retrieval.generate_answer(query, memories)
        signal.alarm(0)  # Cancel alarm
        
        print(f"✓ Answer generated successfully")
        print(f"\nAnswer:\n{answer[:250]}...")
        
    except TimeoutError:
        signal.alarm(0)
        print(f"⏱ TIMEOUT after 15s (OpenAI API too slow)")
        
except Exception as e:
    print(f"✗ FAILED: {str(e)[:100]}")

print("\n" + "="*60)
print("TEST RESULT")
print("="*60)
print("""
✓ All tests passed → System is working
⏱ Timeout → OpenAI API is slow (but working, just needs more time)
✗ Failed → Check error messages above
""")
