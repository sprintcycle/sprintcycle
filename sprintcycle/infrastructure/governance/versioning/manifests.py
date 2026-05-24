"""Version manifest helpers.

向后兼容：从 Domain 层导入并 re-export。
"""

from sprintcycle.domain.core.evolution.manifest import VersionManifest

__all__ = ["VersionManifest"]
