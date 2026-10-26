"""Small transactional journal and reusable personal assets; no model dependencies."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class WorkspaceStore:
    def __init__(self, directory: Path) -> None:
        self.path = directory / "workbench.sqlite3"

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS items (kind TEXT NOT NULL, id TEXT NOT NULL, value TEXT NOT NULL, updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(kind,id))"
        )
        self.path.chmod(0o600)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def put(
        self, kind: str, key: str, value: dict[str, Any], *, create: bool = False
    ) -> bool:
        payload = json.dumps(value, ensure_ascii=False, allow_nan=False)
        if len(payload.encode()) > 5000000:
            raise ValueError("Workspace item exceeds five megabytes.")
        with self._connect() as connection:
            if create:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO items(kind,id,value) VALUES (?,?,?)",
                    (kind, key, payload),
                )
            else:
                cursor = connection.execute(
                    "INSERT INTO items(kind,id,value) VALUES (?,?,?) ON CONFLICT(kind,id) DO UPDATE SET value=excluded.value, updated=CURRENT_TIMESTAMP",
                    (kind, key, payload),
                )
            return cursor.rowcount > 0

    def get(self, kind: str, key: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM items WHERE kind=? AND id=?", (kind, key)
            ).fetchone()
        if row is None:
            return None
        result = json.loads(row[0])
        if not isinstance(result, dict):
            raise ValueError("Workspace record is corrupt; restore from a backup.")
        return result

    def list(self, kind: str, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT value FROM items WHERE kind=? ORDER BY updated DESC, id DESC LIMIT ?",
                (kind, min(10000, max(0, limit))),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def organization(self) -> dict[str, dict[str, Any]]:
        return {item["id"]: item for item in self.list("organization", 10000)}

    def organize(
        self,
        result_id: str,
        *,
        tags: str = "",
        pinned: bool = False,
        archived: bool = False,
    ) -> None:
        values = [part.strip() for part in tags.split(",") if part.strip()]
        if len(values) > 12 or any(len(part) > 40 for part in values):
            raise ValueError("Use at most twelve tags, each up to forty characters.")
        self.put(
            "organization",
            result_id,
            {
                "id": result_id,
                "tags": values,
                "pinned": bool(pinned),
                "archived": bool(archived),
            },
        )
