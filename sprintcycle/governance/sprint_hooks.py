"""
Sprint 生命周期钩子：治理 Planning（before）与 Review（after）。

链顺序（见 ``SprintOrchestrator._build_sprint_hooks``）::

    ChainedSprintHooks((
        KnowledgeInjectionHook,   # before: 知识注入
        GovernanceSprintHooks,     # before: Planning；after: Review
        _OrchestratorSprintHooks,  # before: 事件；after: 测量与知识卡片
    ))

``on_after_sprint`` 调用顺序为**逆序**，故实际为：编排收尾 → 治理 Review → 知识（no-op）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger

from sprintcycle.domain.models import ReleasePlan, SprintDefinition
from ..execution.events import Event, EventType, ExecutionEventBackend
from ..execution.hooks.sprint_hooks import SprintLifecycleHooks
from ..execution.sprint_types import SprintResult
from .arch_guard.config import ArchGuardConfig
from .arch_guard.engine import ArchGuardEngine
from .arch_guard.reporter import GovernanceReportAdapter
from .report import GovernanceReport
from .runner import persist_planning_report, persist_report

if TYPE_CHECKING:
    from ..infrastructure.config.runtime_config import RuntimeConfig


class GovernanceSprintHooks(SprintLifecycleHooks):
    def __init__(
        self,
        project_path: str,
        config: "RuntimeConfig",
        event_bus: Optional[ExecutionEventBackend] = None,
    ):
        self._project_path = project_path
        self._config = config
        self._event_bus = event_bus

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
                "sprint_status", getattr(getattr(result, "status", None), "value", str(getattr(result, "status", "")))
            )
        return ctx

    async def _emit_gate_summary(
        self,
        gate: str,
        sprint: SprintDefinition,
        report: GovernanceReport,
    ) -> None:
        if self._event_bus is None:
            return
        viol = list(report.violations)
        compose_hits = [
            {"rule_id": v.rule_id, "message": (v.message or "")[:400]}
            for v in viol
            if str(v.rule_id).startswith("compose:")
        ]
        n_err = sum(1 for v in viol if v.severity == "error")
        n_warn = sum(1 for v in viol if v.severity == "warning")
        await self._event_bus.emit(
            Event(
                type=EventType.GOVERNANCE_GATE,
                data={
                    "gate": gate,
                    "sprint_name": sprint.name,
                    "error_count": n_err,
                    "warning_count": n_warn,
                    "compose_rule_ids": [h["rule_id"] for h in compose_hits],
                    "compose_hits": compose_hits[:15],
                    "violation_rule_ids_sample": [v.rule_id for v in viol[:24]],
                },
            )
        )

    def _enabled(self) -> bool:
        return bool(getattr(self._config, "governance_enabled", False))

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
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
            await self._emit_gate_summary("planning", sprint, gov_report)
        except Exception as e:
            logger.warning("Governance planning gate skipped: {}", e)

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        result: SprintResult,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
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
                    "`sprintcycle governance check` 并修复（governance_block_on={})",
                    block,
                )
            await self._emit_gate_summary("review", sprint, gov_report)
        except Exception as e:
            logger.warning("Governance review gate skipped: {}", e)
