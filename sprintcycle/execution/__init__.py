"""
Execution 模块 - 统一执行引擎
"""

from .engine import ExecutionEngine
from .strategies import NormalStrategy, EvolutionStrategy as StrategyEvolutionStrategy, ExecutionStrategy, get_strategy
from .sprint_executor import SprintExecutor, TaskStatus, TaskResult, SprintResult
from .events import EventBus, Event, EventType, get_event_bus
from .state_store import StateStore, ExecutionState, ExecutionStateStatus, get_state_store
from .feedback import FeedbackLoop, ExecutionFeedback, FeedbackLevel, FeedbackCategory
from .cache import ExecutionCache, CacheEntry, get_cache, set_cache
from .agents import (
    AgentType, AgentContext, AgentResult, AgentExecutor, CoderAgent, BatchTask, BatchConfig,
    EvolverAgent, TesterAgent, TestCase, TestType, TestResult,
)
# 错误处理组件 (新增)
from .error_knowledge import ErrorKnowledgeBase, ErrorPattern, PatternMatch, get_error_knowledge_base, reset_error_knowledge_base
from .error_router import ErrorRouter, RoutingLevel, RoutingContext, RoutingResult, get_error_router
from .rollback import RollbackManager, BackupRecord, RollbackResult, get_rollback_manager
from .error_handler import ErrorHandler, ErrorContext, FixResult, get_error_handler, reset_error_handler
# Use execution.engine.ExecutionEngine._get_evolution_engine() instead
from ..evolution.types import SprintContext

EvolutionStrategy = StrategyEvolutionStrategy


def _get_evolution_pipeline():
    """Lazy import to avoid circular dependency with evolution module"""
    from ..evolution.pipeline import EvolutionPipeline
    from ..evolution.prd_source import ManualPRDSource, DiagnosticPRDSource
    return EvolutionPipeline, ManualPRDSource, DiagnosticPRDSource

__all__ = [
    "ExecutionEngine", "SprintExecutor", "NormalStrategy", "EvolutionStrategy", "ExecutionStrategy", "get_strategy",
    "TaskStatus", "TaskResult", "SprintResult",
    "EventBus", "Event", "EventType", "get_event_bus",
    "StateStore", "ExecutionState", "ExecutionStateStatus", "get_state_store",
    "FeedbackLoop", "ExecutionFeedback", "FeedbackLevel", "FeedbackCategory",
    "ExecutionCache", "CacheEntry", "get_cache", "set_cache",
    "AgentType", "AgentContext", "AgentResult", "AgentExecutor", "CoderAgent", "BatchTask", "BatchConfig",
    "EvolverAgent", "TesterAgent", "TestCase", "TestType", "TestResult",
    # 错误处理
    "ErrorKnowledgeBase", "ErrorPattern", "PatternMatch", "get_error_knowledge_base", "reset_error_knowledge_base",
    "ErrorRouter", "RoutingLevel", "RoutingContext", "RoutingResult", "get_error_router",
    "RollbackManager", "BackupRecord", "RollbackResult", "get_rollback_manager",
    "ErrorHandler", "ErrorContext", "FixResult", "get_error_handler", "reset_error_handler",
    "EvolutionEngine", "SprintContext",
]
