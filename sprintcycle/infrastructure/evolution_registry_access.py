"""Evolution version registry access boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig

if TYPE_CHECKING:
    pass


def create_evolution_registry(config: RuntimeConfig) -> Any:
    from sprintcycle.infrastructure.persistence import SQLiteVersionRegistry

    root_dir = str(
        getattr(getattr(config, "evolution_versioning", None), "root_dir", None) or ".sprintcycle/versioning"
    )
    return SQLiteVersionRegistry(root_dir=root_dir)


def evolution_sandbox_status(config: RuntimeConfig) -> dict[str, Any]:
    try:
        sandbox = getattr(config, "evolution_sandbox", None)
        return {
            "available": True,
            "backend": getattr(sandbox, "backend", "worktree"),
            "root_dir": getattr(sandbox, "root_dir", ".sprintcycle/evolution"),
        }
    except Exception:
        return {"available": False}


__all__ = ["create_evolution_registry", "evolution_sandbox_status"]
