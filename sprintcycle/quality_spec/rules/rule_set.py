from dataclasses import dataclass, field
from typing import Any, Dict, List

from .rule import Rule


@dataclass
class RuleSet:
    name: str
    rules: List[Rule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def extend_rules(self, rules: List[Rule]) -> None:
        self.rules.extend(rules)

    def filter_enabled(self) -> "RuleSet":
        return RuleSet(
            name=self.name,
            rules=[r for r in self.rules if r.enabled],
            metadata=dict(self.metadata),
        )

    def for_gate(self, gate: str) -> "RuleSet":
        return RuleSet(
            name=f"{self.name}:{gate}",
            rules=[r for r in self.rules if r.applies_to_gate(gate)],
            metadata=dict(self.metadata),
        )
