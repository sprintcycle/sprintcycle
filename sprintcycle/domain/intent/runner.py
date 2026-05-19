"""
已解析 Release Plan 的执行适配（弃用路径）

首选：``SprintCycle.run_release_plan(release_plan)``，返回与 ``run()`` 一致的 ``RunResult``。

``RunnerHandler`` 仅保留向后兼容，委托 ``run_release_plan`` 并映射为 ``IntentResult``。
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Optional

from loguru import logger

from ...application.release_plan.parser import ReleasePlanParser
from .base import IntentHandler, IntentResult

if TYPE_CHECKING:
    from ..api import SprintCycle
    from ...infrastructure.config import RuntimeConfig
    from ...application.release_plan.models import ReleasePlan


def parse_release_plan_file(file_path: str) -> "ReleasePlan":
    """从 YAML 文件解析 Release Plan。"""
    return ReleasePlanParser().parse_file(file_path)


class RunnerHandler(IntentHandler):
    """已弃用：请使用 ``SprintCycle.run_release_plan``；需 ``IntentResult`` 时用 ``IntentResult.from_run_result``。"""

    def __init__(
        self,
        api: Optional["SprintCycle"] = None,
        *,
        project_path: str = ".",
        config: Optional["RuntimeConfig"] = None,
    ):
        warnings.warn(
            "RunnerHandler is deprecated; use SprintCycle.run_release_plan(release_plan) "
            "and IntentResult.from_run_result(plan, run_result) if you need IntentResult.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__()
        if api is not None:
            self._api = api
        else:
            from ..api import SprintCycle as _SprintCycle

            self._api = _SprintCycle(project_path=project_path, config=config)

    def execute(self, release_plan: "ReleasePlan") -> IntentResult:
        """执行已解析计划（委托 ``SprintCycle.run_release_plan``）。"""
        logger.info("🚀 开始执行 Release Plan: {}", release_plan.project.name)
        run_result = self._api.run_release_plan(
            release_plan,
            confirm_knowledge=False,
        )
        return IntentResult.from_run_result(release_plan, run_result)

    @staticmethod
    def parse_release_plan_file(file_path: str) -> "ReleasePlan":
        """从 YAML 文件解析 Release Plan（等价于模块级 ``parse_release_plan_file``）。"""
        return parse_release_plan_file(file_path)
