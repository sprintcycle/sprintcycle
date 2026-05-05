"""
Runner 意图处理器

从已解析的 Release Plan 执行交付：委托 ``SprintCycle._run_resolved_plan``，
与 ``SprintCycle.run`` 共用知识门、并发度（``parallel_tasks``）与编排器配置。
"""

import logging
import time
from typing import TYPE_CHECKING, Optional

from .base import IntentHandler, IntentResult
from ..release_plan.parser import ReleasePlanParser

if TYPE_CHECKING:
    from ..api import SprintCycle
    from ..config import RuntimeConfig
    from ..release_plan.models import PRD

logger = logging.getLogger(__name__)


class RunnerHandler(IntentHandler):
    """从 Release Plan 对象执行（与 ``SprintCycle.run(prd_yaml=…)`` 行为对齐）。"""

    def __init__(
        self,
        api: Optional["SprintCycle"] = None,
        *,
        project_path: str = ".",
        config: Optional["RuntimeConfig"] = None,
    ):
        super().__init__()
        if api is not None:
            self._api = api
        else:
            from ..api import SprintCycle as _SprintCycle

            self._api = _SprintCycle(project_path=project_path, config=config)

    def execute(self, release_plan: "PRD") -> IntentResult:
        """执行已解析计划（经 ``SprintCycle`` 统一路径）。"""
        logger.info("🚀 开始执行 Release Plan: %s", release_plan.project.name)

        if not self.validate_release_plan(release_plan):
            return IntentResult(
                success=False,
                release_plan=release_plan,
                error="Release Plan 验证失败",
            )

        start = time.time()
        try:
            run_result, sprint_results = self._api._run_resolved_plan(
                release_plan,
                start,
                confirm_knowledge=False,
            )
            if run_result.pending_knowledge_confirmation:
                return IntentResult(
                    success=False,
                    release_plan=release_plan,
                    error=run_result.message or "知识注入待确认",
                    details={
                        "pending_knowledge_confirmation": True,
                        "knowledge_injection_preview": run_result.knowledge_injection_preview,
                    },
                )
            if not run_result.success:
                return IntentResult(
                    success=False,
                    release_plan=release_plan,
                    error=run_result.error or "执行失败",
                )

            return self._build_result(run_result.success, release_plan, sprint_results)
        except Exception as e:
            logger.exception("Release Plan 执行失败")
            return IntentResult(
                success=False,
                release_plan=release_plan,
                error=str(e),
            )

    @staticmethod
    def parse_release_plan_file(file_path: str) -> "PRD":
        """从 YAML 文件解析 Release Plan。"""
        return ReleasePlanParser().parse_file(file_path)
