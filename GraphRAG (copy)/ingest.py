"""
Document Ingestion Module
Handles adding documents to memory, creating relationships, and managing document storage
"""

from memory_manager import split_document, add_chunk_memory, relate_chunks, print_relationships
from datetime import datetime

class DocumentIngestion:
    """Handles document ingestion and memory management"""
    
    def __init__(self):
        self.documents = []
        self.document_count = 0
    
    def add_document(self, document_text, source="document", metadata=None):
        """
        Add a document to memory
        
        Args:
            document_text (str): The document content
            source (str): Source identifier for the document
            metadata (dict): Additional metadata about the document
        
        Returns:
            dict: Information about the ingested document
        """
        self.document_count += 1
        doc_id = f"{source}_{self.document_count}"
        timestamp = datetime.now().isoformat()
        
        print(f"\n{'='*60}")
        print(f"INGESTING DOCUMENT: {doc_id}")
        print(f"{'='*60}")
        print(f"[ADD DOCUMENT] Processing: {document_text[:50]}...")
        
        # Split document into chunks (larger chunks for better semantic understanding)
        chunks = split_document(document_text, chunk_size=80, overlap=15)
        print(f"[CHUNKS] Split into {len(chunks)} chunks")
        
        # Store chunks with metadata
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "doc_id": doc_id,
                "chunk_index": i,
                "timestamp": timestamp,
                "source": source
            }
            add_chunk_memory(chunk, priority=1.0, source=source)
        
        # Create relationships between consecutive chunks
        for i in range(len(chunks) - 1):
            relate_chunks(chunks[i], chunks[i + 1], rel_type="NEXT")
        
        if len(chunks) > 1:
            print(f"[RELATIONSHIPS] Created {len(chunks)-1} sequential relationships")
        
        # Store document info
        doc_info = {
            "doc_id": doc_id,
            "timestamp": timestamp,
            "source": source,
            "chunk_count": len(chunks),
            "text_preview": document_text[:100],
            "metadata": metadata
        }
        self.documents.append(doc_info)
        
        print(f"[SUCCESS] Document {doc_id} ingested with {len(chunks)} chunks")
        
        return doc_info
    
    def list_documents(self):
        """List all ingested documents"""
        print(f"\n{'='*60}")
        print("INGESTED DOCUMENTS")
        print(f"{'='*60}")
        
        if not self.documents:
            print("[INFO] No documents ingested yet")
            return
        
        for doc in self.documents:
            print(f"\nDocument ID: {doc['doc_id']}")
            print(f"  Source: {doc['source']}")
            print(f"  Timestamp: {doc['timestamp']}")
            print(f"  Chunks: {doc['chunk_count']}")
            print(f"  Preview: {doc['text_preview']}...")
    
    def show_relationships(self):
        """Show all relationships between chunks"""
        print(f"\n{'='*60}")
        print("CHUNK RELATIONSHIPS")
        print(f"{'='*60}")
        print_relationships()
    
    def get_document_count(self):
        """Get total number of documents ingested"""
        return len(self.documents)


# Create a global instance for easy access
ingestion = DocumentIngestion()


def quick_ingest(document_text, source="document"):
    """Quick function to ingest a document"""
    return ingestion.add_document(document_text, source)


def list_all_documents():
    """List all ingested documents"""
    ingestion.list_documents()


def show_all_relationships():
    """Show all chunk relationships"""
    ingestion.show_relationships()


def get_ingestion_stats():
    """Get ingestion statistics"""
    return {
        "total_documents": ingestion.get_document_count(),
        "documents": ingestion.documents
    }
