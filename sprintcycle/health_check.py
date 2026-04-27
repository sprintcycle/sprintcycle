#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SprintCycle Health Check Module"""
import os, sys
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class HealthStatus:
    name: str
    status: str  # ok, warning, error
    message: str = ""
    details: Dict = field(default_factory=dict)

@dataclass
class HealthReport:
    project_path: str
    timestamp: datetime
    checks: List[HealthStatus] = field(default_factory=list)
    overall_status: str = "ok"

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == "ok")

    @property
    def warnings(self) -> int:
        return sum(1 for c in self.checks if c.status == "warning")

    @property
    def errors(self) -> int:
        return sum(1 for c in self.checks if c.status == "error")

    def to_dict(self) -> Dict:
        return {
            "project_path": self.project_path,
            "timestamp": self.timestamp.isoformat(),
            "checks": [{"name": c.name, "status": c.status, "message": c.message} for c in self.checks],
            "overall_status": self.overall_status,
            "summary": {"passed": self.passed, "warnings": self.warnings, "errors": self.errors}
        }

class ProjectHealthChecker:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()

    def check_all(self) -> HealthReport:
        report = HealthReport(project_path=str(self.project_path), timestamp=datetime.now())
        report.checks.append(self._check_structure())
        report.checks.append(self._check_dependencies())
        report.checks.append(self._check_config())
        report.checks.append(self._check_files())
        report.checks.append(self._check_git())
        if report.errors > 0:
            report.overall_status = "error"
        elif report.warnings > 0:
            report.overall_status = "warning"
        return report

    def _check_structure(self) -> HealthStatus:
        required = ["README.md", ".gitignore"]
        missing = [f for f in required if not (self.project_path / f).exists()]
        if missing:
            return HealthStatus(name="structure", status="warning", message=f"Missing: {missing}")
        return HealthStatus(name="structure", status="ok", message="OK")

    def _check_dependencies(self) -> HealthStatus:
        has_req = (self.project_path / "requirements.txt").exists()
        has_pyproject = (self.project_path / "pyproject.toml").exists()
        has_pkg = (self.project_path / "package.json").exists()
        if not (has_req or has_pyproject or has_pkg):
            return HealthStatus(name="dependencies", status="warning", message="No dependency file")
        return HealthStatus(name="dependencies", status="ok", message="OK")

    def _check_config(self) -> HealthStatus:
        config_files = ["config.yaml", "pyproject.toml"]
        for name in config_files:
            fp = self.project_path / name
            if fp.exists():
                try:
                    content = fp.read_text()
                    if name.endswith(".yaml"):
                        import yaml; yaml.safe_load(content)
                    elif name.endswith(".toml"):
                        pass
                except Exception as e:
                    return HealthStatus(name="config", status="error", message=str(e)[:50])
        return HealthStatus(name="config", status="ok", message="OK")

    def _check_files(self) -> HealthStatus:
        py_files = list(self.project_path.rglob("*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f) and "venv" not in str(f)]
        return HealthStatus(name="files", status="ok", message=f"Found {len(py_files)} files")

    def _check_git(self) -> HealthStatus:
        if not (self.project_path / ".git").exists():
            return HealthStatus(name="git", status="warning", message="Not a git repo")
        return HealthStatus(name="git", status="ok", message="OK")

    def quick_check(self) -> Dict:
        return self.check_all().to_dict()

def quick_health_check(project_path: str) -> Dict:
    return ProjectHealthChecker(project_path).quick_check()
