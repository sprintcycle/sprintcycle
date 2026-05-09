"""HITL 内存存储：测试/开发用。"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
from typing import Any, Dict, List, Optional

from ..types import HitlRequestRecord


class HitlMemoryStore:
    def __init__(self) -> None:
        self._rows: Dict[str, HitlRequestRecord] = {}
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def insert_open(self, row: HitlRequestRecord) -> None:
        async with self._lock:
            self._rows[row.request_id] = deepcopy(row)

    async def resolve(self, request_id: str, decision: str, note: Optional[str], from_timeout: bool = False) -> bool:
        async with self._lock:
            row = self._rows.get(request_id)
            if row is None or row.status == "resolved":
                return False
            row.status = "resolved"
            row.decision = decision
            row.decision_note = note
            row.decided_at = row.decided_at or row.created_at
            self._rows[request_id] = row
            self._events.setdefault(request_id, []).append(
                {"type": "resolved", "decision": decision, "note": note, "from_timeout": from_timeout}
            )
            return True

    async def get(self, request_id: str) -> Optional[HitlRequestRecord]:
        async with self._lock:
            row = self._rows.get(request_id)
            return deepcopy(row) if row else None

    async def list_open(self, execution_id: Optional[str] = None) -> List[HitlRequestRecord]:
        async with self._lock:
            rows = [r for r in self._rows.values() if r.status != "resolved"]
            if execution_id:
                rows = [r for r in rows if r.execution_id == execution_id]
            return [deepcopy(r) for r in rows]

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50) -> List[HitlRequestRecord]:
        async with self._lock:
            rows = list(self._rows.values())
            if execution_id:
                rows = [r for r in rows if r.execution_id == execution_id]
            rows.sort(key=lambda r: r.created_at, reverse=True)
            return [deepcopy(r) for r in rows[:limit]]

    async def append_event(self, request_id: str, event: Dict[str, Any]) -> None:
        async with self._lock:
            self._events.setdefault(request_id, []).append(deepcopy(event))
