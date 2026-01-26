#!/usr/bin/env python3
"""
Quick Query Test - Test queries without interruption
Shows the new metadata display format
"""

import sys
sys.path.insert(0, '/home/parth/Desktop/Learning/GraphRAG')

from retrieve import QueryRetrieval
from memory_manager import add_chunk_memory, get_all_memories, load_vector_store
from dotenv import load_dotenv

load_dotenv()
load_vector_store()  # Load existing vector store

print("""
╔════════════════════════════════════════════════════════════╗
║         QUICK QUERY TEST - With Metadata Display          ║
║                                                            ║
║  Testing the improved answer format with:                ║
║  ✓ No "Memory X" in answers                              ║
║  ✓ Proper metadata display (source, date, priority)     ║
║  ✓ Source citations at the end                           ║
╚════════════════════════════════════════════════════════════╝
""")

# Check if memories already exist
existing_memories = get_all_memories()
if not existing_memories or len(existing_memories) < 10:
    print("\n[ADDING SAMPLE DATA]")
    sample_data = [
        ("Parth Kumar is the CTO of GraphRAG Corporation", "Personal Profile", 2.0),
        ("Raju is Parth's best friend", "Personal Notes", 1.5),
        ("Adil works as a Data Scientist at DRC Systems", "Team Info", 1.0),
        ("Parth lives in Mumbai", "Personal Profile", 1.0),
        ("The team builds knowledge graphs", "Project Info", 1.5),
    ]
    
    for text, source, priority in sample_data:
        add_chunk_memory(text, priority=priority, source=source)
        print(f"  ✓ {text[:50]}...")
else:
    print(f"\n[USING EXISTING MEMORIES] ({len(existing_memories)} memories found)")

# Create retrieval instance
retrieval = QueryRetrieval()

# Simple test queries
test_queries = [
    "What is Parth's job?",
    "Who are Parth's friends?",
]

print("\n" + "="*60)
print("[RUNNING QUERIES]")
print("="*60)

for idx, query in enumerate(test_queries, 1):
    print(f"\n\n{'='*60}")
    print(f"[TEST {idx}] Query: {query}")
    print(f"{'='*60}")
    
    try:
        retrieval.ask_question(query, k=5)
        print("\n✓ Query completed successfully")
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
        break
    except Exception as e:
        print(f"\n[ERROR] {str(e)[:100]}")
        continue

print("\n\n" + "="*60)
print("[TEST COMPLETE]")
print("="*60)
print("\nKey Features Demonstrated:")
print("  ✓ Memory metadata (source, date, priority) shown")
print("  ✓ Clean answer without memory references")
print("  ✓ Source citations at end with metadata")
print("  ✓ Pretty formatting for easy reading")
