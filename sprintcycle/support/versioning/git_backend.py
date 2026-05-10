"""Git-backed helpers for versioning.

These helpers intentionally stay small and focused.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple


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


class GitVersionBackend:
    def __init__(self, repo_path: str) -> None:
        self._repo_path = str(Path(repo_path).expanduser().resolve())

    def current_commit(self) -> str:
        rc, stdout, _ = _run_git(["rev-parse", "HEAD"], cwd=self._repo_path)
        return stdout.strip() if rc == 0 else ""

    def tag(self, tag_name: str, ref: str = "HEAD") -> str:
        rc, _, stderr = _run_git(["tag", "-f", tag_name, ref], cwd=self._repo_path)
        if rc != 0:
            raise RuntimeError(f"git tag failed: {stderr}")
        return tag_name

    def checkout(self, ref: str) -> str:
        rc, _, stderr = _run_git(["checkout", ref], cwd=self._repo_path)
        if rc != 0:
            raise RuntimeError(f"git checkout failed: {stderr}")
        return ref

    def branch(self, branch_name: str, ref: str = "HEAD") -> str:
        rc, _, stderr = _run_git(["branch", branch_name, ref], cwd=self._repo_path)
        if rc != 0:
            raise RuntimeError(f"git branch failed: {stderr}")
        return branch_name
