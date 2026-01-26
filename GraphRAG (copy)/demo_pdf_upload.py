"""
PDF Upload Demo
Shows how PDF processing works step by step
"""

from pdf_processor import pdf_processor, upload_pdf
import os

# Create sample PDF for testing
def create_sample_pdf():
    """Create a sample PDF file for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        print("[INFO] reportlab not installed, creating text file instead")
        create_sample_txt()
        return
    
    pdf_path = "/home/parth/Desktop/Learning/GraphRAG/uploads/sample_document.pdf"
    os.makedirs("/home/parth/Desktop/Learning/GraphRAG/uploads", exist_ok=True)
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # Page 1
    c.drawString(50, 750, "SAMPLE DOCUMENT - Company Information")
    c.drawString(50, 720, "")
    y = 700
    
    text = [
        "Company: GraphRAG Corp",
        "Founded: 2025",
        "",
        "Our Leadership Team:",
        "- Parth Kumar: Chief Technology Officer",
        "- Mr. Raju: VP of Engineering",
        "- Adil: Head of Research",
        "",
        "What we do:",
        "GraphRAG Corp specializes in AI and machine learning solutions.",
        "We build knowledge graphs for enterprise customers.",
        "Our AI systems extract relationships and entities from documents.",
        "",
        "Office Locations:",
        "- Headquarters: Mumbai, India",
        "- R&D Center: Bangalore, India",
        "",
        "Our Technology:",
        "We use graph databases like Neo4j for storing relationships.",
        "Vector embeddings from OpenAI power our semantic search.",
        "FAISS provides fast similarity matching across millions of documents."
    ]
    
    for line in text:
        c.drawString(50, y, line)
        y -= 20
    
    c.showPage()
    c.save()
    print(f"[CREATED] Sample PDF: {pdf_path}")
    return pdf_path


def create_sample_txt():
    """Create a sample TXT file"""
    txt_path = "/home/parth/Desktop/Learning/GraphRAG/uploads/sample_document.txt"
    os.makedirs("/home/parth/Desktop/Learning/GraphRAG/uploads", exist_ok=True)
    
    content = """
COMPANY INFORMATION DOCUMENT
=====================================

Company: GraphRAG Corp
Founded: 2025
Industry: Artificial Intelligence & Machine Learning

LEADERSHIP TEAM
=====================================
- Parth Kumar: Chief Technology Officer
- Mr. Raju: VP of Engineering  
- Adil: Head of Research

COMPANY OVERVIEW
=====================================
GraphRAG Corp specializes in AI and machine learning solutions.
We build knowledge graphs for enterprise customers.
Our AI systems extract relationships and entities from documents.
We help companies understand complex data relationships.

OFFICE LOCATIONS
=====================================
- Headquarters: Mumbai, India
- R&D Center: Bangalore, India

TECHNOLOGY STACK
=====================================
We use graph databases like Neo4j for storing relationships.
Vector embeddings from OpenAI power our semantic search.
FAISS provides fast similarity matching across millions of documents.
Python is our primary development language.

PRODUCTS & SERVICES
=====================================
1. GraphRAG Platform - Knowledge Graph Creation
2. Entity Extraction Service - Automated entity identification
3. Relationship Discovery - Find hidden connections in data
4. Semantic Search - AI-powered document search
5. Custom AI Solutions - Tailored for enterprise needs

PARTNERSHIPS
=====================================
We partner with leading AI and database vendors.
Our team has expertise with Neo4j, OpenAI, and LangChain.
We collaborate with academic institutions for research.
"""
    
    with open(txt_path, 'w') as f:
        f.write(content)
    
    print(f"[CREATED] Sample TXT: {txt_path}")
    return txt_path


def demo_pdf_workflow():
    """Demonstrate complete PDF workflow"""
    
    print("\n" + "="*80)
    print("PDF UPLOAD & PROCESSING WORKFLOW DEMONSTRATION")
    print("="*80)
    
    # Create sample files
    print("\n[STEP 1] Creating sample documents...")
    txt_file = create_sample_txt()
    
    try:
        pdf_file = create_sample_pdf()
    except:
        print("[INFO] PDF creation skipped, will use TXT instead")
        pdf_file = None
    
    # Import GraphRAG components
    from memory_manager import load_vector_store
    from retrieve import retrieval
    
    print("\n[STEP 2] Loading vector store...")
    load_vector_store()
    
    # Upload TXT file
    print("\n[STEP 3] Uploading TXT document...")
    result1 = upload_pdf(txt_file, source="company_info")
    
    if result1:
        print(f"\n✅ SUCCESS! Document ingested:")
        print(f"   - Characters extracted: {result1['extracted_chars']}")
        print(f"   - Chunks created: {result1['doc_info']['chunk_count']}")
        print(f"   - Source: {result1['source']}")
    
    # Upload PDF if available
    if pdf_file and os.path.exists(pdf_file):
        print("\n[STEP 4] Uploading PDF document...")
        result2 = upload_pdf(pdf_file, source="sample_pdf")
        
        if result2:
            print(f"\n✅ SUCCESS! PDF ingested:")
            print(f"   - Characters extracted: {result2['extracted_chars']}")
            print(f"   - Chunks created: {result2['doc_info']['chunk_count']}")
            print(f"   - Source: {result2['source']}")
    
    # Query the uploaded documents
    print("\n[STEP 5] Testing queries on uploaded documents...")
    
    test_queries = [
        "Who is the CTO of GraphRAG Corp?",
        "What is the headquarters location?",
        "What technology stack do they use?",
        "Who are the key team members?",
        "What services does GraphRAG Corp provide?"
    ]
    
    print(f"\n{'='*80}")
    print("TESTING QUERIES")
    print(f"{'='*80}")
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        print("-" * 80)
        retrieval.ask_question(query)
        print()


def show_pdf_workflow_explanation():
    """Explain how PDF processing works"""
    
    explanation = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    HOW PDF UPLOAD WORKS IN GRAPHRAG                        ║
╚════════════════════════════════════════════════════════════════════════════╝

STEP 1: FILE DETECTION
━━━━━━━━━━━━━━━━━━━━━
User selects: [2] Upload PDF/Document file
Supported formats: PDF, TXT, DOCX, PPTX
System detects file type from extension

STEP 2: TEXT EXTRACTION
━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────┐
│ PDF File:      PyPDF2.PdfReader extracts    │
│                text from each page           │
├─────────────────────────────────────────────┤
│ TXT File:      Simple file.read()            │
├─────────────────────────────────────────────┤
│ DOCX File:     python-docx extracts from    │
│                paragraphs                    │
└─────────────────────────────────────────────┘

STEP 3: TEXT CLEANING
━━━━━━━━━━━━━━━━━━━━
✓ Remove extra whitespace
✓ Clean special characters
✓ Preserve readability
✓ Remove null bytes

STEP 4: DOCUMENT INGESTION
━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────┐
│ Raw Text (200KB)                            │
│         ↓                                    │
│ split_document() - Sentence-based chunking   │
│         ↓                                    │
│ 25 Chunks (80-100 words each)              │
│         ↓                                    │
│ OpenAI Embeddings (Semantic vectors)        │
│         ↓                                    │
│ FAISS Vector Store (Fast similarity search) │
│         ↓                                    │
│ Neo4j Graph DB (Entity relationships)       │
└─────────────────────────────────────────────┘

STEP 5: MEMORY CREATION
━━━━━━━━━━━━━━━━━━━━━━
For each chunk:
├─ Create embedding (OpenAI)
├─ Store in FAISS (faiss_index/)
├─ Extract entities (Named Entity Recognition)
├─ Store entities in Neo4j
├─ Create relationships (NEXT, RELATED, etc.)
└─ Add metadata (timestamp, source, chunk_index)

STEP 6: QUERY RETRIEVAL
━━━━━━━━━━━━━━━━━━━━━
When user asks question:
├─ Question → OpenAI Embedding
├─ Search FAISS (k=15 nearest chunks)
├─ Re-rank by entity matching
├─ Combine with Neo4j graph data
├─ Send to GPT-4o-mini
└─ Generate answer with citations

═══════════════════════════════════════════════════════════════════════════════

EXAMPLE: Upload "company.pdf" containing company info

INPUT:  "company.pdf" (250KB, 10 pages)
           ↓
EXTRACTED: 5000 characters of text
           ↓
CHUNKS: 50 chunks (80-100 words each)
           ↓
FAISS VECTORS: 50 embeddings
           ↓
NEO4J ENTITIES: [Company, Person, Location, Product]
           ↓
RELATIONSHIPS: Company-HAS-Employee, Company-LOCATED_IN-Location

USER QUERY: "Who works at the company?"
           ↓
FAISS SEARCH: Retrieves 15 most relevant chunks
           ↓
ENTITY MATCHING: Finds Person entities linked to Company
           ↓
NEO4J QUERY: Finds all employees via WORKS_AT relationships
           ↓
ANSWER: "Based on the document, [List of people and their roles]"

═══════════════════════════════════════════════════════════════════════════════

KEY FILES INVOLVED
━━━━━━━━━━━━━━━━
pdf_processor.py     → PDF extraction & processing
ingest.py            → Document ingestion
memory_manager.py    → Chunking & embeddings
db.py                → Neo4j database
vector_store.py      → FAISS storage
retrieve.py          → Query & answer generation

═══════════════════════════════════════════════════════════════════════════════
"""
    
    print(explanation)


if __name__ == "__main__":
    show_pdf_workflow_explanation()
    print("\n[RUNNING] PDF Upload Demo...\n")
    demo_pdf_workflow()
