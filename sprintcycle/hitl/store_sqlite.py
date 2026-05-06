"""HITL 请求 SQLite 持久化（跨进程决策依赖 DB 真相源）。"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import HitlRequestRecord


def default_hitl_db_path(project_root: str) -> str:
    root = Path(project_root).expanduser().resolve()
    p = root / ".sprintcycle" / "hitl.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


class HitlSqliteStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._lock = asyncio.Lock()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, timeout=30.0)

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
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
                    timeout_seconds INTEGER NOT NULL DEFAULT 300
                );
                CREATE INDEX IF NOT EXISTS idx_hitl_exec_status
                    ON hitl_requests(execution_id, status);
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _insert_open_sync(self, row: HitlRequestRecord) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO hitl_requests (
                    request_id, execution_id, gate, status, title, summary,
                    context_json, created_at, timeout_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    row.timeout_seconds,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def _get_sync(self, request_id: str) -> Optional[HitlRequestRecord]:
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                SELECT request_id, execution_id, gate, status, title, summary,
                       context_json, created_at, decided_at, decision, decision_note,
                       timeout_seconds
                FROM hitl_requests WHERE request_id = ?
                """,
                (request_id,),
            )
            r = cur.fetchone()
            if not r:
                return None
            return self._row_to_record(r)
        finally:
            conn.close()

    def _resolve_sync(
        self,
        request_id: str,
        decision: str,
        note: Optional[str],
        from_timeout: bool,
    ) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT status FROM hitl_requests WHERE request_id = ?",
                (request_id,),
            )
            row = cur.fetchone()
            if not row or row[0] != "open":
                return False
            cur = conn.execute(
                """
                UPDATE hitl_requests SET
                    status = 'resolved',
                    decided_at = ?,
                    decision = ?,
                    decision_note = ?
                WHERE request_id = ? AND status = 'open'
                """,
                (
                    datetime.now().isoformat(),
                    decision,
                    (note or ("timeout" if from_timeout else "")) or None,
                    request_id,
                ),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def _list_open_sync(self, execution_id: Optional[str]) -> List[HitlRequestRecord]:
        conn = self._connect()
        try:
            if execution_id:
                cur = conn.execute(
                    """
                    SELECT request_id, execution_id, gate, status, title, summary,
                           context_json, created_at, decided_at, decision, decision_note,
                           timeout_seconds
                    FROM hitl_requests
                    WHERE status = 'open' AND execution_id = ?
                    ORDER BY created_at ASC
                    """,
                    (execution_id,),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT request_id, execution_id, gate, status, title, summary,
                           context_json, created_at, decided_at, decision, decision_note,
                           timeout_seconds
                    FROM hitl_requests
                    WHERE status = 'open'
                    ORDER BY created_at ASC
                    """,
                )
            return [self._row_to_record(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def _list_history_sync(self, execution_id: Optional[str], limit: int) -> List[HitlRequestRecord]:
        conn = self._connect()
        try:
            if execution_id:
                cur = conn.execute(
                    """
                    SELECT request_id, execution_id, gate, status, title, summary,
                           context_json, created_at, decided_at, decision, decision_note,
                           timeout_seconds
                    FROM hitl_requests
                    WHERE execution_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (execution_id, limit),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT request_id, execution_id, gate, status, title, summary,
                           context_json, created_at, decided_at, decision, decision_note,
                           timeout_seconds
                    FROM hitl_requests
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            return [self._row_to_record(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def _row_to_record(r: tuple[Any, ...]) -> HitlRequestRecord:
        (
            request_id,
            execution_id,
            gate,
            status,
            title,
            summary,
            context_json,
            created_at,
            decided_at,
            decision,
            decision_note,
            timeout_seconds,
        ) = r
        try:
            ctx = json.loads(context_json) if context_json else {}
        except json.JSONDecodeError:
            ctx = {}
        return HitlRequestRecord(
            request_id=request_id,
            execution_id=execution_id,
            gate=gate,
            status=status,
            title=title,
            summary=summary,
            context=ctx if isinstance(ctx, dict) else {},
            created_at=created_at,
            decided_at=decided_at,
            decision=decision,
            decision_note=decision_note,
            timeout_seconds=int(timeout_seconds or 300),
        )

    async def insert_open(self, row: HitlRequestRecord) -> None:
        async with self._lock:
            await asyncio.to_thread(self._insert_open_sync, row)

    async def get(self, request_id: str) -> Optional[HitlRequestRecord]:
        async with self._lock:
            return await asyncio.to_thread(self._get_sync, request_id)

    async def resolve(
        self,
        request_id: str,
        decision: str,
        note: Optional[str],
        *,
        from_timeout: bool = False,
    ) -> bool:
        async with self._lock:
            return bool(
                await asyncio.to_thread(
                    self._resolve_sync, request_id, decision, note, from_timeout
                )
            )

    async def list_open(self, execution_id: Optional[str] = None) -> List[HitlRequestRecord]:
        async with self._lock:
            return list(await asyncio.to_thread(self._list_open_sync, execution_id))

    async def list_history(
        self, execution_id: Optional[str] = None, limit: int = 50
    ) -> List[HitlRequestRecord]:
        async with self._lock:
            return list(await asyncio.to_thread(self._list_history_sync, execution_id, limit))
