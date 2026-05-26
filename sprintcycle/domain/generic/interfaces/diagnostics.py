"""Diagnostics interfaces and types."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DiagnoseResult:
    """Diagnose result type."""

    success: bool = True
    error: Optional[str] = None
    duration: float = 0.0
    health_score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    coverage: float = 0.0
    complexity: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}
