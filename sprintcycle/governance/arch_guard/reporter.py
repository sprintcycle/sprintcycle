from __future__ import annotations

from typing import List

from .model import GuardReport
from ..report import GovernanceReport, GovernanceViolation


class GovernanceReportAdapter:
    @staticmethod
    def to_governance_report(report: GuardReport) -> GovernanceReport:
        violations: List[GovernanceViolation] = []
        for f in report.findings:
            violations.append(
                GovernanceViolation(
                    rule_id=f.rule_id,
                    severity=f.severity,
                    message=f.message,
                    location=dict(f.location),
                )
            )
        return GovernanceReport(
            gate=report.gate,
            violations=violations,
            metadata=dict(report.metadata),
        )
