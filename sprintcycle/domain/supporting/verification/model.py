from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Protocol

VerificationSeverity = Literal["error", "warning", "info"]
VerificationAction = Literal["block", "warn", "info"]
VerificationGate = Literal["test", "verify", "arch", "security", "all"]


@dataclass
class VerificationRule:
    rule_id: str
    title: str
    gate: VerificationGate = "verify"
    severity: VerificationSeverity = "warning"
    action: VerificationAction = "warn"
    enabled: bool = True
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationFinding:
    rule_id: str
    severity: VerificationSeverity
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
class VerificationPolicy:
    name: str = "default"
    enabled: bool = True
    rules: list[VerificationRule] = field(default_factory=list)
    block_on_error: bool = True
    block_on_warning: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def enabled_rules_for_gate(self, gate: str) -> list[VerificationRule]:
        if gate == "all":
            return [r for r in self.rules if r.enabled]
        return [r for r in self.rules if r.enabled and (r.gate == gate or r.gate == "all")]


@dataclass
class VerificationReport:
    gate: VerificationGate
    findings: list[VerificationFinding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

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


class VerificationProvider(Protocol):
    name: str

    def run(self, project_root: str, context: Dict[str, Any]) -> List[VerificationFinding]: ...
