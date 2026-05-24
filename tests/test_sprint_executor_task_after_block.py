"""SprintExecutor：治理 task_after 阻断（G v3）与 context 约定。"""

from __future__ import annotations

import pytest

from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
from sprintcycle.execution.hooks.governance_context import (
    CTX_GOVERNANCE_TASK_AFTER_DETAIL,
    CTX_GOVERNANCE_TASK_AFTER_FAILED,
)
from sprintcycle.execution.hooks.task_hooks import TaskLifecycleHooks
from sprintcycle.execution.sprint_executor import SprintExecutor
from sprintcycle.execution.sprint_types import ExecutionStatus
from sprintcycle.domain.generic.models import SprintBacklogItem


class _BlockHook(TaskLifecycleHooks):
    async def on_after_task_complete(self, task, sprint_name, context, task_result):
        if task_result.status == ExecutionStatus.SUCCESS:
            context[CTX_GOVERNANCE_TASK_AFTER_FAILED] = True
            context[CTX_GOVERNANCE_TASK_AFTER_DETAIL] = "blocked-by-test-hook"


@pytest.mark.asyncio
async def test_sprint_executor_marks_failed_when_governance_context_set():
    ex = SprintExecutor(runtime_config=RuntimeConfig(dry_run=True))
    ex.set_task_hooks(_BlockHook())
    task = SprintBacklogItem(description="noop", agent="coder")
    res = await ex._execute_task(task, "S1", {})
    assert res.status == ExecutionStatus.FAILED
    assert "blocked-by-test-hook" in (res.error or "")
    assert res.output  # dry_run 仍有输出
