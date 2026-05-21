from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

GuardSeverity = Literal["error", "warning", "info"]
GuardAction = Literal["block", "warn", "info"]
GuardGate = Literal["planning", "review", "ci", "local"]


@dataclass
class GuardRule:
    rule_id: str
    title: str
    severity: GuardSeverity = "warning"
    action: GuardAction = "warn"
    gate: str = "review"
    description: str = ""
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GuardFinding:
    rule_id: str
    severity: GuardSeverity
    message: str
    location: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "location": dict(self.location),
            "metadata": dict(self.metadata),
        }


@dataclass
class GuardPolicy:
    name: str = "default"
    enabled: bool = True
    rules: List[GuardRule] = field(default_factory=list)
    block_on_error: bool = True
    block_on_warning: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def enabled_rules_for_gate(self, gate: str) -> List[GuardRule]:
        return [r for r in self.rules if r.enabled and r.gate == gate]


class GuardReport:
    gate: str
    findings: List[GuardFinding]
    metadata: Dict[str, Any]

    def __init__(
        self,
        gate: str = "",
        findings: Optional[List[GuardFinding]] = None,
        violations: Optional[List[GuardFinding]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.gate = gate
        self.findings = list(violations or findings or [])
        self.metadata = dict(metadata or {})

    @property
    def violations(self) -> List[GuardFinding]:
        return self.findings

    @violations.setter
    def violations(self, value: List[GuardFinding]) -> None:
        self.findings = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "findings": [f.to_dict() for f in self.findings],
            "metadata": dict(self.metadata),
        }

    def has_error(self) -> bool:
        return any(f.severity == "error" for f in self.findings)

    def has_warning(self) -> bool:
        return any(f.severity == "warning" for f in self.findings)

    def has_error_severity(self) -> bool:
        return self.has_error()

    def should_block_ci(self, mode: str = "on_error") -> bool:
        if mode == "none":
            return False
        if mode == "always":
            return True
        return self.has_error()
