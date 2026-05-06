"""治理相关的任务级钩子（可选；与 ``governance_task_hooks_enabled`` 联用）。"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

from ..execution.events import EventBus, EventType, create_event
from ..execution.hooks.governance_context import (
    CTX_GOVERNANCE_TASK_AFTER_DETAIL,
    CTX_GOVERNANCE_TASK_AFTER_FAILED,
)
from ..execution.hooks.task_hooks import TaskLifecycleHooks
from ..execution.sprint_types import ExecutionStatus, TaskResult
from ..release_plan.models import SprintBacklogItem
from .report import GovernanceViolation
from .yaml_checks import checks_for_gate, load_governance_yaml, run_argv_item

if TYPE_CHECKING:
    from ..config.runtime_config import RuntimeConfig


def _resolve_governance_yaml(project_root: Path, config_path: str) -> Optional[Path]:
    raw = (config_path or "").strip()
    if not raw:
        return None
    p = Path(raw)
    if not p.is_absolute():
        p = (project_root / raw).resolve()
    else:
        p = p.expanduser().resolve()
    return p if p.is_file() else None


class GovernanceTaskLifecycleHooks(TaskLifecycleHooks):
    """
    任务完成后：结构化日志 + 可选治理 YAML ``task_after`` 子进程（Daily / 自定义门禁 v1）。

    ``task_after`` 与 ``planning`` / ``review`` 使用相同 argv 字段；额外支持：

    - ``run_when``: ``success``（默认）| ``failure`` | ``always`` — 何时执行该条检查。
    - 子进程环境变量（字符串）：``SPRINTCYCLE_TASK_AGENT``、``SPRINTCYCLE_TASK_TARGET``、
      ``SPRINTCYCLE_TASK_DESCRIPTION``、``SPRINTCYCLE_SPRINT_NAME``、``SPRINTCYCLE_TASK_STATUS``。

    检查失败时按条目的 ``severity`` 打 log。
    若 ``[governance] task_after_block_on_failure`` 或 YAML 单条 ``block_on_failure: true``，
    且**任务本体已成功**（``task_after`` 仍执行），则向 context 写入阻断标记；``SprintExecutor``
    将把该任务标为 **failed**（G v3）。
    若构造时传入 ``event_bus``，每条 ``task_after`` 执行后发送 ``EventType.GOVERNANCE_TASK_CHECK``。
    """

    def __init__(
        self,
        config: "RuntimeConfig",
        project_root: str,
        event_bus: Optional[EventBus] = None,
    ):
        self._config = config
        self._root = Path(project_root).expanduser().resolve()
        self._event_bus = event_bus
        self._task_after_items: Optional[List[Dict[str, Any]]] = None

    def _get_task_after_items(self) -> List[Dict[str, Any]]:
        if self._task_after_items is not None:
            return self._task_after_items
        cfg_path = getattr(self._config, "governance_config_path", None) or ""
        yaml_path = _resolve_governance_yaml(self._root, str(cfg_path))
        data = load_governance_yaml(yaml_path) if yaml_path is not None else {}
        self._task_after_items = checks_for_gate(data, "task_after")
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

    async def _emit_task_check(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        check_id: str,
        viols: List[GovernanceViolation],
    ) -> None:
        if self._event_bus is None:
            return
        try:
            ok = not viols
            first = viols[0] if viols else None
            ev = create_event(
                EventType.GOVERNANCE_TASK_CHECK,
                sprint_name=sprint_name,
                agent_type=task.agent or None,
                description=(task.description or "")[:240] or None,
                status="passed" if ok else "failed",
                message=(first.message[:1200] if first else "ok") or "ok",
                check_id=check_id,
                governance_rule_id=first.rule_id if first else "task_after:ok",
            )
            await self._event_bus.emit(ev)
        except Exception as e:
            logger.warning("治理 task_after 事件发送失败: {}", e)

    async def on_after_task_complete(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        context: Dict[str, Any],
        task_result: TaskResult,
    ) -> None:
        st = task_result.status
        wi = task_result.work_item
        logger.info(
            "治理任务钩子: sprint={} agent={} status={} target={} desc={}",
            sprint_name,
            wi.agent,
            st.value,
            (wi.target or "")[:120],
            (wi.description or "")[:120],
        )
        if st != ExecutionStatus.SUCCESS:
            logger.warning("治理任务钩子: 任务未成功完成")

        items = self._get_task_after_items()
        if not items:
            return

        task_ok = st == ExecutionStatus.SUCCESS
        extra = self._extra_env(task, sprint_name, task_result)
        for item in items:
            if not isinstance(item, dict):
                continue
            when = str(item.get("run_when", "success"))
            if not self._should_run_item(when, task_ok):
                continue
            rid = str(item.get("id") or item.get("name") or "anonymous")
            viols = run_argv_item(item, self._root, "task_after", extra_env=extra)
            for v in viols:
                msg = f"task_after[{rid}] {v.message}"
                if v.severity == "error":
                    logger.error(msg)
                elif v.severity == "warning":
                    logger.warning(msg)
                else:
                    logger.info(msg)
            await self._emit_task_check(task, sprint_name, rid, viols)
            if viols and self._item_blocks(item) and task_ok:
                context[CTX_GOVERNANCE_TASK_AFTER_FAILED] = True
                line = "; ".join(f"{rid}:{v.message[:400]}" for v in viols[:5])
                prev = context.get(CTX_GOVERNANCE_TASK_AFTER_DETAIL)
                context[CTX_GOVERNANCE_TASK_AFTER_DETAIL] = (
                    f"{prev}\n{line}".strip() if isinstance(prev, str) and prev else line
                )
