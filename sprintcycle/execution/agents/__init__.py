"""
Agent 执行器模块

提供多种 Agent 执行器实现：
- CoderAgent: 代码编写（含批量处理和缓存）
- EvolverAgent: 代码进化优化
- TesterAgent: 测试验证
- BugAnalyzerAgent: Bug 分析与修复

使用方式：
```python
from sprintcycle.execution.agents import CoderAgent, EvolverAgent, TesterAgent, BugAnalyzerAgent

# Coder Agent
coder = CoderAgent()
result = await coder.execute("实现登录功能", context)

# Coder Agent 批量执行
from sprintcycle.execution.agents import BatchTask, BatchConfig
tasks = [BatchTask(task="task1", context=ctx), BatchTask(task="task2", context=ctx)]
results = await coder.execute_batch(tasks)

# Evolver Agent
evolver = EvolverAgent(strategy="performance")
result = await evolver.execute("优化性能", context)

# Tester Agent
tester = TesterAgent(test_type="unit")
result = await tester.execute("测试登录模块", context)

# Bug Analyzer Agent
analyzer = BugAnalyzerAgent()
result = await analyzer.execute("分析并修复 NameError", context)
```
"""

from .base import AgentType, AgentContext, AgentResult, AgentExecutor
from .coder import CoderAgent, BatchTask, BatchConfig
from .evolver import EvolverAgent, EvolutionStrategy
from .tester import TesterAgent, TestCase, TestType, TestResult
from .analyzer import BugAnalyzerAgent
from .bug_models import (
    BugReport,
    BugSeverity,
    ErrorCategory,
    Location,
    FixSuggestion,
    FixResult,
    AnalysisRequest,
    AnalysisResult,
)

__all__ = [
    # 基础组件
    "AgentType",
    "AgentContext",
    "AgentResult",
    "AgentExecutor",
    # Coder Agent
    "CoderAgent",
    "BatchTask",
    "BatchConfig",
    # Evolver Agent
    "EvolverAgent",
    "EvolutionStrategy",
    # Tester Agent
    "TesterAgent",
    "TestCase",
    "TestType",
    "TestResult",
    # Bug Analyzer Agent
    "BugAnalyzerAgent",
    # Bug 分析数据模型
    "BugReport",
    "BugSeverity",
    "ErrorCategory",
    "Location",
    "FixSuggestion",
    "FixResult",
    "AnalysisRequest",
    "AnalysisResult",
]
