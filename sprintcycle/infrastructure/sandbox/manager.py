"""Sandbox manager interfaces.

Sandbox is responsible only for isolation and lifecycle management.
It must not contain domain business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ...application.evolution.models import EvolutionPlan, SandboxSpec


class SandboxManager(ABC):
    @abstractmethod
    async def create(self, plan: EvolutionPlan) -> SandboxSpec:
        """创建沙盒。"""

    @abstractmethod
    async def prepare(self, sandbox: SandboxSpec) -> None:
        """准备 worktree / 容器 / 依赖环境。"""

    @abstractmethod
    async def destroy(self, sandbox_id: str) -> None:
        """销毁沙盒。"""

    @abstractmethod
    async def exists(self, sandbox_id: str) -> bool:
        """检查沙盒是否存在。"""


class WorktreeSandboxBackend(ABC):
    @abstractmethod
    async def create_worktree(self, repo_path: str, sandbox_path: str, base_ref: str = "HEAD") -> Path:
        """创建 Git worktree。"""

    @abstractmethod
    async def remove_worktree(self, sandbox_path: str) -> None:
        """删除 worktree。"""

    @abstractmethod
    async def current_commit(self, repo_path: str) -> str:
        """返回当前 HEAD commit。"""

    @abstractmethod
    async def commit(self, repo_path: str, message: str) -> str:
        """在沙盒中提交变更并返回 commit hash。"""

    @abstractmethod
    async def tag(self, repo_path: str, tag_name: str, ref: str = "HEAD") -> str:
        """为候选版本打 tag。"""


class DockerSandboxBackend(ABC):
    @abstractmethod
    async def start(self, sandbox: SandboxSpec) -> str:
        """启动容器并返回 container id。"""

    @abstractmethod
    async def exec(self, sandbox_id: str, command: list[str], cwd: Optional[str] = None, env: Optional[dict[str, str]] = None, timeout_seconds: int = 300) -> int:
        """在容器中执行命令并返回退出码。"""

    @abstractmethod
    async def stop(self, sandbox_id: str) -> None:
        """停止容器。"""
