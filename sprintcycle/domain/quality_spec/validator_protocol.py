"""
Domain Validator Protocol - 领域验证器协议

定义验证器的抽象接口，供 domain 层使用。
实际验证逻辑仍在 application 层实现。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from sprintcycle.domain.models import ReleasePlan


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ValidatorProtocol:
    """验证器抽象基类"""
    
    def validate(self, plan: "ReleasePlan") -> ValidationResult:
        """验证执行计划"""
        raise NotImplementedError


# 导入实际实现（保持兼容性）
from sprintcycle.application.release_plan.validator import (
    ReleasePlanValidator as ReleasePlanValidator,
    ValidationError,
    ValidationResult as AppValidationResult,
)

__all__ = [
    "ValidatorProtocol",
    "ValidationResult",
    "ReleasePlanValidator",
    "ValidationError",
]
