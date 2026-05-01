"""
统一配置管理器

合并来源：
- 配置文件 (config.yaml)
- 环境变量
- CLI 参数

v0.9.2: 适配 pydantic-settings 化的 RuntimeConfig
  - ConfigManager.get_runtime() 现在直接实例化 RuntimeConfig()
  - 保留 yaml/json 配置文件加载能力
"""

from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 重新导出（向后兼容）
from .runtime_config import RuntimeConfig
from .llm_config import LLMConfig


class ConfigManager:
    """
    统一配置管理器

    管理配置的加载、合并和访问。
    支持配置文件、环境变量、CLI 参数等多来源配置。

    v0.9.2: 适配 pydantic-settings，RuntimeConfig 现在会自动从环境变量加载
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径（YAML 或 JSON）
        """
        self.config_file = config_file
        self._runtime_config: Optional[RuntimeConfig] = None
        self._file_config: Dict[str, Any] = {}

        if config_file is not None and Path(config_file).exists():
            self._load_file_config()

    def _load_file_config(self) -> None:
        """从文件加载配置"""
        import yaml
        import json

        assert self.config_file is not None
        path = Path(self.config_file)
        try:
            if path.suffix in (".yaml", ".yml"):
                with open(path, encoding="utf-8") as f:
                    self._file_config = yaml.safe_load(f) or {}
            elif path.suffix == ".json":
                with open(path, encoding="utf-8") as f:
                    self._file_config = json.load(f) or {}
            else:
                logger.warning(f"Unknown config file format: {path.suffix}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            self._file_config = {}

    def get_runtime(self) -> RuntimeConfig:
        """
        获取运行时配置

        按优先级合并：默认值 < 文件配置 < 环境变量

        v0.9.2: RuntimeConfig 现在支持 pydantic-settings，会自动从环境变量加载
        此方法保持向后兼容，按优先级合并多来源配置

        Returns:
            RuntimeConfig 实例
        """
        if self._runtime_config is None:
            # 按优先级合并
            # 优先级: 环境变量 > 文件配置 > 默认值

            # 1. 从文件加载基础配置
            if self._file_config:
                file_config = RuntimeConfig.from_dict(self._file_config)
            else:
                file_config = None

            # 2. RuntimeConfig() 现在会自动从环境变量加载
            # 但我们仍然使用 merge 来确保文件配置可以覆盖默认值
            self._runtime_config = RuntimeConfig.merge(
                RuntimeConfig(),  # 默认值
                file_config,  # 配置文件
            )
        return self._runtime_config

    def update_runtime(self, **kwargs: Any) -> RuntimeConfig:
        """
        更新运行时配置

        Args:
            **kwargs: 要更新的配置项

        Returns:
            更新后的 RuntimeConfig
        """
        runtime = self.get_runtime()
        self._runtime_config = runtime.update(**kwargs)
        return self._runtime_config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        支持点号分隔的嵌套访问，如 "evolution.max_variations"

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        runtime = self.get_runtime()

        # 先检查 RuntimeConfig 的属性
        if hasattr(runtime, key):
            return getattr(runtime, key)

        # 再检查文件配置
        keys = key.split(".")
        value: Any = self._file_config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        runtime = self.get_runtime()
        if hasattr(runtime, key):
            self._runtime_config = runtime.update(**{key: value})

    def save(self, output_path: Optional[str] = None) -> None:
        """
        保存当前配置到文件

        Args:
            output_path: 输出路径，默认覆盖原文件
        """
        import yaml

        path = output_path or self.config_file
        if not path:
            raise ValueError("No output path specified")

        runtime = self.get_runtime()
        config_data = {
            **self._file_config,
            **runtime.to_dict(),
        }

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)


# 全局默认配置管理器实例
_default_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """获取默认配置管理器"""
    global _default_manager
    if _default_manager is None:
        _default_manager = ConfigManager(config_file)
    return _default_manager


def reset_config_manager() -> ConfigManager:
    """重置配置管理器"""
    global _default_manager
    _default_manager = ConfigManager()
    return _default_manager
