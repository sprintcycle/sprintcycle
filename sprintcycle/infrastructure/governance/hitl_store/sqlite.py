"""HITL SQLite 存储（基于 BaseSqliteStore）。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from sprintcycle.infrastructure.governance.hitl_store.base import HitlStore
from sprintcycle.infrastructure.persistence.base import BaseSqliteStore
from sprintcycle.application.governance.hitl.types import HitlCorrection, HitlReplayDirective, HitlRequestRecord


def default_hitl_db_path(project_root: str) -> str:
    from pathlib import Path

    root = Path(project_root).expanduser().resolve()
    return str(root / ".sprintcycle" / "hitl.sqlite3")


class HitlSqliteStore(BaseSqliteStore, HitlStore):
    """HITL 请求持久化（基于 BaseSqliteStore）。"""

    # ─────────────────────────────────────────────────────────────────
    # BaseSqliteStore 模板方法实现
    # ─────────────────────────────────────────────────────────────────

    def _define_schema(self, conn: AsyncConnection) -> None:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS hitl_requests (
                    request_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    gate TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    decision TEXT,
                    decision_note TEXT,
                    timeout_seconds INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    parent_request_id TEXT,
                    revision INTEGER NOT NULL DEFAULT 1,
                    decision_kind TEXT,
                    status_reason TEXT,
                    superseded_by TEXT,
                    replay_count INTEGER NOT NULL DEFAULT 0,
                    applied_context_json TEXT NOT NULL DEFAULT '{}',
                    correction_json TEXT,
                    replay_directive_json TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_hitl_requests_execution_status "
                "ON hitl_requests(execution_id, status, created_at DESC)"
            )
        )

    # ─────────────────────────────────────────────────────────────────
    # HitlStore 接口实现
    # ─────────────────────────────────────────────────────────────────

    async def insert_open(self, row: HitlRequestRecord) -> None:
        await self.execute_modify(
            """
            INSERT OR REPLACE INTO hitl_requests (
                request_id, execution_id, gate, status, title, summary,
                context_json, created_at, decided_at, decision, decision_note,
                timeout_seconds, risk_level, parent_request_id, revision, decision_kind,
                status_reason, superseded_by, replay_count, applied_context_json,
                correction_json, replay_directive_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.request_id,
                row.execution_id,
                row.gate,
                row.status,
                row.title,
                row.summary,
                self.json_dumps(row.context),
                row.created_at,
                row.decided_at,
                row.decision,
                row.decision_note,
                row.timeout_seconds,
                row.risk_level,
                row.parent_request_id,
                row.revision,
                row.decision_kind,
                row.status_reason,
                row.superseded_by,
                row.replay_count,
                self.json_dumps(row.applied_context),
                self.json_dumps(row.correction.to_dict()) if row.correction else None,
                self.json_dumps(row.replay_directive.to_dict()) if row.replay_directive else None,
            ),
        )

    async def update_decision(
        self,
        request_id: str,
        *,
        decision: str,
        note: Optional[str] = None,
        decision_kind: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        rows = await self.execute_modify(
            """
            UPDATE hitl_requests
            SET status = ?, decided_at = ?, decision = ?, decision_note = ?, decision_kind = ?
            WHERE request_id = ? AND status IN ('open', 'modified', 'retrying')
            """,
            (status or "resolved", self.now_iso(), decision, note, decision_kind, request_id),
        )
        return rows > 0

    async def resolve(
        self,
        request_id: str,
        decision: str,
        note: Optional[str] = None,
        from_timeout: bool = False,
    ) -> bool:
        decision_kind = "timeout" if from_timeout else "manual"
        return await self.update_decision(
            request_id,
            decision=decision,
            note=note,
            decision_kind=decision_kind,
            status="resolved",
        )

    async def get(self, request_id: str) -> Optional[HitlRequestRecord]:
        row = await self.execute_one(
            "SELECT * FROM hitl_requests WHERE request_id = ?",
            (request_id,),
        )
        return self._row_to_record(row) if row else None

    async def list_open(self, execution_id: Optional[str] = None) -> list[HitlRequestRecord]:
        if execution_id is None:
            rows = await self.execute(
                """
                SELECT * FROM hitl_requests
                WHERE status IN ('open', 'modified', 'retrying')
                ORDER BY created_at DESC
                """
            )
        else:
            rows = await self.execute(
                """
                SELECT * FROM hitl_requests
                WHERE status IN ('open', 'modified', 'retrying') AND execution_id = ?
                ORDER BY created_at DESC
                """,
                (execution_id,),
            )
        return [self._row_to_record(r) for r in rows]

    async def list_history(
        self,
        execution_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[HitlRequestRecord]:
        if execution_id is None:
            rows = await self.execute(
                "SELECT * FROM hitl_requests ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        else:
            rows = await self.execute(
                """
                SELECT * FROM hitl_requests
                WHERE execution_id = ? ORDER BY created_at DESC LIMIT ?
                """,
                (execution_id, limit),
            )
        return [self._row_to_record(r) for r in rows]

    async def insert_correction(self, request_id: str, correction: HitlCorrection) -> None:
        await self.execute_modify(
            """
            UPDATE hitl_requests
            SET correction_json = ?, status = 'modified'
            WHERE request_id = ?
            """,
            (self.json_dumps(correction.to_dict()), request_id),
        )

    async def insert_replay(self, request_id: str, replay: HitlReplayDirective) -> None:
        await self.execute_modify(
            """
            UPDATE hitl_requests
            SET replay_directive_json = ?, status = 'retrying', replay_count = replay_count + 1
            WHERE request_id = ?
            """,
            (self.json_dumps(replay.to_dict()), request_id),
        )

    async def append_event(self, *args, **kwargs) -> None:
        return None

    def _row_to_record(self, row: tuple) -> HitlRequestRecord:
        """将查询行转换为 HitlRequestRecord。"""
        correction_json = row[20]
        replay_directive_json = row[21]
        return HitlRequestRecord(
            request_id=str(row[0]),
            execution_id=str(row[1]),
            gate=str(row[2]),
            status=str(row[3]),
            title=str(row[4]),
            summary=str(row[5]),
            context=self.json_loads(row[6]),
            created_at=str(row[7]),
            decided_at=row[8],
            decision=row[9],
            decision_note=row[10],
            timeout_seconds=int(row[11]) if row[11] else 300,
            risk_level=str(row[12]) if row[12] else "medium",
            parent_request_id=row[13],
            revision=int(row[14]) if row[14] else 1,
            decision_kind=row[15],
            status_reason=row[16],
            superseded_by=row[17],
            replay_count=int(row[18]) if row[18] else 0,
            applied_context=self.json_loads(row[19]),
            correction=HitlCorrection(**self.json_loads(correction_json)) if correction_json else None,
            replay_directive=HitlReplayDirective(**self.json_loads(replay_directive_json)) if replay_directive_json else None,
        )
