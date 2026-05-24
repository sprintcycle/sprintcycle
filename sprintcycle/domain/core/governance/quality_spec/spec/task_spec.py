from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TaskSpec:
    id: str
    title: str
    type: str = "feature"
    spec_refs: List[str] = field(default_factory=list)
    acceptance_refs: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    verification_strategy: Dict[str, Any] = field(default_factory=dict)
    rollback_plan: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "medium"
    intent: str = ""
    summary: str = ""
    priority: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "spec_refs": list(self.spec_refs),
            "acceptance_refs": list(self.acceptance_refs),
            "constraints": dict(self.constraints),
            "verification_strategy": dict(self.verification_strategy),
            "rollback_plan": dict(self.rollback_plan),
            "risk_level": self.risk_level,
            "intent": self.intent,
            "summary": self.summary,
            "priority": self.priority,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskSpec":
        return cls(
            id=str(data.get("id", "")).strip(),
            title=str(data.get("title", "")).strip(),
            type=str(data.get("type", "feature")),
            spec_refs=list(data.get("spec_refs") or []),
            acceptance_refs=list(data.get("acceptance_refs") or []),
            constraints=dict(data.get("constraints") or {}),
            verification_strategy=dict(data.get("verification_strategy") or {}),
            rollback_plan=dict(data.get("rollback_plan") or {}),
            risk_level=str(data.get("risk_level", "medium")),
            intent=str(data.get("intent", "")),
            summary=str(data.get("summary", "")),
            priority=str(data.get("priority", "medium")),
            metadata=dict(data.get("metadata") or {}),
        )

    @classmethod
    def from_release_plan(cls, plan: Dict[str, Any]) -> "TaskSpec":
        return cls.from_dict(plan)

    def validate_minimal(self) -> None:
        if not self.id:
            raise ValueError("TaskSpec.id is required")
        if not self.title:
            raise ValueError("TaskSpec.title is required")
        if not self.type:
            raise ValueError("TaskSpec.type is required")
        if not self.spec_refs:
            raise ValueError("TaskSpec.spec_refs is required")
        if not self.acceptance_refs:
            raise ValueError("TaskSpec.acceptance_refs is required")
