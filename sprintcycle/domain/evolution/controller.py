"""Evolution controller contracts and default orchestration.

This module wires the evolution control plane together without touching
SprintCycle's main execution path.

使用接口协议，由外层注入具体实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from loguru import logger

from sprintcycle.domain.interfaces import (
    VersionRegistryProtocol,
    SandboxManagerProtocol,
    ReleasePlanGeneratorProtocol,
    ReleasePlanValidatorProtocol,
)

from sprintcycle.domain.evolution.manifest import VersionManifest
from .models import (
    EvolutionPlan,
    EvolutionRequest,
    PromotionResult,
    RollbackOutcome,
    SandboxSpec,
    ValidationResult,
    VersionArtifact,
)


class CodeEvolutionAdapter(ABC):
    @abstractmethod
    async def plan(self, request: EvolutionRequest) -> EvolutionPlan:
        """生成代码自进化计划。"""

    @abstractmethod
    async def apply(self, sandbox: SandboxSpec, plan: EvolutionPlan) -> None:
        """在沙盒中修改代码 / 配置 / 规则。"""

    @abstractmethod
    async def validate(self, sandbox: SandboxSpec, plan: EvolutionPlan) -> ValidationResult:
        """执行代码相关验证。"""


class RequirementEvolutionAdapter(ABC):
    @abstractmethod
    async def plan(self, request: EvolutionRequest) -> EvolutionPlan:
        """生成需求进化计划。"""

    @abstractmethod
    async def apply(self, sandbox: SandboxSpec, plan: EvolutionPlan) -> None:
        """在沙盒中修改 intent / plan / spec / backlog。"""

    @abstractmethod
    async def validate(self, sandbox: SandboxSpec, plan: EvolutionPlan) -> ValidationResult:
        """执行需求相关验证。"""


class EvolutionController(ABC):
    @abstractmethod
    async def intake(self, request: EvolutionRequest) -> EvolutionPlan:
        """接收输入并形成进化计划。"""

    @abstractmethod
    async def create_sandbox(self, plan: EvolutionPlan) -> SandboxSpec:
        """为候选版本创建沙盒。"""

    @abstractmethod
    async def apply(self, plan: EvolutionPlan, sandbox: SandboxSpec) -> None:
        """将计划应用到沙盒。"""

    @abstractmethod
    async def validate(self, plan: EvolutionPlan, sandbox: SandboxSpec) -> ValidationResult:
        """执行测试、治理与契约验证。"""

    @abstractmethod
    async def promote(self, plan: EvolutionPlan, sandbox: SandboxSpec, validation: ValidationResult) -> PromotionResult:
        """将通过验证的候选版本提升为可发布版本。"""

    @abstractmethod
    async def rollback(self, version_id: str) -> RollbackOutcome:
        """回滚到指定版本。"""


class DefaultEvolutionController(EvolutionController):
    """默认控制器：只负责编排，不编码具体演化策略。"""

    def __init__(
        self,
        *,
        project_path: str,
        code_adapter: CodeEvolutionAdapter,
        requirement_adapter: RequirementEvolutionAdapter,
        sandbox_manager: SandboxManagerProtocol,
        version_registry: VersionRegistryProtocol,
        release_plan_generator: Optional[ReleasePlanGeneratorProtocol] = None,
        release_plan_validator: Optional[ReleasePlanValidatorProtocol] = None,
    ) -> None:
        self._project_path = project_path
        self._code_adapter = code_adapter
        self._requirement_adapter = requirement_adapter
        self._sandbox_manager = sandbox_manager
        self._version_registry = version_registry
        self._release_plan_generator = release_plan_generator
        self._release_plan_validator = release_plan_validator

    async def intake(self, request: EvolutionRequest) -> EvolutionPlan:
        if request.target == "code":
            return await self._code_adapter.plan(request)
        return await self._requirement_adapter.plan(request)

    async def create_sandbox(self, plan: EvolutionPlan) -> SandboxSpec:
        sandbox_config = {"root_dir": self._project_path, "target": plan.target}
        sandbox_id = self._sandbox_manager.create_sandbox(sandbox_config)
        sandbox = SandboxSpec(
            sandbox_id=sandbox_id,
            root_dir=str(Path(self._project_path) / ".sprintcycle" / "sandbox" / sandbox_id),
        )
        return sandbox

    async def apply(self, plan: EvolutionPlan, sandbox: SandboxSpec) -> None:
        if plan.target == "code":
            await self._code_adapter.apply(sandbox, plan)
        else:
            await self._requirement_adapter.apply(sandbox, plan)

    async def validate(self, plan: EvolutionPlan, sandbox: SandboxSpec) -> ValidationResult:
        if plan.target == "code":
            return await self._code_adapter.validate(sandbox, plan)
        return await self._requirement_adapter.validate(sandbox, plan)

    async def promote(self, plan: EvolutionPlan, sandbox: SandboxSpec, validation: ValidationResult) -> PromotionResult:
        if not validation.success:
            return PromotionResult(
                success=False,
                message="validation failed",
                metadata={"validation": validation.to_dict()},
            )

        manifest = VersionManifest(
            version_id=f"{plan.target}:{plan.request_id}",
            target=plan.target,
            sandbox_id=sandbox.sandbox_id,
            metadata={
                "plan": plan.to_dict(),
                "validation": validation.to_dict(),
                "sandbox": sandbox.to_dict(),
            },
        )
        manifest_path = Path(sandbox.root_dir) / f"{manifest.version_id}.manifest.json"
        manifest.dump(str(manifest_path))

        artifact = VersionArtifact(
            version_id=manifest.version_id,
            target=plan.target,
            sandbox_id=sandbox.sandbox_id,
            manifest_path=str(manifest_path),
            metadata={
                "plan": plan.to_dict(),
                "validation": validation.to_dict(),
                "manifest": manifest.to_dict(),
            },
        )
        artifact = await self._version_registry.register(artifact)
        await self._version_registry.set_active(artifact.version_id)
        logger.info("Promoted version {} with manifest {}", artifact.version_id, manifest_path)
        return PromotionResult(success=True, artifact=artifact, message="promoted")

    async def rollback(self, version_id: str) -> RollbackOutcome:
        artifact: Optional[VersionArtifact] = await self._version_registry.get(version_id)
        if artifact is None:
            return RollbackOutcome(success=False, version_id=version_id, message="version not found")
        await self._version_registry.set_active(version_id)
        return RollbackOutcome(success=True, version_id=version_id, restored_to=version_id, message="rolled back")


__all__ = [
    "CodeEvolutionAdapter",
    "RequirementEvolutionAdapter",
    "EvolutionController",
    "DefaultEvolutionController",
]
