"""
LLMConfig - LLM 配置与兼容别名
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os

from .runtime_config import _resolve_env_var, _mask_sensitive


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4"
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096

    def __post_init__(self):
        self.api_key = _resolve_env_var(self.api_key) if self.api_key else None
        if not self.api_key:
            self.api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        if self.api_base is None:
            self.api_base = os.getenv("LLM_API_BASE")

    @property
    def chat_endpoint(self) -> str:
        base = self.api_base or ""
        return f"{base.rstrip('/')}/chat/completions"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "api_base": self.api_base,
            "api_key": _mask_sensitive(self.api_key) if self.api_key else None,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


# Compatible aliases
CodingLLMConfig = LLMConfig
CodingClaudeConfig = LLMConfig
EvolutionLLMConfig = LLMConfig
