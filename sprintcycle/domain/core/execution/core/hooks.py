"""Execution hooks used to keep the core extension-friendly."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from sprintcycle.domain.core.execution.core.protocols import ExecutionContext

Hook = Callable[[ExecutionContext], None]


@dataclass
class ExecutionHooks:
    before_task_start: List[Hook] = field(default_factory=list)
    after_task_start: List[Hook] = field(default_factory=list)
    before_stage: List[Hook] = field(default_factory=list)
    after_stage: List[Hook] = field(default_factory=list)
    before_step: List[Hook] = field(default_factory=list)
    after_step: List[Hook] = field(default_factory=list)
    before_deploy: List[Hook] = field(default_factory=list)
    after_deploy: List[Hook] = field(default_factory=list)
    on_error: List[Hook] = field(default_factory=list)

    def run(self, hooks: List[Hook], context: ExecutionContext) -> None:
        for hook in hooks:
            hook(context)
