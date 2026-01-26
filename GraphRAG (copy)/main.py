"""
GraphRAG Main Module
Orchestrates document ingestion and query retrieval
"""

from ingest import ingestion, list_all_documents, show_all_relationships
from retrieve import retrieval, get_query_history, clear_history
from memory_manager import load_vector_store
from pdf_processor import upload_pdf, upload_directory

# ================================
# CONFIGURATION AND DEFINITIONS
# ================================

# Define entities and their relationships
ENTITIES = {
    "Parth": {
        "type": "person",
        "description": "A professional who works at DRC Systems",
        "attributes": ["likes AI", "likes reading", "prefers Python"]
    },
    "Mr. Raju": {
        "type": "person",
        "description": "A friend and colleague of Parth",
        "attributes": ["works at DRC Systems", "is Parth's friend"]
    },
    "DRC Systems": {
        "type": "organization",
        "description": "A company where Parth and Raju work",
        "attributes": ["employer", "workplace"]
    }
}

# Define relationship types
RELATIONSHIP_TYPES = {
    "WORKS_AT": "Employment relationship",
    "IS_FRIEND_OF": "Friendship relationship",
    "RELATED": "General relationship",
    "KNOWS": "Acquaintance relationship",
    "NEXT": "Sequential chunk relationship"
}


def print_entity_definitions():
    """Print all defined entities"""
    print("\n[ENTITY DEFINITIONS]")
    for entity, info in ENTITIES.items():
        print(f"\n  {entity}:")
        print(f"    Type: {info['type']}")
        print(f"    Description: {info['description']}")
        print(f"    Attributes: {', '.join(info['attributes'])}")


def print_relationship_definitions():
    """Print all defined relationship types"""
    print("\n[RELATIONSHIP TYPE DEFINITIONS]")
    for rel_type, description in RELATIONSHIP_TYPES.items():
        print(f"  {rel_type}: {description}")


def print_menu():
    """Print the interactive menu"""
    print(f"\n{'='*60}")
    print("GRAPHRAG INTERACTIVE MENU")
    print(f"{'='*60}")
    print("\n[1] Add a text document")
    print("[2] Upload PDF/Document file")
    print("[3] Ask a question")
    print("[4] View all documents")
    print("[5] View all relationships")
    print("[6] View query history")
    print("[7] Clear query history")
    print("[8] Exit")
    print(f"\n{'='*60}")


def interactive_mode():
    """Run the GraphRAG system in interactive mode"""
    # Load existing vector store
    load_vector_store()
    
    # Print definitions
    print_entity_definitions()
    print_relationship_definitions()
    while True:
        print_menu()
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            # Add text document
            print("\n[ADD DOCUMENT MODE]")
            print("Enter your document (type 'END' on a new line when done):")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            
            if lines:
                document_text = "\n".join(lines)
                source = input("\nEnter source name (default: 'document'): ").strip() or "document"
                ingestion.add_document(document_text, source=source)
            else:
                print("[ERROR] Empty document")
        
        elif choice == "2":
            # Upload PDF/Document file
            print("\n[FILE UPLOAD MODE]")
            print("[1] Upload single file")
            print("[2] Upload entire directory")
            sub_choice = input("\nEnter choice (1-2): ").strip()
            
            if sub_choice == "1":
                file_path = input("Enter file path (PDF, TXT, DOCX): ").strip()
                if file_path:
                    source = input("Enter source name (optional): ").strip() or None
                    result = upload_pdf(file_path, source=source)
                    if result:
                        print(f"\n[SUCCESS] File uploaded successfully!")
                        print(f"  Extracted: {result['extracted_chars']} characters")
                    else:
                        print("[ERROR] Failed to upload file")
                else:
                    print("[ERROR] No file path provided")
            
            elif sub_choice == "2":
                dir_path = input("Enter directory path: ").strip()
                source_prefix = input("Enter source prefix (optional): ").strip() or None
                if dir_path:
                    results = upload_directory(dir_path, source_prefix=source_prefix)
                    if results:
                        print(f"\n[SUCCESS] Uploaded {len(results)} files")
                    else:
                        print("[ERROR] Failed to upload directory")
                else:
                    print("[ERROR] No directory path provided")
            else:
                print("[ERROR] Invalid choice")
        
        elif choice == "3":
            # Ask question
            print("\n[QUERY MODE]")
            query = input("Enter your question: ").strip()
            if query:
                retrieval.ask_question(query)
            else:
                print("[ERROR] Empty query")
        
        elif choice == "4":
            # View documents
            list_all_documents()
        
        elif choice == "5":
            # View relationships
            show_all_relationships()
        
        elif choice == "6":
            # View query history
            get_query_history()
        
        elif choice == "7":
            # Clear history
            confirm = input("\nAre you sure? (yes/no): ").strip().lower()
            if confirm == "yes":
                clear_history()
        
        elif choice == "8":
            # Exit
            print("\n[EXIT] Thank you for using GraphRAG!")
            break
        
        else:
            print("[ERROR] Invalid choice. Please try again.")
            print("[ERROR] Invalid choice. Please try again.")


def demo_mode():
    """Run demo with predefined examples - COMPREHENSIVE DATASET"""
    # Load existing vector store
    load_vector_store()
    
    # Print definitions
    print_entity_definitions()
    print_relationship_definitions()
    
    # ================================
    # DEMO: Document 1 - Parth's Basic Info
    # ================================
    print(f"\n{'='*60}")
    print("DEMO 1: Parth's Profile and Job")
    print(f"{'='*60}")
    
    doc1 = """
    Parth is a Software Engineer working at DRC Systems. 
    Parth works as a Software Engineer. He is employed at DRC Systems as a professional.
    Parth works at DRC Systems. DRC Systems is his workplace and employer.
    Parth's job is Software Engineer. He is employed and working full-time.
    """
    ingestion.add_document(doc1, source="profile")
    
    # ================================
    # DEMO: Document 2 - Parth's Preferences and Interests
    # ================================
    print(f"\n{'='*60}")
    print("DEMO 2: Parth's Preferences and Interests")
    print(f"{'='*60}")
    
    doc2 = """
    Parth likes AI and artificial intelligence. He enjoys working with AI technologies.
    Parth likes reading books, especially technology books. Reading is his hobby.
    Parth prefers Python programming language. Python is his favorite language.
    Parth enjoys sunny weather and likes outdoor activities on sunny days.
    Parth likes cats and coffee. He enjoys cats and likes drinking coffee.
    Parth hates rainy days and dislikes bad weather.
    """
    ingestion.add_document(doc2, source="preferences")
    
    # ================================
    # DEMO: Document 3 - Parth's Friends
    # ================================
    print(f"\n{'='*60}")
    print("DEMO 3: Parth's Friends and Relationships")
    print(f"{'='*60}")
    
    doc3 = """
    Parth is a good friend of Mr. Raju. They are friends and good friends.
    Raju is Parth's friend. Parth and Raju are friends.
    Adil is Parth's good friend. Parth is friends with Adil.
    Adil is my good friend. Adil and I are close friends.
    """
    ingestion.add_document(doc3, source="relationships")
    
    # ================================
    # DEMO: Document 4 - Raju's Original Status
    # ================================
    print(f"\n{'='*60}")
    print("DEMO 4: Raju's Initial Employment")
    print(f"{'='*60}")
    
    doc4 = """
    Raju works at DRC Systems. Raju is employed at DRC Systems as a colleague.
    Raju and Parth work together at DRC Systems. They both work at the same company.
    Raju works with Parth at DRC Systems.
    """
    ingestion.add_document(doc4, source="raju_initial")
    
    # ================================
    # DEMO: Document 5 - Raju's Update
    # ================================
    print(f"\n{'='*60}")
    print("DEMO 5: Raju's Career Update")
    print(f"{'='*60}")
    
    doc5 = """
    Raju is not working at DRC Systems anymore. He left DRC Systems.
    Raju left the company last month. He no longer works at DRC Systems.
    Raju is now working as a freelance consultant. He is a freelancer.
    Raju left DRC and is working as a consultant now.
    """
    ingestion.add_document(doc5, source="raju_update")
    
    show_all_relationships()
    
    # ================================
    # DEMO QUESTIONS
    # ================================
    print(f"\n{'='*60}")
    print("DEMO QUESTIONS - COMPREHENSIVE TEST")
    print(f"{'='*60}")
    
    demo_questions = [
        "Who is Raju? Is he your friend?",
        "Is Raju still working at DRC?",
        "What is your job?",
        "Where do you work?",
        "Do you work at DRC Systems?",
        "Who are your good friends?",
        "Is Adil your friend?",
        "What do you like?",
        "Do you like AI?",
        "Do you prefer Python?",
        "Do you like sunny weather?",
        "What are your hobbies?",
        "Tell me about yourself",
        "What is Raju's current job?",
        "Who works with you?"
    ]
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n[Question {i}] {question}")
        retrieval.ask_question(question)
    
    
    # Show query history
    print(f"\n{'='*60}")
    print("DEMO: Query History")
    print(f"{'='*60}")
    get_query_history()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run demo mode
        demo_mode()
    else:
        # Run interactive mode
        interactive_mode()
