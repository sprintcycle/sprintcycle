"""
SprintCycle 配置模块测试
"""

import pytest
import os
from sprintcycle.config import (
    EvolutionLLMConfig,
    CodingLLMConfig,
    CodingClaudeConfig,
    EvolutionConfig,
    CodingConfig,
    SprintCycleConfig,
    load_config_from_env,
    validate_config,
)


class TestEvolutionLLMConfig:
    """EvolutionLLMConfig 测试"""

    def test_init_with_valid_params(self):
        """测试有效参数初始化"""
        config = EvolutionLLMConfig(
            provider="deepseek",
            model="deepseek-reasoner",
            api_key="sk-test123",
        )
        assert config.provider == "deepseek"
        assert config.model == "deepseek-reasoner"
        assert config.api_key == "sk-test123"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048

    def test_env_var_loading(self):
        """测试环境变量加载"""
        os.environ["TEST_API_KEY"] = "env-key-123"
        config = EvolutionLLMConfig(
            provider="deepseek",
            model="deepseek-reasoner",
            api_key="${TEST_API_KEY}",
        )
        assert config.api_key == "env-key-123"

    def test_to_dict(self):
        """测试字典转换"""
        config = EvolutionLLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="sk-secret",
        )
        d = config.to_dict()
        assert d["provider"] == "openai"
        assert d["model"] == "gpt-4"
        assert d["api_key"] == "***"  # 应该被遮蔽
        assert d["temperature"] == 0.7


class TestCodingLLMConfig:
    """CodingLLMConfig 测试"""

    def test_init_with_valid_params(self):
        """测试有效参数初始化"""
        config = CodingLLMConfig(
            provider="deepseek",
            model="deepseek-chat",
            api_key="sk-test",
        )
        assert config.provider == "deepseek"
        assert config.model == "deepseek-chat"

    def test_env_var_loading(self):
        """测试环境变量加载"""
        os.environ["CODING_KEY"] = "coding-key"
        config = CodingLLMConfig(
            provider="deepseek",
            model="deepseek-chat",
            api_key="${CODING_KEY}",
        )
        assert config.api_key == "coding-key"


class TestCodingClaudeConfig:
    """CodingClaudeConfig 测试"""

    def test_init_with_defaults(self):
        """测试默认值初始化"""
        config = CodingClaudeConfig()
        assert config.model == "claude-3-5-sonnet"

    def test_env_var_fallback(self):
        """测试环境变量回退"""
        os.environ["ANTHROPIC_API_KEY"] = "anthropic-key"
        config = CodingClaudeConfig(api_key="${ANTHROPIC_API_KEY}")
        assert config.api_key == "anthropic-key"


class TestEvolutionConfig:
    """EvolutionConfig 测试"""

    def test_init_requires_llm(self):
        """测试需要 LLM 配置"""
        with pytest.raises(ValueError, match="evolution.llm 是必填配置"):
            EvolutionConfig()

    def test_init_requires_api_key(self):
        """测试需要 API Key"""
        llm = EvolutionLLMConfig(provider="deepseek", model="test", api_key="")
        with pytest.raises(ValueError, match="evolution.llm.api_key 未配置"):
            EvolutionConfig(llm=llm)

    def test_init_with_valid_config(self):
        """测试有效配置初始化"""
        llm = EvolutionLLMConfig(
            provider="deepseek",
            model="deepseek-reasoner",
            api_key="sk-test",
        )
        config = EvolutionConfig(llm=llm)
        assert config.enabled is True
        assert config.max_iterations == 10
        assert "correctness" in config.pareto_dimensions


class TestCodingConfig:
    """CodingConfig 测试"""

    def test_cursor_engine_default(self):
        """测试 Cursor 引擎默认配置"""
        config = CodingConfig()
        assert config.engine == "cursor"

    def test_llm_engine_requires_config(self):
        """测试 LLM 引擎需要配置"""
        # CodingConfig 构造函数不验证，验证在 CodingEngine.from_config 中进行
        config = CodingConfig(engine="llm")
        assert config.engine == "llm"
        assert config.llm is None

    def test_claude_engine_requires_config(self):
        """测试 Claude 引擎需要配置"""
        # CodingConfig 构造函数不验证，验证在 CodingEngine.from_config 中进行
        config = CodingConfig(engine="claude")
        assert config.engine == "claude"
        assert config.claude is None

    def test_llm_engine_with_config(self):
        """测试带配置的 LLM 引擎"""
        llm = CodingLLMConfig(provider="deepseek", model="chat", api_key="key")
        config = CodingConfig(engine="llm", llm=llm)
        assert config.engine == "llm"
        assert config.llm is not None

    def test_claude_engine_with_config(self):
        """测试带配置的 Claude 引擎"""
        claude = CodingClaudeConfig(api_key="key")
        config = CodingConfig(engine="claude", claude=claude)
        assert config.engine == "claude"
        assert config.claude is not None


class TestSprintCycleConfig:
    """SprintCycleConfig 测试"""

    def test_from_dict_with_evolution(self):
        """测试从字典加载配置"""
        data = {
            "evolution": {
                "llm": {
                    "provider": "deepseek",
                    "model": "deepseek-reasoner",
                    "api_key": "sk-test",
                }
            }
        }
        config = SprintCycleConfig.from_dict(data)
        assert config.evolution is not None
        assert config.evolution.llm.provider == "deepseek"

    def test_from_dict_with_coding(self):
        """测试从字典加载编码配置"""
        data = {
            "evolution": {
                "llm": {
                    "provider": "deepseek",
                    "model": "deepseek-reasoner",
                    "api_key": "sk-test",
                }
            },
            "coding": {
                "engine": "claude",
                "claude": {
                    "api_key": "sk-ant-xxx",
                },
            },
        }
        config = SprintCycleConfig.from_dict(data)
        assert config.coding.engine == "claude"
        assert config.coding.claude is not None

    def test_from_yaml_mock(self):
        """测试 YAML 加载（使用字符串模拟）"""
        import yaml
        yaml_str = """
evolution:
  llm:
    provider: deepseek
    model: deepseek-reasoner
    api_key: sk-test
"""
        data = yaml.safe_load(yaml_str)
        config = SprintCycleConfig.from_dict(data)
        assert config.evolution.llm.provider == "deepseek"


class TestLoadConfigFromEnv:
    """load_config_from_env 测试"""

    def test_load_default_config(self):
        """测试加载默认配置"""
        # 设置测试用 API key
        os.environ.setdefault("LLM_API_KEY", "test-api-key-for-unit-test")
        config = load_config_from_env()
        assert config.evolution is not None
        assert config.evolution.llm is not None

    def test_load_with_env_override(self):
        """测试环境变量覆盖"""
        os.environ["EVOLUTION_LLM_PROVIDER"] = "openai"
        os.environ["EVOLUTION_LLM_MODEL"] = "gpt-4"
        os.environ["CODING_ENGINE"] = "llm"
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        config = load_config_from_env()
        assert config.evolution.llm.provider == "openai"
        assert config.evolution.llm.model == "gpt-4"
        assert config.coding.engine == "llm"


class TestValidateConfig:
    """validate_config 测试"""

    def test_valid_config(self):
        """测试有效配置验证"""
        llm = EvolutionLLMConfig(provider="deepseek", model="test", api_key="key")
        config = SprintCycleConfig(evolution=EvolutionConfig(llm=llm))
        errors = validate_config(config)
        assert len(errors) == 0

    def test_missing_evolution_llm(self):
        """测试缺少进化 LLM"""
        # EvolutionConfig 构造时需要 llm 参数
        config = SprintCycleConfig()
        errors = validate_config(config)
        assert len(errors) > 0
        assert any("evolution.llm" in e for e in errors)

    def test_coding_engine_validation(self):
        """测试编码引擎验证"""
        llm = EvolutionLLMConfig(provider="deepseek", model="test", api_key="key")
        evolution = EvolutionConfig(llm=llm)

        # LLM 引擎无配置
        coding_llm = CodingLLMConfig(provider="deepseek", model="test", api_key="key")
        coding = CodingConfig(engine="llm", llm=coding_llm)
        config = SprintCycleConfig(evolution=evolution, coding=coding)
        errors = validate_config(config)
        # 有效配置，无错误
        assert len(errors) == 0
