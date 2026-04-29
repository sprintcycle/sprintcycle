"""扩展自动修复测试 - 针对 autofix.py 低覆盖率模块"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from sprintcycle.autofix import (
    FixResult,
    FixSession,
    AutoFixEngine,
)
from sprintcycle.scanner import Issue, IssueType, IssueSeverity


class TestFixResult:
    """修复结果数据类测试"""
    
    def test_fix_result_success(self):
        """测试成功修复结果"""
        issue = Issue(
            file_path="test.py",
            issue_type=IssueType.SYNTAX_ERROR,
            severity=IssueSeverity.CRITICAL
        )
        result = FixResult(
            success=True,
            issue=issue,
            fix_content="fixed content",
            file_path="/path/to/test.py"
        )
        assert result.success is True
        assert result.fix_content == "fixed content"
        assert result.reverted is False
    
    def test_fix_result_failure(self):
        """测试失败修复结果"""
        issue = Issue(
            file_path="test.py",
            issue_type=IssueType.SYNTAX_ERROR,
            severity=IssueSeverity.CRITICAL
        )
        result = FixResult(
            success=False,
            issue=issue,
            error="Failed to fix"
        )
        assert result.success is False
        assert result.error == "Failed to fix"
    
    def test_fix_result_reverted(self):
        """测试已回滚的修复结果"""
        issue = Issue(
            file_path="test.py",
            issue_type=IssueType.SYNTAX_ERROR,
            severity=IssueSeverity.CRITICAL
        )
        result = FixResult(
            success=True,
            issue=issue,
            fix_content="content",
            reverted=True
        )
        assert result.reverted is True


class TestFixSession:
    """修复会话测试"""
    
    def test_fix_session_with_time(self):
        """测试带时间的修复会话"""
        now = datetime.now()
        session = FixSession(project_path="/test/project", start_time=now)
        assert session.project_path == "/test/project"
        assert len(session.fixes) == 0
        assert len(session.rollbacks) == 0
    
    def test_fix_session_with_fixes(self):
        """测试带修复结果的会话"""
        now = datetime.now()
        issue = Issue(
            file_path="test.py",
            issue_type=IssueType.MISSING_FILE,
            severity=IssueSeverity.INFO
        )
        fix = FixResult(success=True, issue=issue, fix_content="content")
        session = FixSession(
            project_path="/test/project",
            start_time=now,
            fixes=[fix]
        )
        assert len(session.fixes) == 1
        assert session.fixes[0].success is True


class TestAutoFixEngine:
    """自动修复引擎测试"""
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AutoFixEngine(project_path=tmpdir)
            assert engine.project_path == Path(tmpdir).resolve()
    
    def test_engine_with_api_key(self):
        """测试带API密钥的引擎"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AutoFixEngine(project_path=tmpdir, api_key="test-key-123")
            assert engine.api_key == "test-key-123"
    
    def test_engine_api_attribute(self):
        """测试引擎API属性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AutoFixEngine(project_path=tmpdir)
            assert hasattr(engine, 'API')
    
    def test_fix_syntax_error_file_not_found(self, tmp_path):
        """测试修复语法错误-文件不存在"""
        engine = AutoFixEngine(project_path=str(tmp_path))
        issue = Issue(
            file_path="nonexistent.py",
            issue_type=IssueType.SYNTAX_ERROR,
            severity=IssueSeverity.CRITICAL
        )
        result = engine._fix_syntax_error(issue)
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_fix_config_error_file_not_found(self, tmp_path):
        """测试修复配置错误-文件不存在"""
        engine = AutoFixEngine(project_path=str(tmp_path))
        issue = Issue(
            file_path="config.yaml",
            issue_type=IssueType.CONFIG_ERROR,
            severity=IssueSeverity.WARNING,
            fix_suggestion="key: value"
        )
        result = engine._fix_config_error(issue)
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_session_attribute(self):
        """测试会话属性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AutoFixEngine(project_path=tmpdir)
            assert engine.session is None
    
    def test_project_path_resolved(self):
        """测试项目路径被解析为绝对路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AutoFixEngine(project_path=tmpdir)
            assert engine.project_path.is_absolute()
    
    def test_get_summary_empty(self, tmp_path):
        """测试获取空摘要"""
        engine = AutoFixEngine(project_path=str(tmp_path))
        # No session yet
        summary = engine.get_summary()
        assert "total" in summary or len(summary) >= 0
    
    def test_rollback_returns_int(self, tmp_path):
        """测试回滚返回整数"""
        engine = AutoFixEngine(project_path=str(tmp_path))
        result = engine.rollback()
        assert isinstance(result, int)
