"""HITL 存储抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from sprintcycle.domain.core.governance.hitl.types import HitlCorrection, HitlReplayDirective, HitlRequestRecord


class HitlStore(ABC):
    @abstractmethod
    async def insert_open(self, row: HitlRequestRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_decision(
        self,
        request_id: str,
        *,
        decision: str,
        note: Optional[str] = None,
        decision_kind: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get(self, request_id: str) -> Optional[HitlRequestRecord]:
        raise NotImplementedError

    @abstractmethod
    async def list_open(self, execution_id: Optional[str] = None) -> list[HitlRequestRecord]:
        raise NotImplementedError

    @abstractmethod
    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50) -> list[HitlRequestRecord]:
        raise NotImplementedError

    async def insert_correction(self, request_id: str, correction: HitlCorrection) -> None:
        return None

    async def insert_replay(self, request_id: str, replay: HitlReplayDirective) -> None:
        return None
