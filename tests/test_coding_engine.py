"""
编码引擎测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sprintcycle.coding_engine import (
    CodingEngine,
    CodingStrategy,
    CursorStrategy,
    LLMStrategy,
    ClaudeStrategy,
    CodingEngineResult,
)
from sprintcycle.config import CodingConfig, CodingLLMConfig, CodingClaudeConfig


class TestCodingEngineResult:
    """CodingEngineResult 测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = CodingEngineResult(
            success=True,
            content="def foo(): pass",
            metadata={"engine": "llm"},
        )
        assert result.success
        assert result.content == "def foo(): pass"
        assert result.error is None

    def test_failure_result(self):
        """测试失败结果"""
        result = CodingEngineResult(
            success=False,
            error="API key invalid",
        )
        assert not result.success
        assert result.error == "API key invalid"
        assert result.metadata is not None

    def test_default_metadata(self):
        """测试默认元数据"""
        result = CodingEngineResult(success=True)
        assert result.metadata == {}


class TestCursorStrategy:
    """Cursor 策略测试"""

    @pytest.fixture
    def cursor_strategy(self):
        """创建 Cursor 策略"""
        return CursorStrategy()

    def test_is_available_without_cursor(self, cursor_strategy):
        """测试 Cursor 不可用"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert not cursor_strategy.is_available()


class TestLLMStrategy:
    """LLM 策略测试"""

    @pytest.fixture
    def llm_config(self):
        """创建 LLM 配置"""
        return CodingLLMConfig(
            provider="deepseek",
            model="deepseek-chat",
            api_key="test-key",
            api_base="https://api.deepseek.com",
        )

    @pytest.fixture
    def llm_strategy(self, llm_config):
        """创建 LLM 策略"""
        return LLMStrategy(llm_config)

    def test_is_available_with_key(self, llm_strategy):
        """测试有 API Key 时可用"""
        assert llm_strategy.is_available()

    def test_is_available_without_key(self, llm_config):
        """测试无 API Key 时不可用"""
        llm_config.api_key = ""
        strategy = LLMStrategy(llm_config)
        assert not strategy.is_available()

    @pytest.mark.asyncio
    async def test_generate_code_success(self, llm_strategy):
        """测试成功生成代码"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="def foo(): pass"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        llm_strategy._client = mock_client

        result = await llm_strategy.generate_code("写一个函数")
        assert "def foo(): pass" in result

    @pytest.mark.asyncio
    async def test_generate_code_with_context(self, llm_strategy):
        """测试带上下文生成"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="class Foo: pass"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        llm_strategy._client = mock_client

        context = {"language": "python", "style": "pep8"}
        await llm_strategy.generate_code("写一个类", context=context)
        # 验证上下文被包含在消息中
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert any("上下文" in str(m) for m in messages)


class TestClaudeStrategy:
    """Claude 策略测试"""

    @pytest.fixture
    def claude_config(self):
        """创建 Claude 配置"""
        return CodingClaudeConfig(
            model="claude-3-5-sonnet",
            api_key="test-key",
        )

    @pytest.fixture
    def claude_strategy(self, claude_config):
        """创建 Claude 策略"""
        return ClaudeStrategy(claude_config)

    def test_is_available_with_key(self, claude_strategy):
        """测试有 API Key 时可用"""
        assert claude_strategy.is_available()

    def test_is_available_without_key(self, claude_config):
        """测试无 API Key 时不可用"""
        claude_config.api_key = ""
        strategy = ClaudeStrategy(claude_config)
        assert not strategy.is_available()

    @pytest.mark.asyncio
    async def test_generate_code_success(self, claude_strategy):
        """测试成功生成代码"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="def bar(): pass")]
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        claude_strategy._client = mock_client

        result = await claude_strategy.generate_code("写一个函数")
        assert "def bar(): pass" in result


class TestCodingEngineFactory:
    """编码引擎工厂测试"""

    def test_create_cursor_engine(self):
        """测试创建 Cursor 引擎"""
        config = CodingConfig(engine="cursor")
        engine = CodingEngine.from_config(config)
        assert engine.engine_name == "cursor"

    def test_create_llm_engine(self):
        """测试创建 LLM 引擎"""
        config = CodingConfig(
            engine="llm",
            llm=CodingLLMConfig(
                provider="deepseek",
                model="deepseek-chat",
                api_key="test-key",
            ),
        )
        engine = CodingEngine.from_config(config)
        assert engine.engine_name == "llm"

    def test_create_claude_engine(self):
        """测试创建 Claude 引擎"""
        config = CodingConfig(
            engine="claude",
            claude=CodingClaudeConfig(api_key="test-key"),
        )
        engine = CodingEngine.from_config(config)
        assert engine.engine_name == "claude"

    def test_unsupported_engine(self):
        """测试不支持的引擎"""
        config = CodingConfig(engine="unknown")
        with pytest.raises(ValueError, match="不支持"):
            CodingEngine.from_config(config)

    def test_llm_engine_missing_config(self):
        """测试 LLM 引擎缺少配置"""
        config = CodingConfig(engine="llm")
        with pytest.raises(ValueError, match="coding.llm"):
            CodingEngine.from_config(config)

    def test_claude_engine_missing_config(self):
        """测试 Claude 引擎缺少配置"""
        config = CodingConfig(engine="claude")
        with pytest.raises(ValueError, match="coding.claude"):
            CodingEngine.from_config(config)

    def test_create_quick(self):
        """测试快速创建方法"""
        engine = CodingEngine.create("llm", api_key="test-key")
        assert engine.engine_name == "llm"
        assert engine.is_available()

    def test_create_claude_quick(self):
        """测试快速创建 Claude"""
        engine = CodingEngine.create("claude", api_key="test-key", model="claude-3-5-sonnet")
        assert engine.engine_name == "claude"


class TestCodingEngineOperations:
    """编码引擎操作测试"""

    @pytest.fixture
    def llm_engine(self):
        """创建 LLM 引擎"""
        config = CodingConfig(
            engine="llm",
            llm=CodingLLMConfig(
                provider="deepseek",
                model="deepseek-chat",
                api_key="test-key",
            ),
        )
        return CodingEngine.from_config(config)

    @pytest.mark.asyncio
    async def test_generate_code(self, llm_engine):
        """测试生成代码"""
        mock_strategy = MagicMock()
        mock_strategy.generate_code = AsyncMock(return_value="def test(): pass")
        mock_strategy.is_available = MagicMock(return_value=True)
        llm_engine._strategy = mock_strategy

        result = await llm_engine.generate_code("写一个测试函数")
        assert result.success
        assert "def test()" in result.content
        assert result.metadata["engine"] == "llm"

    @pytest.mark.asyncio
    async def test_generate_code_failure(self, llm_engine):
        """测试生成代码失败"""
        mock_strategy = MagicMock()
        mock_strategy.generate_code = AsyncMock(side_effect=Exception("API error"))
        mock_strategy.is_available = MagicMock(return_value=True)
        llm_engine._strategy = mock_strategy

        result = await llm_engine.generate_code("写一个函数")
        assert not result.success
        assert "API error" in result.error

    @pytest.mark.asyncio
    async def test_review_code(self, llm_engine):
        """测试审查代码"""
        mock_strategy = MagicMock()
        mock_strategy.review_code = AsyncMock(return_value={"score": 8})
        mock_strategy.is_available = MagicMock(return_value=True)
        llm_engine._strategy = mock_strategy

        result = await llm_engine.review_code("print('hello')", "general")
        assert result.success
        assert result.content["score"] == 8

    @pytest.mark.asyncio
    async def test_explain_code(self, llm_engine):
        """测试解释代码"""
        mock_strategy = MagicMock()
        mock_strategy.explain_code = AsyncMock(return_value="This is a function")
        mock_strategy.is_available = MagicMock(return_value=True)
        llm_engine._strategy = mock_strategy

        result = await llm_engine.explain_code("def foo(): pass")
        assert result.success
        assert "function" in result.content

    def test_is_available(self, llm_engine):
        """测试检查可用性"""
        mock_strategy = MagicMock()
        mock_strategy.is_available = MagicMock(return_value=True)
        llm_engine._strategy = mock_strategy
        assert llm_engine.is_available()


class TestCodingEngineRegistry:
    """编码引擎注册表测试"""

    def test_list_available_engines(self):
        """测试列出可用引擎"""
        engines = CodingEngine.list_available_engines()
        assert "cursor" in engines
        assert "llm" in engines
        assert "claude" in engines

    def test_register_custom_engine(self):
        """测试注册自定义引擎"""
        class CustomStrategy(CodingStrategy):
            async def generate_code(self, prompt, context=None):
                return "custom code"

            async def review_code(self, code, review_type="general"):
                return {"score": 10}

            async def explain_code(self, code):
                return "explanation"

            def is_available(self):
                return True

        CodingEngine.register_engine("custom", CustomStrategy)
        engines = CodingEngine.list_available_engines()
        assert "custom" in engines

    def test_register_invalid_engine(self):
        """测试注册无效引擎"""
        with pytest.raises(TypeError, match="CodingStrategy"):
            CodingEngine.register_engine("invalid", str)
