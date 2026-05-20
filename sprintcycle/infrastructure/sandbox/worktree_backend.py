"""Git worktree sandbox backend.

This backend is intentionally minimal and uses the git CLI.
It is suitable as the default isolation backend for SprintCycle evolution.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from .manager import WorktreeSandboxBackend


def _run_git(args: List[str], cwd: str = ".", timeout: int = 120) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "git command timed out"
    except Exception as e:
        return -1, "", str(e)


class GitWorktreeSandboxBackend(WorktreeSandboxBackend):
    async def create_worktree(self, repo_path: str, sandbox_path: str, base_ref: str = "HEAD") -> Path:
        path = Path(sandbox_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rc, _, stderr = _run_git(["worktree", "add", "--force", str(path), base_ref], cwd=repo_path)
        if rc != 0:
            raise RuntimeError(f"failed to create worktree: {stderr}")
        return path

    async def remove_worktree(self, sandbox_path: str) -> None:
        path = Path(sandbox_path)
        if not path.exists():
            return
        root = str(path.parent.parent) if path.parent.parent.exists() else str(path.parent)
        _run_git(["worktree", "remove", "--force", str(path)], cwd=root)
        if path.exists():
            # 最后兜底清理，避免残留目录影响后续候选版本。
            import shutil

            shutil.rmtree(path, ignore_errors=True)

    async def current_commit(self, repo_path: str) -> str:
        rc, stdout, _ = _run_git(["rev-parse", "HEAD"], cwd=repo_path)
        return stdout.strip() if rc == 0 else ""

    async def commit(self, repo_path: str, message: str) -> str:
        rc, _, stderr = _run_git(["add", "-A"], cwd=repo_path)
        if rc != 0:
            raise RuntimeError(f"git add failed: {stderr}")
        rc, _, stderr = _run_git(["commit", "-m", message], cwd=repo_path)
        if rc != 0:
            raise RuntimeError(f"git commit failed: {stderr}")
        return await self.current_commit(repo_path)

    async def tag(self, repo_path: str, tag_name: str, ref: str = "HEAD") -> str:
        rc, _, stderr = _run_git(["tag", "-f", tag_name, ref], cwd=repo_path)
        if rc != 0:
            raise RuntimeError(f"git tag failed: {stderr}")
        return tag_name
