"""SprintCycle Diagnostic 模块测试"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from sprintcycle.diagnostic import (
    DiagnosticStatus, ProblemType, DiagnosticIssue, DiagnosticResult,
    ServiceChecker, APIChecker, DatabaseChecker, LogAnalyzer,
    DiagnosticEngine, quick_diagnose
)


class TestEnums:
    def test_diagnostic_status(self):
        assert DiagnosticStatus.PASS.value == "pass"
        assert DiagnosticStatus.WARN.value == "warn"
        assert DiagnosticStatus.FAIL.value == "fail"
    
    def test_problem_type(self):
        assert ProblemType.SERVICE.value == "service"
        assert ProblemType.API.value == "api"
        assert ProblemType.FULL.value == "full"


class TestDiagnosticIssue:
    def test_issue_creation(self):
        issue = DiagnosticIssue(
            type="service",
            severity=DiagnosticStatus.WARN,
            location="localhost:3000",
            description="Service not running",
            suggestion="Start service"
        )
        assert issue.type == "service"
        assert issue.severity == DiagnosticStatus.WARN


class TestDiagnosticResult:
    def test_result_creation(self):
        result = DiagnosticResult(
            success=True,
            status=DiagnosticStatus.PASS,
            issues=[],
            report_path="/tmp/report.json",
            summary="All checks passed"
        )
        assert result.success is True
        assert result.status == DiagnosticStatus.PASS


class TestServiceChecker:
    def test_check_port_failure(self):
        result = ServiceChecker.check_port("127.0.0.1", 59999, timeout=0.5)
        assert result is False
    
    def test_check_services(self):
        checker = ServiceChecker()
        issues = checker.check_services("/tmp")
        assert isinstance(issues, list)


class TestAPIChecker:
    def test_test_endpoint_invalid_url(self):
        result = APIChecker.test_endpoint("http://invalid.url.localtest")
        assert result["success"] is False
    
    def test_test_api(self):
        checker = APIChecker()
        issues = checker.test_api("https://httpbin.org")
        assert isinstance(issues, list)


class TestDatabaseChecker:
    @pytest.fixture
    def project_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_check_database_sqlite(self, project_dir):
        import sqlite3
        db_path = Path(project_dir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        
        checker = DatabaseChecker()
        issues = checker.check_database(project_dir)
        assert isinstance(issues, list)


class TestLogAnalyzer:
    @pytest.fixture
    def project_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_analyze_logs_no_logs(self, project_dir):
        analyzer = LogAnalyzer()
        issues = analyzer.analyze_logs(project_dir)
        assert len(issues) == 0
    
    def test_analyze_logs_with_errors(self, project_dir):
        log_dir = Path(project_dir) / "logs"
        log_dir.mkdir()
        log_file = log_dir / "app.log"
        with open(log_file, "w") as f:
            f.write("INFO: Application started\n")
            f.write("ERROR: Database connection failed\n")
        
        analyzer = LogAnalyzer()
        issues = analyzer.analyze_logs(project_dir)
        assert len(issues) >= 1


class TestDiagnosticEngine:
    @pytest.fixture
    def project_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_engine_initialization(self, project_dir):
        engine = DiagnosticEngine(project_dir)
        assert engine.project_path == Path(project_dir)
    
    def test_run_full_diagnostic(self, project_dir):
        engine = DiagnosticEngine(project_dir)
        result = engine.run("full")
        assert isinstance(result, DiagnosticResult)
    
    def test_run_service_diagnostic(self, project_dir):
        engine = DiagnosticEngine(project_dir)
        result = engine.run("service")
        assert isinstance(result, DiagnosticResult)
    
    def test_run_database_diagnostic(self, project_dir):
        engine = DiagnosticEngine(project_dir)
        result = engine.run("database")
        assert isinstance(result, DiagnosticResult)
    
    def test_run_log_diagnostic(self, project_dir):
        engine = DiagnosticEngine(project_dir)
        result = engine.run("log")
        assert isinstance(result, DiagnosticResult)
    
    def test_generate_fix_suggestions(self, project_dir):
        engine = DiagnosticEngine(project_dir)
        issues = [
            DiagnosticIssue("service", DiagnosticStatus.FAIL, "localhost", "Service not running"),
            DiagnosticIssue("api", DiagnosticStatus.WARN, "/api", "API warning")
        ]
        suggestions = engine._generate_fix_suggestions(issues)
        assert len(suggestions) == 2
    
    def test_generate_summary(self, project_dir):
        engine = DiagnosticEngine(project_dir)
        summary_pass = engine._generate_summary([], DiagnosticStatus.PASS)
        assert "通过" in summary_pass


class TestQuickDiagnose:
    @pytest.fixture
    def project_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_quick_diagnose(self, project_dir):
        result = quick_diagnose(project_dir, "full")
        assert isinstance(result, DiagnosticResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
