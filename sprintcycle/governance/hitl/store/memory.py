"""HITL 内存存储。"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, Optional

from .base import HitlStore
from ..types import HitlCorrection, HitlRequestRecord, HitlReplayDirective


class HitlMemoryStore(HitlStore):
    def __init__(self) -> None:
        self._requests: Dict[str, HitlRequestRecord] = {}
        self._corrections: Dict[str, HitlCorrection] = {}
        self._replays: Dict[str, HitlReplayDirective] = {}

    async def insert_open(self, row: HitlRequestRecord) -> None:
        self._requests[row.request_id] = row

    async def update_decision(
        self,
        request_id: str,
        *,
        decision: str,
        note: Optional[str] = None,
        decision_kind: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        row = self._requests.get(request_id)
        if row is None or row.status not in {"open", "modified", "retrying"}:
            return False
        self._requests[request_id] = replace(
            row,
            status=status or "resolved",
            decision=decision,
            decision_note=note,
            decision_kind=decision_kind,
        )
        return True

    async def get(self, request_id: str) -> Optional[HitlRequestRecord]:
        return self._requests.get(request_id)

    async def list_open(self, execution_id: Optional[str] = None) -> list[HitlRequestRecord]:
        rows = [r for r in self._requests.values() if r.status in {"open", "modified", "retrying"}]
        if execution_id:
            rows = [r for r in rows if r.execution_id == execution_id]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50) -> list[HitlRequestRecord]:
        rows = list(self._requests.values())
        if execution_id:
            rows = [r for r in rows if r.execution_id == execution_id]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)[:limit]

    async def insert_correction(self, request_id: str, correction: HitlCorrection) -> None:
        self._corrections[request_id] = correction
        row = self._requests.get(request_id)
        if row is not None:
            self._requests[request_id] = replace(row, correction=correction, status="modified")

    async def insert_replay(self, request_id: str, replay: HitlReplayDirective) -> None:
        self._replays[request_id] = replay
        row = self._requests.get(request_id)
        if row is not None:
            self._requests[request_id] = replace(row, replay_directive=replay, status="retrying", replay_count=row.replay_count + 1)
