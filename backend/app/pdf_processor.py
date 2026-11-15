import hashlib
import os
import tempfile
import fitz  # PyMuPDF
from fastapi import HTTPException

MAX_CHUNK_CHARS = 3000
OVERLAP_CHARS = 500


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_text_with_temp_file(pdf_bytes: bytes) -> list[dict]:
    """
    Saves PDF bytes to a secure temporary file, extracts text page-by-page with PyMuPDF,
    and guarantees temp file deletion. Raises HTTPException if no extractable text.
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(temp_fd, "wb") as tmp:
            tmp.write(pdf_bytes)

        doc = fitz.open(temp_path)
        pages = []
        try:
            for i, page in enumerate(doc):
                text = page.get_text() or ""
                pages.append({"page": i + 1, "text": text})
        finally:
            doc.close()

        total_text = "".join(p["text"] for p in pages).strip()
        if not total_text:
            raise HTTPException(
                status_code=400,
                detail="PDF contains no extractable text. Scanned PDFs are not supported.",
            )
        return pages
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Chunk text with ~3000 characters and ~500 overlap per page.
    Each chunk preserves its original page number.
    Returns list of {"text": str, "page": int}.
    """
    chunks = []
    for p in pages:
        text = p["text"]
        page_num = p["page"]
        if not text.strip():
            continue

        if len(text) <= MAX_CHUNK_CHARS:
            chunks.append({"text": text.strip(), "page": page_num})
            continue

        start = 0
        text_len = len(text)
        step = MAX_CHUNK_CHARS - OVERLAP_CHARS
        while start < text_len:
            end = min(start + MAX_CHUNK_CHARS, text_len)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page": page_num})
            if end >= text_len:
                break
            start += step

    return chunks
