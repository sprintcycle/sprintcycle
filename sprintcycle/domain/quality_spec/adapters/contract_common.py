from typing import Any, List

from ..reports.finding import Finding
from ..reports.report import Report


class ContractAdapterBase:
    name: str = "contract-base"

    def normalize_contract_output(self, output: Any, gate: str) -> Report:
        report = Report(gate=gate, passed=True, source=self.name)
        if isinstance(output, list):
            for item in output:
                if isinstance(item, Finding):
                    report.add_finding(item)
        elif isinstance(output, Finding):
            report.add_finding(output)
        report.recompute_summary()
        return report

    def parse_contract_stdout(self, stdout: str) -> List[Finding]:
        findings: List[Finding] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if "error" in line.lower():
                findings.append(Finding(rule_id=f"{self.name}:stdout", severity="error", message=line))
            elif "warning" in line.lower():
                findings.append(Finding(rule_id=f"{self.name}:stdout", severity="warning", message=line))
        return findings

    def parse_contract_stderr(self, stderr: str) -> List[Finding]:
        return self.parse_contract_stdout(stderr)

    def build_contract_finding(self, rule_id: str, message: str, severity: str = "error") -> Finding:
        return Finding(rule_id=rule_id, severity=severity, message=message)
