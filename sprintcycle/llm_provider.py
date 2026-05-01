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
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# 预定义 Provider 端点
PROVIDER_DEFAULTS: Dict[str, Dict[str, str]] = {
    "openai": {"api_base": "https://api.openai.com/v1", "model": "gpt-4"},
    "deepseek": {"api_base": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "anthropic": {"api_base": "https://api.anthropic.com/v1", "model": "claude-3-sonnet-20240229"},
}


def resolve_provider(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
):
    """解析 LLM Provider 配置，返回 LLMConfig 实例。优先级：显式参数 > 环境变量 > Provider默认值"""
    from .config.manager import LLMConfig
    provider_name = (provider or os.environ.get("LLM_PROVIDER", "") or "openai").lower()
    defaults = PROVIDER_DEFAULTS.get(provider_name, PROVIDER_DEFAULTS["openai"])
    resolved_key = api_key or os.environ.get("LLM_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    resolved_base = api_base or os.environ.get("LLM_API_BASE", "") or defaults["api_base"]
    resolved_model = model or os.environ.get("LLM_MODEL", "") or defaults["model"]
    return LLMConfig(provider=provider_name, model=resolved_model, api_base=resolved_base, api_key=resolved_key)


def _to_litellm_model(provider: str, model: str) -> str:
    """转换 model 名为 litellm 格式: provider/model"""
    if "/" in model:
        return model
    prefix_map = {"deepseek": "deepseek", "anthropic": "anthropic", "openai": "openai"}
    return f"{prefix_map.get(provider, provider)}/{model}"


async def call_llm_async(
    model: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    **kwargs,
) -> str:
    """统一异步LLM调用，使用 LiteLLM"""
    import litellm
    resolved = resolve_provider(api_key=api_key, api_base=api_base, model=model)
    litellm_model = _to_litellm_model(resolved.provider, resolved.model)
    response = await litellm.acompletion(
        model=litellm_model, messages=messages or [], api_key=resolved.api_key,
        api_base=resolved.api_base, temperature=temperature, max_tokens=max_tokens, **kwargs,
    )
    return response.choices[0].message.content or ""


def call_llm(
    model: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    **kwargs,
) -> str:
    """统一同步LLM调用，使用 LiteLLM"""
    import litellm
    resolved = resolve_provider(api_key=api_key, api_base=api_base, model=model)
    litellm_model = _to_litellm_model(resolved.provider, resolved.model)
    response = litellm.completion(
        model=litellm_model, messages=messages or [], api_key=resolved.api_key,
        api_base=resolved.api_base, temperature=temperature, max_tokens=max_tokens, **kwargs,
    )
    return response.choices[0].message.content or ""


# Backward compatibility
from .config.manager import LLMConfig as LLMProviderConfig  # noqa: E402, F401

__all__ = ["LLMProviderConfig", "resolve_provider", "PROVIDER_DEFAULTS", "call_llm", "call_llm_async"]
