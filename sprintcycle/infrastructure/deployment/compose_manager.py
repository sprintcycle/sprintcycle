"""Minimal docker compose helper for phase 1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class ComposeManager:
    project_path: str

    def compose_path(self) -> Path:
        return Path(self.project_path).resolve() / "docker-compose.yml"

    def to_payload(self) -> Dict[str, Any]:
        return {
            "success": True,
            "compose_path": str(self.compose_path()),
            "exists": self.compose_path().is_file(),
        }
