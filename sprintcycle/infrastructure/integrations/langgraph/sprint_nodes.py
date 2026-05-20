"""Per-sprint LangGraph nodes for SprintCycle orchestration."""

from __future__ import annotations

from typing import Literal

from .states import SprintState


async def sprint_prepare(state: SprintState) -> SprintState:
    sprint = dict(state.get("sprint", {}) or {})
    context = dict(state.get("context", {}) or {})
    return {
        **state,
        "sprint_context": {
            "sprint_name": sprint.get("name", ""),
            "runtime_config": context.get("runtime_config", {}),
            "project_name": context.get("project_name", "sprintcycle"),
        },
        "timeline": list(state.get("timeline", []) or []) + [{"node": "prepare", "status": "ok"}],
    }


async def sprint_execute(state: SprintState) -> SprintState:
    sprint_executor = (state.get("context", {}) or {}).get("sprint_executor")
    sprint = dict(state.get("sprint", {}) or {})
    sprint_context = dict(state.get("sprint_context", {}) or {})
    if sprint_executor is None or not hasattr(sprint_executor, "execute_sprint"):
        return {
            **state,
            "error": "sprint_executor_unavailable",
            "sprint_result": {
                "sprint_name": sprint.get("name", ""),
                "status": "failed",
                "task_results": [],
                "error": "sprint_executor_unavailable",
            },
            "timeline": list(state.get("timeline", []) or []) + [{"node": "execute", "status": "error"}],
        }
    result = await sprint_executor.execute_sprint(sprint=sprint, context=sprint_context)
    sprint_result = (
        result.to_dict()
        if hasattr(result, "to_dict")
        else {
            "sprint_name": sprint.get("name", ""),
            "status": getattr(result, "status", "success"),
            "task_results": [],
        }
    )
    return {
        **state,
        "sprint_result": sprint_result,
        "timeline": list(state.get("timeline", []) or []) + [{"node": "execute", "status": "ok"}],
    }


async def sprint_observe(state: SprintState) -> SprintState:
    sprint_result = dict(state.get("sprint_result", {}) or {})
    task_results = list(sprint_result.get("task_results", []) or [])
    total = len(task_results)
    failed = 0
    for task_result in task_results:
        status = str(task_result.get("status", "")).lower()
        if status not in {"success", "succeeded", "completed"}:
            failed += 1
    observation = {
        "task_count": total,
        "failed_count": failed,
        "success_rate": (total - failed) / total if total else 1.0,
    }
    return {
        **state,
        "observation": observation,
        "timeline": list(state.get("timeline", []) or []) + [{"node": "observe", "status": "ok"}],
    }


async def sprint_repair(state: SprintState) -> SprintState:
    observation = dict(state.get("observation", {}) or {})
    success_rate = float(observation.get("success_rate", 1.0) or 1.0)
    attempt = int(state.get("attempt", 1) or 1)
    if success_rate < 1.0 and attempt < 3:
        decision = {"action": "retry", "reason": "success_rate_below_threshold"}
    else:
        decision = {"action": "finalize", "reason": "acceptable"}
    return {
        **state,
        "repair_decision": decision,
        "timeline": list(state.get("timeline", []) or []) + [{"node": "repair", "status": "ok"}],
    }


async def sprint_finalize(state: SprintState) -> SprintState:
    return {
        **state,
        "final_sprint_result": dict(state.get("sprint_result", {}) or {}),
        "timeline": list(state.get("timeline", []) or []) + [{"node": "finalize", "status": "ok"}],
    }


def should_retry_sprint(state: SprintState) -> Literal["sprint_execute", "sprint_finalize"]:
    decision = dict(state.get("repair_decision", {}) or {})
    if decision.get("action") == "retry":
        return "sprint_execute"
    return "sprint_finalize"


__all__ = [
    "sprint_prepare",
    "sprint_execute",
    "sprint_observe",
    "sprint_repair",
    "sprint_finalize",
    "should_retry_sprint",
]
