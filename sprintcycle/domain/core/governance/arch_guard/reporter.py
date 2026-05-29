from __future__ import annotations

from sprintcycle.domain.core.governance.common.model import Finding as GuardFinding, Report as GuardReport


class GovernanceReportAdapter:
    @staticmethod
    def to_governance_report(report: GuardReport) -> GuardReport:
        return report

    @staticmethod
    def to_guard_report(report: GuardReport) -> GuardReport:
        return report

    @staticmethod
    def from_legacy_violations(gate: str, violations, metadata=None) -> GuardReport:
        findings = [
            GuardFinding(
                rule_id=v.rule_id,
                severity=v.severity,
                message=v.message,
                location=dict(getattr(v, "location", {}) or {}),
                metadata=dict(getattr(v, "metadata", {}) or {}),
            )
            for v in violations
        ]
        return GuardReport(gate=gate, findings=findings, metadata=dict(metadata or {}))
