
import os
from pathlib import Path
from app.config import settings

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None

class FileService:
    """Service for handling file uploads and text extraction"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.supported_formats = ['.pdf', '.txt', '.docx']
    
    async def save_file(self, file_obj, filename: str) -> Path:
        """Save uploaded file to disk"""
        file_path = self.upload_dir / filename
        
        # Determine unique filename if exists
        counter = 1
        stem = file_path.stem
        suffix = file_path.suffix
        while file_path.exists():
            file_path = self.upload_dir / f"{stem}_{counter}{suffix}"
            counter += 1
            
        with open(file_path, "wb") as buffer:
            # Handle both FastAPI UploadFile (spooled) and regular bytes
            if hasattr(file_obj, "read"):
                # If it's an UploadFile/SpooledTemporaryFile, read chunks
                while content := await file_obj.read(1024 * 1024):  # 1MB chunks
                    buffer.write(content)
            else:
                buffer.write(file_obj)
                
        return file_path

    def extract_text(self, file_path: Path) -> str:
        """Extract text from file based on extension"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._extract_pdf(file_path)
        elif suffix == '.txt':
            return self._extract_txt(file_path)
        elif suffix == '.docx':
            return self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _extract_pdf(self, path: Path) -> str:
        if not PyPDF2:
            raise ImportError("PyPDF2 is not installed")
            
        text = ""
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {i+1} ---\n{page_text}"
        return text

    def _extract_txt(self, path: Path) -> str:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _extract_docx(self, path: Path) -> str:
        if not Document:
            raise ImportError("python-docx is not installed")
            
        doc = Document(path)
        return "\n".join([para.text for para in doc.paragraphs])

# Global instance
file_service = FileService()
