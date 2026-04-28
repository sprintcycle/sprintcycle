"""
Execution 模块 - 统一执行引擎

提供策略模式的执行架构，支持 Normal 和 Evolution 两种模式。
"""

from .engine import ExecutionEngine
from .strategies import NormalStrategy, EvolutionStrategy as StrategyEvolutionStrategy, ExecutionStrategy, get_strategy
from .sprint_executor import SprintExecutor, TaskStatus, TaskResult, SprintResult
from .events import EventBus, Event, EventType, get_event_bus
from .state_store import StateStore, ExecutionState, ExecutionStateStatus, get_state_store
from .feedback import FeedbackLoop, ExecutionFeedback, FeedbackLevel, FeedbackCategory
from .agents import (
    AgentType,
    AgentContext,
    AgentResult,
    AgentExecutor,
    CoderAgent,
    EvolverAgent,
    TesterAgent,
    TestCase,
    TestType,
    TestResult,
)
from ..evolution.engine import EvolutionEngine
from ..evolution.config import EvolutionEngineConfig
from ..evolution.types import SprintContext

# 重命名以避免与 agents.EvolutionStrategy 冲突
EvolutionStrategy = StrategyEvolutionStrategy

__all__ = [
    # 核心组件
    "ExecutionEngine",
    "SprintExecutor",
    # 策略
    "NormalStrategy",
    "EvolutionStrategy",
    "ExecutionStrategy",
    "get_strategy",
    # 任务执行
    "TaskStatus",
    "TaskResult",
    "SprintResult",
    # 事件系统
    "EventBus",
    "Event",
    "EventType",
    "get_event_bus",
    # 状态持久化
    "StateStore",
    "ExecutionState",
    "ExecutionStateStatus",
    "get_state_store",
    # 反馈闭环
    "FeedbackLoop",
    "ExecutionFeedback",
    "FeedbackLevel",
    "FeedbackCategory",
    # Agent 执行器
    "AgentType",
    "AgentContext",
    "AgentResult",
    "AgentExecutor",
    "CoderAgent",
    "EvolverAgent",
    "TesterAgent",
    "TestCase",
    "TestType",
    "TestResult",
    # Evolution 集成
    "EvolutionEngine",
    "EvolutionEngineConfig",
    "SprintContext",
]
