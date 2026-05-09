from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ConstraintSpec:
    architecture: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    compatibility: Dict[str, Any] = field(default_factory=dict)
    performance: Dict[str, Any] = field(default_factory=dict)
    quality: Dict[str, Any] = field(default_factory=dict)
    domain: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture": dict(self.architecture),
            "security": dict(self.security),
            "compatibility": dict(self.compatibility),
            "performance": dict(self.performance),
            "quality": dict(self.quality),
            "domain": dict(self.domain),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstraintSpec":
        return cls(
            architecture=dict(data.get("architecture") or {}),
            security=dict(data.get("security") or {}),
            compatibility=dict(data.get("compatibility") or {}),
            performance=dict(data.get("performance") or {}),
            quality=dict(data.get("quality") or {}),
            domain=dict(data.get("domain") or {}),
            metadata=dict(data.get("metadata") or {}),
        )

    def has_architecture_constraints(self) -> bool:
        return bool(self.architecture)

    def has_security_constraints(self) -> bool:
        return bool(self.security)
