from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from sprintcycle.execution.events import Event, EventType, ExecutionEventBackend
from sprintcycle.execution.hooks.sprint_hooks import SprintLifecycleHooks
from sprintcycle.execution.sprint_types import SprintResult
from ...application.release_plan.models import ReleasePlan, SprintDefinition
from .config import VerificationConfig
from .engine import VerificationEngine
from .reporter import VerificationReportAdapter


class VerificationSprintHooks(SprintLifecycleHooks):
    def __init__(self, project_path: str, config: Any, event_bus: Optional[ExecutionEventBackend] = None):
        self._project_path = project_path
        self._config = config
        self._event_bus = event_bus

    def _enabled(self) -> bool:
        return bool(getattr(self._config, "verification_enabled", True))

    def _build_context(
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
        ctx.setdefault("sprint_index", sprint_index)
        ctx.setdefault("sprint_name", getattr(sprint, "name", ""))
        if release_plan is not None:
            ctx.setdefault("release_plan_name", getattr(getattr(release_plan, "project", None), "name", ""))
        if result is not None:
            ctx.setdefault("sprint_status", getattr(getattr(result, "status", None), "value", str(getattr(result, "status", ""))))
        return ctx

    async def _emit_gate_summary(self, gate: str, sprint: SprintDefinition, report) -> None:
        if self._event_bus is None:
            return
        viol = list(report.violations)
        await self._event_bus.emit(
            Event(
                type=EventType.GOVERNANCE_GATE,
                data={
                    "gate": f"verification:{gate}",
                    "sprint_name": sprint.name,
                    "error_count": sum(1 for v in viol if v.severity == "error"),
                    "warning_count": sum(1 for v in viol if v.severity == "warning"),
                    "violation_rule_ids_sample": [v.rule_id for v in viol[:24]],
                },
            )
        )

    async def on_before_sprint(self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        if not self._enabled():
            return
        try:
            raw = (context or {}).get("project_path") or self._project_path
            cfg = VerificationConfig.from_runtime_config(self._config, str(raw))
            engine = VerificationEngine(cfg)
            ctx = self._build_context(sprint_index=sprint_index, sprint=sprint, context=context, release_plan=release_plan)
            gate = str(ctx.get("verification_gate", "all"))
            report = await engine.run(gate, str(raw), context=ctx)
            gov = VerificationReportAdapter.to_governance_report(report)
            context["verification_planning_report"] = gov.to_dict()
            context["verification_context"] = ctx
            logger.info("验证 Planning gate: sprint={} violations error={} warning={}", sprint.name, sum(1 for v in gov.violations if v.severity == "error"), sum(1 for v in gov.violations if v.severity == "warning"))
            for v in gov.violations[:20]:
                log = logger.warning if v.severity != "error" else logger.error
                log("  [{}] {}", v.rule_id, v.message)
            await self._emit_gate_summary("planning", sprint, gov)
        except Exception as e:
            logger.warning("Verification planning gate skipped: {}", e)

    async def on_after_sprint(self, sprint_index: int, sprint: SprintDefinition, result: SprintResult, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        if not self._enabled():
            return
        try:
            raw = (context or {}).get("project_path") or self._project_path
            cfg = VerificationConfig.from_runtime_config(self._config, str(raw))
            engine = VerificationEngine(cfg)
            ctx = self._build_context(sprint_index=sprint_index, sprint=sprint, context=context, release_plan=release_plan, result=result)
            gate = str(ctx.get("verification_gate", "all"))
            report = await engine.run(gate, str(raw), context=ctx)
            gov = VerificationReportAdapter.to_governance_report(report)
            context["verification_review_report"] = gov.to_dict()
            context["verification_context"] = ctx
            logger.info("验证 Review gate: sprint={} status={} violations error={} warning={}", sprint.name, getattr(result.status, "value", result.status), sum(1 for v in gov.violations if v.severity == "error"), sum(1 for v in gov.violations if v.severity == "warning"))
            for v in gov.violations[:30]:
                log = logger.warning if v.severity != "error" else logger.error
                log("  [{}] {}", v.rule_id, v.message)
            await self._emit_gate_summary("review", sprint, gov)
        except Exception as e:
            logger.warning("Verification review gate skipped: {}", e)
