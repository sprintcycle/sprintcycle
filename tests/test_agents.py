"""
Tests for Agent Base, Bug Models, Patterns, and Traceback Parser modules.

Coverage targets:
- sprintcycle/execution/agents/base.py
- sprintcycle/execution/agents/bug_models.py
- sprintcycle/execution/agents/patterns.py
- sprintcycle/execution/agents/traceback_parser.py
"""

import pytest
from datetime import datetime

from sprintcycle.execution.agents.base import (
    AgentType,
    AgentConfig,
    AgentContext,
    AgentResult,
    AgentExecutor,
)
from sprintcycle.execution.agents.bug_models import (
    BugReport,
    Severity,
    ErrorCategory,
    Location,
    FixSuggestion,
    FixResult,
    AnalysisRequest,
    StackFrame,
    ParsedTraceback,
)
from sprintcycle.execution.agents.patterns import ROOT_CAUSE_PATTERNS


class TestAgentContext:
    """AgentContext tests"""

    def test_basic_creation(self):
        ctx = AgentContext(prd_id="test", sprint_name="Sprint 1")
        assert ctx.prd_id == "test"
        assert ctx.sprint_name == "Sprint 1"
        assert ctx.iteration == 1
        assert isinstance(ctx.created_at, datetime)

    def test_add_feedback(self):
        ctx = AgentContext()
        ctx.add_feedback("first feedback")
        assert "first feedback" in ctx.feedback_history
        ctx.add_feedback("second feedback")
        assert len(ctx.feedback_history) == 2

    def test_get_dependency(self):
        ctx = AgentContext()
        ctx.dependencies["key1"] = "value1"
        assert ctx.get_dependency("key1") == "value1"
        assert ctx.get_dependency("nonexistent", "default") == "default"


class TestAgentResult:
    """AgentResult tests"""

    def test_basic_creation(self):
        result = AgentResult(success=True, output="test output")
        assert result.success is True
        assert result.output == "test output"
        assert result.error is None

    def test_add_artifact(self):
        result = AgentResult(success=True)
        result.add_artifact("file", "output.txt")
        assert result.artifacts["file"] == "output.txt"

    def test_add_metric(self):
        result = AgentResult(success=True)
        result.add_metric("duration", 1.5)
        assert result.metrics["duration"] == 1.5

    def test_set_feedback(self):
        result = AgentResult(success=True)
        result.set_feedback("well done")
        assert result.feedback == "well done"

    def test_from_error(self):
        result = AgentResult.from_error("something went wrong", AgentType.CODER)
        assert result.success is False
        assert result.error == "something went wrong"
        assert result.agent_type == AgentType.CODER

    def test_timestamp_default(self):
        result = AgentResult(success=True)
        assert isinstance(result.timestamp, datetime)

    def test_retry_count_default(self):
        result = AgentResult(success=True)
        assert result.retry_count == 0


class TestAgentConfig:
    """AgentConfig tests"""

    def test_default_values(self):
        config = AgentConfig()
        assert config.llm_provider == "openai"
        assert config.model == "gpt-4"
        assert config.max_retries == 3
        assert config.timeout == 300

    def test_custom_values(self):
        config = AgentConfig(
            llm_provider="anthropic",
            model="claude-3",
            max_retries=5,
        )
        assert config.llm_provider == "anthropic"
        assert config.model == "claude-3"
        assert config.max_retries == 5


class TestBugReport:
    """BugReport tests"""

    def test_basic_creation(self):
        report = BugReport(
            error_type="ValueError",
            error_message="invalid value",
        )
        assert report.error_type == "ValueError"
        assert report.error_message == "invalid value"
        assert report.severity == Severity.MEDIUM  # default

    def test_to_summary(self):
        report = BugReport(
            error_type="ValueError",
            error_message="invalid value here",
            severity=Severity.HIGH,
        )
        summary = report.to_summary()
        assert "ValueError" in summary
        assert "HIGH" in summary

    def test_to_summary_with_location(self):
        loc = Location(file_path="main.py", line_number=10, column_number=5)
        report = BugReport(
            error_type="TypeError",
            error_message="unsupported",
            location=loc,
        )
        summary = report.to_summary()
        assert "main.py" in summary
        assert "TypeError" in summary


class TestLocation:
    """Location tests"""

    def test_basic_creation(self):
        loc = Location(file_path="test.py", line_number=42)
        assert loc.file_path == "test.py"
        assert loc.line_number == 42

    def test_str_representation(self):
        loc = Location(file_path="app.py", line_number=10, column_number=5)
        s = str(loc)
        assert "app.py" in s
        assert "10" in s


class TestErrorCategory:
    """ErrorCategory enum tests"""

    def test_all_categories_exist(self):
        assert ErrorCategory.SYNTAX == ErrorCategory.SYNTAX
        assert ErrorCategory.IMPORT == ErrorCategory.IMPORT
        assert ErrorCategory.TYPE == ErrorCategory.TYPE
        assert ErrorCategory.RUNTIME == ErrorCategory.RUNTIME
        assert ErrorCategory.UNKNOWN == ErrorCategory.UNKNOWN
        assert ErrorCategory.ATTRIBUTE == ErrorCategory.ATTRIBUTE
        assert ErrorCategory.NAME == ErrorCategory.NAME


class TestSeverity:
    """Severity enum tests"""

    def test_all_severities_exist(self):
        assert Severity.CRITICAL is not None
        assert Severity.HIGH is not None
        assert Severity.MEDIUM is not None
        assert Severity.LOW is not None
        assert Severity.INFO is not None


class TestFixSuggestion:
    """FixSuggestion tests"""

    def test_basic_creation(self):
        suggestion = FixSuggestion(
            old_code="old_code",
            new_code="new_code",
            explanation="fix the bug",
        )
        assert suggestion.old_code == "old_code"
        assert suggestion.new_code == "new_code"
        assert suggestion.explanation == "fix the bug"


class TestFixResult:
    """FixResult tests"""

    def test_basic_creation(self):
        result = FixResult(
            success=True,
            file_path="main.py",
            diff="+ line",
        )
        assert result.success is True
        assert result.file_path == "main.py"


class TestAnalysisRequest:
    """AnalysisRequest tests"""

    def test_basic_creation(self):
        req = AnalysisRequest(
            error_log="error traceback",
            language="python",
        )
        assert req.error_log == "error traceback"
        assert req.language == "python"


class TestStackFrame:
    """StackFrame tests"""

    def test_basic_creation(self):
        frame = StackFrame(
            file_path="test.py",
            line_number=10,
            function_name="test_func",
        )
        assert frame.file_path == "test.py"
        assert frame.line_number == 10
        assert frame.function_name == "test_func"


class TestParsedTraceback:
    """ParsedTraceback tests"""

    def test_basic_creation(self):
        parsed = ParsedTraceback()
        assert parsed.error_type == ""
        assert parsed.error_message == ""
        assert len(parsed.frames) == 0

    def test_add_frame(self):
        parsed = ParsedTraceback()
        frame = StackFrame(file_path="main.py", line_number=5)
        parsed.frames.append(frame)
        assert len(parsed.frames) == 1


class TestRootCausePatterns:
    """ROOT_CAUSE_PATTERNS tests"""

    def test_patterns_loaded(self):
        assert isinstance(ROOT_CAUSE_PATTERNS, dict)
        assert len(ROOT_CAUSE_PATTERNS) > 0


class TestAgentExecutor:
    """AgentExecutor abstract base class tests"""

    def test_abstract_class(self):
        with pytest.raises(TypeError):
            AgentExecutor()
