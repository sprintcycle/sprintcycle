"""Version manifest helpers.

A manifest is the portable, auditable record of a promoted candidate.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(slots=True)
class VersionManifest:
    version_id: str
    target: str
    commit_hash: Optional[str] = None
    tag: Optional[str] = None
    branch: Optional[str] = None
    sandbox_id: Optional[str] = None
    manifest_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def dump(self, path: str) -> str:
        out = Path(path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.manifest_path = str(out)
        return str(out)

    @classmethod
    def load(cls, path: str) -> "VersionManifest":
        data = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
        return cls(**data)
