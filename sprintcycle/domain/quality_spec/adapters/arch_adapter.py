from typing import Any, Dict

from ..reports.finding import Finding
from ..reports.report import Report


class ArchAdapter:
    name = "arch"

    async def analyze_architecture(self, context: Dict[str, Any]) -> Report:
        report = Report(gate="review", passed=True, source=self.name)
        report.add_finding(
            Finding(
                rule_id="arch:stub",
                severity="info",
                message="arch adapter stub",
            )
        )
        report.recompute_summary()
        return report
