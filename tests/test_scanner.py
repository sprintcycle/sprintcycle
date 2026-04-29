"""SprintCycle Scanner 模块测试"""
import pytest
import tempfile
from pathlib import Path
from sprintcycle.scanner import (
    IssueSeverity, IssueType, Issue, ScanResult,
    ProjectScanner
)

class TestIssueSeverity:
    def test_values(self):
        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.WARNING.value == "warning"
        assert IssueSeverity.INFO.value == "info"

class TestIssueType:
    def test_values(self):
        assert IssueType.MISSING_FILE.value == "missing_file"

class TestIssue:
    def test_issue_creation(self):
        issue = Issue(issue_type=IssueType.MISSING_FILE, severity=IssueSeverity.WARNING, file_path="test.py", line=10, message="Missing file")
        assert issue.issue_type == IssueType.MISSING_FILE
    
    def test_to_dict(self):
        issue = Issue(issue_type=IssueType.SYNTAX_ERROR, severity=IssueSeverity.CRITICAL, file_path="broken.py", line=1, message="Syntax error")
        d = issue.to_dict()
        assert d["type"] == "syntax_error"

class TestScanResult:
    def test_scan_result_creation(self):
        result = ScanResult(project_path="/test/project")
        assert result.project_path == "/test/project"
    
    def test_critical_count(self):
        issues = [Issue(IssueType.SYNTAX_ERROR, IssueSeverity.CRITICAL, "f1.py")]
        result = ScanResult(project_path="/test", issues=issues)
        assert result.critical_count == 1

class TestProjectScanner:
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_scanner_init(self, temp_project):
        scanner = ProjectScanner(temp_project)
        assert scanner.project_path == Path(temp_project).resolve()
    
    def test_scan_empty_project(self, temp_project):
        scanner = ProjectScanner(temp_project)
        result = scanner.scan()
        assert isinstance(result, ScanResult)
    
    def test_scan_with_python_files(self, temp_project):
        test_file = Path(temp_project) / "main.py"
        test_file.write_text("print('hello')")
        scanner = ProjectScanner(temp_project)
        result = scanner.scan()
        assert result.scanned_files >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
