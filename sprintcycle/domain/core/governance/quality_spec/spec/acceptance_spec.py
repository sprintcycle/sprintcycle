from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AcceptanceSpec:
    id: str
    description: str
    type: str
    required: bool = True
    evidence: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "required": self.required,
            "evidence": dict(self.evidence),
            "thresholds": dict(self.thresholds),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AcceptanceSpec":
        return cls(
            id=str(data.get("id", "")).strip(),
            description=str(data.get("description", "")).strip(),
            type=str(data.get("type", "")).strip(),
            required=bool(data.get("required", True)),
            evidence=dict(data.get("evidence") or {}),
            thresholds=dict(data.get("thresholds") or {}),
            metadata=dict(data.get("metadata") or {}),
        )

    def validate_minimal(self) -> None:
        if not self.id:
            raise ValueError("AcceptanceSpec.id is required")
        if not self.description:
            raise ValueError("AcceptanceSpec.description is required")
        if not self.type:
            raise ValueError("AcceptanceSpec.type is required")
