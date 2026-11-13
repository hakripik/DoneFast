"""Persistent ChromaDB-backed vector store for document chunks."""

from pathlib import Path

import chromadb

from app.models import Chunk
from app.retrieval.embedder import embed

_CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "chroma_db"
_COLLECTION_NAME = "study_chunks"

_client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
_collection = _client.get_or_create_collection(
    name=_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def add_chunks(chunks: list[Chunk]) -> None:
    """Embed and upsert a batch of chunks into the vector store."""
    if not chunks:
        return

    vectors = embed([chunk.text for chunk in chunks])
    _collection.upsert(
        ids=[chunk.chunk_id for chunk in chunks],
        embeddings=vectors,
        documents=[chunk.text for chunk in chunks],
        metadatas=[
            {
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "heading": chunk.heading or "",
            }
            for chunk in chunks
        ],
    )


def list_documents() -> list[dict]:
    """Return per-document page/chunk counts for every document in the store."""
    results = _collection.get(include=["metadatas"])

    stats: dict[str, dict] = {}
    for metadata in results["metadatas"]:
        name = metadata["document_name"]
        entry = stats.setdefault(name, {"document_name": name, "total_chunks": 0, "pages": set()})
        entry["total_chunks"] += 1
        entry["pages"].add(metadata["page_number"])

    return [
        {
            "document_name": entry["document_name"],
            "total_pages": len(entry["pages"]),
            "total_chunks": entry["total_chunks"],
        }
        for entry in stats.values()
    ]


def clear_all() -> None:
    """Delete every chunk from the vector store."""
    global _collection
    _client.delete_collection(name=_COLLECTION_NAME)
    _collection = _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def search(query: str, top_k: int = 5) -> list[dict]:
    """Embed the query and return the top-k most similar chunks."""
    [query_vector] = embed([query])
    results = _collection.query(query_embeddings=[query_vector], n_results=top_k)

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "chunk_id": chunk_id,
            "text": text,
            "document_name": metadata["document_name"],
            "page_number": metadata["page_number"],
            "heading": metadata["heading"] or None,
            # Cosine distance is in [0, 2]; convert to a 0-1 similarity score.
            "similarity": 1 - (distance / 2),
        }
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances)
    ]
