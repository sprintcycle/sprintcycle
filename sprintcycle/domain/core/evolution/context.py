"""兼容导出：保留旧导入路径 ``sprintcycle.domain.evolution.context``。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvolutionContext:
    decision: Optional[Any] = None
    historical_goals: List[str] = field(default_factory=list)
    historical_constraints: List[str] = field(default_factory=list)
    target: Any = None
    strategy_profile: str = ""
    risk_level: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionContext":
        return cls(
            decision=data.get("decision"),
            historical_goals=list(data.get("historical_goals") or []),
            historical_constraints=list(data.get("historical_constraints") or []),
            target=data.get("target"),
            strategy_profile=str(data.get("strategy_profile", "")),
            risk_level=str(data.get("risk_level", "medium")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.to_dict() if hasattr(self.decision, "to_dict") else self.decision,
            "historical_goals": list(self.historical_goals),
            "historical_constraints": list(self.historical_constraints),
            "target": self.target,
            "strategy_profile": self.strategy_profile,
            "risk_level": self.risk_level,
            "metadata": dict(self.metadata),
        }
