from typing import Any, Dict

from ..reports.finding import Finding
from ..reports.report import Report


class BanditAdapter:
    name = "bandit"

    async def scan(self, context: Dict[str, Any]) -> Report:
        report = Report(gate="review", passed=True, source=self.name)
        report.add_finding(
            Finding(
                rule_id="bandit:stub",
                severity="info",
                message="bandit adapter stub",
            )
        )
        report.recompute_summary()
        return report
