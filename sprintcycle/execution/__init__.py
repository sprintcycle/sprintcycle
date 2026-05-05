"""
Execution 模块 - 统一执行引擎
"""

# Use execution.engine.ExecutionEngine._get_evolution_engine() instead
from ..evolution.types import SprintContext
from .agents import (
    AgentContext,
    AgentExecutor,
    AgentResult,
    AgentType,
    BatchConfig,
    BatchTask,
    CoderAgent,
    EvolverAgent,
    TestCase,
    TesterAgent,
    TestResult,
    TestType,
)
from .cache import CacheEntry, ExecutionCache, get_cache, set_cache
from .engine import ExecutionEngine
from .error_handler import ErrorContext, ErrorHandler, FixResult, get_error_handler, reset_error_handler

# 错误处理组件 (新增)
from .error_knowledge import (
    ErrorKnowledgeBase,
    ErrorPattern,
    PatternMatch,
    get_error_knowledge_base,
    reset_error_knowledge_base,
)
from .error_router import ErrorRouter, RoutingContext, RoutingLevel, RoutingResult, get_error_router
from .events import Event, EventBus, EventType, get_event_bus
from .feedback import ExecutionFeedback, FeedbackCategory, FeedbackLevel, FeedbackLoop
from .hooks.sprint_hooks import ChainedSprintHooks, NoOpSprintLifecycleHooks, SprintLifecycleHooks
from .rollback import BackupRecord, RollbackConfig, RollbackManager, RollbackResult, get_rollback_manager
from .sprint_executor import ExecutionStatus, SprintExecutor, SprintResult, TaskResult
from .state.sqlite_state_store import SqliteExecutionStore
from .state.state_store import (
    ExecutionState,
    StateStore,
    configure_default_store,
    get_state_store,
    reset_default_state_store,
)
from .strategies import EvolutionStrategy as StrategyEvolutionStrategy
from .strategies import ExecutionStrategy, NormalStrategy, get_strategy

EvolutionStrategy = StrategyEvolutionStrategy


def _get_evolution_pipeline():
    """Lazy import to avoid circular dependency with evolution module"""
    from ..evolution.evolution_plan_source import DiagnosticPRDSource, ManualPRDSource
    from ..evolution.pipeline import EvolutionPipeline
    return EvolutionPipeline, ManualPRDSource, DiagnosticPRDSource

__all__ = [
    "ExecutionEngine", "SprintExecutor", "NormalStrategy", "EvolutionStrategy", "ExecutionStrategy", "get_strategy",
    "ExecutionStatus", "TaskResult", "SprintResult",
    "EventBus", "Event", "EventType", "get_event_bus",
    "StateStore", "ExecutionState", "get_state_store", "configure_default_store", "reset_default_state_store",
    "SqliteExecutionStore",
    "FeedbackLoop", "ExecutionFeedback", "FeedbackLevel", "FeedbackCategory",
    "SprintLifecycleHooks", "NoOpSprintLifecycleHooks", "ChainedSprintHooks",
    "ExecutionCache", "CacheEntry", "get_cache", "set_cache",
    "AgentType", "AgentContext", "AgentResult", "AgentExecutor", "CoderAgent", "BatchTask", "BatchConfig",
    "EvolverAgent", "TesterAgent", "TestCase", "TestType", "TestResult",
    # 错误处理
    "ErrorKnowledgeBase", "ErrorPattern", "PatternMatch", "get_error_knowledge_base", "reset_error_knowledge_base",
    "ErrorRouter", "RoutingLevel", "RoutingContext", "RoutingResult", "get_error_router",
    "RollbackManager", "BackupRecord", "RollbackResult", "get_rollback_manager", "RollbackConfig",
    "ErrorHandler", "ErrorContext", "FixResult", "get_error_handler", "reset_error_handler",
    "SprintContext",
]
