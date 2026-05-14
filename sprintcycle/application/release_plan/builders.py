"""
从 dict 切片或诊断参数构造 ``ReleasePlan``（与 ``ReleasePlanParser`` 产物一致的主模型）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import (
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)


def sprint_backlog_item_from_dict(t: Any) -> SprintBacklogItem:
    if isinstance(t, SprintBacklogItem):
        return t
    if isinstance(t, str):
        return SprintBacklogItem(description=t, agent="coder")
    if isinstance(t, dict):
        desc = t.get("description")
        if desc is None or (isinstance(desc, str) and not str(desc).strip()):
            raise ValueError("Sprint Backlog item dict must include non-empty 'description'")
        return SprintBacklogItem(
            description=str(desc),
            agent=str(t.get("agent") or "coder"),
            target=t.get("target"),
            constraints=list(t.get("constraints") or []),
            expected_output=t.get("expected_output"),
            timeout=int(t.get("timeout") or 600),
        )
    return SprintBacklogItem(description=str(t), agent="coder")


def sprint_definition_from_dict(data: Dict[str, Any]) -> SprintDefinition:
    name = str(data.get("name") or "sprint")
    goals = [str(g) for g in data.get("goals", [])]
    raw_tasks = data.get("tasks", [])
    tasks = [sprint_backlog_item_from_dict(x) for x in raw_tasks]
    return SprintDefinition(name=name, goals=goals, tasks=tasks)


def release_plan_from_diagnostic_slices(
    *,
    plan_name: str,
    project_path: str,
    version: str = "v1.0.0",
    sprint_dicts: List[Dict[str, Any]],
    rule: str,
    confidence: float,
    expected_benefit: float,
    priority: int,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> ReleasePlan:
    sprints = [sprint_definition_from_dict(d) for d in sprint_dicts]
    meta: Dict[str, Any] = dict(extra_metadata or {})
    meta.setdefault("plan_source_type", "diagnostic")
    meta["diagnostic_rule"] = rule
    meta["diagnostic_confidence"] = float(confidence)
    meta["diagnostic_expected_benefit"] = float(expected_benefit)
    meta["diagnostic_priority"] = int(priority)
    return ReleasePlan(
        project=ProductAnchor(name=plan_name, path=project_path, version=version),
        mode=ExecutionMode.NORMAL,
        sprints=sprints,
        metadata=meta,
    )


__all__ = [
    "sprint_backlog_item_from_dict",
    "sprint_definition_from_dict",
    "release_plan_from_diagnostic_slices",
]
