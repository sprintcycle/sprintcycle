"""
Execution 模块 - Application 层。

包含执行编排、策略和钩子。
"""

from .orchestrator.execution_orchestrator import ExecutionOrchestrator, ExecutionRunRequest, ExecutionRunResult
from .orchestrator.sprint_executor import SprintExecutor, ExecutionStatus, SprintResult, TaskResult
from .orchestrator.policies import SprintEvaluator, SprintMeasurementPolicy, SprintPersistencePolicy
from .orchestrator.finalization import ReleaseFinalizationPolicy, ReleaseFinalizationResult, ReleaseFinalizationRunner
from .planners import (
    TaskContextBuilder, SprintContextBuilder, SprintLoopResultPolicy,
    ExecutionResult, ExecutionStrategy, NormalStrategy, get_strategy,
    WorkItemSplitter, IntentWorkItem
)
from .hooks import (
    HookContext, QualitySprintLifecycleHooks, QualityTaskLifecycleHooks, SkillLifecycleHook,
    ChainedSprintHooks, SprintLifecycleHooks,
    ChainedTaskHooks, TaskLifecycleHooks
)
from .core import (
    ErrorHandler, ErrorContext, FixResult, get_error_handler, reset_error_handler,
    FeedbackLoop, ExecutionFeedback, FeedbackCategory, FeedbackLevel,
    ExecutionHooks,
    WRITE_POLICIES,
    attach_workspace_metadata, apply_policy_to_tasks, build_workspace_prompt_section,
    effective_write_policy, ensure_project_layout, normalize_reference_paths, normalize_write_policy,
    AnalysisConfig, StaticAnalyzer
)

__all__ = [
    "ExecutionOrchestrator", "ExecutionRunRequest", "ExecutionRunResult",
    "SprintExecutor", "ExecutionStatus", "SprintResult", "TaskResult",
    "SprintEvaluator", "SprintMeasurementPolicy", "SprintPersistencePolicy",
    "ReleaseFinalizationPolicy", "ReleaseFinalizationResult", "ReleaseFinalizationRunner",
    "TaskContextBuilder", "SprintContextBuilder", "SprintLoopResultPolicy",
    "ExecutionResult", "ExecutionStrategy", "NormalStrategy", "get_strategy",
    "WorkItemSplitter", "IntentWorkItem",
    "HookContext", "QualitySprintLifecycleHooks", "QualityTaskLifecycleHooks", "SkillLifecycleHook",
    "ChainedSprintHooks", "SprintLifecycleHooks",
    "ChainedTaskHooks", "TaskLifecycleHooks",
    "ErrorHandler", "ErrorContext", "FixResult", "get_error_handler", "reset_error_handler",
    "FeedbackLoop", "ExecutionFeedback", "FeedbackCategory", "FeedbackLevel",
    "ExecutionHooks",
    "WRITE_POLICIES",
    "attach_workspace_metadata", "apply_policy_to_tasks", "build_workspace_prompt_section",
    "effective_write_policy", "ensure_project_layout", "normalize_reference_paths", "normalize_write_policy",
    "AnalysisConfig", "StaticAnalyzer"
]
