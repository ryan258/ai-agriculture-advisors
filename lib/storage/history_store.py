"""ChromaDB-based storage for query history and results."""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from lib.experts.catalog import validate_advisor_context

logger = logging.getLogger(__name__)

ANNOTATION_LIMITS = {
    "title": 200,
    "status": 20,
    "next_step": 2000,
    "last_step": 2000,
    "blocker": 2000,
    "outcome": 4000,
}
ANNOTATION_FIELDS = tuple(ANNOTATION_LIMITS)
ANNOTATION_STATUSES = ("", "undecided", "decided", "waiting", "tried")
HISTORY_BATCH_SIZE = 100


class HistoryStore:
    """Persistent storage for query results using ChromaDB."""

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the history store with persistent storage.

        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        if not persist_directory:
            persist_directory = os.getenv("CHROMADB_PATH", ".chromadb")

        persist_path = Path(persist_directory).expanduser()
        if not persist_path.is_absolute():
            persist_path = (Path.cwd() / persist_path).resolve()

        # Use PersistentClient for data to survive restarts
        self._client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="query_history",
            metadata={"hnsw:space": "cosine"},
        )

    def save_result(
        self,
        query: str,
        experts: List[str],
        responses: List[Dict[str, Any]],
        result_type: str = "query",
        roundtable_data: Optional[Dict[str, Any]] = None,
        advisor_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save a query result to the store.

        Args:
            query: The original user query
            experts: List of expert roles queried
            responses: List of expert responses
            result_type: Type of result ('query' or 'roundtable')
            roundtable_data: Additional roundtable data if applicable

        Returns:
            The generated result ID
        """
        result_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()

        metadata = {
            "query": query,
            "experts": json.dumps(experts),
            "result_type": result_type,
            "timestamp": timestamp,
        }

        document_data: dict[str, Any] = {
            "query": query,
            "experts": experts,
            "responses": responses,
            "result_type": result_type,
            "timestamp": timestamp,
        }

        if advisor_context is not None:
            document_data["advisor_context"] = validate_advisor_context(
                advisor_context, experts
            )
            metadata["panel_label"] = document_data["advisor_context"]["panel"]["label"]

        if roundtable_data:
            document_data["transcript"] = roundtable_data.get("transcript", [])
            document_data["final_answer"] = roundtable_data.get("final_answer", "")
            document_data["rounds"] = roundtable_data.get("rounds", 0)
            for key in (
                "synthesis_error",
                "synthesis_stale",
                "retry_at",
                "compact_ending",
                "synthesis_model",
            ):
                if key in roundtable_data:
                    document_data[key] = roundtable_data[key]
            if roundtable_data.get("consensus_brief"):
                document_data["consensus_brief"] = roundtable_data.get(
                    "consensus_brief", {}
                )

        self._collection.add(
            ids=[result_id],
            documents=[json.dumps(document_data)],
            metadatas=[metadata],
        )

        logger.info(f"Saved result {result_id} for query: {query[:50]}...")
        return result_id

    def get_history(
        self,
        limit: int = 10,
        search: str = "",
        offset: int = 0,
        *,
        statuses: Optional[tuple[str, ...]] = None,
    ) -> List[Dict[str, Any]]:
        """Find saved metadata and personal notes, newest first.

        Chroma does not order or case-fold metadata text. Scan bounded metadata
        batches before sorting and slicing, so older matching results remain
        discoverable. Advisor documents and embeddings are never loaded here.
        """
        if limit < 0 or offset < 0:
            raise ValueError("History limit and offset must not be negative")
        if statuses is not None and any(
            status not in ANNOTATION_STATUSES for status in statuses
        ):
            raise ValueError("Invalid personal status filter")
        if limit == 0:
            return []

        term = search.strip().casefold()
        history = []
        batch_offset = 0
        annotation_collection = self._annotation_collection()
        while True:
            results = self._collection.get(
                include=["metadatas"], limit=HISTORY_BATCH_SIZE, offset=batch_offset
            )
            result_ids = results["ids"]
            if not result_ids:
                break
            annotations = self._annotations_for_ids(result_ids, annotation_collection)
            metadatas = results.get("metadatas") or []
            for index, result_id in enumerate(result_ids):
                metadata = (metadatas[index] if index < len(metadatas) else {}) or {}
                try:
                    experts = json.loads(str(metadata.get("experts", "[]")))
                except (json.JSONDecodeError, TypeError):
                    experts = []
                if not isinstance(experts, list):
                    experts = []
                row = {
                    "id": result_id,
                    "query": str(metadata.get("query", "")),
                    "experts": experts,
                    "result_type": str(metadata.get("result_type", "query")),
                    "timestamp": str(metadata.get("timestamp", "")),
                    "panel_label": str(metadata.get("panel_label", "")),
                    **annotations.get(result_id, self._empty_annotations()),
                }
                searchable = " ".join(str(value) for value in row.values()).casefold()
                if (not term or term in searchable) and (
                    statuses is None or row["status"] in statuses
                ):
                    history.append(row)
            batch_offset += len(result_ids)
            if len(result_ids) < HISTORY_BATCH_SIZE:
                break

        history.sort(key=lambda row: (row["timestamp"], row["id"]), reverse=True)
        return history[offset : offset + limit]

    def get_open_items(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Return explicitly unfinished work, including older saved results."""
        return self.get_history(limit=limit, statuses=("waiting", "undecided"))

    @staticmethod
    def _empty_annotations() -> dict[str, str]:
        return dict.fromkeys(ANNOTATION_LIMITS, "")

    def _annotation_collection(self, create: bool = False) -> Any:
        """Read without creating storage; create only for an explicit note save."""
        if create:
            return self._client.get_or_create_collection(
                name="personal_annotations", embedding_function=None
            )
        try:
            return self._client.get_collection(
                name="personal_annotations", embedding_function=None
            )
        except chromadb.errors.NotFoundError:
            return None

    def _annotations_for_ids(
        self, result_ids: list[str], collection: Any
    ) -> dict[str, dict[str, str]]:
        if collection is None or not result_ids:
            return {}
        results = collection.get(ids=result_ids, include=["metadatas"])
        annotations = {}
        metadatas = results.get("metadatas") or []
        for result_id, metadata in zip(results["ids"], metadatas):
            metadata = metadata or {}
            annotations[result_id] = {
                field: str(metadata.get(field, "")) for field in ANNOTATION_LIMITS
            }
        return annotations

    def get_annotations(self, result_id: str) -> dict[str, str]:
        """Read optional personal notes separately from saved advisor content."""
        annotations = self._annotations_for_ids(
            [result_id], self._annotation_collection()
        )
        return annotations.get(result_id, self._empty_annotations())

    def update_annotations(
        self, result_id: str, data: dict[str, str]
    ) -> dict[str, str]:
        """Validate and save personal notes without rewriting the saved result."""
        if not isinstance(data, dict) or any(
            field not in ANNOTATION_LIMITS for field in data
        ):
            raise ValueError("Unknown personal note field")
        updates = {}
        for field, value in data.items():
            if not isinstance(value, str):
                raise ValueError(f"{field} must be text")
            value = value.strip()
            if len(value) > ANNOTATION_LIMITS[field]:
                raise ValueError(
                    f"{field} must be at most {ANNOTATION_LIMITS[field]} characters"
                )
            if field == "status" and value not in ANNOTATION_STATUSES:
                raise ValueError("Invalid personal status")
            updates[field] = value

        if not self._collection.get(ids=[result_id], include=[])["ids"]:
            raise ValueError("Saved result not found")
        notes = {**self.get_annotations(result_id), **updates}
        collection = self._annotation_collection(create=True)
        # Notes have no semantic-search use. An explicit inert embedding avoids
        # invoking or downloading an embedding model when notes are saved.
        collection.upsert(ids=[result_id], embeddings=[[0.0]], metadatas=[notes])
        return notes

    def get_result_by_id(self, result_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific result by ID.

        Args:
            result_id: The result ID to retrieve

        Returns:
            The full result data or None if not found
        """
        results = self._collection.get(
            ids=[result_id],
            include=["documents", "metadatas"],
        )

        documents = results.get("documents")
        if not results["ids"] or not documents:
            return None

        try:
            document = json.loads(documents[0])
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Corrupt document for result {result_id}: {e}")
            return None

        return {
            "id": result_id,
            **document,
        }


# Singleton instance
history_store = HistoryStore()
