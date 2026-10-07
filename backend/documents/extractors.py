import os
import pymupdf  # PyMuPDF fitz

MAX_EXTRACTED_CHARS = 50000
ALLOWED_EXTENSIONS = {
    '.pdf': 'PDF',
    '.txt': 'TXT',
}

class DocumentExtractionError(Exception):
    """Custom exception raised when document extraction fails."""
    pass

def validate_file_extension(filename: str) -> str:
    """
    Validates that the file has an allowed extension (.pdf or .txt).
    Returns the normalized file_type string ('PDF' or 'TXT').
    """
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentExtractionError(
            f"Unsupported file type '{ext}'. Only PDF (.pdf) and TXT (.txt) files are allowed."
        )
    return ALLOWED_EXTENSIONS[ext]

def extract_text_from_file(file_obj, file_type: str) -> str:
    """
    Extracts text from an uploaded file object.
    Supports PDF (via PyMuPDF) and TXT.
    Enforces a strict 50,000 character limit.
    """
    text = ""
    file_obj.seek(0)

    if file_type == 'PDF':
        try:
            # Read file bytes into memory for PyMuPDF
            file_bytes = file_obj.read()
            if not file_bytes:
                raise DocumentExtractionError("The uploaded PDF file is empty.")
            
            with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
                if len(doc) == 0:
                    raise DocumentExtractionError("The uploaded PDF has no pages.")
                
                pages_text = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text("text")
                    if page_text:
                        pages_text.append(page_text.strip())
                
                text = "\n\n".join(pages_text).strip()
        except pymupdf.FileDataError as exc:
            raise DocumentExtractionError(f"Corrupted or invalid PDF file: {str(exc)}") from exc
        except DocumentExtractionError:
            raise
        except Exception as exc:
            raise DocumentExtractionError(f"Failed to extract text from PDF: {str(exc)}") from exc

    elif file_type == 'TXT':
        try:
            raw_bytes = file_obj.read()
            if not raw_bytes:
                raise DocumentExtractionError("The uploaded TXT file is empty.")
            
            # Try utf-8 first, fallback to latin-1
            try:
                text = raw_bytes.decode('utf-8').strip()
            except UnicodeDecodeError:
                text = raw_bytes.decode('latin-1', errors='replace').strip()
        except DocumentExtractionError:
            raise
        except Exception as exc:
            raise DocumentExtractionError(f"Failed to read TXT file: {str(exc)}") from exc
    else:
        raise DocumentExtractionError(f"Unsupported file type '{file_type}'.")

    if not text.strip():
        raise DocumentExtractionError(
            "No readable text could be extracted from this document. "
            "(Note: scanned image-only PDFs require OCR which is not enabled in Phase 2)."
        )

    # Enforce 50,000 character maximum limit
    if len(text) > MAX_EXTRACTED_CHARS:
        text = (
            text[:MAX_EXTRACTED_CHARS]
            + f"\n\n[Note: Document truncated at {MAX_EXTRACTED_CHARS:,} characters for on-premise memory protection]"
        )

    return text
