"""Coder agent execution strategy."""

from typing import Any, Dict

from sprintcycle.domain.models import SprintBacklogItem
from sprintcycle.application.execution.core.policies.task_retry_policy import TaskRetryPolicy
from .base_strategy import AgentStrategy
from ..constants import DRY_RUN_CODER_TEMPLATE


class CoderStrategy(AgentStrategy):
    """Strategy for executing coder/implement tasks."""

    def __init__(
        self,
        max_verify_fix_rounds: int = 3,
        project_write_plan=None,
        dry_run: bool = False,
    ):
        super().__init__(project_write_plan=project_write_plan, dry_run=dry_run)
        self.max_verify_fix_rounds = max_verify_fix_rounds
        self.task_retry_policy = TaskRetryPolicy(max_verify_fix_rounds)

    async def execute(
        self,
        task: SprintBacklogItem,
        context: Dict[str, Any],
        build_context_func: Any,
    ) -> str:
        """Execute coder task with retry logic."""
        if self.dry_run:
            return DRY_RUN_CODER_TEMPLATE.format(desc=task.description[:120])

        from sprintcycle.domain.execution.agents.coder_base import CoderAgent

        work = dict(context)
        last_msg = "CoderAgent 执行失败"
        
        for attempt in range(self.max_verify_fix_rounds):
            ctx = build_context_func(task, work.get("sprint_name", ""), work)
            agent = CoderAgent()
            
            if self.project_write_plan is not None:
                agent.set_project_write_plan(self.project_write_plan)
                
            res = await agent.execute(task.description, ctx)
            
            if res.success:
                return res.output or ""
                
            last_msg = res.error or last_msg
            decision = self.task_retry_policy.should_retry(attempt, last_msg)
            
            if not decision.should_retry:
                raise RuntimeError(last_msg)
                
            prev = (work.get("verify_fix_notes") or "").strip()
            work["verify_fix_notes"] = (
                prev + f"\n[attempt {decision.attempt}/{decision.max_attempts}] {last_msg}"
            ).strip()
            
        raise RuntimeError(last_msg)
