"""
Agent 执行器基类 - 定义 Agent 执行器抽象架构
包含完整的模板方法模式和重试机制

v0.9.2: 使用 tenacity 进行重试
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime
import os
import logging
import asyncio

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


class AgentType(Enum):
    CODER = "coder"
    EVOLVER = "evolver"
    TESTER = "tester"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    REGRESSION_TESTER = "regression_tester"
    CUSTOM = "custom"


class _AgentRetryableError(Exception):
    """Agent 执行可重试错误（由 tenacity 处理重试）"""
    pass


@dataclass
class AgentConfig:
    llm_provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""
    api_base: str = ""
    max_retries: int = 3
    timeout: int = 300
    temperature: float = 0.7
    retry_delay: float = 1.0
    retry_backoff: float = 1.0  # 指数退避乘数
    retry_max_delay: float = 60.0  # 最大重试延迟（秒）
    use_cursor: bool = False
    cursor_path: str = "cursor"
    mock_mode: bool = False
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("LLM_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_base:
            self.api_base = os.environ.get("LLM_API_BASE", "")
        if not self.model:
            self.model = os.environ.get("LLM_MODEL", "gpt-4")
        if not self.llm_provider:
            self.llm_provider = os.environ.get("LLM_PROVIDER", "openai")


@dataclass
class AgentContext:
    prd_id: str = ""
    prd_name: str = ""
    project_goals: str = ""
    sprint_name: str = ""
    sprint_index: int = 0
    iteration: int = 1
    dependencies: Dict[str, Any] = field(default_factory=dict)
    codebase_context: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    feedback_history: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_feedback(self, feedback: str) -> None:
        self.feedback_history.append(feedback)
    
    def get_dependency(self, key: str, default: Any = None) -> Any:
        return self.dependencies.get(key, default)


@dataclass
class AgentResult:
    success: bool
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    feedback: Optional[str] = None
    agent_type: AgentType = AgentType.CUSTOM
    task_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    
    def add_artifact(self, key: str, value: Any) -> None:
        self.artifacts[key] = value
    
    def add_metric(self, key: str, value: Any) -> None:
        self.metrics[key] = value
    
    def set_feedback(self, feedback: str) -> None:
        self.feedback = feedback
    
    @classmethod
    def from_error(cls, error: str, agent_type: AgentType = AgentType.CUSTOM) -> "AgentResult":
        return cls(success=False, error=error, agent_type=agent_type)


class AgentExecutor(ABC):
    """
    Agent 执行器抽象基类
    模板方法执行流程：
    1. pre_execute - 执行前钩子
    2. _validate - 任务验证
    3. _before_execute - 前置处理钩子
    4. _do_execute [重试循环] - 核心执行逻辑
    5. _on_error - 错误处理钩子
    6. _after_execute - 后置处理钩子
    7. post_execute - 执行后钩子
    
    重试机制：使用 tenacity 进行指数退避重试
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self._name = self.__class__.__name__
        self._config = config or AgentConfig()
        self._logger = logging.getLogger(self._name)
        self._hooks: Dict[str, List[Callable]] = {
            "pre_execute": [], "post_execute": [], "on_error": [], "on_retry": [],
        }
    
    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        pass
    
    @property
    def config(self) -> AgentConfig:
        """公开的配置属性，供外部访问"""
        return self._config
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        if hook_name in self._hooks:
            self._hooks[hook_name].append(callback)
    
    def _is_retryable(self, exc: Exception) -> bool:
        """判断异常是否可重试"""
        retryable_types = (ConnectionError, TimeoutError, asyncio.TimeoutError)
        non_retryable_types = (ValueError, TypeError, KeyError, AttributeError)
        
        if isinstance(exc, retryable_types):
            return True
        if isinstance(exc, non_retryable_types):
            return False
        
        error_msg = str(exc).lower()
        retryable_keywords = ["timeout", "connection", "network", "temporary", "rate limit"]
        non_retryable_keywords = ["invalid", "not found", "permission denied", "unauthorized"]
        
        for keyword in retryable_keywords:
            if keyword in error_msg:
                return True
        for keyword in non_retryable_keywords:
            if keyword in error_msg:
                return False
        
        return True  # 默认认为可重试
    
    async def execute(self, task: str, context: AgentContext) -> AgentResult:
        """执行任务（带重试）"""
        start_time = datetime.now()
        
        await self._run_hooks("pre_execute", task, context)
        
        # 验证
        if not self._validate(task):
            result = AgentResult.from_error(f"任务验证失败: {task[:50]}...", self.agent_type)
            await self._handle_validation_failure(result, task, context)
            await self._run_hooks("post_execute", result, context)
            return result
        
        await self._before_execute(task, context)
        
        # 执行核心逻辑（带 tenacity 重试）
        result = await self._execute_with_tenacity(task, context)
        
        # 后置处理
        if not result.success:
            await self._on_error(result, context)
        
        await self._after_execute(result, context)
        result.duration = (datetime.now() - start_time).total_seconds()
        await self._run_hooks("post_execute", result, context)
        
        return result
    
    async def _execute_with_tenacity(self, task: str, context: AgentContext) -> AgentResult:
        """使用 tenacity 进行重试"""
        
        @retry(
            stop=stop_after_attempt(self._config.max_retries + 1),
            wait=wait_exponential(
                multiplier=self._config.retry_backoff,
                min=4,
                max=self._config.retry_max_delay,
            ),
            retry=retry_if_exception_type(_AgentRetryableError),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        async def _try_execute() -> AgentResult:
            try:
                result = await self._do_execute(task, context)
                result.agent_type = self.agent_type
                result.task_name = task
                return result
            except Exception as e:
                if self._is_retryable(e):
                    raise _AgentRetryableError(str(e)) from e
                raise
        
        try:
            return await _try_execute()
        except _AgentRetryableError as e:
            return AgentResult.from_error(f"重试耗尽: {e}", self.agent_type)
        except Exception as e:
            return AgentResult.from_error(str(e), self.agent_type)
    
    async def _run_hooks(self, hook_name: str, *args: Any, **kwargs: Any) -> None:
        for callback in self._hooks.get(hook_name, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                self._logger.warning(f"钩子 {hook_name} 执行失败: {e}")
    
    def _validate(self, task: str) -> bool:
        if not task or not task.strip():
            return False
        return True
    
    async def _handle_validation_failure(self, result: AgentResult, task: str, context: AgentContext) -> None:
        pass
    
    async def pre_execute(self, task: str, context: AgentContext) -> None:
        pass
    
    async def _before_execute(self, task: str, context: AgentContext) -> None:
        pass
    
    async def _on_retry(self, task: str, context: AgentContext, retry_count: int) -> None:
        self._logger.info(f"准备重试 (第 {retry_count} 次): {task[:50]}...")
        context.metadata["retry_count"] = retry_count
    
    async def _on_error(self, result: AgentResult, context: AgentContext) -> None:
        error_msg = result.error or "未知错误"
        self._logger.error(f"Agent {self.agent_type.value} 执行失败: {error_msg}")
        if context:
            context.add_feedback(f"[ERROR] {error_msg}")
    
    async def _after_execute(self, result: AgentResult, context: AgentContext) -> None:
        if result.feedback and context:
            context.add_feedback(result.feedback)
    
    async def post_execute(self, result: AgentResult, context: AgentContext) -> None:
        pass
    
    @abstractmethod
    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        pass
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        if not self._config:
            return False
        if self._config.max_retries < 0:
            return False
        if self._config.timeout <= 0:
            return False
        if self._config.retry_backoff <= 0:
            return False
        if self._config.retry_max_delay <= 0:
            return False
        return True


__all__ = ["AgentConfig", "AgentType", "AgentContext", "AgentResult", "AgentExecutor"]
