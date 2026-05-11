"""Lifecycle contract helpers for web-triggered execution chains.

This module centralizes the minimal structured payload used to keep the
Web -> plan -> execute -> observe -> deliver -> runtime -> suggestion ->
evolution chain consistent across services.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


LIFECYCLE_STAGES: tuple[str, ...] = (
    "normalized",
    "planned",
    "scheduled",
    "executing",
    "observing",
    "repairing",
    "delivering",
    "runtime_linked",
    "suggesting",
    "governing",
    "evolving",
)


@dataclass
class LifecycleContract:
    execution_id: str
    task_id: str
    project_path: str
    task_type: str = "project_optimization"
    intent: str = ""
    stage: str = "normalized"
    status: str = "pending"
    failure_kind: str = ""
    failure_reason: str = ""
    delivery_summary: Dict[str, Any] = field(default_factory=dict)
    runtime_linkage: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    governance_refs: Dict[str, Any] = field(default_factory=dict)
    evolution_refs: Dict[str, Any] = field(default_factory=dict)
    repair_refs: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["is_terminal"] = self.status in {"success", "failed", "cancelled"}
        payload["stage_index"] = LIFECYCLE_STAGES.index(self.stage) if self.stage in LIFECYCLE_STAGES else -1
        return payload


def normalize_lifecycle_metadata(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    meta = dict(metadata or {})
    meta.setdefault("task_type", meta.get("task_type") or "project_optimization")
    meta.setdefault("intent", meta.get("intent") or meta.get("task_id") or meta.get("name") or "")
    meta.setdefault("source", meta.get("source") or "web")
    meta.setdefault("stability_contract", "web_end_to_end")
    return meta


def build_lifecycle_contract(
    *,
    execution_id: str,
    task_id: str,
    project_path: str,
    stage: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None,
    failure_kind: str = "",
    failure_reason: str = "",
    delivery_summary: Optional[Dict[str, Any]] = None,
    runtime_linkage: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[Dict[str, Any]]] = None,
    evolution_refs: Optional[Dict[str, Any]] = None,
    repair_refs: Optional[Dict[str, Any]] = None,
    governance_refs: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
) -> LifecycleContract:
    meta = normalize_lifecycle_metadata(metadata)
    return LifecycleContract(
        execution_id=execution_id,
        task_id=task_id,
        project_path=project_path,
        task_type=str(meta.get("task_type") or "project_optimization"),
        intent=str(meta.get("intent") or ""),
        stage=stage,
        status=status,
        failure_kind=failure_kind,
        failure_reason=failure_reason,
        delivery_summary=dict(delivery_summary or {}),
        runtime_linkage=dict(runtime_linkage or {}),
        suggestions=list(suggestions or []),
        evolution_refs=dict(evolution_refs or {}),
        repair_refs=dict(repair_refs or {}),
        governance_refs=dict(governance_refs or {}),
        metrics=dict(metrics or {}),
        metadata=meta,
    )
