from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Rule:
    id: str
    name: str
    category: str
    severity: str = "error"
    enabled: bool = True
    thresholds: Dict[str, Any] = field(default_factory=dict)
    applies_to: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "severity": self.severity,
            "enabled": self.enabled,
            "thresholds": dict(self.thresholds),
            "applies_to": list(self.applies_to),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        return cls(
            id=str(data.get("id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            category=str(data.get("category", "")).strip(),
            severity=str(data.get("severity", "error")).strip(),
            enabled=bool(data.get("enabled", True)),
            thresholds=dict(data.get("thresholds") or {}),
            applies_to=list(data.get("applies_to") or []),
            metadata=dict(data.get("metadata") or {}),
        )

    def applies_to_gate(self, gate: str) -> bool:
        return not self.applies_to or gate in self.applies_to

    def validate_thresholds(self) -> None:
        if not isinstance(self.thresholds, dict):
            raise ValueError("thresholds must be a dict")
