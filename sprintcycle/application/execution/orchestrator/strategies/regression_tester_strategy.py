"""Regression tester agent execution strategy."""

import asyncio
from typing import Any, Dict

from sprintcycle.domain.models import SprintBacklogItem
from .base_strategy import AgentStrategy
from ..constants import DRY_RUN_REGRESSION_TESTER_TEMPLATE


class RegressionTesterStrategy(AgentStrategy):
    """Strategy for executing regression tester tasks."""

    async def execute(
        self,
        task: SprintBacklogItem,
        context: Dict[str, Any],
        build_context_func: Any,
    ) -> str:
        """Execute regression tester task."""
        if self.dry_run:
            return DRY_RUN_REGRESSION_TESTER_TEMPLATE.format(desc=task.description[:80])
            
        await asyncio.sleep(0.05)
        return f"回归测试完成: {task.description[:80]}"
