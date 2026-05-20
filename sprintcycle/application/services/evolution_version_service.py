"""Evolution version query and overview service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
from sprintcycle.infrastructure.evolution_registry_access import (
    create_evolution_registry,
    evolution_sandbox_status,
)
from sprintcycle.results import (
    EvolutionIndexResult,
    EvolutionOverviewResult,
    EvolutionVersionListResult,
    EvolutionVersionSummary,
    FinalSnapshotVersionSummary,
)


@dataclass
class EvolutionVersionService:
    config: RuntimeConfig
    registry: Any = None

    def __post_init__(self) -> None:
        if self.registry is None:
            self.registry = create_evolution_registry(self.config)

    async def get_version(self, version_id: str) -> EvolutionVersionSummary:
        from sprintcycle.governance.versioning.interface import get_version_manifest_summary

        payload = await get_version_manifest_summary(self.registry, version_id)
        return EvolutionVersionSummary(
            success=bool(payload.get("success")),
            error=payload.get("error"),
            version_id=payload.get("version_id", ""),
            target=payload.get("target", ""),
            commit_hash=payload.get("commit_hash", ""),
            tag=payload.get("tag", ""),
            branch=payload.get("branch", ""),
            manifest_path=payload.get("manifest_path", ""),
            sandbox_id=payload.get("sandbox_id", ""),
            metadata=dict(payload.get("metadata", {}) or {}),
        )

    async def list_versions(self, target: Optional[str] = None, limit: int = 20) -> EvolutionVersionListResult:
        versions = await self.registry.list_versions(target=target, limit=limit)
        return EvolutionVersionListResult(
            success=True,
            target=target or "",
            versions=[
                EvolutionVersionSummary(
                    success=True,
                    version_id=v.version_id,
                    target=v.target,
                    commit_hash=v.commit_hash or "",
                    tag=v.tag or "",
                    branch=v.branch or "",
                    manifest_path=v.manifest_path or "",
                    sandbox_id=v.sandbox_id or "",
                    metadata=dict(v.metadata or {}),
                )
                for v in versions
            ],
            total=len(versions),
        )

    async def export_index(self) -> EvolutionIndexResult:
        index = await self.registry.export_manifest_index()
        return EvolutionIndexResult(success=True, index=index)

    async def overview(self) -> EvolutionOverviewResult:
        active_versions: Dict[str, Dict[str, Any]] = {}
        for target in ("code", "requirement"):
            active = await self.registry.get_active(target)
            if active is not None:
                active_versions[target] = active.to_dict()

        recent = await self.registry.list_versions(limit=5)
        index = await self.registry.export_manifest_index()
        totals = {
            "versions": len(recent),
            "code_active": 1 if "code" in active_versions else 0,
            "requirement_active": 1 if "requirement" in active_versions else 0,
        }
        final_snapshot_versions = [
            FinalSnapshotVersionSummary(
                target=target,
                version_id=artifact.get("version_id", ""),
                final_snapshot=artifact.get("metadata", {}).get("final_snapshot", {}),
                promotion_guard=artifact.get("promotion_guard", {}),
            )
            for target, artifact in active_versions.items()
        ]
        result = EvolutionOverviewResult(
            success=True,
            active_versions=active_versions,
            recent_candidates=[
                EvolutionVersionSummary(
                    success=True,
                    version_id=v.version_id,
                    target=v.target,
                    commit_hash=v.commit_hash or "",
                    tag=v.tag or "",
                    branch=v.branch or "",
                    manifest_path=v.manifest_path or "",
                    sandbox_id=v.sandbox_id or "",
                    metadata=dict(v.metadata or {}),
                )
                for v in recent
            ],
            index=index,
            totals=totals,
            sandbox_status=evolution_sandbox_status(self.config),
        )
        result.final_snapshot_versions = final_snapshot_versions
        return result


__all__ = ["EvolutionVersionService"]
