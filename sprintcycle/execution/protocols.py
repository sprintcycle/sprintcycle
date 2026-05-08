"""执行层跨模块协议。"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class ExecutionContext:
    execution_id: str = "default"
    sprint_name: str = ""
    sprint_index: int = 0
    release_plan_id: str = ""
    project_path: str = "."
    coding_engine: str = "cursor"
    quality_level: str = "L2"
    project_goals: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    codebase_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_any(cls, value: Any) -> "ExecutionContext":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                execution_id=str(value.get("execution_id", "default")),
                sprint_name=str(value.get("sprint_name", "")),
                sprint_index=int(value.get("sprint_index", 0) or 0),
                release_plan_id=str(value.get("release_plan_id", "")),
                project_path=str(value.get("project_path", ".") or "."),
                coding_engine=str(value.get("coding_engine", "cursor")),
                quality_level=str(value.get("quality_level", "L2")),
                project_goals=str(value.get("project_goals", "")),
                metadata=dict(value.get("metadata", {}) or {}),
                codebase_context=dict(value.get("codebase_context", {}) or {}),
            )
        return cls()


@dataclass
class SkillChecklistItem:
    category: str
    title: str
    required: bool = True
    source: str = "skill"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkillTrace:
    execution_id: str
    sprint_name: str
    task_name: str
    scene: str
    matched_skills: List[str] = field(default_factory=list)
    injected_skills: List[str] = field(default_factory=list)
    review_checklist: List[SkillChecklistItem] = field(default_factory=list)
    review_status: str = "pending"
    review_score: float = 0.0
    retro_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["review_checklist"] = [item.to_dict() for item in self.review_checklist]
        return data


@dataclass
class SkillLifecycleSnapshot:
    skill_id: str
    scene: str
    version: str
    source: str
    status: str
    path: str = ""
    checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = ["ExecutionContext", "SkillChecklistItem", "SkillTrace", "SkillLifecycleSnapshot"]
