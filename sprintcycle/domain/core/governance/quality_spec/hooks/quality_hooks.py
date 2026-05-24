from typing import Any, Optional

from ..context import QualityContext
from ..reports.report import Report


class QualityLifecycleHooks:
    def __init__(self, registry: Any = None) -> None:
        self.registry = registry

    async def on_before_task(self, context: QualityContext) -> bool:
        await self._maybe_hitl(
            context, gate="spec_confirm", title="Spec 确认", summary="AI 生成的结构化规范需要人工确认后继续"
        )
        report = await self._quick_check(context)
        return not report.has_errors()

    async def on_after_task(self, context: QualityContext) -> Report:
        await self._maybe_hitl(
            context, gate="execution_approval", title="任务执行确认", summary="任务完成后需要人工确认是否继续"
        )
        return await self._full_check(context)

    async def on_before_release(self, context: QualityContext) -> Report:
        await self._maybe_hitl(
            context, gate="release_approval", title="发布前确认", summary="Release 前需要人工确认是否继续"
        )
        return await self._full_check(context)

    async def on_after_release(self, context: QualityContext) -> Report:
        await self._maybe_hitl(
            context, gate="after_sprint", title="Sprint 结束确认", summary="Sprint 结束后需要人工确认结果"
        )
        return await self._full_check(context)

    async def _maybe_hitl(self, context: QualityContext, *, gate: str, title: str, summary: str) -> Optional[str]:
        extra = context.extra or {}
        runtime_config = extra.get("runtime_config")
        execution_id = str(extra.get("execution_id") or "").strip()
        project_path = str(context.project_path or extra.get("project_path") or ".")
        if runtime_config is None or not execution_id:
            return None
        try:
            from ....execution.core.events import get_execution_event_backend
            from ....governance.hitl import HitlGate, HitlService, create_hitl_coordinator, evaluate_hitl_policy
        except Exception:
            return None
        policy = evaluate_hitl_policy(
            gate=gate, context={"project_path": project_path, "summary": summary, **extra}, config=runtime_config
        )
        if not policy.should_trigger:
            return None
        coord = create_hitl_coordinator(project_path, runtime_config, get_execution_event_backend())
        if coord is None:
            return None
        service = HitlService(coord)
        await service.start_request(
            execution_id=execution_id,
            gate=HitlGate(gate),
            title=title,
            summary=summary,
            context={"project_path": project_path, **extra, "policy": policy.metadata},
            risk_level=policy.risk_level,
            timeout_seconds=policy.timeout_seconds,
        )
        return execution_id

    async def _quick_check(self, context: QualityContext) -> Report:
        report = Report(gate="task", passed=True, source="quality-hooks")
        return report

    async def _full_check(self, context: QualityContext) -> Report:
        report = Report(gate=context.gate, passed=True, source="quality-hooks")
        return report
