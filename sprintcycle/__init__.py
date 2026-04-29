"""
SprintCycle - AI 驱动的敏捷开发迭代框架

版本: v0.7.1
"""

__version__ = "0.7.1"
__author__ = "SprintCycle Team"

# 核心模块 - 从 server.py 导出
from .server import (
    Chorus,
    SprintChain,
    Config,
    ToolType,
    AgentType,
    TaskStatus,
    ExecutionResult,
    TaskProgress,
    KnowledgeBase,
    ExecutionLayer,
    ChorusAdapter
)

# 模型
from .models import Sprint, Task, Project, Report

# 配置与状态
from .config import SprintCycleConfig, load_config
from .state_manager import StateManager, StateScope, StateEvent, get_state_manager, get_state, set_state

# 调度与并发
from .scheduler import SprintScheduler, Task as SchedTask, TaskStatus as SchedTaskStatus, Priority
from .scheduler import DependencyGraph, ResourcePool

# 性能与监控
from .benchmark import BenchmarkSuite, BenchmarkResult, get_benchmark_suite, get_performance_monitor
from .resource_monitor import ResourceMonitor, Alert, AlertLevel, AlertConfig, get_resource_monitor

# 状态模块
from .states import SprintState, TaskState, AgentState

# 工具
from .exceptions import SprintCycleError
from .sprint_logger import SprintLogger

__all__ = [
    # 版本
    "__version__",
    
    # 核心
    "Chorus",
    "SprintChain",
    "Config",
    "ToolType",
    "AgentType",
    "TaskStatus",
    "ExecutionResult",
    "TaskProgress",
    "KnowledgeBase",
    "ExecutionLayer",
    "ChorusAdapter",
    
    # 模型
    "Sprint",
    "Task",
    "Project",
    "Report",
    
    # 配置与状态
    "SprintCycleConfig",
    "load_config",
    "StateManager",
    "StateScope",
    "StateEvent",
    "get_state_manager",
    "get_state",
    "set_state",
    
    # 调度
    "SprintScheduler",
    "SchedTask",
    "SchedTaskStatus",
    "Priority",
    "DependencyGraph",
    "ResourcePool",
    
    # 性能
    "BenchmarkSuite",
    "BenchmarkResult",
    "get_benchmark_suite",
    "get_performance_monitor",
    
    # 监控
    "ResourceMonitor",
    "Alert",
    "AlertLevel",
    "AlertConfig",
    "get_resource_monitor",
    
    # 状态
    "SprintState",
    "TaskState",
    "AgentState",
    
    # 工具
    "SprintCycleError",
    "SprintLogger",
]
