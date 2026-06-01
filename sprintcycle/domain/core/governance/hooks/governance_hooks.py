"""
治理相关的钩子统一模块。

**已精简**：将 sprint_hooks.py 和 task_hooks.py 合并到此文件。

**架构说明**：
- 适配器通过依赖注入提供，不直接依赖 application 层
- 使用全局注册机制获取治理适配器
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

from sprintcycle.domain.generic.models import ReleasePlan, SprintDefinition, SprintBacklogItem
from sprintcycle.domain.generic.interfaces import SprintResult, ExecutionStatus, TaskResult
from sprintcycle.domain.core.execution.hooks.lifecycle_hooks import SprintLifecycleHooks, TaskLifecycleHooks
from sprintcycle.domain.ports.config import RuntimeConfigProtocol
from sprintcycle.domain.core.governance.arch_guard.config import ArchGuardConfig
from sprintcycle.domain.core.governance.arch_guard.engine import ArchGuardEngine
from sprintcycle.domain.core.governance.arch_guard.reporter import GovernanceReportAdapter
from sprintcycle.domain.core.governance.arch_guard.checks import checks_for_gate, filter_argv_items_by_governance_sources, run_argv_item
from sprintcycle.domain.core.governance.core import persist_planning_report, persist_report, load_merged_governance_data
from sprintcycle.domain.core.governance.common.model import Finding as GovernanceViolation

if TYPE_CHECKING:
    from sprintcycle.domain.ports.observability import ObservabilityFacadeProtocol
    from sprintcycle.domain.ports.governance import LinterAdapterProtocol

# 全局适配器注册表
_governance_adapters: Optional[Dict[str, Any]] = None


def register_governance_adapters(adapters: Dict[str, Any]) -> None:
    """注册治理适配器（由 application 层在初始化时调用）"""
    global _governance_adapters
    _governance_adapters = adapters


def _get_governance_engine_adapters() -> Dict[str, Any]:
    """获取治理引擎所需的适配器"""
    global _governance_adapters
    if _governance_adapters is None:
        raise RuntimeError(
            "治理适配器未注册。请先调用 register_governance_adapters() 注册适配器。"
        )
    return _governance_adapters


class GovernanceSprintHooks(SprintLifecycleHooks):
    """治理 Sprint 钩子 - 继承统一的 SprintLifecycleHooks"""

    def __init__(
        self,
        project_path: str,
        config: RuntimeConfigProtocol,
        observability: Optional["ObservabilityFacadeProtocol"] = None,
    ):
        self._project_path = project_path
        self._config = config
        self._observability = observability

    def _build_governance_context(
        self,
        *,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan] = None,
        result: Optional[SprintResult] = None,
    ) -> Dict[str, Any]:
        ctx: Dict[str, Any] = dict(context or {})
        ctx.setdefault("project_path", self._project_path)
        ctx.setdefault("governance_extension_bypass", False)
        ctx.setdefault("breaking_change", False)
        ctx.setdefault("compatibility_plan", None)
        ctx.setdefault("evolution_mainline", "")
        ctx.setdefault("sprint_index", sprint_index)
        ctx.setdefault("sprint_name", getattr(sprint, "name", ""))
        if release_plan is not None:
            ctx.setdefault("release_plan_name", getattr(getattr(release_plan, "project", None), "name", ""))
            ctx.setdefault(
                "release_plan_mode",
                getattr(getattr(release_plan, "mode", None), "value", str(getattr(release_plan, "mode", ""))),
            )
        if result is not None:
            ctx.setdefault(
                "sprint_status", getattr(getattr(result.status, None), "value", str(getattr(result.status, "")))
            )
        return ctx

    def _enabled(self) -> bool:
        return bool(getattr(self._config, "governance_enabled", False))

    async def on_sprint_start(
        self,
        sprint: SprintDefinition,
        **kwargs: Any,
    ) -> None:
        """Sprint 开始钩子 - Planning"""
        sprint_index = kwargs.get("sprint_index", 0)
        context = kwargs.get("context", {})
        release_plan = kwargs.get("release_plan")

        if not self._enabled():
            return
        try:
            raw = (context or {}).get("project_path") or self._project_path
            cfg = ArchGuardConfig.from_runtime_config(self._config, str(raw))
            adapters = _get_governance_engine_adapters()
            engine = ArchGuardEngine(
                cfg,
                import_linter_adapter=adapters.get("import_linter"),
                grimp_adapter=adapters.get("grimp"),
                archguard_adapter=adapters.get("archguard"),
                ruff_adapter=adapters.get("ruff"),
                typecheck_adapter=adapters.get("typecheck"),
            )
            ctx = self._build_governance_context(
                sprint_index=sprint_index,
                sprint=sprint,
                context=context,
                release_plan=release_plan,
            )
            report = await engine.run_planning_gate(str(raw), release_plan=release_plan, context=ctx)
            gov_report = GovernanceReportAdapter.to_governance_report(report)
            context["governance_planning_report"] = gov_report.to_dict()
            context["governance_context"] = ctx
            n_warn = sum(1 for v in gov_report.violations if v.severity == "warning")
            n_err = sum(1 for v in gov_report.violations if v.severity == "error")
            logger.info(
                "治理 Planning gate: sprint={} violations error={} warning={} duration_sec={}",
                sprint.name,
                n_err,
                n_warn,
                gov_report.metadata.get("duration_sec"),
            )
            for v in gov_report.violations[:20]:
                log = logger.warning if v.severity != "error" else logger.error
                log("  [{}] {}", v.rule_id, v.message)
            persist_planning_report(gov_report, str(raw), self._config)
        except Exception as e:
            logger.warning("Governance planning gate skipped: {}", e)

    async def on_sprint_complete(
        self,
        sprint: SprintDefinition,
        result: SprintResult,
        **kwargs: Any,
    ) -> None:
        """Sprint 完成钩子 - Review"""
        sprint_index = kwargs.get("sprint_index", 0)
        context = kwargs.get("context", {})
        release_plan = kwargs.get("release_plan")

        if not self._enabled():
            return
        try:
            raw = (context or {}).get("project_path") or self._project_path
            cfg = ArchGuardConfig.from_runtime_config(self._config, str(raw))
            adapters = _get_governance_engine_adapters()
            engine = ArchGuardEngine(
                cfg,
                import_linter_adapter=adapters.get("import_linter"),
                grimp_adapter=adapters.get("grimp"),
                archguard_adapter=adapters.get("archguard"),
                ruff_adapter=adapters.get("ruff"),
                typecheck_adapter=adapters.get("typecheck"),
            )
            ctx = self._build_governance_context(
                sprint_index=sprint_index,
                sprint=sprint,
                context=context,
                release_plan=release_plan,
                result=result,
            )
            report = await engine.run_review_gate(str(raw), context=ctx)
            gov_report = GovernanceReportAdapter.to_governance_report(report)
            context["governance_review_report"] = gov_report.to_dict()
            context["governance_context"] = ctx
            n_err = sum(1 for v in gov_report.violations if v.severity == "error")
            n_warn = sum(1 for v in gov_report.violations if v.severity == "warning")
            logger.info(
                "治理 Review gate: sprint={} status={} violations error={} warning={} duration_sec={}",
                sprint.name,
                getattr(result.status, "value", result.status),
                n_err,
                n_warn,
                gov_report.metadata.get("duration_sec"),
            )
            for v in gov_report.violations[:30]:
                log = logger.warning if v.severity != "error" else logger.error
                log("  [{}] {}", v.rule_id, v.message)
            persist_report(gov_report, str(raw), self._config)
            block = getattr(self._config, "governance_block_on", "none") or "none"
            if gov_report.should_block_ci(block) and block != "none":
                logger.error(
                    "治理 Review 存在 error 级别违规；当前 Sprint 已完成，请在本地或 CI 运行 "
                    "`sprintcycle governance check` 并修复（governance_block_on={}）",
                    block,
                )
        except Exception as e:
            logger.warning("Governance review gate skipped: {}", e)


class GovernanceTaskLifecycleHooks(TaskLifecycleHooks):
    """治理任务钩子 - 继承统一的 TaskLifecycleHooks"""

    def __init__(
        self,
        config: RuntimeConfigProtocol,
        project_root: str,
    ):
        self._config = config
        self._root = Path(project_root).expanduser().resolve()
        self._task_after_items: Optional[List[Dict[str, Any]]] = None
        self._hitl_service: Optional[Any] = None

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


__all__ = [
    "GovernanceSprintHooks",
    "GovernanceTaskLifecycleHooks",
]
