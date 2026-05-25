import os
import pypdf
import docx2txt
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def extract_text_from_txt(file_path: Path) -> str:
    """Extracts text from a plain text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        return ""

def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts text from a PDF file preserving layout and tables using pdfplumber."""
    try:
        import pdfplumber
        logger.info(f"Extracting layout-aware text from PDF using pdfplumber: {file_path.name}")
        text_parts = []
        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                else:
                    logger.warning(f"No text extracted from page {i+1} of {file_path.name}")
        full_text = "\n\n".join(text_parts)
        if full_text and full_text.strip():
            return full_text
        logger.warning(f"pdfplumber returned empty text for {file_path.name}. Falling back to pypdf.")
    except Exception as e:
        logger.error(f"Error reading PDF file {file_path} with pdfplumber: {e}. Falling back to pypdf.")
        
    # Fallback to standard pypdf extraction
    try:
        reader = pypdf.PdfReader(str(file_path))
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            else:
                logger.warning(f"No text extracted from page {i+1} of {file_path.name}")
        return "\n".join(text_parts)
    except Exception as fallback_err:
        logger.error(f"Fallback pypdf also failed for {file_path}: {fallback_err}")
        return ""

def extract_text_from_docx(file_path: Path) -> str:
    """Extracts text from a Word document (.docx) using docx2txt."""
    try:
        return docx2txt.process(str(file_path))
    except Exception as e:
        logger.error(f"Error reading DOCX file {file_path}: {e}")
        return ""

def extract_text(file_path: Path) -> str:
    """Extracts text from a file based on its extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    elif suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        logger.warning(f"Unsupported file format: {suffix} for file {file_path.name}")
        return ""

def get_supported_files(directory: Path) -> list[Path]:
    """Recursively finds all supported files in the given directory."""
    supported_extensions = {".txt", ".pdf", ".docx"}
    files = []
    if not directory.exists():
        return files
        
    for p in directory.rglob("*"):
        if p.is_file() and p.suffix.lower() in supported_extensions:
            files.append(p)
    return files
