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

logger = logging.getLogger(__name__)


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

        document_data = {
            "query": query,
            "experts": experts,
            "responses": responses,
            "result_type": result_type,
            "timestamp": timestamp,
        }

        if roundtable_data:
            document_data["transcript"] = roundtable_data.get("transcript", [])
            document_data["final_answer"] = roundtable_data.get("final_answer", "")
            document_data["rounds"] = roundtable_data.get("rounds", 0)

        self._collection.add(
            ids=[result_id],
            documents=[json.dumps(document_data)],
            metadatas=[metadata],
        )

        logger.info(f"Saved result {result_id} for query: {query[:50]}...")
        return result_id

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent query history.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent query results (metadata only)
        """
        results = self._collection.get(
            include=["metadatas"],
        )

        if not results["ids"]:
            return []

        # Combine IDs with metadata and sort by timestamp
        history = []
        for i, result_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i]
            history.append(
                {
                    "id": result_id,
                    "query": metadata.get("query", ""),
                    "experts": json.loads(metadata.get("experts", "[]")),
                    "result_type": metadata.get("result_type", "query"),
                    "timestamp": metadata.get("timestamp", ""),
                }
            )

        # Sort by timestamp descending
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history[:limit]

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

        if not results["ids"]:
            return None

        try:
            document = json.loads(results["documents"][0])
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Corrupt document for result {result_id}: {e}")
            return None

        return {
            "id": result_id,
            **document,
        }

    def export_to_markdown(self, result_id: str) -> Optional[str]:
        """
        Export a result to markdown format.

        Args:
            result_id: The result ID to export

        Returns:
            Markdown string or None if not found
        """
        result = self.get_result_by_id(result_id)
        if not result:
            return None

        lines = [
            "# Agricultural Advisory Query",
            "",
            f"**Date:** {result.get('timestamp', 'Unknown')}",
            "",
            "## Query",
            "",
            f"{result.get('query', '')}",
            "",
        ]

        if result.get("result_type") == "roundtable":
            lines.extend(
                [
                    "## Roundtable Discussion",
                    "",
                    f"**Participants:** {', '.join(result.get('experts', []))}",
                    f"**Rounds:** {result.get('rounds', 0)}",
                    "",
                    "### Transcript",
                    "",
                ]
            )

            for entry in result.get("transcript", []):
                lines.extend(
                    [
                        f"**{entry.get('speaker', 'Unknown')}** (Round {entry.get('round', '?')})",
                        "",
                        f"{entry.get('text', '')}",
                        "",
                        "---",
                        "",
                    ]
                )

            lines.extend(
                [
                    "### Consensus",
                    "",
                    f"{result.get('final_answer', '')}",
                ]
            )
        else:
            lines.extend(
                [
                    "## Expert Responses",
                    "",
                ]
            )

            for response in result.get("responses", []):
                if "error" in response:
                    lines.extend(
                        [
                            f"### {response.get('label', response.get('role', 'Unknown'))}",
                            "",
                            f"*Error: {response.get('error')}*",
                            "",
                        ]
                    )
                else:
                    lines.extend(
                        [
                            f"### {response.get('label', response.get('role', 'Unknown'))}",
                            "",
                            f"{response.get('response', '')}",
                            "",
                        ]
                    )

        lines.extend(
            [
                "---",
                "",
                "*Generated by AI Agriculture Advisors*",
            ]
        )

        return "\n".join(lines)


# Singleton instance
history_store = HistoryStore()
