"""
SprintCycle 配置管理模块 v0.3

提供统一的配置管理，支持：
- 环境变量覆盖
- 配置验证
- 热更新
- 默认值处理
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field

from .exceptions import (
    ConfigurationError,
    ConfigFileNotFoundError,
    ConfigValidationError
)


@dataclass
class ToolConfig:
    """工具配置"""
    command: str = ""
    model: str = "gpt-4"
    api_key_env: str = "LLM_API_KEY"
    timeout: int = 180
    max_retries: int = 1


@dataclass
class SchedulerConfig:
    """调度器配置"""
    max_concurrent: int = 3
    retry_delay: int = 5


@dataclass
class ReviewConfig:
    """审查配置"""
    enabled: bool = True
    max_iterations: int = 3
    fail_on_critical: bool = True
    check_security: bool = True
    check_performance: bool = True
    check_style: bool = True


@dataclass
class PlaywrightConfig:
    """Playwright 配置"""
    enabled: bool = True
    headless: bool = True
    timeout: int = 30000
    mcp_command: str = "npx @playwright/mcp@latest"


@dataclass
class SprintCycleConfig:
    """SprintCycle 主配置类"""
    tools: Dict[str, ToolConfig] = field(default_factory=dict)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    review: ReviewConfig = field(default_factory=ReviewConfig)
    playwright: PlaywrightConfig = field(default_factory=PlaywrightConfig)
    
    # 知识库配置
    knowledge_base_path: str = "./knowledge"
    knowledge_auto_save: bool = True
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_structured: bool = False
    
    # 执行配置
    execution_timeout: int = 600
    dry_run: bool = False
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "SprintCycleConfig":
        """
        从 YAML 文件加载配置
        
        Args:
            path: 配置文件路径
            
        Returns:
            SprintCycleConfig 实例
            
        Raises:
            ConfigFileNotFoundError: 配置文件不存在
            ConfigValidationError: 配置验证失败
        """
        config_path = Path(path)
        if not config_path.exists():
            raise ConfigFileNotFoundError(str(config_path))
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigValidationError(
                f"YAML 解析失败: {e}",
                config_key="yaml_parse",
                expected="valid YAML",
                actual=str(e)
            )
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SprintCycleConfig":
        """
        从字典加载配置
        
        Args:
            data: 配置字典
            
        Returns:
            SprintCycleConfig 实例
        """
        config = cls()
        
        # 工具配置
        if "tools" in data:
            for name, tool_data in data["tools"].items():
                config.tools[name] = ToolConfig(**tool_data)
        
        # 调度器配置
        if "scheduler" in data:
            config.scheduler = SchedulerConfig(**data["scheduler"])
        
        # 审查配置
        if "review" in data:
            config.review = ReviewConfig(**data["review"])
        
        # Playwright 配置
        if "playwright" in data:
            config.playwright = PlaywrightConfig(**data["playwright"])
        
        # 知识库配置
        if "knowledge_base" in data:
            kb_config = data["knowledge_base"]
            config.knowledge_base_path = kb_config.get("path", config.knowledge_base_path)
            config.knowledge_auto_save = kb_config.get("auto_save", config.knowledge_auto_save)
        
        # 日志配置
        if "logging" in data:
            log_config = data["logging"]
            config.log_level = log_config.get("level", config.log_level)
            config.log_file = log_config.get("file")
            config.log_structured = log_config.get("structured", config.log_structured)
        
        # 执行配置
        if "execution" in data:
            exec_config = data["execution"]
            config.execution_timeout = exec_config.get("timeout", config.execution_timeout)
            config.dry_run = exec_config.get("dry_run", config.dry_run)
        
        # 应用环境变量覆盖
        config.apply_env_overrides()
        
        # 验证配置
        config.validate()
        
        return config
    
    def apply_env_overrides(self):
        """应用环境变量覆盖"""
        env_mappings = {
            "LLM_API_KEY": "OPENAI_API_KEY",
            "LOG_LEVEL": "LOG_LEVEL",
            "LOG_FILE": "LOG_FILE",
            "KNOWLEDGE_BASE_PATH": "KNOWLEDGE_BASE_PATH",
        }
        
        for config_key, env_key in env_mappings.items():
            if env_key in os.environ:
                if config_key == "LOG_LEVEL":
                    self.log_level = os.environ[env_key]
                elif config_key == "LOG_FILE":
                    self.log_file = os.environ[env_key]
                elif config_key == "KNOWLEDGE_BASE_PATH":
                    self.knowledge_base_path = os.environ[env_key]
    
    def validate(self) -> None:
        """
        验证配置有效性
        
        Raises:
            ConfigValidationError: 配置验证失败
        """
        errors = []
        
        # 验证调度器配置
        if self.scheduler.max_concurrent < 1:
            errors.append("scheduler.max_concurrent 必须 >= 1")
        
        if self.scheduler.retry_delay < 0:
            errors.append("scheduler.retry_delay 必须 >= 0")
        
        # 验证超时配置
        if self.execution_timeout < 60:
            errors.append("execution.timeout 必须 >= 60 秒")
        
        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            errors.append(f"logging.level 必须是 {valid_levels} 之一")
        
        # 验证工具配置
        for name, tool in self.tools.items():
            if not tool.command:
                errors.append(f"tools.{name}.command 不能为空")
            if tool.timeout < 10:
                errors.append(f"tools.{name}.timeout 必须 >= 10 秒")
        
        if errors:
            raise ConfigValidationError(
                f"配置验证失败: {', '.join(errors)}",
                config_key="root",
                expected="valid configuration",
                actual=errors
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            配置字典
        """
        return {
            "tools": {name: vars(tool) for name, tool in self.tools.items()},
            "scheduler": vars(self.scheduler),
            "review": vars(self.review),
            "playwright": vars(self.playwright),
            "knowledge_base": {
                "path": self.knowledge_base_path,
                "auto_save": self.knowledge_auto_save,
            },
            "logging": {
                "level": self.log_level,
                "file": self.log_file,
                "structured": self.log_structured,
            },
            "execution": {
                "timeout": self.execution_timeout,
                "dry_run": self.dry_run,
            }
        }
    
    def get_tool_config(self, name: str) -> Optional[ToolConfig]:
        """
        获取工具配置
        
        Args:
            name: 工具名称
            
        Returns:
            工具配置或 None
        """
        return self.tools.get(name)
    
    def reload(self, path: Union[str, Path]) -> None:
        """
        热更新：重新加载配置
        
        Args:
            path: 配置文件路径
        """
        new_config = self.from_yaml(path)
        self.__dict__.update(new_config.__dict__)


# 全局配置实例
_global_config: Optional[SprintCycleConfig] = None


def get_config() -> SprintCycleConfig:
    """
    获取全局配置实例
    
    Returns:
        SprintCycleConfig 实例
    """
    global _global_config
    if _global_config is None:
        _global_config = SprintCycleConfig()
    return _global_config


def load_config(path: Union[str, Path]) -> SprintCycleConfig:
    """
    加载配置并设置为全局实例
    
    Args:
        path: 配置文件路径
        
    Returns:
        SprintCycleConfig 实例
    """
    global _global_config
    _global_config = SprintCycleConfig.from_yaml(path)
    return _global_config


def reset_config() -> None:
    """重置全局配置"""
    global _global_config
    _global_config = None


__all__ = [
    "SprintCycleConfig",
    "ToolConfig",
    "SchedulerConfig",
    "ReviewConfig",
    "PlaywrightConfig",
    "get_config",
    "load_config",
    "reset_config",
]
