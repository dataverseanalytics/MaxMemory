import os
import uuid
from pathlib import Path
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

# Directory to store uploaded files
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"⚠️  Invalid file extension: {file_ext}")
        return False
    
    # Check content type
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"⚠️  Invalid content type: {file.content_type}")
        return False
    
    return True


async def save_upload_file(file: UploadFile, user_id: int) -> str:
    """Save uploaded file and return the file path"""
    logger.info(f"💾 Saving uploaded file: {file.filename}")
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"user_{user_id}_{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    logger.info(f"📁 Saving to: {file_path}")
    contents = await file.read()
    
    # Check file size
    if len(contents) > MAX_FILE_SIZE:
        logger.warning(f"⚠️  File too large: {len(contents)} bytes")
        raise ValueError(f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB")
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    logger.info(f"✅ File saved successfully: {unique_filename}")
    
    # Return relative path for URL
    return f"/uploads/avatars/{unique_filename}"


def delete_avatar_file(avatar_url: str) -> None:
    """Delete avatar file from disk"""
    if not avatar_url:
        return
    
    try:
        # Extract filename from URL
        filename = avatar_url.split("/")[-1]
        file_path = UPLOAD_DIR / filename
        
        if file_path.exists():
            logger.info(f"🗑️ Deleting old avatar: {filename}")
            file_path.unlink()
            logger.info(f"✅ Avatar deleted successfully")
    except Exception as e:
        logger.warning(f"⚠️  Failed to delete avatar file: {e}")
