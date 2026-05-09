"""Versioning package.

Keeps version registry and rollback contracts isolated from execution logic.
"""

from .git_backend import GitVersionBackend
from .interface import get_version_manifest_summary
from .manifests import VersionManifest
from .registry import VersionRegistry, VersionRollbackManager
from .rollback import DefaultVersionRollbackManager
from .sqlite_registry import SQLiteVersionRegistry

__all__ = [
    "GitVersionBackend",
    "VersionManifest",
    "VersionRegistry",
    "VersionRollbackManager",
    "DefaultVersionRollbackManager",
    "SQLiteVersionRegistry",
    "get_version_manifest_summary",
]
