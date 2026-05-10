"""Sandbox isolation package.

This package is intentionally small: it only provides contracts and backend wiring
for isolated candidate execution.
"""

from .manager import DockerSandboxBackend, SandboxManager, WorktreeSandboxBackend

__all__ = ["SandboxManager", "WorktreeSandboxBackend", "DockerSandboxBackend"]
