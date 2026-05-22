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


# =============================================================================
# 向后兼容警告：以下函数已弃用，将在后续版本移除
# 请使用 create_evolution_facade 并通过依赖注入传递 Infrastructure 实现
# =============================================================================
def _create_default_evolution_facade_internal(project_path: str) -> EvolutionFacade:
    """
    [内部] Create evolution facade with default implementations.
    
    此函数仅用于快速原型和向后兼容。
    正式代码应使用 create_evolution_facade 并显式注入依赖。
    """
    from sprintcycle.infrastructure.persistence import SQLiteVersionRegistry
    from sprintcycle.governance.versioning.rollback import DefaultVersionRollbackManager
    from sprintcycle.execution.planners.generator import IntentReleasePlanGenerator
    from sprintcycle.domain.quality_spec.validator_protocol import ReleasePlanValidator
    from sprintcycle.infrastructure.sandbox.default_manager import DefaultSandboxManager
    
    return create_evolution_facade(
        project_path=project_path,
        version_registry=SQLiteVersionRegistry(root_dir=f"{project_path}/.sprintcycle/versioning"),
        rollback_manager=DefaultVersionRollbackManager(),
        release_plan_generator=IntentReleasePlanGenerator(),
        release_plan_validator=ReleasePlanValidator(),
        sandbox_manager=DefaultSandboxManager(),
    )


def create_default_evolution_facade(project_path: str) -> EvolutionFacade:
    """
    [已弃用] 请使用 create_evolution_facade。
    
    DEPRECATED: 此函数仅用于快速原型。
    """
    import warnings
    warnings.warn(
        "create_default_evolution_facade is deprecated. "
        "Use create_evolution_facade with explicit dependency injection.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _create_default_evolution_facade_internal(project_path)
