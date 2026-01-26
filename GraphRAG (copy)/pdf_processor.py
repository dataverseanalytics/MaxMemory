"""
PDF Document Processor Module
Handles PDF file uploads, extraction, and processing
"""

import os
import sys
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("[ERROR] PyPDF2 not installed. Installing...")
    os.system(f"{sys.executable} -m pip install PyPDF2 -q")
    import PyPDF2

try:
    from pptx import Presentation
except ImportError:
    print("[INFO] python-pptx not installed. PPT support disabled.")
    Presentation = None

from ingest import ingestion
from datetime import datetime


class PDFProcessor:
    """Process PDF and document files"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt', '.docx']
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def extract_pdf_text(self, pdf_path):
        """
        Extract text from PDF file
        
        Args:
            pdf_path (str): Path to PDF file
            
        Returns:
            str: Extracted text from PDF
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                print(f"[PDF] Found {num_pages} pages")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page.extract_text()
            
            return text
        except Exception as e:
            print(f"[ERROR] Failed to extract PDF: {str(e)}")
            return None
    
    def extract_txt_text(self, txt_path):
        """
        Extract text from TXT file
        
        Args:
            txt_path (str): Path to TXT file
            
        Returns:
            str: Content of TXT file
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return text
        except Exception as e:
            print(f"[ERROR] Failed to read TXT file: {str(e)}")
            return None
    
    def extract_docx_text(self, docx_path):
        """
        Extract text from DOCX file
        
        Args:
            docx_path (str): Path to DOCX file
            
        Returns:
            str: Extracted text from DOCX
        """
        try:
            from docx import Document
            doc = Document(docx_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except ImportError:
            print("[ERROR] python-docx not installed. DOCX support disabled.")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to extract DOCX: {str(e)}")
            return None
    
    def process_file(self, file_path, source=None):
        """
        Process any supported file format
        
        Args:
            file_path (str): Path to file
            source (str): Source identifier
            
        Returns:
            dict: Processing results
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            return None
        
        file_ext = file_path.suffix.lower()
        
        if file_ext not in self.supported_formats:
            print(f"[ERROR] Unsupported format: {file_ext}")
            print(f"[INFO] Supported formats: {', '.join(self.supported_formats)}")
            return None
        
        # Set default source from filename
        if not source:
            source = file_path.stem
        
        print(f"\n{'='*60}")
        print(f"[PROCESSING] {file_ext.upper()} FILE")
        print(f"{'='*60}")
        print(f"[FILE] {file_path.name}")
        print(f"[SOURCE] {source}")
        print(f"[SIZE] {file_path.stat().st_size / 1024:.2f} KB")
        
        # Extract text based on file type
        extracted_text = None
        if file_ext == '.pdf':
            extracted_text = self.extract_pdf_text(file_path)
        elif file_ext == '.txt':
            extracted_text = self.extract_txt_text(file_path)
        elif file_ext == '.docx':
            extracted_text = self.extract_docx_text(file_path)
        
        if not extracted_text:
            print(f"[ERROR] Failed to extract text from file")
            return None
        
        # Clean up extracted text
        extracted_text = self._clean_text(extracted_text)
        
        print(f"[EXTRACTED] {len(extracted_text)} characters")
        print(f"[PREVIEW] {extracted_text[:100]}...")
        
        # Add to GraphRAG system
        print(f"\n[INGESTING] into GraphRAG system...")
        doc_info = ingestion.add_document(extracted_text, source=source)
        
        # Copy file to uploads directory (only if not already there)
        import shutil
        dest_path = os.path.join(self.upload_dir, file_path.name)
        file_path_abs = str(file_path.resolve())
        dest_path_abs = str(Path(dest_path).resolve())
        
        if file_path_abs != dest_path_abs:
            shutil.copy2(file_path, dest_path)
            print(f"[SAVED] File copied to {dest_path}")
        else:
            print(f"[SAVED] File already in uploads directory")
        
        return {
            "status": "success",
            "file": str(file_path.name),
            "source": source,
            "file_type": file_ext,
            "extracted_chars": len(extracted_text),
            "doc_info": doc_info
        }
    
    def _clean_text(self, text):
        """Clean extracted text"""
        # Remove multiple spaces
        text = ' '.join(text.split())
        # Remove special characters but keep readable text
        text = text.replace('\x00', '').strip()
        return text
    
    def process_directory(self, directory_path, source_prefix=None):
        """
        Process all documents in a directory
        
        Args:
            directory_path (str): Path to directory
            source_prefix (str): Prefix for source names
            
        Returns:
            list: Results for each file
        """
        dir_path = Path(directory_path)
        
        if not dir_path.is_dir():
            print(f"[ERROR] Directory not found: {directory_path}")
            return []
        
        results = []
        files = [f for f in dir_path.iterdir() if f.suffix.lower() in self.supported_formats]
        
        print(f"\n{'='*60}")
        print(f"[BATCH PROCESSING] Directory")
        print(f"{'='*60}")
        print(f"[DIRECTORY] {directory_path}")
        print(f"[FILES FOUND] {len(files)}")
        
        for file_path in files:
            source = f"{source_prefix}_{file_path.stem}" if source_prefix else file_path.stem
            result = self.process_file(file_path, source=source)
            if result:
                results.append(result)
        
        print(f"\n[COMPLETED] Processed {len(results)} files")
        return results
    
    def upload_from_url(self, url, filename=None):
        """
        Download and process document from URL
        
        Args:
            url (str): URL to document
            filename (str): Filename to save as
            
        Returns:
            dict: Processing results
        """
        try:
            import requests
            
            print(f"\n{'='*60}")
            print(f"[DOWNLOADING] From URL")
            print(f"{'='*60}")
            print(f"[URL] {url}")
            
            response = requests.get(url)
            response.raise_for_status()
            
            if not filename:
                filename = url.split('/')[-1] or 'downloaded_file'
            
            file_path = os.path.join(self.upload_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"[SAVED] {filename}")
            
            # Process the downloaded file
            return self.process_file(file_path, source=Path(filename).stem)
        
        except ImportError:
            print("[ERROR] requests library not installed. Run: pip install requests")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to download: {str(e)}")
            return None


# Create global instance
pdf_processor = PDFProcessor()


def upload_pdf(file_path, source=None):
    """Convenient function to upload PDF"""
    return pdf_processor.process_file(file_path, source=source)


def upload_directory(directory_path, source_prefix=None):
    """Convenient function to upload entire directory"""
    return pdf_processor.process_directory(directory_path, source_prefix=source_prefix)


def upload_from_url(url, filename=None):
    """Convenient function to download and upload from URL"""
    return pdf_processor.upload_from_url(url, filename=filename)
