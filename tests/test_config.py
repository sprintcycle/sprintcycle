"""
SprintCycle 配置模块测试 v0.3
"""

import pytest
import tempfile
import os
from pathlib import Path

from sprintcycle.config import (
    SprintCycleConfig,
    ToolConfig,
    SchedulerConfig,
    ReviewConfig,
    PlaywrightConfig,
    get_config,
    load_config,
    reset_config
)
from sprintcycle.exceptions import (
    ConfigFileNotFoundError,
    ConfigValidationError
)


class TestToolConfig:
    """ToolConfig 测试"""
    
    def test_default_values(self):
        """测试默认值"""
        config = ToolConfig()
        assert config.command == ""
        assert config.model == "gpt-4"
        assert config.api_key_env == "LLM_API_KEY"
        assert config.timeout == 180
        assert config.max_retries == 1
    
    def test_custom_values(self):
        """测试自定义值"""
        config = ToolConfig(
            command="aider",
            model="claude-3",
            timeout=300,
            max_retries=3
        )
        assert config.command == "aider"
        assert config.model == "claude-3"
        assert config.timeout == 300
        assert config.max_retries == 3


class TestSchedulerConfig:
    """SchedulerConfig 测试"""
    
    def test_default_values(self):
        """测试默认值"""
        config = SchedulerConfig()
        assert config.max_concurrent == 3
        assert config.retry_delay == 5
    
    def test_validation(self):
        """测试验证"""
        config = SchedulerConfig()
        # 默认值应该通过验证
        assert config.max_concurrent >= 1
        assert config.retry_delay >= 0


class TestSprintCycleConfig:
    """SprintCycleConfig 测试"""
    
    def test_from_dict(self):
        """测试从字典加载"""
        data = {
            "tools": {
                "aider": {
                    "command": "/usr/bin/aider",
                    "model": "gpt-4",
                    "timeout": 200
                }
            },
            "scheduler": {
                "max_concurrent": 5,
                "retry_delay": 10
            },
            "review": {
                "enabled": True,
                "max_iterations": 5
            }
        }
        
        config = SprintCycleConfig.from_dict(data)
        
        assert "aider" in config.tools
        assert config.tools["aider"].command == "/usr/bin/aider"
        assert config.scheduler.max_concurrent == 5
        assert config.review.enabled is True
    
    def test_validation_failure(self):
        """测试验证失败"""
        config = SprintCycleConfig()
        config.scheduler.max_concurrent = 0
        
        with pytest.raises(ConfigValidationError) as exc_info:
            config.validate()
        
        assert "max_concurrent" in str(exc_info.value)
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = SprintCycleConfig()
        config_dict = config.to_dict()
        
        assert "tools" in config_dict
        assert "scheduler" in config_dict
        assert "review" in config_dict
        assert "playwright" in config_dict
    
    def test_env_overrides(self):
        """测试环境变量覆盖"""
        os.environ["LOG_LEVEL"] = "DEBUG"
        
        config = SprintCycleConfig()
        config.apply_env_overrides()
        
        assert config.log_level == "DEBUG"
        
        del os.environ["LOG_LEVEL"]
    
    def test_get_tool_config(self):
        """测试获取工具配置"""
        config = SprintCycleConfig()
        config.tools["aider"] = ToolConfig(command="/usr/bin/aider")
        
        tool = config.get_tool_config("aider")
        assert tool is not None
        assert tool.command == "/usr/bin/aider"
        
        missing = config.get_tool_config("missing")
        assert missing is None


class TestConfigFile:
    """配置文件测试"""
    
    def test_load_from_yaml(self):
        """测试从 YAML 加载"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
tools:
  aider:
    command: /usr/bin/aider
    model: gpt-4
    timeout: 200

scheduler:
  max_concurrent: 5
  retry_delay: 10

review:
  enabled: true
  max_iterations: 3

playwright:
  enabled: true
  headless: true
""")
            temp_path = f.name
        
        try:
            config = SprintCycleConfig.from_yaml(temp_path)
            
            assert "aider" in config.tools
            assert config.scheduler.max_concurrent == 5
            assert config.review.enabled is True
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found(self):
        """测试文件不存在"""
        with pytest.raises(ConfigFileNotFoundError):
            SprintCycleConfig.from_yaml("/nonexistent/path/config.yaml")
    
    def test_invalid_yaml(self):
        """测试无效 YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigValidationError):
                SprintCycleConfig.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)


class TestGlobalConfig:
    """全局配置测试"""
    
    def test_get_config(self):
        """测试获取全局配置"""
        reset_config()
        config = get_config()
        
        assert isinstance(config, SprintCycleConfig)
        
        # 应该是同一个实例
        config2 = get_config()
        assert config is config2
    
    def test_load_config(self):
        """测试加载配置"""
        reset_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
scheduler:
  max_concurrent: 10
""")
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            assert config.scheduler.max_concurrent == 10
            
            # 验证全局实例已更新
            global_config = get_config()
            assert global_config.scheduler.max_concurrent == 10
        finally:
            os.unlink(temp_path)
            reset_config()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
