"""LLM interface - re-exported from infrastructure for backwards compatibility."""

from __future__ import annotations

from typing import Any, Optional

from sprintcycle.infrastructure.integrations.llm_provider import resolve_provider


class LLMInterface:
    """Minimal async LLM wrapper."""

    def __init__(self, provider: Optional[str] = None) -> None:
        self._config = resolve_provider(provider=provider)
        self._client: Any = None

    async def ainvoke(self, prompt: str) -> Any:
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self._config.api_key,
                base_url=self._config.api_base,
            )
        response = await self._client.chat.completions.create(
            model=self._config.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content if response.choices else ""


_llm_instance: Optional[LLMInterface] = None


def get_llm(provider: Optional[str] = None) -> LLMInterface:
    global _llm_instance
    if _llm_instance is None or provider is not None:
        _llm_instance = LLMInterface(provider=provider)
    return _llm_instance
