"""
LLM Provider Registry - 统一LLM提供者管理

所有LLM调用通过此模块获取 provider 配置（api_key/api_base/model），
消除散落在各模块的硬编码URL。

优先级：显式参数 > 环境变量 > 默认值

环境变量:
    LLM_API_KEY: API密钥
    LLM_API_BASE: API基础URL
    LLM_MODEL: 默认模型名
    LLM_PROVIDER: 提供者名称 (openai/deepseek/anthropic/custom)
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# 预定义 Provider 端点
PROVIDER_DEFAULTS: Dict[str, Dict[str, str]] = {
    "openai": {
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4",
    },
    "deepseek": {
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "anthropic": {
        "api_base": "https://api.anthropic.com/v1",
        "model": "claude-3-sonnet-20240229",
    },
}


@dataclass
class LLMProviderConfig:
    """LLM Provider 配置"""
    api_key: str = ""
    api_base: str = ""
    model: str = ""
    provider: str = "openai"

    @property
    def chat_endpoint(self) -> str:
        """获取 chat completions 端点"""
        return f"{self.api_base.rstrip('/')}/chat/completions"

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("LLM_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")


def resolve_provider(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMProviderConfig:
    """
    解析 LLM Provider 配置
    
    优先级：显式参数 > 环境变量 > Provider默认值
    
    Args:
        provider: 提供者名称 (openai/deepseek/anthropic/custom)
        api_key: API密钥
        api_base: API基础URL
        model: 模型名称
    
    Returns:
        LLMProviderConfig
    """
    # 1. 确定 provider 名称
    provider_name = (
        provider
        or os.environ.get("LLM_PROVIDER", "")
        or "openai"
    ).lower()
    
    # 2. 获取 provider 默认值
    defaults = PROVIDER_DEFAULTS.get(provider_name, PROVIDER_DEFAULTS["openai"])
    
    # 3. 按优先级合并
    resolved_key = api_key or os.environ.get("LLM_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    resolved_base = api_base or os.environ.get("LLM_API_BASE", "") or defaults["api_base"]
    resolved_model = model or os.environ.get("LLM_MODEL", "") or defaults["model"]
    
    config = LLMProviderConfig(
        api_key=resolved_key,
        api_base=resolved_base,
        model=resolved_model,
        provider=provider_name,
    )
    
    logger.debug(f"LLM Provider resolved: {provider_name}, base={resolved_base}, model={resolved_model}")
    return config


__all__ = ["LLMProviderConfig", "resolve_provider", "PROVIDER_DEFAULTS"]
