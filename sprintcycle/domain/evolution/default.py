"""Default evolution wiring.

This module provides a convenient factory for assembling the evolution control plane.

使用接口协议，由外层注入具体实现。
"""

from __future__ import annotations

from typing import Any

from sprintcycle.domain.interfaces import (
    VersionRegistryProtocol,
    RollbackManagerProtocol,
    ReleasePlanGeneratorProtocol,
    ReleasePlanValidatorProtocol,
    SandboxManagerProtocol,
)

from .controller import DefaultEvolutionController, EvolutionController
from .facade import EvolutionFacade
from .workflows import DefaultCodeEvolutionAdapter, DefaultRequirementEvolutionAdapter


class DefaultEvolutionService(EvolutionFacade):
    """Convenience facade that also exposes a rollback manager."""

    def __init__(
        self,
        controller: EvolutionController,
        rollback_manager: RollbackManagerProtocol,
    ) -> None:
        super().__init__(controller)
        self.rollback_manager = rollback_manager


def create_evolution_facade(
    *,
    project_path: str,
    version_registry: VersionRegistryProtocol,
    rollback_manager: RollbackManagerProtocol,
    release_plan_generator: ReleasePlanGeneratorProtocol,
    release_plan_validator: ReleasePlanValidatorProtocol,
    sandbox_manager: SandboxManagerProtocol,
) -> EvolutionFacade:
    """Create evolution facade with injected dependencies."""
    
    # Create workflow adapters
    code_adapter = DefaultCodeEvolutionAdapter()
    req_adapter = DefaultRequirementEvolutionAdapter()
    
    # Create controller with injected dependencies
    controller = DefaultEvolutionController(
        project_path=project_path,
        version_registry=version_registry,
        release_plan_generator=release_plan_generator,
        release_plan_validator=release_plan_validator,
        sandbox_manager=sandbox_manager,
        code_evolution_adapter=code_adapter,
        requirement_evolution_adapter=req_adapter,
    )
    
    # Create service with rollback manager
    service = DefaultEvolutionService(
        controller=controller,
        rollback_manager=rollback_manager,
    )
    
    return service


__all__ = [
    "DefaultEvolutionService",
    "create_evolution_facade",
    "EvolutionFacade",
    "EvolutionController",
]
