from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class VerificationStrategySpec:
    static: bool = True
    contract: bool = False
    property: bool = False
    integration: bool = False
    acceptance: bool = False
    security: bool = False
    architecture: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "static": self.static,
            "contract": self.contract,
            "property": self.property,
            "integration": self.integration,
            "acceptance": self.acceptance,
            "security": self.security,
            "architecture": self.architecture,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationStrategySpec":
        return cls(
            static=bool(data.get("static", True)),
            contract=bool(data.get("contract", False)),
            property=bool(data.get("property", False)),
            integration=bool(data.get("integration", False)),
            acceptance=bool(data.get("acceptance", False)),
            security=bool(data.get("security", False)),
            architecture=bool(data.get("architecture", True)),
            metadata=dict(data.get("metadata") or {}),
        )

    @classmethod
    def default_for_task_type(cls, task_type: str) -> "VerificationStrategySpec":
        task_type = (task_type or "").lower()
        if task_type in {"bugfix", "refactor"}:
            return cls(static=True, contract=True, property=False, integration=False, acceptance=True, architecture=True)
        if task_type in {"feature"}:
            return cls(static=True, contract=True, property=True, integration=True, acceptance=True, architecture=True)
        return cls()
