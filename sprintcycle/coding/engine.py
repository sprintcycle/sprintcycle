"""
Coding Engine - 编码引擎

支持三种编码引擎:
- cursor: 用户本地 Cursor AI
- llm: 内置 LLM 引擎 (deepseek-chat)
- claude: Anthropic Claude 引擎

使用工厂模式 + 策略模式实现
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Type

from .strategy import CodingStrategy, CursorStrategy, LLMStrategy, ClaudeStrategy
from .result import CodingEngineResult, CodeReviewResult, CodeFixResult
from ..config import CodingConfig, CodingLLMConfig

logger = logging.getLogger(__name__)


class CodingEngine:
    """
    编码引擎

    使用策略模式支持多种编码方式。
    """

    STRATEGIES: Dict[str, Type[CodingStrategy]] = {
        "cursor": CursorStrategy,
        "llm": LLMStrategy,
        "claude": ClaudeStrategy,
    }

    def __init__(
        self,
        config: Optional[CodingConfig] = None,
        strategy_name: str = "llm",
    ):
        """
        初始化编码引擎

        Args:
            config: 编码配置
            strategy_name: 策略名称 (cursor/llm/claude)
        """
        self.config = config or CodingConfig()
        self._strategy_name = strategy_name
        self._strategy: CodingStrategy
        self._init_strategy()

    def _init_strategy(self) -> None:
        """初始化策略"""
        strategy_class = self.STRATEGIES.get(self._strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {self._strategy_name}")

        if self._strategy_name == "cursor":
            self._strategy = CursorStrategy()
        elif self._strategy_name == "llm":
            llm_config = self.config.llm or CodingLLMConfig()
            self._strategy = LLMStrategy(
                api_key=llm_config.api_key,
                api_base=llm_config.api_base,
                model=llm_config.model,
            )
        elif self._strategy_name == "claude":
            claude_config = self.config.claude or CodingLLMConfig()
            self._strategy = ClaudeStrategy(api_key=claude_config.api_key)

        if self._strategy is None:
            raise RuntimeError(f"Failed to initialize strategy: {self._strategy_name}")

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CodingEngineResult:
        """
        生成代码

        Args:
            prompt: 生成提示
            context: 上下文信息

        Returns:
            CodingEngineResult
        """
        import time
        start = time.time()

        try:
            output = await self._strategy.generate_code(prompt, context)
            return CodingEngineResult(
                success=True,
                output=output,
                strategy=self._strategy_name,
                duration=time.time() - start,
            )
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return CodingEngineResult(
                success=False,
                error=str(e),
                strategy=self._strategy_name,
                duration=time.time() - start,
            )

    async def review(
        self,
        code: str,
        review_type: str = "general",
    ) -> CodingEngineResult:
        """
        审查代码

        Args:
            code: 代码内容
            review_type: 审查类型 (general/security/performance)

        Returns:
            CodingEngineResult
        """
        import time
        start = time.time()

        try:
            review_result = await self._strategy.review_code(code, review_type)
            return CodingEngineResult(
                success=review_result.get("success", False),
                output=review_result.get("review", review_result.get("output", "")),
                strategy=self._strategy_name,
                duration=time.time() - start,
                code_review=review_result,
            )
        except Exception as e:
            logger.error(f"Code review failed: {e}")
            return CodingEngineResult(
                success=False,
                error=str(e),
                strategy=self._strategy_name,
                duration=time.time() - start,
            )

    async def explain(
        self,
        code: str,
    ) -> CodingEngineResult:
        """
        解释代码

        Args:
            code: 代码内容

        Returns:
            CodingEngineResult
        """
        import time
        start = time.time()

        try:
            explanation = await self._strategy.explain_code(code)
            return CodingEngineResult(
                success=True,
                output=explanation,
                strategy=self._strategy_name,
                duration=time.time() - start,
            )
        except Exception as e:
            logger.error(f"Code explanation failed: {e}")
            return CodingEngineResult(
                success=False,
                error=str(e),
                strategy=self._strategy_name,
                duration=time.time() - start,
            )

    async def fix(
        self,
        code: str,
        error: str,
    ) -> CodingEngineResult:
        """
        修复代码

        Args:
            code: 代码内容
            error: 错误信息

        Returns:
            CodingEngineResult
        """
        import time
        start = time.time()

        try:
            fixed_code = await self._strategy.fix_code(code, error)
            return CodingEngineResult(
                success=True,
                output=fixed_code,
                strategy=self._strategy_name,
                duration=time.time() - start,
                artifacts={"fixed_code": fixed_code},
            )
        except Exception as e:
            logger.error(f"Code fix failed: {e}")
            return CodingEngineResult(
                success=False,
                error=str(e),
                strategy=self._strategy_name,
                duration=time.time() - start,
            )

    async def execute_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CodingEngineResult:
        """
        执行编码任务

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            CodingEngineResult
        """
        return await self.generate(task, context)


def create_coding_engine(
    engine: str = "llm",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
) -> CodingEngine:
    """
    创建编码引擎工厂函数

    Args:
        engine: 引擎类型 (cursor/llm/claude)
        api_key: API 密钥
        api_base: API 基础 URL

    Returns:
        CodingEngine 实例
    """
    if engine == "llm":
        llm_config = CodingLLMConfig(
            provider="deepseek",
            model="deepseek-chat",
            api_key=api_key,
            api_base=api_base,
        )
        config = CodingConfig(engine=engine, llm=llm_config)
    elif engine == "claude":
        claude_config = CodingLLMConfig(api_key=api_key)
        config = CodingConfig(engine=engine, claude=claude_config)
    else:
        config = CodingConfig(engine=engine)

    return CodingEngine(config=config, strategy_name=engine)
