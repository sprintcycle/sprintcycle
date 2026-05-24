from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class LifecycleReport:
    stage: str
    passed: bool
    findings: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "passed": self.passed,
            "findings": list(self.findings),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_report(cls, report: Any) -> "LifecycleReport":
        return cls(
            stage=getattr(report, "gate", ""),
            passed=bool(getattr(report, "passed", True)),
            findings=list(getattr(report, "findings", []) or []),
            metadata=dict(getattr(report, "metadata", {}) or {}),
        )

    def to_report(self) -> Any:
        from ..reports.report import Report

        return Report(
            gate=self.stage,
            passed=self.passed,
            findings=list(self.findings),
            metadata=dict(self.metadata),
        )
