"""Agent 执行器模块 - 统一导出接口。"""

from .base import (
    AgentConfig,
    AgentType,
    AgentContext,
    AgentResult,
    AgentExecutor,
)

from .coder import (
    CoderAgent,
    EngineAdapterProtocol,
    EngineResult,
    EngineAdapterConfig,
    register_cache_backend_factory,
    register_engine_adapter_factory,
    BatchTask,
    BatchConfig,
    CodeRequirements,
    CodeResult,
)

from .tester import (
    TesterAgent,
    TestCase,
    TestType,
    TestResult,
)

from .analyzer import (
    BugAnalyzerAgent,
    BugReport,
    FixSuggestion,
    FixResult,
    AnalysisRequest,
    AnalysisResult,
    StackFrame,
    ParsedTraceback,
    PatternMatch,
    ROOT_CAUSE_PATTERNS,
    parse_traceback,
    ErrorCategory,
    Location,
    Severity,
)

from .architect import (
    ArchitectureAgent,
)

from .regression_tester import (
    RegressionTestAgent,
)

__all__ = [
    "AgentConfig",
    "AgentType",
    "AgentContext",
    "AgentResult",
    "AgentExecutor",
    "CoderAgent",
    "EngineAdapterProtocol",
    "EngineResult",
    "EngineAdapterConfig",
    "register_cache_backend_factory",
    "register_engine_adapter_factory",
    "BatchTask",
    "BatchConfig",
    "CodeRequirements",
    "CodeResult",
    "TesterAgent",
    "TestCase",
    "TestType",
    "TestResult",
    "BugAnalyzerAgent",
    "BugReport",
    "FixSuggestion",
    "FixResult",
    "AnalysisRequest",
    "AnalysisResult",
    "StackFrame",
    "ParsedTraceback",
    "PatternMatch",
    "ROOT_CAUSE_PATTERNS",
    "parse_traceback",
    "ErrorCategory",
    "Location",
    "Severity",
    "ArchitectureAgent",
    "RegressionTestAgent",
]
