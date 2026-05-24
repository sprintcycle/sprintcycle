"""
Domain Validator Protocol - 领域验证器协议

定义验证器的抽象接口，供 domain 层使用。
实际验证逻辑在 domain/quality_spec/plan 中实现。
"""

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sprintcycle.domain.models import ReleasePlan
    from sprintcycle.domain.quality_spec.plan import ValidationResult as DomainValidationResult


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True  # 兼容 Execution/SprintResult
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class ValidatorProtocol:
    """验证器抽象基类"""
    
    def validate(self, plan: "ReleasePlan") -> ValidationResult:
        """验证执行计划"""
        raise NotImplementedError


# 兼容层：提供 ReleasePlanValidator 别名指向实际实现
def ReleasePlanValidator():
    """
    兼容工厂函数：创建 ReleasePlanValidator 实例
    
    请优先使用:
    - 从 sprintcycle.domain.quality_spec.plan 导入
    - 或使用 create_validator()
    """
    from sprintcycle.domain.quality_spec.plan import ReleasePlanValidator as DomainValidator
    return DomainValidator()


__all__ = [
    "ValidatorProtocol",
    "ValidationResult",
    "ReleasePlanValidator",
]
