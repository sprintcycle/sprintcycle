"""Suggestion persistence store.

SQLite-backed persistence keeps the implementation lightweight and reusable.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from sprintcycle.application.governance.suggestion.models import (
    Suggestion,
    SuggestionApprovalRecord,
    SuggestionReviewRecord,
    SuggestionSourceType,
    SuggestionStatus,
)


class SuggestionStore:
    def __init__(self, root_dir: str = ".sprintcycle/governance/suggestion") -> None:
        self._root_dir = Path(root_dir).expanduser().resolve()
        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._root_dir / "suggestions.sqlite3"
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
                CREATE TABLE IF NOT EXISTS suggestions (
                    suggestion_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_id TEXT,
                    title TEXT,
                    summary TEXT,
                    details TEXT,
                    impact_scope_json TEXT,
                    severity TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    reviewed_at TEXT,
                    approved_at TEXT,
                    reviewer TEXT,
                    review_notes TEXT,
                    linked_evolution_id TEXT,
                    linked_version_id TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS suggestion_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suggestion_id TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    reviewed_at TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS suggestion_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suggestion_id TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    approved_at TEXT,
                    promoted INTEGER NOT NULL DEFAULT 0,
                    evolution_request_id TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.commit()

    async def save(self, suggestion: Suggestion) -> Suggestion:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO suggestions
                    (suggestion_id, source_type, source_id, title, summary, details, impact_scope_json,
                     severity, status, created_at, updated_at, reviewed_at, approved_at, reviewer,
                     review_notes, linked_evolution_id, linked_version_id, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        suggestion.suggestion_id,
                        suggestion.source_type,
                        suggestion.source_id,
                        suggestion.title,
                        suggestion.summary,
                        suggestion.details,
                        json.dumps(suggestion.impact_scope, ensure_ascii=False),
                        suggestion.severity,
                        suggestion.status,
                        suggestion.created_at,
                        suggestion.updated_at,
                        suggestion.reviewed_at,
                        suggestion.approved_at,
                        suggestion.reviewer,
                        suggestion.review_notes,
                        suggestion.linked_evolution_id,
                        suggestion.linked_version_id,
                        json.dumps(suggestion.metadata, ensure_ascii=False),
                    ),
                )
                conn.commit()
        return suggestion

    async def get(self, suggestion_id: str) -> Optional[Suggestion]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM suggestions WHERE suggestion_id=?", (suggestion_id,)).fetchone()
        return self._row_to_suggestion(row) if row else None

    async def list(
        self,
        status: Optional[SuggestionStatus] = None,
        source_type: Optional[SuggestionSourceType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Suggestion]:
        q = "SELECT * FROM suggestions WHERE 1=1"
        params: list[object] = []
        if status is not None:
            q += " AND status=?"
            params.append(status)
        if source_type is not None:
            q += " AND source_type=?"
            params.append(source_type)
        q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self._connect() as conn:
            rows = conn.execute(q, tuple(params)).fetchall()
        return [self._row_to_suggestion(r) for r in rows]

    async def update_status(self, suggestion_id: str, status: SuggestionStatus) -> Suggestion:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE suggestions SET status=?, updated_at=CURRENT_TIMESTAMP WHERE suggestion_id=?",
                    (status, suggestion_id),
                )
                conn.commit()
        suggestion = await self.get(suggestion_id)
        if suggestion is None:
            raise KeyError(f"suggestion not found: {suggestion_id}")
        suggestion.status = status
        return suggestion

    async def update_evolution_link(self, suggestion_id: str, evolution_id: str) -> Suggestion:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE suggestions SET linked_evolution_id=?, updated_at=CURRENT_TIMESTAMP WHERE suggestion_id=?",
                    (evolution_id, suggestion_id),
                )
                conn.commit()
        suggestion = await self.get(suggestion_id)
        if suggestion is None:
            raise KeyError(f"suggestion not found: {suggestion_id}")
        suggestion.linked_evolution_id = evolution_id
        return suggestion

    async def append_review(self, record: SuggestionReviewRecord) -> None:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO suggestion_reviews
                    (suggestion_id, reviewer, status, notes, reviewed_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.suggestion_id,
                        record.reviewer,
                        record.status,
                        record.notes,
                        record.reviewed_at,
                        json.dumps(record.metadata, ensure_ascii=False),
                    ),
                )
                conn.commit()

    async def append_approval(self, record: SuggestionApprovalRecord) -> None:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO suggestion_approvals
                    (suggestion_id, approved_by, approved_at, promoted, evolution_request_id, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.suggestion_id,
                        record.approved_by,
                        record.approved_at,
                        1 if record.promoted else 0,
                        record.evolution_request_id,
                        json.dumps(record.metadata, ensure_ascii=False),
                    ),
                )
                conn.commit()

    def _row_to_suggestion(self, row: sqlite3.Row) -> Suggestion:
        return Suggestion(
            suggestion_id=row["suggestion_id"],
            source_type=row["source_type"],
            source_id=row["source_id"],
            title=row["title"] or "",
            summary=row["summary"] or "",
            details=row["details"] or "",
            impact_scope=json.loads(row["impact_scope_json"] or "[]"),
            severity=row["severity"] or "medium",
            status=row["status"] or "pending",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            reviewed_at=row["reviewed_at"],
            approved_at=row["approved_at"],
            reviewer=row["reviewer"],
            review_notes=row["review_notes"] or "",
            linked_evolution_id=row["linked_evolution_id"],
            linked_version_id=row["linked_version_id"],
            metadata=json.loads(row["metadata_json"] or "{}"),
        )
