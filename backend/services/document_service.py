import os
import re
import uuid
import hashlib
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from PIL import Image
import pypdf

from backend.config import (
    UPLOAD_DIR,
    MAX_UPLOAD_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
)

# Optional OCR support
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and remove problematic characters.
    """
    # Remove path components
    basename = os.path.basename(filename)
    # Strip null bytes and non-printable characters
    basename = basename.replace("\x00", "").strip()
    # Replace unsafe characters with underscore
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', basename)
    # Avoid empty names or pure dots
    clean = clean.lstrip(".")
    if not clean:
        clean = "document"
    return clean[:120]  # Cap filename length


def compute_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content for duplicate detection."""
    return hashlib.sha256(content).hexdigest()


def validate_file_metadata(filename: str, file_size: int, content_type: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate file extension, size, and MIME type.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    if file_size <= 0:
        return False, "Uploaded file is empty."

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        return False, f"File exceeds maximum allowed size of {max_mb:.0f} MB."

    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        # Fall back to extension check if browser sent generic application/octet-stream
        if content_type.lower() != "application/octet-stream":
            return False, f"Unsupported MIME type '{content_type}'."

    return True, "File metadata valid."


def extract_text_from_pdf(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """
    Extract text from a PDF document using pypdf.
    """
    metadata: Dict[str, Any] = {"pages": 0, "encrypted": False}
    extracted_text_parts = []

    try:
        reader = pypdf.PdfReader(str(file_path))
        metadata["pages"] = len(reader.pages)
        metadata["encrypted"] = reader.is_encrypted

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_text_parts.append(page_text.strip())

        full_text = "\n\n".join(extracted_text_parts).strip()
        # Cap extracted text length for security
        return full_text[:25000], metadata
    except Exception as e:
        return "", {"error": f"PDF parsing error: {str(e)}"}


def extract_text_from_image(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """
    Extract text or metadata from image files (PNG/JPG).
    Gracefully handles environments where Tesseract binary is not installed.
    """
    metadata: Dict[str, Any] = {}
    try:
        with Image.open(str(file_path)) as img:
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["format"] = img.format
            metadata["mode"] = img.mode

        if PYTESSERACT_AVAILABLE:
            try:
                # Attempt OCR extraction
                text = pytesseract.image_to_string(str(file_path))
                clean_text = text.strip()
                if clean_text:
                    metadata["ocr_engine"] = "tesseract"
                    return clean_text[:25000], metadata
            except Exception as ocr_err:
                # Common when tesseract executable is not on PATH
                metadata["ocr_note"] = (
                    "Tesseract OCR executable not found on system PATH. "
                    "Image uploaded successfully; fields can be confirmed manually."
                )
        else:
            metadata["ocr_note"] = "pytesseract library not available for OCR."

        return "", metadata
    except Exception as e:
        return "", {"error": f"Image processing error: {str(e)}"}


def process_uploaded_document(filename: str, content: bytes) -> Dict[str, Any]:
    """
    Save uploaded file locally and extract its content.
    Returns details including stored path, hash, and extracted text.
    """
    # 1. Validate
    is_valid, msg = validate_file_metadata(filename, len(content))
    if not is_valid:
        raise ValueError(msg)

    # 2. Compute hash
    file_hash = compute_file_hash(content)

    # 3. Create unique sanitized path
    clean_name = sanitize_filename(filename)
    unique_prefix = uuid.uuid4().hex[:8]
    stored_name = f"{unique_prefix}_{clean_name}"
    target_path = UPLOAD_DIR / stored_name

    # 4. Save to local storage
    with open(target_path, "wb") as f:
        f.write(content)

    # 5. Extract text
    ext = os.path.splitext(clean_name)[1].lower()
    if ext == ".pdf":
        text, meta = extract_text_from_pdf(target_path)
        file_type = "pdf"
    else:
        text, meta = extract_text_from_image(target_path)
        file_type = "image"

    return {
        "original_filename": clean_name,
        "stored_filename": stored_name,
        "file_path": str(target_path),
        "file_type": file_type,
        "file_size": len(content),
        "file_hash": file_hash,
        "extracted_text": text,
        "metadata": meta,
    }
