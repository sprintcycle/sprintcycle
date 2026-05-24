from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    """A single memory entry stored by MemoryStore."""

    memory_type: str
    content: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    success: bool = True
    score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    memory_id: str = ""


@dataclass
class StoreResult:
    """Result returned by MemoryStore.store()."""

    success: bool
    memory_id: str
    entry: Optional[MemoryEntry] = None
    error: str = ""


class MemoryStore:
    """In-memory store for evolution-related memories.

    Used by UserIntentEvolutionLoop to persist learning events.
    """

    def __init__(self, runtime_config: Optional[Any] = None) -> None:
        self._runtime_config = runtime_config
        self._entries: List[MemoryEntry] = []
        self._counter: int = 0

    def store(
        self,
        memory_type: str,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None,
        success: bool = True,
        score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StoreResult:
        self._counter += 1
        entry = MemoryEntry(
            memory_type=memory_type,
            content=dict(content or {}),
            tags=list(tags or []),
            success=success,
            score=float(score),
            metadata=dict(metadata or {}),
            memory_id=f"mem-{self._counter}",
        )
        self._entries.append(entry)
        return StoreResult(success=True, memory_id=entry.memory_id, entry=entry)

    def list_entries(self, memory_type: Optional[str] = None, limit: int = 100) -> List[MemoryEntry]:
        entries = self._entries
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        return entries[-limit:]

    def clear(self) -> None:
        self._entries.clear()
        self._counter = 0
