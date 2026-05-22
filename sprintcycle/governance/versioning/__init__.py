"""Versioning package.

Keeps version registry and rollback contracts isolated from execution logic.
SQLite implementation moved to infrastructure/persistence/.
"""

from .git_backend import GitVersionBackend
from .interface import get_version_manifest_summary
from .manifests import VersionManifest
from .registry import VersionRegistry, VersionRollbackManager
from .rollback import DefaultVersionRollbackManager

__all__ = [
    "GitVersionBackend",
    "VersionManifest",
    "VersionRegistry",
    "VersionRollbackManager",
    "DefaultVersionRollbackManager",
    "get_version_manifest_summary",
]
