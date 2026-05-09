"""兼容导出：保留旧导入路径 ``sprintcycle.evolution.decision``。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class EvolutionDecisionType(str, Enum):
    REPLAN = "replan"
    CONTINUE = "continue"
    STOP = "stop"


@dataclass
class EvolutionDecision:
    decision_type: EvolutionDecisionType = EvolutionDecisionType.CONTINUE
    should_replan: bool = False
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_type": self.decision_type.value,
            "should_replan": self.should_replan,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }
