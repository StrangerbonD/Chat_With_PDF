import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db, Document, User
from app.deps import get_current_user
from app.pdf_processor import compute_sha256, extract_text_with_temp_file, chunk_pages
from app.rag import embed_chunks, embed_query, generate_answer
from app.vector_store import add_chunks, delete_document_chunks, query_chunks

import uuid
from datetime import datetime, timezone

router = APIRouter(tags=["main"])


# ── Health ───────────────────────────────────────────────────────────────────

@router.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Documents ────────────────────────────────────────────────────────────────

doc_router = APIRouter(prefix="/api/documents", tags=["documents"])


@doc_router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()

    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")

    # Read file content
    pdf_bytes = await file.read()

    # Validate magic bytes
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(400, "File does not appear to be a valid PDF")

    # Validate size
    max_bytes = settings.max_file_mb * 1024 * 1024
    if len(pdf_bytes) > max_bytes:
        raise HTTPException(413, f"File exceeds maximum size of {settings.max_file_mb} MB")

    # Extract text using safe temporary file
    pages = extract_text_with_temp_file(pdf_bytes)  # raises HTTPException if no text

    # Validate page count
    if len(pages) > settings.max_pages:
        raise HTTPException(400, f"PDF exceeds maximum of {settings.max_pages} pages")

    # Compute hash and check for duplicate
    file_hash = compute_sha256(pdf_bytes)
    existing = (
        await db.execute(
            select(Document).where(
                Document.file_hash == file_hash,
                Document.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        return {
            "id": existing.id,
            "document_id": existing.id,
            "filename": existing.filename,
            "total_pages": existing.total_pages,
            "processing_status": "ready",
        }

    # Chunk and embed
    chunks = chunk_pages(pages)
    embeddings = await embed_chunks(chunks)

    # Persist Document row
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename,
        file_hash=file_hash,
        total_pages=len(pages),
        created_at=datetime.now(timezone.utc),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Store embeddings in Chroma
    add_chunks(doc_id, current_user.id, chunks, embeddings)

    return {
        "id": doc_id,
        "document_id": doc_id,
        "filename": file.filename,
        "total_pages": len(pages),
        "processing_status": "ready",
    }


@doc_router.get("")
@doc_router.get("/")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = (
        await db.execute(select(Document).where(Document.user_id == current_user.id))
    ).scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "total_pages": d.total_pages,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@doc_router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (
        await db.execute(
            select(Document).where(
                Document.id == document_id, Document.user_id == current_user.id
            )
        )
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(404, "Document not found")

    delete_document_chunks(document_id)
    await db.execute(delete(Document).where(Document.id == document_id))
    await db.commit()


# ── Chat ─────────────────────────────────────────────────────────────────────

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])

INSUFFICIENT_INFO = "The document does not contain sufficient information to answer this question."


class ChatRequest(BaseModel):
    document_id: str
    question: str


@chat_router.post("")
@chat_router.post("/")
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify document belongs to user
    doc = (
        await db.execute(
            select(Document).where(
                Document.id == body.document_id,
                Document.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    # Embed the question
    query_emb = await embed_query(body.question)

    # Retrieve relevant chunks from Chroma
    chunks = query_chunks(body.document_id, current_user.id, query_emb, n_results=5)

    # Generate answer
    answer = await generate_answer(body.question, chunks)

    # Collect source pages (empty if no chunks or insufficient info)
    if chunks and INSUFFICIENT_INFO.lower() not in answer.strip().lower():
        source_pages = sorted({c["page"] for c in chunks})
    else:
        source_pages = []

    return {"answer": answer, "source_pages": source_pages}


# ── Register sub-routers on main router ──────────────────────────────────────

router.include_router(doc_router)
router.include_router(chat_router)
