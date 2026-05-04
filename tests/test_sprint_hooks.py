"""SprintLifecycleHooks + execute_sprints 单一编排"""

import asyncio
from typing import Any, Dict, List, Optional

from sprintcycle.config import RuntimeConfig
from sprintcycle.execution.sprint_executor import SprintExecutor
from sprintcycle.execution.sprint_hooks import ChainedSprintHooks, SprintLifecycleHooks
from sprintcycle.prd.models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode


class CountingHooks(SprintLifecycleHooks):
    def __init__(self) -> None:
        self.before: List[int] = []
        self.after: List[int] = []

    async def on_before_sprint(
        self, sprint_index: int, sprint: PRDSprint, context: Dict[str, Any], prd: Optional[PRD]
    ) -> None:
        self.before.append(sprint_index)

    async def on_after_sprint(
        self, sprint_index: int, sprint: PRDSprint, result, context: Dict[str, Any], prd: Optional[PRD]
    ) -> None:
        self.after.append(sprint_index)


def test_execute_sprints_invokes_hooks_once_per_sprint():
    hooks = CountingHooks()
    ex = SprintExecutor(
        max_verify_fix_rounds=1,
        runtime_config=RuntimeConfig(dry_run=True, quality_level="L1"),
        sprint_hooks=hooks,
    )
    prd = PRD(
        project=PRDProject(name="p", path="."),
        mode=ExecutionMode.NORMAL,
        sprints=[
            PRDSprint(name="S1", tasks=[PRDTask(task="t1", agent="coder")]),
            PRDSprint(name="S2", tasks=[PRDTask(task="t2", agent="coder")]),
        ],
    )
    ex.set_prd(prd)
    ctx: Dict[str, Any] = {
        "project_path": ".",
        "prd_name": "p",
        "coding_engine": "aider",
        "quality_level": "L1",
    }

    async def _run() -> None:
        results = await ex.execute_sprints(prd.sprints, mode="normal", context=ctx, prd=prd)
        assert len(results) == 2

    asyncio.run(_run())
    assert hooks.before == [0, 1]
    assert hooks.after == [0, 1]


def test_chained_sprint_hooks_invokes_in_order():
    order: list[str] = []

    class H1(SprintLifecycleHooks):
        async def on_before_sprint(self, sprint_index, sprint, context, prd):
            order.append("1b")

        async def on_after_sprint(self, sprint_index, sprint, result, context, prd):
            order.append("1a")

    class H2(SprintLifecycleHooks):
        async def on_before_sprint(self, sprint_index, sprint, context, prd):
            order.append("2b")

        async def on_after_sprint(self, sprint_index, sprint, result, context, prd):
            order.append("2a")

    chain = ChainedSprintHooks((H1(), H2()))
    prd = PRD(
        project=PRDProject(name="p", path="."),
        mode=ExecutionMode.NORMAL,
        sprints=[PRDSprint(name="S", tasks=[PRDTask(task="t", agent="coder")])],
    )
    sprint = prd.sprints[0]

    async def _run() -> None:
        from sprintcycle.execution.sprint_types import SprintResult, ExecutionStatus

        ctx: Dict[str, Any] = {}
        await chain.on_before_sprint(0, sprint, ctx, prd)
        res = SprintResult(sprint=sprint, status=ExecutionStatus.SUCCESS, task_results=[])
        await chain.on_after_sprint(0, sprint, res, ctx, prd)

    asyncio.run(_run())
    assert order == ["1b", "2b", "2a", "1a"]


def test_dispatcher_uses_execute_sprints_not_per_sprint_loop():
    """Dispatcher Normal 路径应单次调用 execute_sprints（通过 patch 验证）。"""
    from unittest.mock import AsyncMock, patch

    from sprintcycle.scheduler.dispatcher import TaskDispatcher
    from sprintcycle.prd.models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode

    prd = PRD(
        project=PRDProject(name="x", path="."),
        mode=ExecutionMode.NORMAL,
        sprints=[PRDSprint(name="S1", tasks=[PRDTask(task="a", agent="coder")])],
    )
    fake = AsyncMock(return_value=[])

    d = TaskDispatcher(config=RuntimeConfig(dry_run=True, quality_level="L1"))

    async def _run_disp() -> None:
        await d._execute_normal_mode(prd, max_concurrent=2)

    with patch.object(SprintExecutor, "execute_sprints", fake):
        asyncio.run(_run_disp())

    fake.assert_awaited_once()
    kwargs = fake.await_args.kwargs
    assert kwargs.get("prd") is prd
    assert kwargs.get("sprint_index_offset") == 0
