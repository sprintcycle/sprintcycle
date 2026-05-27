"""
Sprint 生命周期钩子：治理 Planning（before）与 Review（after）。

使用 Domain 定义的协议接口，打破 Governance → Execution 循环依赖。

**分层**：GovernanceHooks 通过构造函数接收依赖。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger

from sprintcycle.domain.generic.models import ReleasePlan, SprintDefinition
from sprintcycle.domain.generic.interfaces import SprintLifecycleHookProtocol
from sprintcycle.domain.generic.interfaces import SprintResult
from sprintcycle.domain.ports.config import RuntimeConfigProtocol
from ..arch_guard.config import ArchGuardConfig
from ..arch_guard.engine import ArchGuardEngine
from ..arch_guard.reporter import GovernanceReportAdapter
from sprintcycle.domain.core.governance.core import persist_planning_report, persist_report

if TYPE_CHECKING:
    from sprintcycle.domain.ports.observability import ObservabilityFacadeProtocol


class GovernanceSprintHooks(SprintLifecycleHookProtocol):
    """治理 Sprint 钩子 - 实现协议接口"""

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
            engine = ArchGuardEngine(cfg)
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
            engine = ArchGuardEngine(cfg)
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
