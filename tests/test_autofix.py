"""SprintCycle AutoFix 模块测试"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from sprintcycle.autofix import (
    FixResult, FixSession, AutoFixEngine
)
from sprintcycle.scanner import Issue, IssueType, IssueSeverity

class TestFixResult:
    def test_result_success(self):
        issue = Issue(IssueType.SYNTAX_ERROR, IssueSeverity.CRITICAL, "test.py", message="Error")
        result = FixResult(success=True, issue=issue, fix_content="fixed code")
        assert result.success is True
        assert result.issue == issue
        assert result.fix_content == "fixed code"
    
    def test_result_with_error(self):
        issue = Issue(IssueType.SYNTAX_ERROR, IssueSeverity.CRITICAL, "test.py")
        result = FixResult(success=False, issue=issue, error="Syntax error")
        assert result.success is False
        assert result.error == "Syntax error"

class TestFixSession:
    def test_session_creation(self):
        session = FixSession(project_path="/test", start_time=datetime.now())
        assert session.project_path == "/test"
        assert len(session.fixes) == 0
        assert len(session.rollbacks) == 0

class TestAutoFixEngine:
    def test_engine_init(self, tmp_path):
        engine = AutoFixEngine(str(tmp_path))
        assert engine.project_path == tmp_path.resolve()
    
    def test_engine_with_api_key(self, tmp_path):
        engine = AutoFixEngine(str(tmp_path), api_key="test-key")
        assert engine.api_key == "test-key"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
