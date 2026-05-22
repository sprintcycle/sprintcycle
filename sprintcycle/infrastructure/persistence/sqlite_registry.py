"""SQLite-backed version registry.

Persists version artifacts and active pointers.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Optional

from ...domain.evolution.models import EvolutionTarget, VersionArtifact
from sprintcycle.governance.versioning.registry import VersionRegistry  # noqa: E402


class SQLiteVersionRegistry(VersionRegistry):
    def __init__(self, root_dir: str = ".sprintcycle/versioning") -> None:
        self._root_dir = Path(root_dir).expanduser().resolve()
        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._root_dir / "versions.sqlite3"
        self._lock = asyncio.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS versions (
                    version_id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    commit_hash TEXT,
                    tag TEXT,
                    branch TEXT,
                    manifest_path TEXT,
                    sandbox_id TEXT,
                    metadata_json TEXT,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_versions_target_active
                ON versions(target, is_active, created_at DESC)
                """
            )
            conn.commit()

    async def register(self, artifact: VersionArtifact) -> VersionArtifact:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO versions
                    (version_id, target, commit_hash, tag, branch, manifest_path, sandbox_id, metadata_json, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT is_active FROM versions WHERE version_id=?), 0))
                    """,
                    (
                        artifact.version_id,
                        artifact.target,
                        artifact.commit_hash,
                        artifact.tag,
                        artifact.branch,
                        artifact.manifest_path,
                        artifact.sandbox_id,
                        json.dumps(artifact.metadata, ensure_ascii=False),
                        artifact.version_id,
                    ),
                )
                conn.commit()
        return artifact

    async def set_active(self, version_id: str) -> None:
        async with self._lock:
            with self._connect() as conn:
                row = conn.execute("SELECT target FROM versions WHERE version_id=?", (version_id,)).fetchone()
                if row is None:
                    raise KeyError(f"version not found: {version_id}")
                target = row["target"]
                conn.execute("UPDATE versions SET is_active=0 WHERE target=?", (target,))
                conn.execute("UPDATE versions SET is_active=1 WHERE version_id=?", (version_id,))
                conn.commit()

    async def get_active(self, target: EvolutionTarget) -> Optional[VersionArtifact]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM versions WHERE target=? AND is_active=1 ORDER BY created_at DESC LIMIT 1",
                (target,),
            ).fetchone()
        return self._row_to_artifact(row) if row else None

    async def get(self, version_id: str) -> Optional[VersionArtifact]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM versions WHERE version_id=?", (version_id,)).fetchone()
        return self._row_to_artifact(row) if row else None

    async def list_versions(self, target: Optional[EvolutionTarget] = None, limit: int = 20) -> list[VersionArtifact]:
        with self._connect() as conn:
            if target is None:
                rows = conn.execute("SELECT * FROM versions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM versions WHERE target=? ORDER BY created_at DESC LIMIT ?",
                    (target, limit),
                ).fetchall()
        return [self._row_to_artifact(r) for r in rows]

    async def list_targets(self) -> list[EvolutionTarget]:
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT target FROM versions ORDER BY target ASC").fetchall()
        return [row[0] for row in rows]

    async def export_manifest_index(self) -> dict[str, list[str]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT target, version_id FROM versions ORDER BY created_at DESC").fetchall()
        index: dict[str, list[str]] = {}
        for row in rows:
            target = row[0]
            version_id = row[1]
            index.setdefault(target, []).append(version_id)
        return index

    def _row_to_artifact(self, row: sqlite3.Row) -> VersionArtifact:
        return VersionArtifact(
            version_id=row["version_id"],
            target=row["target"],
            commit_hash=row["commit_hash"],
            tag=row["tag"],
            branch=row["branch"],
            manifest_path=row["manifest_path"],
            sandbox_id=row["sandbox_id"],
            metadata=json.loads(row["metadata_json"] or "{}"),
        )
