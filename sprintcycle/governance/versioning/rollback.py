"""Version-level rollback helpers.

This bridges the version registry with actual git-backed restore steps.
"""

from __future__ import annotations

from loguru import logger

from ...domain.evolution.models import EvolutionTarget, RollbackOutcome
from .git_backend import GitVersionBackend
from .registry import VersionRegistry, VersionRollbackManager


class DefaultVersionRollbackManager(VersionRollbackManager):
    def __init__(self, registry: VersionRegistry, repo_path: str) -> None:
        self._registry = registry
        self._git = GitVersionBackend(repo_path)

    async def rollback_to_version(self, version_id: str) -> RollbackOutcome:
        artifact = await self._registry.get(version_id)
        if artifact is None:
            return RollbackOutcome(success=False, version_id=version_id, message="version not found")

        ref = artifact.tag or artifact.commit_hash or version_id
        try:
            self._git.checkout(ref)
            await self._registry.set_active(version_id)
            logger.info("Rolled back to version {} via ref {}", version_id, ref)
            return RollbackOutcome(
                success=True,
                version_id=version_id,
                restored_to=ref,
                message="rolled back",
                metadata={"commit_hash": artifact.commit_hash, "tag": artifact.tag, "branch": artifact.branch},
            )
        except Exception as e:
            return RollbackOutcome(success=False, version_id=version_id, message=f"rollback failed: {e}")

    async def rollback_to_previous(self, target: EvolutionTarget) -> RollbackOutcome:
        versions = await self._registry.list_versions(target=target, limit=2)
        if len(versions) < 2:
            return RollbackOutcome(success=False, message="no previous version")
        previous = versions[1]
        return await self.rollback_to_version(previous.version_id)
