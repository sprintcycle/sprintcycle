"""
Agent 执行器模块

提供多种 Agent 执行器实现：
- CoderAgent: 代码编写
- EvolverAgent: 代码进化优化
- TesterAgent: 测试验证
"""

from .base import AgentType, AgentContext, AgentResult, AgentExecutor
from .coder import CoderAgent
from .evolver import EvolverAgent, EvolutionStrategy
from .tester import TesterAgent, TestCase, TestType, TestResult

__all__ = [
    # 基础组件
    "AgentType",
    "AgentContext",
    "AgentResult",
    "AgentExecutor",
    # Coder Agent
    "CoderAgent",
    # Evolver Agent
    "EvolverAgent",
    "EvolutionStrategy",
    # Tester Agent
    "TesterAgent",
    "TestCase",
    "TestType",
    "TestResult",
]
