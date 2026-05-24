"""Version registry interfaces and minimal persistence contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from sprintcycle.domain.core.evolution.models import EvolutionTarget, RollbackOutcome, VersionArtifact


class VersionRegistry(ABC):
    @abstractmethod
    async def register(self, artifact: VersionArtifact) -> VersionArtifact:
        """注册候选版本。"""

    @abstractmethod
    async def set_active(self, version_id: str) -> None:
        """切换 active 指针。"""

    @abstractmethod
    async def get_active(self, target: EvolutionTarget) -> Optional[VersionArtifact]:
        """获取当前 active 版本。"""

    @abstractmethod
    async def get(self, version_id: str) -> Optional[VersionArtifact]:
        """按 version_id 查询版本。"""

    @abstractmethod
    async def list_versions(self, target: Optional[EvolutionTarget] = None, limit: int = 20) -> list[VersionArtifact]:
        """列出版本历史。"""


class VersionRollbackManager(ABC):
    @abstractmethod
    async def rollback_to_version(self, version_id: str) -> RollbackOutcome:
        """回滚到指定版本。"""

    @abstractmethod
    async def rollback_to_previous(self, target: EvolutionTarget) -> RollbackOutcome:
        """回滚到上一个稳定版本。"""
