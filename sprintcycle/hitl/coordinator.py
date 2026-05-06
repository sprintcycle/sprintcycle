"""HITL 协调器：落库、SSE 事件、轮询等待决策（跨进程安全）。"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import uuid4

from loguru import logger

from ..execution.events import Event, EventType, ExecutionEventBackend
from .store_sqlite import HitlSqliteStore, default_hitl_db_path
from .types import HitlDecision, HitlGate, HitlRequestRecord

if TYPE_CHECKING:
    from ..config.runtime_config import RuntimeConfig


def _timeout_decision(config: "RuntimeConfig") -> HitlDecision:
    b = (getattr(config, "hitl_timeout_behavior", None) or "approve").strip().lower()
    if b == "abort_execution":
        return HitlDecision.ABORT_EXECUTION
    if b == "skip_sprint":
        return HitlDecision.SKIP_SPRINT
    return HitlDecision.APPROVE


class HitlCoordinator:
    """与 SprintCycle / Dashboard 共享：阻塞等待以 DB 为准的决策。"""

    def __init__(
        self,
        *,
        project_root: str,
        config: "RuntimeConfig",
        event_bus: ExecutionEventBackend,
        store: HitlSqliteStore,
    ) -> None:
        self._project_root = project_root
        self._config = config
        self._event_bus = event_bus
        self._store = store
        self._poll_interval = 0.25

    @property
    def store(self) -> HitlSqliteStore:
        return self._store

    async def wait_for_decision(
        self,
        *,
        execution_id: str,
        gate: HitlGate,
        title: str,
        summary: str,
        context: Dict[str, Any],
    ) -> HitlDecision:
        timeout_s = max(1, int(getattr(self._config, "hitl_default_timeout_seconds", 300) or 300))
        request_id = str(uuid4())
        now = datetime.now().isoformat()
        row = HitlRequestRecord(
            request_id=request_id,
            execution_id=execution_id,
            gate=gate.value,
            status="open",
            title=title,
            summary=summary,
            context=context,
            created_at=now,
            timeout_seconds=timeout_s,
        )
        await self._store.insert_open(row)
        await self._emit_open(row)
        deadline = time.monotonic() + float(timeout_s)
        while True:
            cur = await self._store.get(request_id)
            if cur and cur.status == "resolved" and cur.decision:
                try:
                    return HitlDecision(cur.decision)
                except ValueError:
                    logger.warning("HITL invalid decision stored: {}", cur.decision)
                    return HitlDecision.APPROVE
            if time.monotonic() >= deadline:
                td = _timeout_decision(self._config)
                ok = await self._store.resolve(
                    request_id,
                    td.value,
                    None,
                    from_timeout=True,
                )
                if ok:
                    await self._emit_resolved(request_id, execution_id, td.value, "timeout")
                return td
            await asyncio.sleep(self._poll_interval)

    async def submit_decision(
        self, request_id: str, decision: str, note: Optional[str] = None
    ) -> Optional[HitlRequestRecord]:
        try:
            HitlDecision(decision)
        except ValueError:
            return None
        ok = await self._store.resolve(request_id, decision, note, from_timeout=False)
        if not ok:
            return None
        rec = await self._store.get(request_id)
        if rec:
            await self._emit_resolved(
                request_id, rec.execution_id, decision, (note or "").strip() or None
            )
        return rec

    async def list_pending(self, execution_id: Optional[str] = None) -> list[Dict[str, Any]]:
        rows = await self._store.list_open(execution_id)
        return [r.to_dict() for r in rows]

    async def list_history(
        self, execution_id: Optional[str] = None, limit: int = 50
    ) -> list[Dict[str, Any]]:
        rows = await self._store.list_history(execution_id, limit)
        return [r.to_dict() for r in rows]

    async def _emit_open(self, row: HitlRequestRecord) -> None:
        try:
            await self._event_bus.emit(
                Event(
                    type=EventType.HITL_REQUEST_OPEN,
                    data={
                        "request_id": row.request_id,
                        "execution_id": row.execution_id,
                        "gate": row.gate,
                        "title": row.title,
                        "summary": row.summary,
                        "timeout_seconds": row.timeout_seconds,
                        "created_at": row.created_at,
                    },
                )
            )
        except Exception as e:
            logger.warning("HITL emit open failed: {}", e)

    async def _emit_resolved(
        self,
        request_id: str,
        execution_id: str,
        decision: str,
        note: Optional[str],
    ) -> None:
        try:
            await self._event_bus.emit(
                Event(
                    type=EventType.HITL_REQUEST_RESOLVED,
                    data={
                        "request_id": request_id,
                        "execution_id": execution_id,
                        "decision": decision,
                        "note": note,
                    },
                )
            )
        except Exception as e:
            logger.warning("HITL emit resolved failed: {}", e)


def create_hitl_coordinator(
    project_root: str,
    config: "RuntimeConfig",
    event_bus: ExecutionEventBackend,
) -> Optional[HitlCoordinator]:
    if not getattr(config, "hitl_enabled", False):
        return None
    raw = getattr(config, "hitl_db_path", None)
    db_path = (
        str(raw).strip()
        if isinstance(raw, str) and str(raw).strip()
        else default_hitl_db_path(project_root)
    )
    store = HitlSqliteStore(db_path)
    return HitlCoordinator(project_root=project_root, config=config, event_bus=event_bus, store=store)
