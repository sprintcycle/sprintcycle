"""Diagnostics adapter implementation."""

from __future__ import annotations

from typing import Any


class DiagnosticAdapter:
    """Infrastructure adapter for diagnostics."""

    def __init__(self, project_path: str):
        self.project_path = project_path

    def diagnose(self, execution_id: str = "") -> Any:
        """Run diagnostics on the system or specific execution."""
        from sprintcycle.infrastructure.adapters.generic.observability.diagnostics.provider import ProjectDiagnostic
        from sprintcycle.domain.generic.interfaces.diagnostics import DiagnoseResult

        diag = ProjectDiagnostic(self.project_path)
        report = diag.diagnose(execution_id=execution_id)
        if isinstance(report, DiagnoseResult):
            return report.to_dict()
        if isinstance(report, dict):
            return {
                "success": report.get("success", True),
                "health_score": report.get("health_score", 0.0),
                "issues": report.get("issues", []),
                "coverage": report.get("coverage", 0.0),
                "complexity": report.get("complexity", {}),
                "duration": report.get("duration", 0.0),
            }
        return {
            "success": True,
            "health_score": getattr(report, "health_score", 0.0) if hasattr(report, "health_score") else 0.0,
            "issues": getattr(report, "issues", []) if hasattr(report, "issues") else [],
            "coverage": getattr(report, "coverage", 0.0) if hasattr(report, "coverage") else 0.0,
            "complexity": getattr(report, "complexity", {}) if hasattr(report, "complexity") else {},
            "duration": getattr(report, "duration", 0.0) if hasattr(report, "duration") else 0.0,
        }
