"""Checkpoint abstraction for LangGraph orchestration recovery."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Protocol


class CheckpointStore(Protocol):
    def load(self, key: str) -> Optional[Dict[str, Any]]: ...

    def save(self, key: str, state: Dict[str, Any]) -> None: ...


@dataclass
class LocalJsonCheckpointStore:
    checkpoint_dir: str = ".sprintcycle/checkpoints"

    def _path_for(self, key: str) -> Path:
        return Path(self.checkpoint_dir) / f"{key}.json"

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._path_for(key)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, key: str, state: Dict[str, Any]) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)


__all__ = ["CheckpointStore", "LocalJsonCheckpointStore"]
