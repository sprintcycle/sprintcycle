"""HITL SQLite 存储。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from ..types import HitlCorrection, HitlReplayDirective, HitlRequestRecord
from .base import HitlStore


def default_hitl_db_path(project_root: str) -> str:
    root = Path(project_root).expanduser().resolve()
    return str(root / ".sprintcycle" / "hitl.sqlite3")


class HitlSqliteStore(HitlStore):
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path).expanduser().resolve()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
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
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hitl_requests_execution_status ON hitl_requests(execution_id, status, created_at DESC)"
            )
            conn.commit()

    async def insert_open(self, row: HitlRequestRecord) -> None:
        with self._connect() as conn:
            conn.execute(
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
                    json.dumps(row.context, ensure_ascii=False),
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
                    json.dumps(row.applied_context, ensure_ascii=False),
                    json.dumps(row.correction.to_dict(), ensure_ascii=False) if row.correction else None,
                    json.dumps(row.replay_directive.to_dict(), ensure_ascii=False) if row.replay_directive else None,
                ),
            )
            conn.commit()

    async def update_decision(
        self,
        request_id: str,
        *,
        decision: str,
        note: Optional[str] = None,
        decision_kind: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        decided_at = self._now_iso()
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE hitl_requests
                SET status = ?, decided_at = ?, decision = ?, decision_note = ?, decision_kind = ?
                WHERE request_id = ? AND status IN ('open', 'modified', 'retrying')
                """,
                (status or "resolved", decided_at, decision, note, decision_kind, request_id),
            )
            conn.commit()
            return cur.rowcount > 0

    async def get(self, request_id: str) -> Optional[HitlRequestRecord]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM hitl_requests WHERE request_id = ?", (request_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return self._row_to_record(row)

    async def list_open(self, execution_id: Optional[str] = None) -> list[HitlRequestRecord]:
        sql = "SELECT * FROM hitl_requests WHERE status IN ('open', 'modified', 'retrying')"
        params: list[object] = []
        if execution_id:
            sql += " AND execution_id = ?"
            params.append(execution_id)
        sql += " ORDER BY created_at DESC"
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            return [self._row_to_record(r) for r in cur.fetchall()]

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50) -> list[HitlRequestRecord]:
        sql = "SELECT * FROM hitl_requests"
        params: list[object] = []
        if execution_id:
            sql += " WHERE execution_id = ?"
            params.append(execution_id)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            return [self._row_to_record(r) for r in cur.fetchall()]

    async def insert_correction(self, request_id: str, correction: HitlCorrection) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE hitl_requests SET correction_json = ?, status = 'modified' WHERE request_id = ?",
                (json.dumps(correction.to_dict(), ensure_ascii=False), request_id),
            )
            conn.commit()

    async def insert_replay(self, request_id: str, replay: HitlReplayDirective) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE hitl_requests SET replay_directive_json = ?, status = 'retrying', replay_count = replay_count + 1 WHERE request_id = ?",
                (json.dumps(replay.to_dict(), ensure_ascii=False), request_id),
            )
            conn.commit()

    async def append_event(self, *args, **kwargs) -> None:
        return None

    def _row_to_record(self, row: sqlite3.Row) -> HitlRequestRecord:
        correction = row["correction_json"]
        replay = row["replay_directive_json"]
        return HitlRequestRecord(
            request_id=row["request_id"],
            execution_id=row["execution_id"],
            gate=row["gate"],
            status=row["status"],
            title=row["title"],
            summary=row["summary"],
            context=json.loads(row["context_json"] or "{}"),
            created_at=row["created_at"],
            decided_at=row["decided_at"],
            decision=row["decision"],
            decision_note=row["decision_note"],
            timeout_seconds=int(row["timeout_seconds"] or 300),
            risk_level=row["risk_level"] or "medium",
            parent_request_id=row["parent_request_id"],
            revision=int(row["revision"] or 1),
            decision_kind=row["decision_kind"],
            status_reason=row["status_reason"],
            superseded_by=row["superseded_by"],
            replay_count=int(row["replay_count"] or 0),
            applied_context=json.loads(row["applied_context_json"] or "{}"),
            correction=HitlCorrection(**json.loads(correction)) if correction else None,
            replay_directive=HitlReplayDirective(**json.loads(replay)) if replay else None,
        )

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime

        return datetime.now().isoformat()
