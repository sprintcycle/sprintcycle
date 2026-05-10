from typing import Any, Dict
from .contract_common import ContractAdapterBase
from ..reports.finding import Finding
from ..reports.report import Report


class DealAdapter(ContractAdapterBase):
    name = "deal"

    async def check_contracts(self, context: Dict[str, Any]) -> Report:
        return await self.run_lint(context)

    async def run_lint(self, context: Dict[str, Any]) -> Report:
        report = Report(gate="review", passed=True, source=self.name)
        report.add_finding(Finding(
            rule_id="deal:stub",
            severity="info",
            message="deal adapter stub",
        ))
        report.recompute_summary()
        return report

    async def run_runtime_check(self, context: Dict[str, Any]) -> Report:
        return await self.run_lint(context)

    def parse_output(self, stdout: str, stderr: str) -> Report:
        report = Report(gate="review", passed=True, source=self.name)
        report.extend_findings(self.parse_contract_stdout(stdout))
        report.extend_findings(self.parse_contract_stderr(stderr))
        report.recompute_summary()
        return report
