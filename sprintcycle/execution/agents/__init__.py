"""
Agent 执行器模块

提供多种 Agent 执行器实现：
- CoderAgent: 代码编写（含批量处理和缓存）
- TesterAgent: 测试验证
- BugAnalyzerAgent: Bug 分析与修复
- ArchitectureAgent: 架构设计
- RegressionTestAgent: 回归测试

``EvolutionPath`` 定义于 ``release_plan.expand``（自进化展开时的策略维度枚举）。

使用方式：
```python
from sprintcycle.execution.agents import CoderAgent, TesterAgent, BugAnalyzerAgent

# Coder Agent
coder = CoderAgent()
result = await coder.execute("实现登录功能", context)

# Coder Agent 批量执行
from sprintcycle.execution.agents import BatchTask, BatchConfig
tasks = [BatchTask(task="task1", context=ctx), BatchTask(task="task2", context=ctx)]
results = await coder.execute_batch(tasks)

# Tester Agent
tester = TesterAgent(test_type="unit")
result = await tester.execute("测试登录模块", context)

# Bug Analyzer Agent
analyzer = BugAnalyzerAgent()
result = await analyzer.execute("分析并修复 NameError", context)
```
"""

from ...application.release_plan.expand import EvolutionPath
from .analyzer import BugAnalyzerAgent
from .architect import ArchitectureAgent
from .base import AgentContext, AgentExecutor, AgentResult, AgentType
from .bug_models import (
    AnalysisRequest,
    AnalysisResult,
    BugReport,
    ErrorCategory,
    FixResult,
    FixSuggestion,
    Location,
    Severity,
)
from .coder_base import CoderAgent
from .coder_types import BatchConfig, BatchTask
from .regression_tester import RegressionTestAgent
from .tester import TestCase, TesterAgent, TestResult, TestType

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
    "EvolutionPath",
    # Tester Agent
    "TesterAgent",
    "TestCase",
    "TestType",
    "TestResult",
    # Architecture Agent
    "ArchitectureAgent",
    # Regression Test Agent
    "RegressionTestAgent",
    # Bug Analyzer Agent
    "BugAnalyzerAgent",
    # Bug 分析数据模型
    "BugReport",
    "Severity",
    "ErrorCategory",
    "Location",
    "FixSuggestion",
    "FixResult",
    "AnalysisRequest",
    "AnalysisResult",
]
