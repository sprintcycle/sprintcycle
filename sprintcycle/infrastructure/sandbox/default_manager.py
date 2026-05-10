"""Default sandbox manager.

The default implementation uses git worktree for isolation.
It intentionally avoids heavy runtime dependencies.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from ..evolution.models import EvolutionPlan, SandboxSpec
from .manager import SandboxManager
from .worktree_backend import GitWorktreeSandboxBackend


class DefaultSandboxManager(SandboxManager):
    def __init__(self, project_path: str, config: Any) -> None:
        self._project_path = Path(project_path).expanduser().resolve()
        self._config = config
        self._backend = GitWorktreeSandboxBackend()
        self._sandboxes: Dict[str, SandboxSpec] = {}
        self._root_dir = Path(
            getattr(getattr(config, "evolution_sandbox", None), "root_dir", None) or ".sprintcycle/evolution"
        ).expanduser().resolve()
        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def create(self, plan: EvolutionPlan) -> SandboxSpec:
        async with self._lock:
            sandbox_id = f"{plan.target}-{plan.request_id}"
            sandbox_path = self._root_dir / sandbox_id
            return SandboxSpec(
                sandbox_id=sandbox_id,
                root_dir=str(self._root_dir),
                worktree_path=str(sandbox_path),
                backend="worktree",
                metadata={"request_id": plan.request_id, "target": plan.target},
            )

    async def prepare(self, sandbox: SandboxSpec) -> None:
        async with self._lock:
            if sandbox.sandbox_id in self._sandboxes:
                logger.info("Sandbox already exists: {}", sandbox.sandbox_id)
                return
            path = await self._backend.create_worktree(
                repo_path=str(self._project_path),
                sandbox_path=sandbox.worktree_path,
                base_ref="HEAD",
            )
            sandbox.worktree_path = str(path)
            self._sandboxes[sandbox.sandbox_id] = sandbox
            logger.info("Prepared sandbox {} at {}", sandbox.sandbox_id, sandbox.worktree_path)

    async def destroy(self, sandbox_id: str) -> None:
        async with self._lock:
            sandbox = self._sandboxes.pop(sandbox_id, None)
            if sandbox is None:
                return
            await self._backend.remove_worktree(sandbox.worktree_path)
            logger.info("Destroyed sandbox {}", sandbox_id)

    async def exists(self, sandbox_id: str) -> bool:
        async with self._lock:
            sandbox = self._sandboxes.get(sandbox_id)
            return sandbox is not None and Path(sandbox.worktree_path).exists()
