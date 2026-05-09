"""Optional helper interface functions for version inspection."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import VersionRegistry


async def get_version_manifest_summary(registry: VersionRegistry, version_id: str) -> Dict[str, Any]:
    artifact = await registry.get(version_id)
    if artifact is None:
        return {"success": False, "error": "version not found", "version_id": version_id}
    return {
        "success": True,
        "version_id": artifact.version_id,
        "target": artifact.target,
        "commit_hash": artifact.commit_hash,
        "tag": artifact.tag,
        "branch": artifact.branch,
        "manifest_path": artifact.manifest_path,
        "sandbox_id": artifact.sandbox_id,
        "metadata": artifact.metadata,
    }
