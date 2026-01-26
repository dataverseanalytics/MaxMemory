# GraphRAG Architecture & Potential Issues Analysis

## 1. EMBEDDING STRATEGY (Entity Representation)

### ✅ Current Setup
- **FAISS Vector Store**: Uses `OpenAIEmbeddings` from langchain_openai
- **File**: memory_manager.py, line 4: `from langchain_openai import OpenAIEmbeddings`
- **Initialization**: `embeddings = OpenAIEmbeddings(api_key=api_key)`
- **YES - Using OpenAI for embeddings**: Each chunk gets embedded using OpenAI's embedding model
- **Entity Representation**: Not explicitly extracting entities - treating entire chunks as semantic units

### ⚠️ Potential Issues
1. **No Named Entity Recognition (NER)**: System doesn't extract individual entities (Parth, Raju, Adil, DRC Systems)
2. **Chunk-Based Not Entity-Based**: Retrieval relies on semantic similarity of text chunks, not entity relationships
3. **Missing Entity Linking**: No explicit connection between "Parth", "Software Engineer", "DRC Systems" in graph

## 2. RETRIEVAL FLOW (FAISS)

### Current Flow
```
Query
  ↓
OpenAI Embedding (text → vector)
  ↓
FAISS Similarity Search (vector similarity matching)
  ↓
Top-K Chunks Retrieved
  ↓
LLM Answer Generation
```

### ✅ What's Working
- FAISS properly loads/saves to disk
- Chunks are stored in both FAISS (semantic) and Neo4j (graph)
- Multiple search strategies (typo correction, keyword fallback)

### ⚠️ Potential Issues
1. **Vector Quality**: If OpenAI embedding API is slow/fails, system silently falls back to Neo4j
2. **Semantic Mismatch**: "Who is your friend?" may not semantically match "Parth is good friend of Raju"
3. **Chunk Size Sensitivity**: 100-word chunks may not align perfectly with entity boundaries

## 3. NEO4J STORAGE (Graph Database)

### Current Structure
```
(Memory {text: chunk, timestamp, priority, source})
```

### ⚠️ Issues
1. **Flat Structure**: No explicit entity nodes (Person, Company, Job)
2. **No Relationships**: Graph stores only Memory nodes, not entity connections
3. **Unused Potential**: Neo4j is used for storage only, not for querying relationships
4. **Missing Graph Traversal**: Can't query "Parth → friends → Raju"

## 4. ANSWER GENERATION (LLM)

### Current Setup
- Uses ChatOpenAI (gpt-4o-mini)
- Receives top-K chunks from FAISS
- Generates answer based on chunk text only

### ⚠️ Issues
1. **Hallucination**: LLM might infer info not explicitly in chunks
2. **Negation Logic**: LLM struggles with "NOT working", "no longer"
3. **Multi-Entity**: When multiple friends exist, retrieval might not get all chunks

## 5. ROOT CAUSES FOR RETRIEVAL FAILURES

### Problem 1: Missing Adil in Results
- Document says "Adil is Parth's good friend"
- Query: "who are my good friends?"
- Expected: "Raju and Adil"
- Actual: "Raju" only

**Possible Causes:**
1. FAISS only returns top-5 chunks, Adil chunk might rank lower
2. OpenAI embedding may rank Raju chunk higher (appears in multiple docs)
3. Chunk boundary might split "Adil is friend" across chunks

### Problem 2: Negation Not Working
- Document: "Raju is NOT working at DRC" / "He left DRC"
- Query: "Is Raju still at DRC?"
- Expected: "No"
- Actual: Might say "Yes" or list him as working

**Possible Cause:**
- LLM doesn't see the negation chunk due to FAISS ranking
- Chunk with "left the company" might not be retrieved

## 6. RECOMMENDATIONS

### Quick Fixes (High Impact)
1. **Increase k parameter**: Retrieve top-10 or top-15 instead of top-5
2. **Add entity extraction**: Parse chunks for names, companies, jobs
3. **Explicit negation handling**: Add markers like [NEGATION: NOT] to chunks

### Medium Fixes
1. **Use graph retrieval**: Query Neo4j for entity relationships
2. **Hybrid search**: Combine FAISS (semantic) + Neo4j (graph) results
3. **Re-rank results**: Order chunks by entity importance, not just similarity

### Long-term Architecture
1. **True GraphRAG**: Extract entities → store in graph → retrieve via relationships
2. **Entity-aware embeddings**: Embed entities separately from descriptions
3. **Knowledge graph**: Explicit Person, Company, Relationship nodes

