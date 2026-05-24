"""
Execution Domain 层 - 核心执行逻辑的领域模型

本模块包含 Execution 相关的领域对象：
- agents: Agent 执行器（AgentExecutor, CoderAgent, TesterAgent 等）
- core: 核心领域类型（ExecutionContext, EventBus, ExecutionStateMachine 等）
- project_write: 项目写入策略
"""

from sprintcycle.domain.execution.agents import (
    AgentContext,
    AgentExecutor,
    AgentResult,
    AgentType,
    ArchitectureAgent,
    BatchConfig,
    BatchTask,
    BugAnalyzerAgent,
    CoderAgent,
    EvolutionPath,
    RegressionTestAgent,
    TesterAgent,
    TestCase,
    TestResult,
    TestType,
)
from sprintcycle.domain.execution.core import (
    ExecutionContext,
    ExecutionEvent,
    ExecutionEventBus,
    ExecutionState,
    ExecutionStateMachine,
)
from sprintcycle.domain.execution.project_write import (
    BackupRecord,
    ChangeHint,
    GitRecord,
    IncrementalDiffSummary,
    ProjectWritePlan,
    ProjectWriteStrategy,
    ReferenceProjectSummary,
)

__all__ = [
    # Agents
    "AgentType",
    "AgentContext",
    "AgentResult",
    "AgentExecutor",
    "CoderAgent",
    "BatchTask",
    "BatchConfig",
    "EvolutionPath",
    "TesterAgent",
    "TestCase",
    "TestType",
    "TestResult",
    "ArchitectureAgent",
    "RegressionTestAgent",
    "BugAnalyzerAgent",
    # Core
    "ExecutionContext",
    "ExecutionState",
    "ExecutionStateMachine",
    "ExecutionEvent",
    "ExecutionEventBus",
    # Project Write
    "ProjectWriteStrategy",
    "ProjectWritePlan",
    "ReferenceProjectSummary",
    "BackupRecord",
    "GitRecord",
    "ChangeHint",
    "IncrementalDiffSummary",
]
