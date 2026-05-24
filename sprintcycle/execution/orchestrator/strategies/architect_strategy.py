"""Architect agent execution strategy."""

from typing import Any, Dict

from sprintcycle.domain.models import SprintBacklogItem
from .base_strategy import AgentStrategy
from ..constants import DRY_RUN_ARCHITECT_TEMPLATE


class ArchitectStrategy(AgentStrategy):
    """Strategy for executing architect tasks."""

    async def execute(
        self,
        task: SprintBacklogItem,
        context: Dict[str, Any],
        build_context_func: Any,
    ) -> str:
        """Execute architect task."""
        if self.dry_run:
            summary = DRY_RUN_ARCHITECT_TEMPLATE.format(desc=task.description[:80])
            context["architecture_design"] = summary
            return summary

        from ..agents.architect import ArchitectureAgent

        ctx = build_context_func(task, context.get("sprint_name", ""), context)
        agent = ArchitectureAgent()
        
        if self.project_write_plan is not None:
            agent.set_project_write_plan(self.project_write_plan)
            
        res = await agent.execute(task.description, ctx)
        
        if not res.success:
            raise RuntimeError(res.error or "ArchitectureAgent 执行失败")
            
        arch = ctx.codebase_context.get("architecture_design") or res.output or ""
        if arch:
            context["architecture_design"] = arch
            
        return str(arch)
