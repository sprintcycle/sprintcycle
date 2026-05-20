"""Default evolution wiring.

This module provides a convenient factory for assembling the evolution control plane.
"""

from __future__ import annotations

from typing import Any

from ...governance.versioning.rollback import DefaultVersionRollbackManager
from ...governance.versioning.sqlite_registry import SQLiteVersionRegistry
from ..release_plan.generator import IntentReleasePlanGenerator
from ..release_plan.validator import ReleasePlanValidator
from ..sandbox.default_manager import DefaultSandboxManager
from .controller import DefaultEvolutionController, EvolutionController
from .facade import EvolutionFacade
from .workflows import DefaultCodeEvolutionAdapter, DefaultRequirementEvolutionAdapter


class DefaultEvolutionService(EvolutionFacade):
    """Convenience facade that also exposes a rollback manager."""

    def __init__(self, controller: EvolutionController, rollback_manager: DefaultVersionRollbackManager) -> None:
        super().__init__(controller)
        self.rollback_manager = rollback_manager


def create_evolution_facade(
    *,
    project_path: str,
    config: Any,
) -> DefaultEvolutionService:
    registry = SQLiteVersionRegistry(
        root_dir=str(
            getattr(getattr(config, "evolution_versioning", None), "root_dir", None) or ".sprintcycle/versioning"
        )
    )
    governance_runner = None
    try:
        from ...governance.runner import GovernanceRunner

        governance_runner = GovernanceRunner(config)
    except Exception:
        governance_runner = None

    controller: EvolutionController = DefaultEvolutionController(
        code_adapter=DefaultCodeEvolutionAdapter(governance_runner=governance_runner),
        requirement_adapter=DefaultRequirementEvolutionAdapter(
            plan_validator=ReleasePlanValidator(),
            plan_generator=IntentReleasePlanGenerator,
        ),
        sandbox_manager=DefaultSandboxManager(project_path=project_path, config=config),
        version_registry=registry,
    )
    rollback_manager = DefaultVersionRollbackManager(registry=registry, repo_path=project_path)
    return DefaultEvolutionService(controller, rollback_manager)
