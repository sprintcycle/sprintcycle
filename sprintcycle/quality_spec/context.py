from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def normalize_changed_files(files: List[str]) -> List[str]:
    return sorted({f.strip() for f in files if f and f.strip()})


@dataclass
class QualityContext:
    project_path: str
    gate: str
    task_id: Optional[str] = None
    sprint_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    changed_files: List[str] = field(default_factory=list)
    spec: Any = None
    acceptance: List[Any] = field(default_factory=list)
    constraints: Any = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.changed_files = normalize_changed_files(self.changed_files)


def build_quality_context(**kwargs: Any) -> QualityContext:
    return QualityContext(**kwargs)
