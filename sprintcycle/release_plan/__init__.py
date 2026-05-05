"""
SprintCycle Release Plan 模块（工程包名 ``release_plan``）

提供可执行多 Sprint 计划（类型仍导出为 ``PRD`` 等）的解析、验证与模板。
"""

from .parser import PRD, PRDProject, PRDSprint, PRDTask, PRDParser
from .validator import PRDValidator, ValidationError, ValidationResult

__all__ = [
    "PRD",
    "PRDProject", 
    "PRDSprint",
    "PRDTask",
    "PRDParser",
    "PRDValidator",
    "ValidationError",
    "ValidationResult",
]
