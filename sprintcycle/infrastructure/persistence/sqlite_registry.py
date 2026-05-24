"""SQLite-backed version registry.

Persists version artifacts and active pointers.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from sprintcycle.domain.evolution.models import EvolutionTarget, VersionArtifact
from sprintcycle.infrastructure.governance.versioning.registry import VersionRegistry
from sprintcycle.infrastructure.persistence.base import BaseSqliteStore


class SQLiteVersionRegistry(BaseSqliteStore, VersionRegistry):
    """基于 BaseSqliteStore 的版本注册中心实现。"""

    def __init__(self, root_dir: str = ".sprintcycle/versioning") -> None:
        from pathlib import Path

        root = Path(root_dir).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        super().__init__(str(root / "versions.sqlite3"))
        self._root_dir = root

    # ─────────────────────────────────────────────────────────────────
    # BaseSqliteStore 模板方法实现
    # ─────────────────────────────────────────────────────────────────

    def _define_schema(self, conn: AsyncConnection) -> None:
        conn.execute(
            text(
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
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_versions_target_active
                ON versions(target, is_active, created_at DESC)
                """
            )
        )

    # ─────────────────────────────────────────────────────────────────
    # VersionRegistry 接口实现
    # ─────────────────────────────────────────────────────────────────

    async def register(self, artifact: VersionArtifact) -> VersionArtifact:
        # 查询当前 is_active 值（aiosqlite 不支持绑定参数在 COALESCE 子查询中）
        row = await self.execute_one(
            "SELECT is_active FROM versions WHERE version_id = ?",
            (artifact.version_id,),
        )
        is_active = int(row[0]) if row else 0

        await self.execute_modify(
            """
            INSERT OR REPLACE INTO versions
            (version_id, target, commit_hash, tag, branch, manifest_path, sandbox_id, metadata_json, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact.version_id,
                artifact.target,
                artifact.commit_hash,
                artifact.tag,
                artifact.branch,
                artifact.manifest_path,
                artifact.sandbox_id,
                self.json_dumps(artifact.metadata),
                is_active,
            ),
        )
        return artifact

    async def set_active(self, version_id: str) -> None:
        row = await self.execute_one("SELECT target FROM versions WHERE version_id = ?", (version_id,))
        if row is None:
            raise KeyError(f"version not found: {version_id}")
        target = row[0]

        await self.execute_modify(
            "UPDATE versions SET is_active=0 WHERE target = ?",
            (target,),
        )
        await self.execute_modify(
            "UPDATE versions SET is_active=1 WHERE version_id = ?",
            (version_id,),
        )

    async def get_active(self, target: EvolutionTarget) -> Optional[VersionArtifact]:
        row = await self.execute_one(
            """
            SELECT * FROM versions
            WHERE target = ? AND is_active = 1
            ORDER BY created_at DESC LIMIT 1
            """,
            (target,),
        )
        return self._row_to_artifact(row) if row else None

    async def get(self, version_id: str) -> Optional[VersionArtifact]:
        row = await self.execute_one(
            "SELECT * FROM versions WHERE version_id = ?",
            (version_id,),
        )
        return self._row_to_artifact(row) if row else None

    async def list_versions(
        self,
        target: Optional[EvolutionTarget] = None,
        limit: int = 20,
    ) -> list[VersionArtifact]:
        if target is None:
            rows = await self.execute(
                "SELECT * FROM versions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        else:
            rows = await self.execute(
                """
                SELECT * FROM versions
                WHERE target = ? ORDER BY created_at DESC LIMIT ?
                """,
                (target, limit),
            )
        return [self._row_to_artifact(r) for r in rows]

    async def list_targets(self) -> list[EvolutionTarget]:
        rows = await self.execute(
            "SELECT DISTINCT target FROM versions ORDER BY target ASC"
        )
        return [row[0] for row in rows]

    async def export_manifest_index(self) -> dict[str, list[str]]:
        rows = await self.execute(
            "SELECT target, version_id FROM versions ORDER BY created_at DESC"
        )
        index: dict[str, list[str]] = {}
        for row in rows:
            target = str(row[0])
            version_id = str(row[1])
            index.setdefault(target, []).append(version_id)
        return index

    def _row_to_artifact(self, row: tuple) -> VersionArtifact:
        """将查询行转换为 VersionArtifact。"""
        return VersionArtifact(
            version_id=str(row[0]),
            target=str(row[1]),
            commit_hash=row[2],
            tag=row[3],
            branch=row[4],
            manifest_path=row[5],
            sandbox_id=row[6],
            metadata=self.json_loads(row[7]),
        )
