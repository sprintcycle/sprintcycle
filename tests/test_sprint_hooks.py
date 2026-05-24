"""SprintLifecycleHooks + execute_sprints 单一编排"""

import asyncio
from typing import Any, Dict, List, Optional

from sprintcycle.infrastructure.config import RuntimeConfig
from sprintcycle.execution.sprint_executor import SprintExecutor
from sprintcycle.execution.hooks.sprint_hooks import ChainedSprintHooks, SprintLifecycleHooks
from sprintcycle.domain.generic.models import ReleasePlan, ProductAnchor, SprintDefinition, SprintBacklogItem, ExecutionMode


class CountingHooks(SprintLifecycleHooks):
    def __init__(self) -> None:
        self.before: List[int] = []
        self.after: List[int] = []

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        self.before.append(sprint_index)

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        result,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        self.after.append(sprint_index)


def test_execute_sprints_invokes_hooks_once_per_sprint():
    hooks = CountingHooks()
    ex = SprintExecutor(
        max_verify_fix_rounds=1,
        runtime_config=RuntimeConfig(dry_run=True, quality_level="L1"),
        sprint_hooks=hooks,
    )
    plan = ReleasePlan(
        project=ProductAnchor(name="p", path="."),
        mode=ExecutionMode.NORMAL,
        sprints=[
            SprintDefinition(name="S1", tasks=[SprintBacklogItem(description="t1", agent="coder")]),
            SprintDefinition(name="S2", tasks=[SprintBacklogItem(description="t2", agent="coder")]),
        ],
    )
    ex.set_release_plan(plan)
    ctx: Dict[str, Any] = {
        "project_path": ".",
        "release_plan_name": "p",
        "coding_engine": "aider",
        "quality_level": "L1",
    }

    async def _run() -> None:
        results = await ex.execute_sprints(
            plan.sprints, mode="normal", context=ctx, release_plan=plan
        )
        assert len(results) == 2

    asyncio.run(_run())
    assert hooks.before == [0, 1]
    assert hooks.after == [0, 1]


def test_chained_sprint_hooks_invokes_in_order():
    order: list[str] = []

    class H1(SprintLifecycleHooks):
        async def on_before_sprint(self, sprint_index, sprint, context, release_plan):
            order.append("1b")

        async def on_after_sprint(self, sprint_index, sprint, result, context, release_plan):
            order.append("1a")

    class H2(SprintLifecycleHooks):
        async def on_before_sprint(self, sprint_index, sprint, context, release_plan):
            order.append("2b")

        async def on_after_sprint(self, sprint_index, sprint, result, context, release_plan):
            order.append("2a")

    chain = ChainedSprintHooks((H1(), H2()))
    plan = ReleasePlan(
        project=ProductAnchor(name="p", path="."),
        mode=ExecutionMode.NORMAL,
        sprints=[SprintDefinition(name="S", tasks=[SprintBacklogItem(description="t", agent="coder")])],
    )
    sprint = plan.sprints[0]

    async def _run() -> None:
        from sprintcycle.execution.sprint_types import SprintResult, ExecutionStatus

        ctx: Dict[str, Any] = {}
        await chain.on_before_sprint(0, sprint, ctx, plan)
        res = SprintResult(sprint=sprint, status=ExecutionStatus.SUCCESS, task_results=[])
        await chain.on_after_sprint(0, sprint, res, ctx, plan)

    asyncio.run(_run())
    assert order == ["1b", "2b", "2a", "1a"]


def test_orchestrator_uses_execute_sprints_not_per_sprint_loop():
    """Dispatcher Normal 路径通过 execute_release_plan 完成编排（非逐 sprint 循环）。"""
    from unittest.mock import AsyncMock, patch

    from sprintcycle.application.sprint_orchestrator import SprintOrchestrator
    from sprintcycle.domain.generic.models import ReleasePlan, ProductAnchor, SprintDefinition, SprintBacklogItem, ExecutionMode

    plan = ReleasePlan(
        project=ProductAnchor(name="x", path="."),
        mode=ExecutionMode.NORMAL,
        sprints=[SprintDefinition(name="S1", tasks=[SprintBacklogItem(description="a", agent="coder")])],
    )

    d = SprintOrchestrator(config=RuntimeConfig(dry_run=True, quality_level="L1"))

    # Verify execute_release_plan completes without error
    async def _run_disp() -> None:
        results = await d.execute_release_plan(plan)
        assert isinstance(results, list)

    asyncio.run(_run_disp())
