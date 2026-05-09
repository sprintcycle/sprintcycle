from typing import Any, Dict

from ..reports.finding import Finding
from ..reports.report import Report


class SecurityProvider:
    name = "security"

    async def scan(self, context: Dict[str, Any]) -> Report:
        report = Report(gate="review", passed=True, source=self.name)
        report.add_finding(Finding(
            rule_id="security:stub",
            severity="info",
            message="security provider stub",
        ))
        report.recompute_summary()
        return report
