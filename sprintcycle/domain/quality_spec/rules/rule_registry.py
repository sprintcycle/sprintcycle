from typing import Dict, List, Optional

from .rule import Rule


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: Dict[str, Rule] = {}

    def register(self, rule: Rule) -> None:
        self._rules[rule.id] = rule

    def register_many(self, rules: List[Rule]) -> None:
        for rule in rules:
            self.register(rule)

    def get(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def list(self) -> List[Rule]:
        return list(self._rules.values())

    def for_gate(self, gate: str) -> List[Rule]:
        return [rule for rule in self._rules.values() if rule.applies_to_gate(gate)]

    def clear(self) -> None:
        self._rules.clear()
