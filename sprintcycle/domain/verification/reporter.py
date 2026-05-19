from __future__ import annotations

from typing import List

from .model import VerificationFinding, VerificationReport

from ...governance.report import GovernanceReport, GovernanceViolation


class VerificationReportAdapter:
    @staticmethod
    def to_governance_report(report: VerificationReport) -> GovernanceReport:
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
            gate=str(report.gate),
            violations=violations,
            metadata=dict(report.metadata),
        )
