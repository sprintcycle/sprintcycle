"""Base strategy interface for agent execution."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sprintcycle.domain.models import SprintBacklogItem
from sprintcycle.domain.execution.project_write import ProjectWritePlan


class AgentStrategy(ABC):
    """Abstract base class for agent execution strategies."""

    def __init__(
        self,
        project_write_plan: Optional[ProjectWritePlan] = None,
        dry_run: bool = False,
    ):
        self.project_write_plan = project_write_plan
        self.dry_run = dry_run

    @abstractmethod
    async def execute(
        self,
        task: SprintBacklogItem,
        context: Dict[str, Any],
        build_context_func: Any,
    ) -> str:
        """
        Execute a task using this strategy.
        
        Args:
            task: The task to execute
            context: Execution context
            build_context_func: Function to build agent-specific context
            
        Returns:
            The execution output as a string
            
        Raises:
            RuntimeError: If execution fails
        """
        pass
