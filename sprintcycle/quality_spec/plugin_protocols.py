from __future__ import annotations

from typing import Protocol, runtime_checkable, Any


@runtime_checkable
class QualityPlugin(Protocol):
    name: str

    def register(self, registry: Any) -> None:
        ...
