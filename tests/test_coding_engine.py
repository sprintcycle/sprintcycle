"""
Coding Engine Tests - 编码引擎测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sprintcycle.coding.engine import (
    CodingEngine,
    create_coding_engine,
)
from sprintcycle.coding.strategy import (
    CodingStrategy,
    CursorStrategy,
    LLMStrategy,
    ClaudeStrategy,
)
from sprintcycle.coding.result import (
    CodingEngineResult,
    CodeReviewResult,
    CodeFixResult,
)
from sprintcycle.config import CodingConfig, CodingLLMConfig


class TestCodingEngineResult:
    """CodingEngineResult 测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = CodingEngineResult(
            success=True,
            output="def foo(): pass",
            strategy="llm",
        )
        assert result.success
        assert result.output == "def foo(): pass"
        assert result.error is None

    def test_failure_result(self):
        """测试失败结果"""
        result = CodingEngineResult(
            success=False,
            error="API key invalid",
            strategy="llm",
        )
        assert not result.success
        assert result.error == "API key invalid"
        assert result.artifacts is not None

    def test_default_artifacts(self):
        """测试默认 artifacts"""
        result = CodingEngineResult(success=True)
        assert result.artifacts == {}


class TestCodeReviewResult:
    """CodeReviewResult 测试"""

    def test_review_result(self):
        """测试审查结果"""
        result = CodeReviewResult(
            file_path="test.py",
            issues=[],
            score=9.0,
            approved=True,
        )
        assert result.file_path == "test.py"
        assert result.score == 9.0
        assert result.approved is True


class TestCodeFixResult:
    """CodeFixResult 测试"""

    def test_fix_result(self):
        """测试修复结果"""
        result = CodeFixResult(
            original_code="def foo(): pass",
            fixed_code="def foo(): print('hello')",
            error_resolved=True,
        )
        assert result.original_code == "def foo(): pass"
        assert result.error_resolved is True


class TestCreateCodingEngine:
    """create_coding_engine 工厂函数测试"""

    def test_create_llm_engine(self):
        """测试创建 LLM 引擎"""
        engine = create_coding_engine(engine="llm", api_key="test-key")
        assert isinstance(engine, CodingEngine)
        assert engine.strategy_name == "llm"

    def test_create_cursor_engine(self):
        """测试创建 Cursor 引擎"""
        engine = create_coding_engine(engine="cursor")
        assert isinstance(engine, CodingEngine)
        assert engine.strategy_name == "cursor"

    def test_create_claude_engine(self):
        """测试创建 Claude 引擎"""
        engine = create_coding_engine(engine="claude", api_key="test-key")
        assert isinstance(engine, CodingEngine)
        assert engine.strategy_name == "claude"


class TestCodingEngine:
    """CodingEngine 主类测试"""

    def test_init_default(self):
        """测试默认初始化"""
        engine = CodingEngine()
        assert engine.strategy_name == "llm"

    def test_init_with_config(self):
        """测试带配置初始化"""
        config = CodingConfig(engine="cursor")
        engine = CodingEngine(config=config, strategy_name="cursor")
        assert engine.strategy_name == "cursor"

    def test_init_invalid_strategy(self):
        """测试无效策略"""
        with pytest.raises(ValueError, match="Unknown strategy"):
            CodingEngine(strategy_name="invalid")
