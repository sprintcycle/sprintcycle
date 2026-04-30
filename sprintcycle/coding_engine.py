"""
SprintCycle Coding Engine - 编码引擎抽象层

支持三种编码引擎:
- cursor: 用户本地 Cursor AI
- llm: 内置 LLM 引擎 (deepseek-chat)
- claude: Anthropic Claude 引擎

使用工厂模式 + 策略模式实现
"""

import asyncio
import subprocess
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Type

from .config import CodingConfig, CodingLLMConfig, CodingClaudeConfig

logger = logging.getLogger(__name__)


# ============ 策略接口 ============

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
    async def explain_code(
        self,
        code: str,
    ) -> str:
        """解释代码"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        pass


# ============ 具体策略实现 ============

class CursorStrategy(CodingStrategy):
    """Cursor AI 策略 - 本地 Cursor 编辑器"""

    def __init__(self, config: Optional[CodingConfig] = None):
        self.config = config

    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """通过 Cursor CLI 生成代码"""
        try:
            full_prompt = prompt
            if context:
                context_str = "\n".join([f"# {k}: {v}" for k, v in context.items()])
                full_prompt = f"{context_str}\n\n{prompt}"

            result = subprocess.run(
                ["cursor", "--no-input", "--prompt", full_prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Cursor CLI 执行失败: {result.stderr}")
                raise RuntimeError(f"Cursor CLI 执行失败: {result.stderr}")

        except FileNotFoundError:
            raise RuntimeError("Cursor CLI 未安装或不在 PATH 中")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Cursor CLI 执行超时")

    async def review_code(
        self,
        code: str,
        review_type: str = "general",
    ) -> Dict[str, Any]:
        """通过 Cursor 进行代码审查"""
        prompt = f"""审查以下代码 (审查类型: {review_type}):

```{code}
```

请提供:
1. 代码质量评分 (1-10)
2. 发现的问题列表
3. 改进建议
"""
        try:
            result = await self.generate_code(prompt)
            return {
                "review": result,
                "review_type": review_type,
                "success": True,
            }
        except Exception as e:
            return {
                "review": "",
                "review_type": review_type,
                "success": False,
                "error": str(e),
            }

    async def explain_code(self, code: str) -> str:
        """通过 Cursor 解释代码"""
        prompt = f"""解释以下代码的功能和实现逻辑:

```{code}
```"""
        return await self.generate_code(prompt)

    def is_available(self) -> bool:
        """检查 Cursor CLI 是否可用"""
        try:
            result = subprocess.run(
                ["which", "cursor"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False


class LLMStrategy(CodingStrategy):
    """内置 LLM 策略 - 支持 DeepSeek 等 OpenAI 兼容 API"""

    def __init__(self, config: CodingLLMConfig):
        self.config = config
        self._client = None

    async def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            try:
                import openai  # type: ignore[import-not-found]
                self._client = openai.AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.api_base or __import__('os').environ.get("LLM_API_BASE", "https://api.deepseek.com"),
                )
            except ImportError:
                raise RuntimeError("请安装 openai 库: pip install openai")
        return self._client

    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """通过 LLM 生成代码"""
        client = await self._get_client()

        system_prompt = """你是一个专业的 Python 程序员。请根据用户的请求生成高质量的 Python 代码。
要求:
1. 代码简洁、可读性强
2. 遵循 PEP 8 规范
3. 添加必要的注释
4. 包含类型注解
5. 处理异常情况"""

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if context:
            context_str = "## 上下文信息\n" + "\n".join(
                [f"- **{k}**: {v}" for k, v in context.items()]
            )
            messages.append({"role": "user", "content": f"{context_str}\n\n## 请求\n{prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=self.config.model or "deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            raise RuntimeError(f"LLM 生成失败: {e}")

    async def review_code(
        self,
        code: str,
        review_type: str = "general",
    ) -> Dict[str, Any]:
        """通过 LLM 审查代码"""
        review_prompts = {
            "security": "安全审查",
            "performance": "性能审查",
            "style": "代码风格审查",
            "general": "综合审查",
        }

        prompt = f"""请对以下 Python 代码进行 **{review_prompts.get(review_type, '综合')}**：

```{code}
```

请提供 JSON 格式的审查结果:
{{
    "score": <评分 1-10>,
    "issues": [
        {{"severity": "high/medium/low", "line": <行号>, "description": "<问题描述>", "suggestion": "<建议>"}}
    ],
    "summary": "<总体评价>",
    "recommendations": ["<建议1>", "<建议2>"]
}}"""

        try:
            result = await self.generate_code(prompt)
            import json
            import re
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"raw_review": result, "success": True}
        except Exception as e:
            return {
                "score": 5,
                "issues": [],
                "summary": f"审查失败: {e}",
                "recommendations": [],
                "success": False,
                "error": str(e),
            }

    async def explain_code(self, code: str) -> str:
        """通过 LLM 解释代码"""
        prompt = f"""请详细解释以下 Python 代码的功能、实现逻辑和关键点：

```{code}
```

请使用清晰的格式组织你的解释。"""
        return await self.generate_code(prompt)

    def is_available(self) -> bool:
        """检查 LLM 配置是否完整"""
        return bool(self.config.api_key)


class ClaudeStrategy(CodingStrategy):
    """Anthropic Claude 策略"""

    def __init__(self, config: CodingClaudeConfig):
        self.config = config
        self._client = None

    async def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic  # type: ignore[import-not-found]
                self._client = AsyncAnthropic(api_key=self.config.api_key)
            except ImportError:
                raise RuntimeError("请安装 anthropic 库: pip install anthropic")
        return self._client

    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """通过 Claude 生成代码"""
        client = await self._get_client()

        system_prompt = """你是一个专业的 Python 程序员。请根据用户的请求生成高质量的 Python 代码。
要求:
1. 代码简洁、可读性强
2. 遵循 PEP 8 规范
3. 添加必要的注释
4. 包含类型注解
5. 处理异常情况"""

        messages = []
        if context:
            context_str = "## 上下文信息\n" + "\n".join(
                [f"- **{k}**: {v}" for k, v in context.items()]
            )
            messages.append({"role": "user", "content": f"{context_str}\n\n## 请求\n{prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})

        try:
            response = await client.messages.create(
                model=self.config.model or "claude-3-5-sonnet-20241022",
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude 生成失败: {e}")
            raise RuntimeError(f"Claude 生成失败: {e}")

    async def review_code(
        self,
        code: str,
        review_type: str = "general",
    ) -> Dict[str, Any]:
        """通过 Claude 审查代码"""
        review_prompts = {
            "security": "安全审查",
            "performance": "性能审查",
            "style": "代码风格审查",
            "general": "综合审查",
        }

        prompt = f"""请对以下 Python 代码进行 **{review_prompts.get(review_type, '综合')}**：

```
{code}
```

请提供 JSON 格式的审查结果:
{{
    "score": <评分 1-10>,
    "issues": [
        {{"severity": "high/medium/low", "line": <行号>, "description": "<问题描述>", "suggestion": "<建议>"}}
    ],
    "summary": "<总体评价>",
    "recommendations": ["<建议1>", "<建议2>"]
}}"""

        try:
            result = await self.generate_code(prompt)
            import json
            import re
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"raw_review": result, "success": True}
        except Exception as e:
            return {
                "score": 5,
                "issues": [],
                "summary": f"审查失败: {e}",
                "recommendations": [],
                "success": False,
                "error": str(e),
            }

    async def explain_code(self, code: str) -> str:
        """通过 Claude 解释代码"""
        prompt = f"""请详细解释以下 Python 代码的功能、实现逻辑和关键点：

```
{code}
```

请使用清晰的格式组织你的解释。"""
        return await self.generate_code(prompt)

    def is_available(self) -> bool:
        """检查 Claude 配置是否完整"""
        return bool(self.config.api_key)


# ============ 策略注册表 ============

_STRATEGY_REGISTRY: Dict[str, Type[CodingStrategy]] = {
    "cursor": CursorStrategy,
    "llm": LLMStrategy,
    "claude": ClaudeStrategy,
}


# ============ 工厂类 ============

@dataclass
class CodingEngineResult:
    """编码引擎结果"""
    success: bool
    content: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CodingEngine:
    """
    编码引擎工厂类

    使用工厂模式 + 策略模式，根据配置创建和管理编码引擎。

    使用示例:
    ```python
    from sprintcycle.config import CodingConfig, CodingLLMConfig

    # 方式 1: 从配置创建
    config = CodingConfig(engine="llm", llm=CodingLLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        api_key="sk-xxx"
    ))
    engine = CodingEngine.from_config(config)

    # 方式 2: 使用 LLM 引擎
    code = await engine.generate_code("实现一个快速排序函数")

    # 方式 3: 使用 Claude 引擎
    engine = CodingEngine.create("claude", api_key="sk-ant-xxx")
    review = await engine.review_code(my_code, "security")
    ```
    """

    def __init__(self, strategy: CodingStrategy, engine_name: str):
        self._strategy = strategy
        self._engine_name = engine_name

    @classmethod
    def from_config(cls, config: CodingConfig) -> "CodingEngine":
        """
        从配置创建编码引擎

        Args:
            config: 编码引擎配置

        Returns:
            CodingEngine 实例

        Raises:
            ValueError: 引擎类型不支持或配置不完整
        """
        engine_name = config.engine

        if engine_name not in _STRATEGY_REGISTRY:
            available = ", ".join(_STRATEGY_REGISTRY.keys())
            raise ValueError(
                f"不支持的引擎类型: {engine_name}。支持的引擎: {available}"
            )

        strategy_class = _STRATEGY_REGISTRY[engine_name]

        # 根据引擎类型创建策略
        if engine_name == "cursor":
            strategy = strategy_class(config)  # type: ignore[call-arg]
        elif engine_name == "llm":
            if config.llm is None:
                raise ValueError("engine='llm' 时必须提供 CodingLLMConfig")
            strategy = strategy_class(config.llm)  # type: ignore[call-arg]
        elif engine_name == "claude":
            if config.claude is None:
                raise ValueError("engine='claude' 时必须提供 CodingClaudeConfig")
            strategy = strategy_class(config.claude)  # type: ignore[call-arg]
        else:
            raise ValueError(f"不支持的引擎类型: {engine_name}")

        return cls(strategy=strategy, engine_name=engine_name)

    @classmethod
    def create(
        cls,
        engine: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> "CodingEngine":
        """
        快速创建编码引擎

        Args:
            engine: 引擎类型 (cursor/llm/claude)
            api_key: API 密钥 (llm/claude 需要)
            model: 模型名称 (可选)
            api_base: API 基础 URL (可选)

        Returns:
            CodingEngine 实例
        """
        if engine == "cursor":
            config = CodingConfig(engine="cursor")
        elif engine == "llm":
            config = CodingConfig(
                engine="llm",
                llm=CodingLLMConfig(
                    provider="deepseek",
                    model=model or "deepseek-chat",
                    api_key=api_key or "",
                    api_base=api_base,
                ),
            )
        elif engine == "claude":
            config = CodingConfig(
                engine="claude",
                claude=CodingClaudeConfig(
                    model=model or "claude-3-5-sonnet",
                    api_key=api_key or "",
                ),
            )
        else:
            raise ValueError(f"不支持的引擎类型: {engine}")

        return cls.from_config(config)

    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CodingEngineResult:
        """
        生成代码

        Args:
            prompt: 生成提示词
            context: 上下文信息

        Returns:
            CodingEngineResult 结果对象
        """
        try:
            content = await self._strategy.generate_code(prompt, context)
            return CodingEngineResult(
                success=True,
                content=content,
                metadata={"engine": self._engine_name},
            )
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            return CodingEngineResult(
                success=False,
                error=str(e),
                metadata={"engine": self._engine_name},
            )

    async def review_code(
        self,
        code: str,
        review_type: str = "general",
    ) -> CodingEngineResult:
        """
        审查代码

        Args:
            code: 要审查的代码
            review_type: 审查类型 (general/security/performance/style)

        Returns:
            CodingEngineResult 结果对象
        """
        try:
            content = await self._strategy.review_code(code, review_type)
            return CodingEngineResult(
                success=True,
                content=content,
                metadata={"engine": self._engine_name, "review_type": review_type},
            )
        except Exception as e:
            logger.error(f"代码审查失败: {e}")
            return CodingEngineResult(
                success=False,
                error=str(e),
                metadata={"engine": self._engine_name, "review_type": review_type},
            )

    async def explain_code(self, code: str) -> CodingEngineResult:
        """
        解释代码

        Args:
            code: 要解释的代码

        Returns:
            CodingEngineResult 结果对象
        """
        try:
            content = await self._strategy.explain_code(code)
            return CodingEngineResult(
                success=True,
                content=content,
                metadata={"engine": self._engine_name},
            )
        except Exception as e:
            logger.error(f"代码解释失败: {e}")
            return CodingEngineResult(
                success=False,
                error=str(e),
                metadata={"engine": self._engine_name},
            )

    def is_available(self) -> bool:
        """检查当前引擎是否可用"""
        return self._strategy.is_available()

    @property
    def engine_name(self) -> str:
        """获取引擎名称"""
        return self._engine_name

    @classmethod
    def list_available_engines(cls) -> List[str]:
        """列出所有可用的引擎"""
        return list(_STRATEGY_REGISTRY.keys())

    @classmethod
    def register_engine(cls, name: str, strategy_class: Type[CodingStrategy]) -> None:
        """
        注册新的编码引擎

        Args:
            name: 引擎名称
            strategy_class: 策略类
        """
        if not issubclass(strategy_class, CodingStrategy):
            raise TypeError("strategy_class 必须继承自 CodingStrategy")
        _STRATEGY_REGISTRY[name] = strategy_class
        logger.info(f"已注册编码引擎: {name}")
