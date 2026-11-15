import os
import chromadb
from app.config import get_settings

_client = None

def get_chroma_client():
    global _client
    if _client is None:
        settings = get_settings()
        os.makedirs(settings.chroma_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.chroma_path)
    return _client

def get_collection(name: str = "documents"):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

def add_chunks(document_id: str, user_id: str, chunks: list[dict], embeddings: list[list[float]]):
    """chunks: list of {text, page}. embeddings: parallel list of float vectors."""
    if not chunks or not embeddings:
        return
    collection = get_collection()
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = [{"user_id": user_id, "document_id": document_id, "page": c["page"]} for c in chunks]
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

def query_chunks(document_id: str, user_id: str, query_embedding: list[float], n_results: int = 5) -> list[dict]:
    """Returns list of {text, page}."""
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"$and": [{"user_id": {"$eq": user_id}}, {"document_id": {"$eq": document_id}}]}
    )
    if not results["documents"] or not results["documents"][0]:
        return []
    return [
        {"text": doc, "page": meta["page"]}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]

def delete_document_chunks(document_id: str):
    collection = get_collection()
    collection.delete(where={"document_id": {"$eq": document_id}})
