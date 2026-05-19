"""Release finalization 组件。

用于在所有 Sprint 执行完毕后，对 Release 做最终测试、最终评估、必要修正与交付判定。
该层不是独立迭代主循环，而是由 SprintOrchestrator 在主执行完成后触发。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger

from ..sprint_types import ExecutionStatus, SprintResult
from ...application.release_plan.models import ReleasePlan, SprintBacklogItem, SprintDefinition


@dataclass
class ReleaseFinalizationResult:
    success: bool
    ready_to_release: bool = False
    summary: str = ""
    issues: List[str] = field(default_factory=list)
    fix_tasks: List[SprintBacklogItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sprint_results: List[Dict[str, Any]] = field(default_factory=list)
    executed_fix_sprints: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "ready_to_release": self.ready_to_release,
            "summary": self.summary,
            "issues": list(self.issues),
            "fix_tasks": [
                {
                    "description": t.description,
                    "agent": t.agent,
                    "target": t.target,
                }
                for t in self.fix_tasks
            ],
            "metadata": dict(self.metadata),
            "sprint_results": list(self.sprint_results),
            "executed_fix_sprints": list(self.executed_fix_sprints),
        }


class ReleaseFinalizationPolicy:
    """Release 收尾策略：决定是否需要最终测试 / 评估 / 修正。"""

    def should_finalize(self, release_plan: ReleasePlan, sprint_results: List[SprintResult]) -> bool:
        return bool(sprint_results)

    def should_retest(self, result: ReleaseFinalizationResult) -> bool:
        return not result.ready_to_release

    def build_fix_sprint(self, release_plan: ReleasePlan, result: ReleaseFinalizationResult) -> Optional[SprintDefinition]:
        if not result.fix_tasks:
            return None
        return SprintDefinition(
            name=f"{release_plan.project.name}-finalization-fix",
            goals=["Release finalization fixes"],
            tasks=list(result.fix_tasks),
        )


class ReleaseFinalizationHooks(ABC):
    @abstractmethod
    async def on_before_finalize(
        self,
        release_plan: ReleasePlan,
        sprint_results: List[SprintResult],
        context: Dict[str, Any],
    ) -> None:
        ...

    @abstractmethod
    async def on_after_finalize(
        self,
        release_plan: ReleasePlan,
        sprint_results: List[SprintResult],
        result: ReleaseFinalizationResult,
        context: Dict[str, Any],
    ) -> None:
        ...


class NoOpReleaseFinalizationHooks(ReleaseFinalizationHooks):
    async def on_before_finalize(
        self,
        release_plan: ReleasePlan,
        sprint_results: List[SprintResult],
        context: Dict[str, Any],
    ) -> None:
        return None

    async def on_after_finalize(
        self,
        release_plan: ReleasePlan,
        sprint_results: List[SprintResult],
        result: ReleaseFinalizationResult,
        context: Dict[str, Any],
    ) -> None:
        return None


class ChainedReleaseFinalizationHooks(ReleaseFinalizationHooks):
    def __init__(self, hooks: List[ReleaseFinalizationHooks]):
        self._hooks = tuple(hooks)

    async def on_before_finalize(
        self,
        release_plan: ReleasePlan,
        sprint_results: List[SprintResult],
        context: Dict[str, Any],
    ) -> None:
        for h in self._hooks:
            try:
                await h.on_before_finalize(release_plan, sprint_results, context)
            except Exception as e:
                logger.warning("ChainedReleaseFinalizationHooks on_before [{}]: {}", type(h).__name__, e)

    async def on_after_finalize(
        self,
        release_plan: ReleasePlan,
        sprint_results: List[SprintResult],
        result: ReleaseFinalizationResult,
        context: Dict[str, Any],
    ) -> None:
        for h in reversed(self._hooks):
            try:
                await h.on_after_finalize(release_plan, sprint_results, result, context)
            except Exception as e:
                logger.warning("ChainedReleaseFinalizationHooks on_after [{}]: {}", type(h).__name__, e)


class ReleaseFinalizationRunner:
    def __init__(
        self,
        policy: Optional[ReleaseFinalizationPolicy] = None,
        hooks: Optional[ReleaseFinalizationHooks] = None,
        sprint_executor_factory: Optional[Any] = None,
    ):
        self.policy = policy or ReleaseFinalizationPolicy()
        self.hooks = hooks or NoOpReleaseFinalizationHooks()
        self._sprint_executor_factory = sprint_executor_factory

    def set_sprint_executor_factory(self, factory: Any) -> None:
        self._sprint_executor_factory = factory

    async def _run_fix_sprint(
        self,
        release_plan: ReleasePlan,
        fix_sprint: SprintDefinition,
        context: Dict[str, Any],
    ) -> Optional[SprintResult]:
        if self._sprint_executor_factory is None:
            return None
        executor = self._sprint_executor_factory()
        if executor is None:
            return None
        try:
            result = await executor.execute_sprint_parallel(
                fix_sprint,
                context=dict(context),
                save_checkpoint=False,
            )
            return result
        except Exception as e:
            logger.warning("release finalization fix sprint failed: {}", e)
            return None

    async def run(
        self,
        release_plan: ReleasePlan,
        sprint_results: List[SprintResult],
        context: Optional[Dict[str, Any]] = None,
    ) -> ReleaseFinalizationResult:
        ctx = dict(context or {})
        if not self.policy.should_finalize(release_plan, sprint_results):
            return ReleaseFinalizationResult(success=True, ready_to_release=True, summary="skip finalize")

        await self.hooks.on_before_finalize(release_plan, sprint_results, ctx)

        issues: List[str] = []
        failed_sprints = [r for r in sprint_results if r.status == ExecutionStatus.FAILED]
        if failed_sprints:
            issues.append(f"failed_sprints={len(failed_sprints)}")

        fix_tasks: List[SprintBacklogItem] = []
        if failed_sprints:
            for fr in failed_sprints:
                fix_tasks.append(
                    SprintBacklogItem(
                        description=f"修复最终验收失败问题：{fr.sprint.name}",
                        agent="coder",
                        target=None,
                    )
                )

        ready = not issues
        result = ReleaseFinalizationResult(
            success=True,
            ready_to_release=ready,
            summary="finalized" if ready else "blocked",
            issues=issues,
            fix_tasks=fix_tasks,
            metadata={"sprint_count": len(sprint_results)},
            sprint_results=[r.to_dict() for r in sprint_results],
        )

        if self.policy.should_retest(result) and fix_tasks:
            fix_sprint = self.policy.build_fix_sprint(release_plan, result)
            if fix_sprint is not None:
                fix_result = await self._run_fix_sprint(release_plan, fix_sprint, ctx)
                if fix_result is not None:
                    result.executed_fix_sprints.append(fix_result.to_dict())
                    result.metadata["fix_sprint_name"] = fix_sprint.name
                    result.metadata["fix_sprint_status"] = fix_result.status.value
                    result.metadata["fix_sprint_tasks"] = len(fix_sprint.tasks)
                    if fix_result.status == ExecutionStatus.SUCCESS:
                        result.ready_to_release = True
                        result.summary = "finalized_after_fix"
                        result.issues = []

        await self.hooks.on_after_finalize(release_plan, sprint_results, result, ctx)
        return result


__all__ = [
    "ChainedReleaseFinalizationHooks",
    "NoOpReleaseFinalizationHooks",
    "ReleaseFinalizationHooks",
    "ReleaseFinalizationPolicy",
    "ReleaseFinalizationResult",
    "ReleaseFinalizationRunner",
]
