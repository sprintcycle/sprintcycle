from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .model import GuardFinding, GuardRule


@dataclass
class GuardCheckContext:
    gate: str
    project_root: str
    context: Dict[str, Any] = field(default_factory=dict)


class GuardRegistry:
    def __init__(self) -> None:
        self._rules: Dict[str, GuardRule] = {}
        self._checks: Dict[str, Callable[[GuardCheckContext], List[GuardFinding]]] = {}

    def register_rule(self, rule: GuardRule) -> None:
        self._rules[rule.rule_id] = rule

    def register_check(self, rule_id: str, check: Callable[[GuardCheckContext], List[GuardFinding]]) -> None:
        self._checks[rule_id] = check

    def enabled_rules_for_gate(self, gate: str) -> List[GuardRule]:
        return [r for r in self._rules.values() if r.enabled and r.gate == gate]

    def run_gate(self, gate: str, project_root: str, context: Optional[Dict[str, Any]] = None) -> List[GuardFinding]:
        findings: List[GuardFinding] = []
        ctx = GuardCheckContext(gate=gate, project_root=project_root, context=context or {})
        for rule in self.enabled_rules_for_gate(gate):
            check = self._checks.get(rule.rule_id)
            if check is None:
                continue
            try:
                findings.extend(check(ctx))
            except Exception as e:
                findings.append(
                    GuardFinding(
                        rule_id=f"{rule.rule_id}:error",
                        severity="warning",
                        message=str(e),
                        location={"rule_id": rule.rule_id, "gate": gate},
                    )
                )
        return findings
