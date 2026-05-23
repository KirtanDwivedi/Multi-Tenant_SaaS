"""
Vector storage for tenant knowledge.

Default: JSON file fallback (no ChromaDB native build required).
Set VECTOR_STORE=chromadb in .env when ChromaDB is installed and ready.
"""

import json
import math
import os
from typing import Any, Dict, List, Optional

# json = default for now; chromadb = opt-in when MSVC + pip install succeed
VECTOR_STORE_MODE = os.getenv("VECTOR_STORE", "json").strip().lower()

CHROMA_AVAILABLE = False
try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None


class FallbackKnowledgeCollection:
    """Local JSON-backed vector store (cosine similarity over stored embeddings)."""

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.records: List[Dict[str, Any]] = []
        if os.path.exists(storage_path):
            with open(storage_path, "r", encoding="utf-8") as f:
                self.records = json.load(f)

    def _persist(self) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2)

    def clear_workspace(self, platform: str, display_name: str) -> None:
        """Remove existing chunks for a workspace before re-ingestion."""
        self.records = [
            record
            for record in self.records
            if not (
                record.get("metadata", {}).get("source_platform") == platform
                and record.get("metadata", {}).get("display_name") == display_name
            )
        ]
        self._persist()

    def add(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        if metadatas:
            platform = metadatas[0].get("source_platform")
            display_name = metadatas[0].get("display_name")
            if platform and display_name:
                self.clear_workspace(platform, display_name)

        for doc_id, text, meta, vector in zip(ids, documents, metadatas, embeddings):
            self.records.append(
                {
                    "id": doc_id,
                    "document": text,
                    "metadata": meta,
                    "embedding": vector,
                }
            )
        self._persist()

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 3,
        source_filters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not self.records:
            return {"documents": [[]], "metadatas": [[]]}

        query_vector = query_embeddings[0]
        candidates = self.records
        if source_filters:
            allowed = {name.strip().lower() for name in source_filters if name.strip()}
            candidates = [
                record
                for record in candidates
                if (record.get("metadata") or {}).get("display_name", "").lower() in allowed
            ]
            if not candidates:
                return {"documents": [[]], "metadatas": [[]]}

        def cosine(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        ranked = sorted(
            candidates,
            key=lambda item: cosine(query_vector, item["embedding"]),
            reverse=True,
        )[:n_results]

        return {
            "documents": [[item["document"] for item in ranked]],
            "metadatas": [[item["metadata"] for item in ranked]],
        }


def query_collection(
    collection: Any,
    query_embeddings: List[List[float]],
    n_results: int = 3,
    source_filters: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Query JSON fallback or Chroma with optional workspace display-name filter."""
    if isinstance(collection, FallbackKnowledgeCollection):
        return collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            source_filters=source_filters,
        )

    kwargs: Dict[str, Any] = {
        "query_embeddings": query_embeddings,
        "n_results": n_results,
    }
    if source_filters:
        allowed = [name.strip() for name in source_filters if name.strip()]
        if allowed:
            kwargs["where"] = {"display_name": {"$in": allowed}}
    return collection.query(**kwargs)


def get_knowledge_collection(chroma_path: str, collection_name: str):
    """
    Returns (collection, backend_name).

    - VECTOR_STORE=json (default): data/chroma_db/fallback_vectors.json
    - VECTOR_STORE=chromadb: Chroma persistent client (requires chromadb installed)
    """
    use_chroma = VECTOR_STORE_MODE == "chromadb" and CHROMA_AVAILABLE

    if use_chroma:
        client = chromadb.PersistentClient(path=chroma_path)
        return client.get_or_create_collection(name=collection_name), "chromadb"

    fallback_file = os.path.join(chroma_path, "fallback_vectors.json")
    if not os.path.exists(fallback_file):
        with open(fallback_file, "w", encoding="utf-8") as f:
            json.dump([], f)

    return FallbackKnowledgeCollection(fallback_file), "json"
