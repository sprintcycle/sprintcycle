"""AI API 封装 - 支持 OpenAI/Anthropic/Mock"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = None) -> str: pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict]) -> str: pass


class MockProvider(AIProvider):
    """Mock 提供者 - 用于测试"""
    
    async def generate(self, prompt: str, system: str = None) -> str:
        return f"[Mock Response] {prompt[:50]}..."
    
    async def chat(self, messages: List[Dict]) -> str:
        return "[Mock Chat Response]"


class OpenAIProvider(AIProvider):
    """OpenAI 提供者"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    async def generate(self, prompt: str, system: str = None) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=self.model, messages=messages
            )
            return response.choices[0].message.content
        except ImportError:
            return "[OpenAI SDK 未安装]"
        except Exception as e:
            return f"[OpenAI Error: {str(e)[:50]}]"
    
    async def chat(self, messages: List[Dict]) -> str:
        return await self.generate(messages[-1].get("content", ""), None)


class AnthropicProvider(AIProvider):
    """Anthropic 提供者"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, prompt: str, system: str = None) -> str:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            kwargs = {"model": self.model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}
            if system:
                kwargs["system"] = system
            
            response = await client.messages.create(**kwargs)
            return response.content[0].text
        except ImportError:
            return "[Anthropic SDK 未安装]"
        except Exception as e:
            return f"[Anthropic Error: {str(e)[:50]}]"
    
    async def chat(self, messages: List[Dict]) -> str:
        return await self.generate(messages[-1].get("content", ""), None)


def create_ai_provider(config) -> AIProvider:
    """创建 AI 提供者"""
    provider = getattr(config, 'provider', 'mock')
    api_key = getattr(config, 'api_key', None)
    model = getattr(config, 'model', 'gpt-4')
    base_url = getattr(config, 'base_url', None)
    
    if provider == "openai" and api_key:
        return OpenAIProvider(api_key, model, base_url)
    elif provider == "anthropic" and api_key:
        return AnthropicProvider(api_key)
    else:
        return MockProvider()
