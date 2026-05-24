"""
Evolution Facade 工厂函数 - 为 domain 层提供默认实现

遵循洋葱架构原则，在此处组装依赖并注入到 domain 层。
"""

from __future__ import annotations

from typing import Optional

from sprintcycle.domain.evolution.default import create_evolution_facade
from sprintcycle.domain.evolution.facade import EvolutionFacade
from sprintcycle.domain.interfaces import (
    VersionRegistryProtocol,
    RollbackManagerProtocol,
    ReleasePlanGeneratorProtocol,
    ReleasePlanValidatorProtocol,
    SandboxManagerProtocol,
)


def create_default_evolution_facade(
    project_path: str,
    *,
    version_registry: Optional[VersionRegistryProtocol] = None,
    rollback_manager: Optional[RollbackManagerProtocol] = None,
    release_plan_generator: Optional[ReleasePlanGeneratorProtocol] = None,
    release_plan_validator: Optional[ReleasePlanValidatorProtocol] = None,
    sandbox_manager: Optional[SandboxManagerProtocol] = None,
) -> EvolutionFacade:
    """
    创建默认配置的 EvolutionFacade。

    新代码建议直接使用 create_evolution_facade 并显式注入所有依赖项。
    
    Args:
        project_path: 项目路径
        version_registry: 可选的版本注册表实现
        rollback_manager: 可选的回滚管理器实现
        release_plan_generator: 可选的发布计划生成器实现
        release_plan_validator: 可选的发布计划验证器实现
        sandbox_manager: 可选的沙箱管理器实现
    
    Returns:
        配置好的 EvolutionFacade 实例
    """
    # 延迟导入，避免循环依赖
    if version_registry is None:
        from sprintcycle.infrastructure.persistence import SQLiteVersionRegistry
        version_registry = SQLiteVersionRegistry(
            root_dir=f"{project_path}/.sprintcycle/versioning"
        )

    if rollback_manager is None:
        from sprintcycle.governance.versioning.rollback import DefaultVersionRollbackManager
        rollback_manager = DefaultVersionRollbackManager()

    if release_plan_generator is None:
        from sprintcycle.execution.planners.generator import IntentReleasePlanGenerator
        release_plan_generator = IntentReleasePlanGenerator()

    if release_plan_validator is None:
        from sprintcycle.domain.quality_spec.plan import ReleasePlanValidator
        release_plan_validator = ReleasePlanValidator()

    if sandbox_manager is None:
        from sprintcycle.infrastructure.sandbox.default_manager import DefaultSandboxManager
        sandbox_manager = DefaultSandboxManager()

    return create_evolution_facade(
        project_path=project_path,
        version_registry=version_registry,
        rollback_manager=rollback_manager,
        release_plan_generator=release_plan_generator,
        release_plan_validator=release_plan_validator,
        sandbox_manager=sandbox_manager,
    )


__all__ = ["create_default_evolution_facade"]
