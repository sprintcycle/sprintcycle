from typing import Any
from ..context import QualityContext
from ..reports.report import Report


class QualityLifecycleHooks:
    def __init__(self, registry: Any = None) -> None:
        self.registry = registry

    async def on_before_task(self, context: QualityContext) -> bool:
        report = await self._quick_check(context)
        return not report.has_errors()

    async def on_after_task(self, context: QualityContext) -> Report:
        return await self._full_check(context)

    async def on_before_release(self, context: QualityContext) -> Report:
        return await self._full_check(context)

    async def on_after_release(self, context: QualityContext) -> Report:
        return await self._full_check(context)

    async def _quick_check(self, context: QualityContext) -> Report:
        report = Report(gate="task", passed=True, source="quality-hooks")
        return report

    async def _full_check(self, context: QualityContext) -> Report:
        report = Report(gate=context.gate, passed=True, source="quality-hooks")
        return report
