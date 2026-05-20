from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class QualityPlugin(Protocol):
    name: str

    def register(self, registry: Any) -> None: ...
