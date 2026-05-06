"""治理报告与违规项数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

Severity = Literal["error", "warning", "info"]


@dataclass
class GovernanceViolation:
    rule_id: str
    severity: Severity
    message: str
    location: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "location": dict(self.location),
        }


@dataclass
class GovernanceReport:
    """单次 Gate 执行结果，可序列化为 JSON。"""

    gate: str
    violations: List[GovernanceViolation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "violations": [v.to_dict() for v in self.violations],
            "metadata": dict(self.metadata),
        }

    def has_error_severity(self) -> bool:
        return any(v.severity == "error" for v in self.violations)

    def should_block_ci(self, block_on: str) -> bool:
        """
        是否应按 ``governance_block_on`` 视为 CI 失败（用于 CLI 退出码）。

        - ``none``: 永不因治理失败退出
        - ``review_only`` / ``planning_and_review``: 存在 severity=error 的违规时为 True
        """
        b = (block_on or "none").strip().lower()
        if b == "none":
            return False
        if b in ("review_only", "planning_and_review"):
            return self.has_error_severity()
        return False
