"""治理相关的任务级钩子。

使用 Domain 定义的协议接口，打破 Governance → Execution 循环依赖。

**分层**：GovernanceHooks 通过构造函数接收依赖。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

from sprintcycle.domain.generic.models import SprintBacklogItem
from sprintcycle.domain.generic.interfaces import TaskLifecycleHookProtocol, ExecutionEventProtocol
from sprintcycle.domain.generic.interfaces import ExecutionStatus, TaskResult
from ..hitl import HitlGate, HitlService, create_hitl_coordinator, evaluate_hitl_policy
from sprintcycle.domain.core.governance.arch_guard.model import GuardFinding as GovernanceViolation
from ..arch_guard.yaml_checks import checks_for_gate, filter_argv_items_by_governance_sources, run_argv_item
from sprintcycle.domain.core.governance.core import load_merged_governance_data

if TYPE_CHECKING:
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig


class GovernanceTaskLifecycleHooks(TaskLifecycleHookProtocol):
    """治理任务钩子 - 实现协议接口"""

    def __init__(
        self,
        config: "RuntimeConfig",
        project_root: str,
    ):
        self._config = config
        self._root = Path(project_root).expanduser().resolve()
        self._task_after_items: Optional[List[Dict[str, Any]]] = None
        self._hitl_service: Optional[HitlService] = None

    def _get_task_after_items(self) -> List[Dict[str, Any]]:
        if self._task_after_items is not None:
            return self._task_after_items
        data = load_merged_governance_data(self._root, self._config)
        raw = checks_for_gate(data, "task_after")
        self._task_after_items = filter_argv_items_by_governance_sources(raw, self._config)
        return self._task_after_items

    def _extra_env(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        task_result: TaskResult,
    ) -> Dict[str, str]:
        st = task_result.status
        status_s = st.value if hasattr(st, "value") else str(st)
        desc = (task.description or "")[:4096]
        return {
            "SPRINTCYCLE_TASK_AGENT": task.agent or "",
            "SPRINTCYCLE_TASK_TARGET": task.target or "",
            "SPRINTCYCLE_TASK_DESCRIPTION": desc,
            "SPRINTCYCLE_SPRINT_NAME": sprint_name,
            "SPRINTCYCLE_TASK_STATUS": status_s,
        }

    def _item_blocks(self, item: Dict[str, Any]) -> bool:
        if "block_on_failure" in item:
            return bool(item["block_on_failure"])
        return bool(getattr(self._config, "governance_task_after_block_on_failure", False))

    @staticmethod
    def _should_run_item(when_raw: str, task_ok: bool) -> bool:
        w = (when_raw or "success").strip().lower()
        if w not in ("success", "failure", "always"):
            w = "success"
        if w == "always":
            return True
        if w == "success":
            return task_ok
        return not task_ok

    async def on_task_complete(
        self,
        task: SprintBacklogItem,
        result: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """任务完成钩子"""
        task_result = kwargs.get("task_result")
        if task_result is None:
            return

        sprint_name = kwargs.get("sprint_name", "")
        context = kwargs.get("context", {})

        st = task_result.status
        wi = task_result.work_item
        logger.info(
            "治理任务钩子: sprint={} agent={} status={} target={} desc={}",
            sprint_name,
            wi.agent,
            st.value,
            (wi.target or "")[:120],
            (wi.description or "")[:200],
        )
        if not getattr(self._config, "governance_task_hooks_enabled", False):
            return
        task_ok = st == ExecutionStatus.SUCCESS or st == ExecutionStatus.SKIPPED
        items = self._get_task_after_items()
        if not items:
            return

        extra_env = self._extra_env(task, sprint_name, task_result)

        for item in items:
            when_raw = item.get("run_when", "success")
            if not self._should_run_item(when_raw, task_ok):
                continue
            check_id = item.get("id") or item.get("name") or "task_after"
            viols: List[GovernanceViolation] = []
            try:
                result = await run_argv_item(
                    item,
                    project_root=str(self._root),
                    config=self._config,
                    extra_env=extra_env,
                )
                viols = result.get("violations", [])
            except Exception as e:
                viols = [
                    GovernanceViolation(
                        rule_id=check_id,
                        severity="error",
                        message=f"Task after check failed: {e}",
                        location={},
                    )
                ]

            for v in viols:
                lv = logger.warning if v.severity != "error" else logger.error
                lv("  [{}] {}", v.rule_id, v.message)

            if viols and self._item_blocks(item):
                context["__governance_task_after_block__"] = True
                logger.error("Task after check 阻断：任务被标记为 failed")

            gov_key = "governance_task_after_results"
            if gov_key not in context:
                context[gov_key] = []
            context[gov_key].append({"check_id": check_id, "violations": [v.to_dict() for v in viols]})
