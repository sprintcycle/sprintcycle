"""HITL 协调器：落库、事件、轮询等待决策（跨进程安全）。"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import uuid4

from loguru import logger

from ...execution.events import Event, EventType, ExecutionEventBackend
from .context import build_replay_context, merge_correction_into_context, summarize_context_diff
from .decision_normalize import normalize_hitl_decision_with_intent, validate_hitl_decision_for_submit
from .events import HitlEventType
from .store import HitlSqliteStore, default_hitl_db_path
from .types import HitlCorrection, HitlDecision, HitlGate, HitlRequestRecord, HitlReplayDirective, HitlRiskLevel

if TYPE_CHECKING:
    from ...infrastructure.config.runtime_config import RuntimeConfig


def _timeout_decision(config: "RuntimeConfig") -> HitlDecision:
    b = (getattr(config, "hitl_timeout_behavior", None) or "approve").strip().lower()
    if b in ("abort_execution", "abort"):
        return HitlDecision.ABORT_EXECUTION
    if b in ("skip_sprint", "skip"):
        return HitlDecision.SKIP_SPRINT
    if b in ("request_changes", "modify"):
        return HitlDecision.REQUEST_CHANGES
    if b in ("reject", "deny"):
        return HitlDecision.REJECT
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

    async def create_request(
        self,
        *,
        execution_id: str,
        gate: HitlGate,
        title: str,
        summary: str,
        context: Dict[str, Any],
        risk_level: str = HitlRiskLevel.MEDIUM.value,
        timeout_seconds: Optional[int] = None,
    ) -> HitlRequestRecord:
        timeout_s = max(1, int(timeout_seconds or getattr(self._config, "hitl_default_timeout_seconds", 300) or 300))
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
            risk_level=risk_level,
        )
        await self._store.insert_open(row)
        await self._emit(HitlEventType.REQUEST_OPEN, row.to_dict())
        return row

    async def wait_for_decision(
        self,
        *,
        execution_id: str,
        gate: HitlGate,
        title: str,
        summary: str,
        context: Dict[str, Any],
        risk_level: str = HitlRiskLevel.MEDIUM.value,
        timeout_seconds: Optional[int] = None,
    ) -> HitlDecision:
        row = await self.create_request(
            execution_id=execution_id,
            gate=gate,
            title=title,
            summary=summary,
            context=context,
            risk_level=risk_level,
            timeout_seconds=timeout_seconds,
        )
        deadline = time.monotonic() + float(row.timeout_seconds)
        while True:
            cur = await self._store.get(row.request_id)
            if cur and cur.status == "resolved" and cur.decision:
                try:
                    return HitlDecision(cur.decision)
                except ValueError:
                    logger.warning("HITL invalid decision stored: {}", cur.decision)
                    return HitlDecision.APPROVE
            if time.monotonic() >= deadline:
                td = _timeout_decision(self._config)
                ok = await self._store.update_decision(
                    row.request_id,
                    decision=td.value,
                    note=None,
                    decision_kind="timeout",
                    status="resolved",
                )
                if ok:
                    await self._emit(
                        HitlEventType.REQUEST_RESOLVED,
                        {
                            "request_id": row.request_id,
                            "execution_id": execution_id,
                            "decision": td.value,
                            "source": "timeout",
                            "status": "resolved",
                        },
                    )
                return td
            await asyncio.sleep(self._poll_interval)

    async def submit_decision(
        self,
        request_id: str,
        decision: str,
        note: Optional[str] = None,
        *,
        correction: Optional[HitlCorrection] = None,
        replay: Optional[HitlReplayDirective] = None,
    ) -> Optional[HitlRequestRecord]:
        canon = validate_hitl_decision_for_submit(decision)
        if canon is None:
            return None
        rec = await self._store.get(request_id)
        if rec is None:
            return None
        intent = normalize_hitl_decision_with_intent(canon)[1]
        if correction is not None:
            rec = await self.submit_correction(request_id, correction) or rec
        if replay is not None:
            rec = await self.request_retry(request_id, replay) or rec
        status = "resolved"
        if canon in (HitlDecision.REQUEST_CHANGES.value, HitlDecision.MODIFY.value):
            status = "modified"
        elif canon == HitlDecision.RETRY.value:
            status = "retrying"
        await self._store.update_decision(
            request_id,
            decision=canon,
            note=note,
            decision_kind=intent,
            status=status,
        )
        rec = await self._store.get(request_id) or rec
        await self._emit(HitlEventType.REQUEST_RESOLVED, {"request_id": request_id, "execution_id": rec.execution_id, "decision": canon, "note": (note or "").strip() or None, "decision_kind": intent, "status": status})
        return rec

    async def submit_correction(self, request_id: str, correction: HitlCorrection, *, emit_decision: bool = True) -> Optional[HitlRequestRecord]:
        rec = await self._store.get(request_id)
        if rec is None:
            return None
        await self._store.insert_correction(request_id, correction)
        updated = await self._store.get(request_id) or rec
        before = dict(updated.context)
        patched = merge_correction_into_context(updated.context, correction)
        updated.context = patched
        updated.applied_context = patched
        updated.correction = correction
        updated.status = "modified"
        await self._store.insert_open(updated)
        await self._emit(HitlEventType.REQUEST_MODIFIED, {"request_id": request_id, "execution_id": updated.execution_id, "correction": correction.to_dict()})
        await self._emit(HitlEventType.PATCH_APPLIED, {"request_id": request_id, "execution_id": updated.execution_id, "diff": summarize_context_diff(before, patched)})
        await self._emit(HitlEventType.CONTEXT_REFLOWED, {"request_id": request_id, "execution_id": updated.execution_id, "context_keys": sorted(patched.keys())})
        return updated

    async def request_retry(self, request_id: str, replay: HitlReplayDirective, *, emit_decision: bool = True) -> Optional[HitlRequestRecord]:
        rec = await self._store.get(request_id)
        if rec is None:
            return None
        await self._store.insert_replay(request_id, replay)
        updated = await self._store.get(request_id) or rec
        updated.replay_directive = replay
        updated.status = "retrying"
        base_context = updated.applied_context or updated.context
        updated.applied_context = build_replay_context(base_context, replay)
        await self._store.insert_open(updated)
        await self._emit(HitlEventType.REPLAY_TRIGGERED, {"request_id": request_id, "execution_id": updated.execution_id, "replay": replay.to_dict()})
        return updated

    async def list_pending(self, execution_id: Optional[str] = None) -> list[Dict[str, Any]]:
        rows = await self._store.list_open(execution_id)
        return [r.to_dict() for r in rows]

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50) -> list[Dict[str, Any]]:
        rows = await self._store.list_history(execution_id, limit)
        return [r.to_dict() for r in rows]

    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        rec = await self._store.get(request_id)
        return rec.to_dict() if rec else None

    async def _emit(self, event_type: HitlEventType, data: Dict[str, Any]) -> None:
        try:
            mapping = {
                HitlEventType.REQUEST_OPEN: EventType.HITL_REQUEST_OPEN,
                HitlEventType.REQUEST_UPDATED: EventType.HITL_REQUEST_OPEN,
                HitlEventType.REQUEST_MODIFIED: EventType.HITL_REQUEST_OPEN,
                HitlEventType.PATCH_APPLIED: EventType.HITL_REQUEST_OPEN,
                HitlEventType.CONTEXT_REFLOWED: EventType.HITL_REQUEST_OPEN,
                HitlEventType.REPLAY_TRIGGERED: EventType.HITL_REQUEST_OPEN,
                HitlEventType.REQUEST_RESOLVED: EventType.HITL_REQUEST_RESOLVED,
            }
            await self._event_bus.emit(Event(type=mapping.get(event_type, EventType.HITL_REQUEST_OPEN), data={**data, "hitl_event_type": event_type.value}))
        except Exception as e:
            logger.warning("HITL emit failed: {}", e)


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
