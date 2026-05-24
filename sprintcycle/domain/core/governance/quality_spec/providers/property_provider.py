from typing import Any, Dict, List

from ..reports.finding import Finding
from ..reports.report import Report


class HypothesisProvider:
    name = "hypothesis"

    async def run_property_tests(self, context: Dict[str, Any]) -> Report:
        report = Report(gate="verification", passed=True, source=self.name)
        targets = self.discover_test_targets(context)
        if not targets:
            report.add_finding(
                Finding(
                    rule_id="hypothesis:no-targets",
                    severity="info",
                    message="no property test targets discovered",
                )
            )
        else:
            for test_file in targets:
                sub = await self.run_test_file(test_file, context)
                report.extend_findings(sub.findings)
        report.recompute_summary()
        return report

    def discover_test_targets(self, context: Dict[str, Any]) -> List[str]:
        return list(context.get("property_test_files") or [])

    async def run_test_file(self, test_file: str, context: Dict[str, Any]) -> Report:
        report = Report(gate="verification", passed=True, source=self.name)
        report.add_finding(
            Finding(
                rule_id="hypothesis:stub",
                severity="info",
                message=f"property test stub for {test_file}",
                location={"file": test_file},
            )
        )
        report.recompute_summary()
        return report

    def parse_hypothesis_stats(self, output: str) -> Dict[str, Any]:
        return {"raw": output}
