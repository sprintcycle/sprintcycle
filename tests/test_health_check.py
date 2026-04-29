"""SprintCycle Health Check 模块测试"""
import pytest
from datetime import datetime
from sprintcycle.health_check import (
    HealthStatus, HealthReport, ProjectHealthChecker
)

class TestHealthStatus:
    def test_status_creation(self):
        status = HealthStatus(name="test", status="ok", message="OK")
        assert status.name == "test"
        assert status.status == "ok"
        assert status.message == "OK"
    
    def test_status_with_details(self):
        status = HealthStatus(name="api", status="warning", message="Slow", details={"latency": 500})
        assert status.details["latency"] == 500

class TestHealthReport:
    def test_report_creation(self):
        report = HealthReport(project_path="/test", timestamp=datetime.now())
        assert report.project_path == "/test"
        assert len(report.checks) == 0
    
    def test_passed_warnings_errors(self):
        report = HealthReport(project_path="/test", timestamp=datetime.now(), checks=[
            HealthStatus(name="check1", status="ok"),
            HealthStatus(name="check2", status="warning"),
            HealthStatus(name="check3", status="error"),
        ])
        assert report.passed == 1
        assert report.warnings == 1
        assert report.errors == 1
    
    def test_to_dict(self):
        report = HealthReport(project_path="/test", timestamp=datetime.now())
        d = report.to_dict()
        assert d["project_path"] == "/test"
        assert "summary" in d

class TestProjectHealthChecker:
    def test_checker_init(self, tmp_path):
        checker = ProjectHealthChecker(str(tmp_path))
        assert checker.project_path == tmp_path.resolve()
    
    def test_check_all(self, tmp_path):
        checker = ProjectHealthChecker(str(tmp_path))
        report = checker.check_all()
        assert isinstance(report, HealthReport)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
