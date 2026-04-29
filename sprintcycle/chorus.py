#!/usr/bin/env python3
"""
SprintCycle Chorus 模块 v4.10 (向后兼容入口)

此文件已重构为 chorus 包，原有内容拆分到 chorus/ 子模块中。
请使用 `from sprintcycle.chorus import ChorusOrchestrator` 或
直接 `from sprintcycle.chorus import Chorus`。

保持向后兼容: 旧的 import 方式仍然有效。
"""
from .chorus import (
    # 枚举
    ToolType,
    AgentType,
    TaskStatus,
    # 数据类
    ExecutionResult,
    TaskProgress,
    # 核心类
    Config,
    KnowledgeBase,
    ExecutionLayer,
    ChorusAdapter,
    Chorus,
    ChorusOrchestrator,
    # 工具函数
    normalize_files_changed,
    extract_files_list,
    has_changes,
    get_change_summary,
    # 凭证管理
    get_credential_manager,
    # 向后兼容
    _get_optimizations,
)

__all__ = [
    "ToolType",
    "AgentType",
    "TaskStatus",
    "ExecutionResult",
    "TaskProgress",
    "Config",
    "KnowledgeBase",
    "ExecutionLayer",
    "ChorusAdapter",
    "Chorus",
    "ChorusOrchestrator",
    "normalize_files_changed",
    "extract_files_list",
    "has_changes",
    "get_change_summary",
    "get_credential_manager",
    "_get_optimizations",
]
