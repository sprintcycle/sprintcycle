"""State models for LangGraph orchestration refactor."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class IntentState(TypedDict, total=False):
    intent: str
    context: Dict[str, Any]
    release_plan: Optional[Dict[str, Any]]
    release_plan_source: str
    sprints: List[Dict[str, Any]]
    sprint_results: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
    attempt: int
    timeline: List[Dict[str, Any]]
    error: Optional[str]
    final_result: Dict[str, Any]


class SprintState(TypedDict, total=False):
    sprint: Dict[str, Any]
    context: Dict[str, Any]
    sprint_context: Dict[str, Any]
    sprint_result: Optional[Dict[str, Any]]
    observation: Optional[Dict[str, Any]]
    repair_decision: Optional[Dict[str, Any]]
    attempt: int
    timeline: List[Dict[str, Any]]
    error: Optional[str]
    final_sprint_result: Optional[Dict[str, Any]]


__all__ = ["IntentState", "SprintState"]
