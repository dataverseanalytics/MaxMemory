#!/usr/bin/env python3
"""
Demo: Improved Answer Display with Metadata
Shows how answers now display with source information and metadata
"""

import sys
sys.path.insert(0, '/home/parth/Desktop/Learning/GraphRAG')

from retrieve import QueryRetrieval
from memory_manager import add_chunk_memory, get_all_memories
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("""
╔═══════════════════════════════════════════════════════════════╗
║   DEMO: Improved Answer Display with Metadata                ║
║                                                               ║
║   This demo shows the new answer format that includes:       ║
║   ✓ Proper answers (not Memory references)                  ║
║   ✓ Source information (document name)                      ║
║   ✓ Timestamps (when added)                                 ║
║   ✓ Priority levels                                         ║
║   ✓ Source citations at the end                             ║
╚═══════════════════════════════════════════════════════════════╝
""")

# Sample data with different sources
sample_data = [
    ("Parth Kumar is the CTO of GraphRAG Corporation", "Personal Profile", 2.0),
    ("Raju is Parth's best friend and works at DRC Systems", "Personal Notes", 1.5),
    ("Adil is another friend who works as a Data Scientist", "Personal Notes", 1.5),
    ("[NEG] Parth no longer works at TechCorp", "Career History", 1.0),
    ("Parth lives in Mumbai and loves coding", "Personal Profile", 1.0),
    ("Raju and Parth met at college in 2018", "Friends Info", 1.0),
    ("DRC Systems is a software development company", "Company Info", 1.0),
    ("GraphRAG is a knowledge graph project", "Project Info", 1.5),
    ("Parth's interests include AI, machine learning, and graph databases", "Personal Profile", 1.0),
    ("The team works on advanced data processing", "Project Info", 1.0),
]

# Add sample data
print("\n[ADDING SAMPLE DATA TO MEMORY]")
print("="*60)

for text, source, priority in sample_data:
    add_chunk_memory(text, priority=priority, source=source)
    print(f"✓ Added: {text[:50]}... (source: {source})")

print(f"\n[TOTAL MEMORIES STORED]: {len(get_all_memories())}")

# Create retrieval instance
retrieval = QueryRetrieval()

# Test queries
test_queries = [
    "What is Parth's job?",
    "Who are Parth's friends?",
    "Where does Parth live?",
    "Is Parth still working at TechCorp?",
    "What are Parth's interests?",
]

print("\n" + "="*60)
print("[TESTING QUERIES WITH NEW METADATA FORMAT]")
print("="*60)

for idx, query in enumerate(test_queries, 1):
    print(f"\n\n[TEST {idx}] Query: {query}")
    print("-"*60)
    retrieval.ask_question(query, k=7)
    
    if idx < len(test_queries):
        input("\n[Press Enter to continue to next query...]")

print("\n" + "="*60)
print("[DEMO COMPLETE]")
print("="*60)
print("""
KEY IMPROVEMENTS:
═════════════════

✓ NO MORE "Memory X" in answers
  ✗ Old: "YES, Parth is the CTO (from Memory 1)"
  ✓ New: "YES, Parth Kumar is the CTO of GraphRAG Corporation"

✓ METADATA IN CONTEXT
  ✓ Each memory shows: Source, Priority, Timestamp
  ✓ LLM sees all metadata for better context understanding

✓ SOURCES CITED AT END
  ✓ After answer, shows which documents were used
  ✓ Example: "Memory 1: Personal Profile (2025-12-19)"

✓ BETTER FORMATTING
  ✓ Pretty boxes around memory info
  ✓ Clear separation between memories
  ✓ Easy to scan and understand

✓ PROPER ANSWER GENERATION
  ✓ Answers focus on content, not memory names
  ✓ Source info is reference, not part of answer
  ✓ More natural language responses
""")
