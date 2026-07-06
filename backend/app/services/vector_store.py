"""
ChromaDB vector store wrapper.

Stores per-file embeddings and supports semantic search across the
project corpus. The collection is created lazily on first use.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger("codeguardian.vector")


_client = None
_collection = None


def _ensure_dirs() -> None:
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)


def get_client():
    """Return (or create) the global ChromaDB client."""
    global _client
    if _client is not None:
        return _client
    _ensure_dirs()
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False),
        )
        return _client
    except Exception as e:  # pragma: no cover
        log_event(logger, 30, "chromadb_init_failed", error=str(e))
        return None


def get_collection():
    """Return the global ChromaDB collection used for project embeddings."""
    global _collection
    if _collection is not None:
        return _collection
    client = get_client()
    if client is None:
        return None
    try:
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as e:  # pragma: no cover
        log_event(logger, 30, "chromadb_collection_failed", error=str(e))
    return _collection


def warm_up() -> None:
    """Best-effort initialization so subsequent calls are fast."""
    get_collection()


def index_documents(project_id: str, documents: List[Dict]) -> int:
    """Index a batch of documents. Each dict has ``id``, ``text``, ``metadata``."""
    if not documents:
        return 0
    collection = get_collection()
    if collection is None:
        return 0
    ids, texts, metadatas = [], [], []
    for d in documents:
        ids.append(d["id"])
        texts.append(d["text"])
        metadatas.append({**d.get("metadata", {}), "project_id": project_id})
    try:
        collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        return len(ids)
    except Exception as e:  # pragma: no cover
        log_event(logger, 30, "chromadb_upsert_failed", error=str(e))
        return 0


def search(project_id: str, query: str, n_results: int = 5) -> List[Dict]:
    """Return the ``n_results`` most similar documents for ``query``."""
    collection = get_collection()
    if collection is None:
        return []
    try:
        res = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"project_id": project_id} if project_id else None,
        )
        out: List[Dict] = []
        for i, doc in enumerate(res.get("documents", [[]])[0]):
            out.append({
                "id": res.get("ids", [[]])[0][i] if res.get("ids") else None,
                "text": doc,
                "metadata": res.get("metadatas", [[]])[0][i] if res.get("metadatas") else {},
                "distance": res.get("distances", [[]])[0][i] if res.get("distances") else None,
            })
        return out
    except Exception as e:  # pragma: no cover
        log_event(logger, 30, "chromadb_query_failed", error=str(e))
        return []


def reset_project(project_id: str) -> None:
    """Delete all documents belonging to a project."""
    collection = get_collection()
    if collection is None:
        return
    try:
        collection.delete(where={"project_id": project_id})
    except Exception:  # pragma: no cover
        pass
