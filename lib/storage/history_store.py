"""ChromaDB-based storage for query history and results."""

import json
import logging
import os
import uuid
import copy
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api.types import PyEmbeddings
from chromadb.config import Settings
from lib.experts.catalog import validate_advisor_context
from lib.contracts import SCHEMA_VERSION, InvalidRecord, fingerprint, validate_result
from lib.engine.config import PROJECT_ROOT
from .workspace_store import WorkspaceStore

logger = logging.getLogger(__name__)

ANNOTATION_LIMITS = {
    "title": 200,
    "status": 20,
    "next_step": 2000,
    "last_step": 2000,
    "blocker": 2000,
    "outcome": 4000,
    "outcome_rating": 30,
}
ANNOTATION_FIELDS = tuple(ANNOTATION_LIMITS)
ANNOTATION_STATUSES = ("", "undecided", "decided", "waiting", "tried")
HISTORY_BATCH_SIZE = 100


class HistoryStore:
    """Persistent storage for query results using ChromaDB."""

    def __init__(self, persist_directory: Optional[str] = None) -> None:
        """
        Initialize the history store with persistent storage.

        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        if not persist_directory:
            persist_directory = os.getenv("CHROMADB_PATH", ".chromadb")

        persist_path = Path(persist_directory).expanduser()
        if not persist_path.is_absolute():
            persist_path = (PROJECT_ROOT / persist_path).resolve()
        persist_path.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.directory = persist_path
        self.workspace = WorkspaceStore(persist_path)
        self._write_lock = threading.RLock()
        self._history_cache: tuple[Any, list[dict[str, Any]]] | None = None
        self._history_revision = 0

        # Use PersistentClient for data to survive restarts
        self._client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="query_history_v3",
            embedding_function=None,
        )
        # Legacy collections are read only. No embedding configuration/dimensions
        # are changed and no existing records are migrated during startup.
        self._legacy: Any = None
        try:
            self._legacy = self._client.get_collection(
                name="query_history", embedding_function=None
            )
        except chromadb.errors.NotFoundError:
            self._legacy = None

    def save_result(
        self,
        query: str,
        experts: List[str],
        responses: List[Dict[str, Any]],
        result_type: str = "query",
        roundtable_data: Optional[Dict[str, Any]] = None,
        advisor_context: Optional[Dict[str, Any]] = None,
        *,
        execution_data: Optional[Dict[str, Any]] = None,
        idempotency_key: str = "",
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
        result_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        metadata = {
            "query": query,
            "experts": json.dumps(experts),
            "result_type": result_type,
            "timestamp": timestamp,
        }

        document_data: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "query": query,
            "experts": experts,
            "responses": responses,
            "result_type": result_type,
            "timestamp": timestamp,
        }
        if execution_data:
            for key in (
                "task_brief",
                "sources",
                "execution_receipts",
                "run_id",
                "parent_result_id",
                "input_sha256",
                "provider_question",
                "advisor_model",
                "synthesis_model",
                "retry_at",
                "run_status",
                "run_error",
                "attempts",
                "planned_calls",
            ):
                if key in execution_data:
                    document_data[key] = copy.deepcopy(execution_data[key])

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

        document_data = validate_result(document_data)
        if idempotency_key:
            if len(idempotency_key) > 200:
                raise ValueError("Invalid save key")
            # Content addressing makes retries survive a lost HTTP response or
            # restart. A new recovered state gets a distinct version naturally.
            stable = {k: v for k, v in document_data.items() if k != "timestamp"}
            result_id = fingerprint({"key": idempotency_key, "result": stable})
        with self._write_lock:
            for _ in range(5):
                existing = self._collection.get(ids=[result_id], include=["documents"])
                if not existing["ids"]:
                    break
                if idempotency_key:
                    prior = json.loads((existing.get("documents") or [""])[0])
                    if {k: v for k, v in prior.items() if k != "timestamp"} == stable:
                        return result_id
                    raise ValueError(
                        "Save identifier conflict. Existing content was retained; use a new save key."
                    )
                result_id = str(uuid.uuid4())
            else:
                raise ValueError(
                    "Could not allocate a distinct result identifier. Existing content was retained."
                )
            embeddings: PyEmbeddings = [[0.0]]
            self._collection.add(
                ids=[result_id],
                embeddings=embeddings,
                documents=[json.dumps(document_data, ensure_ascii=False)],
                metadatas=[metadata],
            )
            self._history_cache = None
            self._history_revision += 1
        logger.info("Saved result %s", result_id)
        return result_id

    def get_history(
        self,
        limit: int = 10,
        search: str = "",
        offset: int = 0,
        *,
        statuses: Optional[tuple[str, ...]] = None,
        panel: str = "",
        archived: bool = False,
        tag: str = "",
        after: str = "",
        before: str = "",
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
        collections = [self._collection] + (
            [self._legacy] if self._legacy is not None else []
        )
        cache_key = (
            self._history_revision,
            *(collection.count() for collection in collections),
        )
        if self._history_cache is not None and self._history_cache[0] == cache_key:
            rows = copy.deepcopy(self._history_cache[1])
            return self._filter_history(
                rows, term, offset, limit, statuses, panel, archived, tag, after, before
            )
        history = []
        batch_offset = 0
        annotation_collection = self._annotation_collection()
        for collection in collections:
            batch_offset = 0
            while True:
                results = collection.get(
                    include=["metadatas"], limit=HISTORY_BATCH_SIZE, offset=batch_offset
                )
                result_ids = results["ids"]
                if not result_ids:
                    break
                annotations = self._annotations_for_ids(
                    result_ids, annotation_collection
                )
                metadatas = results.get("metadatas") or []
                for index, result_id in enumerate(result_ids):
                    metadata = (
                        metadatas[index] if index < len(metadatas) else {}
                    ) or {}
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
                    history.append(row)
                batch_offset += len(result_ids)
                if len(result_ids) < HISTORY_BATCH_SIZE:
                    break

        # Cache complete metadata rows, not a search-specific page.
        self._history_cache = (cache_key, copy.deepcopy(history))
        return self._filter_history(
            history, term, offset, limit, statuses, panel, archived, tag, after, before
        )

    def _filter_history(
        self,
        rows: list[dict[str, Any]],
        term: str,
        offset: int,
        limit: int,
        statuses: Optional[tuple[str, ...]],
        panel: str,
        archived: bool,
        tag: str,
        after: str,
        before: str,
    ) -> list[dict[str, Any]]:
        organization = self.workspace.organization()
        selected = []
        for row in rows:
            row.update(organization.get(row["id"], {}))
            if (
                bool(row.get("archived")) != archived
                or (panel and row.get("panel_label") != panel)
                or (tag and tag not in row.get("tags", []))
            ):
                continue
            if (after and row["timestamp"][:10] < after) or (
                before and row["timestamp"][:10] > before
            ):
                continue
            if (
                term
                and term
                not in " ".join(str(value) for value in row.values()).casefold()
            ):
                continue
            if statuses is not None and row.get("status") not in statuses:
                continue
            selected.append(row)
        selected.sort(
            key=lambda row: (bool(row.get("pinned")), row["timestamp"], row["id"]),
            reverse=True,
        )
        return selected[offset : offset + limit]

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
            if field == "outcome_rating" and value not in (
                "",
                "helped",
                "needed_correction",
                "not_useful",
                "not_tried",
            ):
                raise ValueError("Invalid outcome rating")
            updates[field] = value

        with self._write_lock:
            if self.get_result_by_id(result_id) is None:
                raise ValueError("Saved result not found")
            notes = {**self.get_annotations(result_id), **updates}
            collection = self._annotation_collection(create=True)
            # Notes have no semantic-search use. An explicit inert embedding avoids
            # invoking or downloading an embedding model when notes are saved.
            collection.upsert(ids=[result_id], embeddings=[[0.0]], metadatas=[notes])
            self._history_cache = None
            self._history_revision += 1
            return notes

    def _finish_import_notes(self, result_id: str) -> None:
        pending = self.workspace.get("import-notes", result_id)
        if not pending or not pending.get("pending"):
            return
        collection = self._annotation_collection()
        # A user edit after a partial import always takes precedence.
        if collection is None or not collection.get(ids=[result_id], include=[])["ids"]:
            self.update_annotations(result_id, pending["annotations"])
        self.workspace.put(
            "import-notes", result_id, {"id": result_id, "pending": False}
        )

    def preview_import(self, result: dict[str, Any]) -> str:
        """Classify a proposed import without mutating saved content or notes."""
        result = validate_result(result, legacy=True)
        original_id = result.pop("id", "")
        candidate = original_id or fingerprint({"imported_record": result})
        existing = self.get_result_by_id(candidate)
        if existing is None:
            return "New record"
        if {k: v for k, v in existing.items() if k != "id"} == result:
            return "Already present; local notes retained (unfinished imported notes can resume)"
        candidate = fingerprint({"imported_id": original_id, "record": result})
        return (
            "Conflicting ID; separate imported version already present"
            if self.get_result_by_id(candidate) is not None
            else "Conflicting ID; will add a separate version"
        )

    def import_record(self, result: dict[str, Any], annotations: dict[str, str]) -> str:
        """Additive import; retry can finish notes interrupted after the source write."""
        result = validate_result(result, legacy=True)
        if not isinstance(annotations, dict):
            raise ValueError("Invalid imported annotations")
        for field, value in annotations.items():
            if (
                field not in ANNOTATION_LIMITS
                or not isinstance(value, str)
                or len(value) > ANNOTATION_LIMITS[field]
            ):
                raise ValueError("Invalid imported annotation field")
        if annotations.get("status", "") not in ANNOTATION_STATUSES or annotations.get(
            "outcome_rating", ""
        ) not in ("", "helped", "needed_correction", "not_useful", "not_tried"):
            raise ValueError("Invalid imported personal status")
        original_id = result.pop("id", "")
        candidate = original_id or fingerprint({"imported_record": result})
        with self._write_lock:
            existing = self.get_result_by_id(candidate)
            if existing is not None:
                if {k: v for k, v in existing.items() if k != "id"} == result:
                    self._finish_import_notes(candidate)
                    return candidate
                candidate = fingerprint({"imported_id": original_id, "record": result})
                result["imported_from_id"] = original_id
                conflicting = self.get_result_by_id(candidate)
                if conflicting is not None:
                    if {k: v for k, v in conflicting.items() if k != "id"} != result:
                        raise ValueError(
                            "Archive identifier conflict; existing records were retained."
                        )
                    self._finish_import_notes(candidate)
                    return candidate
            result = validate_result(result, legacy=True)
            metadata = {
                "query": result["query"],
                "experts": json.dumps(result["experts"]),
                "result_type": result["result_type"],
                "timestamp": result.get("timestamp", ""),
            }
            if result.get("advisor_context"):
                metadata["panel_label"] = result["advisor_context"]["panel"]["label"]
            if annotations:
                self.workspace.put(
                    "import-notes",
                    candidate,
                    {"id": candidate, "pending": True, "annotations": annotations},
                )
            embeddings: PyEmbeddings = [[0.0]]
            self._collection.add(
                ids=[candidate],
                embeddings=embeddings,
                documents=[json.dumps(result, ensure_ascii=False)],
                metadatas=[metadata],
            )
            self._history_cache = None
            self._history_revision += 1
            self._finish_import_notes(candidate)
            return candidate

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
        if not results["ids"] and self._legacy is not None:
            results = self._legacy.get(
                ids=[result_id], include=["documents", "metadatas"]
            )

        documents = results.get("documents")
        if not results["ids"] or not documents:
            return None

        try:
            document = json.loads(documents[0])
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Corrupt document for result {result_id}: {e}")
            raise InvalidRecord(
                "The saved record contains invalid JSON. Keep its backup and export; other saved work remains available."
            ) from e

        document = validate_result(document, legacy=True)
        return {
            **document,
            "id": result_id,
        }


class LazyHistoryStore:
    """Importing portable code never opens or creates a database."""

    def __init__(self) -> None:
        self._instance: HistoryStore | None = None
        self._lock = threading.Lock()

    def __getattr__(self, name: str) -> Any:
        with self._lock:
            if self._instance is None:
                self._instance = HistoryStore()
        return getattr(self._instance, name)


history_store = LazyHistoryStore()
