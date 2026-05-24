"""编码引擎注册表与抽象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class EngineMetadata:
    name: str
    display_name: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    supports_execute: bool = True
    supports_review: bool = False
    supports_preview: bool = False
    capabilities: tuple[str, ...] = field(default_factory=tuple)


class CodingEngine:
    """编码引擎统一接口。"""

    def __init__(self, metadata: EngineMetadata):
        self.metadata = metadata

    async def execute(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class EngineRegistry:
    def __init__(self) -> None:
        self._engines: Dict[str, Callable[[], CodingEngine]] = {}
        self._aliases: Dict[str, str] = {}

    def register(
        self, name: str, factory: Callable[[], CodingEngine], aliases: Optional[tuple[str, ...]] = None
    ) -> None:
        self._engines[name] = factory
        for alias in aliases or ():
            self._aliases[alias] = name

    def resolve_name(self, name: str) -> str:
        return self._aliases.get(name, name)

    def get(self, name: str) -> CodingEngine:
        resolved = self.resolve_name(name)
        if resolved not in self._engines:
            raise KeyError(f"Unknown coding engine: {name}")
        return self._engines[resolved]()

    def list_names(self) -> list[str]:
        return sorted(self._engines.keys())


__all__ = ["EngineMetadata", "CodingEngine", "EngineRegistry"]
