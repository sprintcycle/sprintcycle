"""
LLMConfig - LLM 配置与兼容别名

v0.9.2: 使用 pydantic BaseModel 自动从环境变量加载
"""

import os
from typing import Optional, Dict, Any

from pydantic import BaseModel, model_validator

from .runtime_config import _resolve_env_var, _mask_sensitive, _get_api_key_from_env, _get_api_base_from_env


class LLMConfig(BaseModel):
    """
    LLM 配置

    v0.9.2: 使用 pydantic BaseModel 提供类型安全
    """
    provider: str = "openai"
    model: str = "gpt-4"
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096

    @model_validator(mode="before")
    @classmethod
    def _resolve_compat(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """处理向后兼容的环境变量和 ${VAR} 形式的环境变量引用"""
        if not isinstance(values, dict):
            return values
        
        if not values.get("api_key"):
            values["api_key"] = _get_api_key_from_env()
        if not values.get("api_base"):
            values["api_base"] = _get_api_base_from_env()
        if values.get("api_key") and isinstance(values["api_key"], str):
            values["api_key"] = _resolve_env_var(values["api_key"])
        return values

    @property
    def chat_endpoint(self) -> str:
        """聊天端点"""
        base = self.api_base or ""
        return f"{base.rstrip('/')}/chat/completions"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_base": self.api_base,
            "api_key": _mask_sensitive(self.api_key) if self.api_key else None,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        """从字典加载配置"""
        return cls(**data)

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """从环境变量加载配置（pydantic 自动处理）"""
        return cls()


# ============================================================
# Compatible aliases
# ============================================================

CodingLLMConfig = LLMConfig
CodingClaudeConfig = LLMConfig
EvolutionLLMConfig = LLMConfig
