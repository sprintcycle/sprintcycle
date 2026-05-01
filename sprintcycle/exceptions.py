"""
SprintCycle 统一异常体系与公共类型

所有模块抛出的业务异常均继承自 SprintCycleError，
便于调用方统一捕获和处理。

v0.9.1: 新增统一 Severity 枚举，替代散落各处的 ErrorSeverity/BugSeverity/IssueSeverity
"""

from enum import Enum


class Severity(Enum):
    """统一严重级别枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Backward compat aliases — will be removed in v1.0
ErrorSeverity = Severity
BugSeverity = Severity
IssueSeverity = Severity


class SprintCycleError(Exception):
    """SprintCycle 基础异常"""
    pass


class ConfigError(SprintCycleError):
    """配置相关错误（缺失、无效、冲突）"""
    pass


class ExecutionError(SprintCycleError):
    """执行相关错误（任务失败、超时、Agent异常）"""
    pass


class DiagnosticError(SprintCycleError):
    """诊断相关错误（工具不可用、报告生成失败）"""
    pass


class PRDError(SprintCycleError):
    """PRD相关错误（解析失败、生成失败、验证不通过）"""
    pass


class EvolutionError(SprintCycleError):
    """进化相关错误（Pipeline异常、基因变异失败）"""
    pass


class LLMError(SprintCycleError):
    """LLM调用相关错误（API不可用、响应异常、密钥缺失）"""
    pass


__all__ = [
    "Severity",
    "ErrorSeverity",
    "BugSeverity",
    "IssueSeverity",
    "SprintCycleError",
    "ConfigError",
    "ExecutionError",
    "DiagnosticError",
    "PRDError",
    "EvolutionError",
    "LLMError",
]
