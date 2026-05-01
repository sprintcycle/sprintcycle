"""
Coding Strategy - 编码策略抽象层
"""

import asyncio
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CodingStrategy(ABC):
    """编码策略基类"""

    @abstractmethod
    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """生成代码"""
        pass

    @abstractmethod
    async def review_code(
        self,
        code: str,
        review_type: str = "general",
    ) -> Dict[str, Any]:
        """审查代码"""
        pass

    @abstractmethod
    async def explain_code(self, code: str) -> str:
        """解释代码"""
        pass

    @abstractmethod
    async def fix_code(self, code: str, error: str) -> str:
        """修复代码"""
        pass


class CursorStrategy(CodingStrategy):
    """Cursor AI 编码策略"""

    def __init__(self, cursor_path: str = "cursor"):
        self.cursor_path = cursor_path
        self._available = self._check_cursor_available()

    def _check_cursor_available(self) -> bool:
        try:
            result = subprocess.run(["which", self.cursor_path], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    async def generate_code(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        if not self._available:
            raise RuntimeError(f"Cursor not available at: {self.cursor_path}")
        try:
            result = subprocess.run([self.cursor_path, "--generate", prompt], capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(f"Cursor error: {result.stderr}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise RuntimeError("Cursor generation timeout")
        except Exception as e:
            raise RuntimeError(f"Cursor generation failed: {e}")

    async def review_code(self, code: str, review_type: str = "general") -> Dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Cursor not available"}
        try:
            result = subprocess.run([self.cursor_path, "--review", review_type], input=code, capture_output=True, text=True, timeout=60)
            return {"success": result.returncode == 0, "output": result.stdout, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def explain_code(self, code: str) -> str:
        if not self._available:
            return "Cursor not available"
        try:
            result = subprocess.run([self.cursor_path, "--explain"], input=code, capture_output=True, text=True, timeout=60)
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except Exception as e:
            return f"Error: {e}"

    async def fix_code(self, code: str, error: str) -> str:
        if not self._available:
            raise RuntimeError("Cursor not available")
        try:
            result = subprocess.run([self.cursor_path, "--fix", error], input=code, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                raise RuntimeError(f"Cursor fix error: {result.stderr}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise RuntimeError("Cursor fix timeout")
        except Exception as e:
            raise RuntimeError(f"Cursor fix failed: {e}")


class LLMStrategy(CodingStrategy):
    """LLM 编码策略"""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, model: str = "deepseek-chat"):
        from ..llm_provider import resolve_provider
        self._config = resolve_provider(api_key=api_key, api_base=api_base, model=model)
        self._provider = "deepseek"

    async def generate_code(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """通过 LLM 生成代码"""
        import aiohttp
        import json
        
        system_prompt = "你是一个专业的 Python 程序员。请根据用户需求生成高质量的 Python 代码。"
        if context:
            system_prompt += f"\n上下文: {context}"
        
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._config.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self._config.api_key}", "Content-Type": "application/json"},
                    json={"model": self._config.model, "messages": messages, "temperature": 0.7},
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        return data["choices"][0]["message"]["content"]
                    else:
                        raise RuntimeError(f"API error: {data.get('error', {}).get('message', 'Unknown')}")
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")

    async def review_code(self, code: str, review_type: str = "general") -> Dict[str, Any]:
        prompts = {
            "general": f"请审查以下 Python 代码的质量、可读性和潜在问题:\n\n{code}",
            "security": f"请审查以下 Python 代码的安全问题:\n\n{code}",
            "performance": f"请审查以下 Python 代码的性能问题:\n\n{code}",
        }
        prompt = prompts.get(review_type, prompts["general"])
        try:
            review = await self.generate_code(prompt)
            return {"success": True, "review": review}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def explain_code(self, code: str) -> str:
        prompt = f"请解释以下 Python 代码的功能:\n\n{code}"
        try:
            return await self.generate_code(prompt)
        except Exception as e:
            return f"解释失败: {e}"

    async def fix_code(self, code: str, error: str) -> str:
        prompt = f"请修复以下 Python 代码中的错误:\n\n错误信息: {error}\n\n代码:\n{code}"
        try:
            return await self.generate_code(prompt)
        except Exception as e:
            raise RuntimeError(f"LLM fix failed: {e}")


class ClaudeStrategy(CodingStrategy):
    """Claude 编码策略"""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._client = None
        if api_key:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=api_key)
            except ImportError:
                logger.warning("Anthropic SDK not installed")

    async def generate_code(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        if not self._client:
            raise RuntimeError("Claude client not initialized")
        system = "你是一个专业的 Python 程序员。请根据用户需求生成高质量的 Python 代码。"
        try:
            message = self._client.messages.create(model="claude-3-sonnet-20240229", max_tokens=4096, system=system, messages=[{"role": "user", "content": prompt}])
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Claude generation failed: {e}")

    async def review_code(self, code: str, review_type: str = "general") -> Dict[str, Any]:
        if not self._client:
            return {"success": False, "error": "Claude client not initialized"}
        prompt = f"请审查以下 Python 代码的{review_type}:\n\n{code}"
        try:
            message = self._client.messages.create(model="claude-3-sonnet-20240229", max_tokens=1024, messages=[{"role": "user", "content": prompt}])
            return {"success": True, "review": message.content[0].text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def explain_code(self, code: str) -> str:
        if not self._client:
            return "Claude client not initialized"
        prompt = f"请解释以下 Python 代码的功能:\n\n{code}"
        try:
            message = self._client.messages.create(model="claude-3-sonnet-20240229", max_tokens=1024, messages=[{"role": "user", "content": prompt}])
            return message.content[0].text
        except Exception as e:
            return f"解释失败: {e}"

    async def fix_code(self, code: str, error: str) -> str:
        if not self._client:
            raise RuntimeError("Claude client not initialized")
        prompt = f"请修复以下 Python 代码中的错误:\n\n错误信息: {error}\n\n代码:\n{code}"
        try:
            message = self._client.messages.create(model="claude-3-sonnet-20240229", max_tokens=4096, messages=[{"role": "user", "content": prompt}])
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Claude fix failed: {e}")
