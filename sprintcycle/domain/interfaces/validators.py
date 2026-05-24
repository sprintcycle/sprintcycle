"""
Domain 层验证器接口定义

使用纯领域层验证器，无任何外部依赖。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sprintcycle.domain.models import ReleasePlan
    from sprintcycle.domain.quality_spec.plan import ValidationResult


class ValidatorProtocol(ABC):
    """验证器抽象基类"""

    @abstractmethod
    def validate(self, plan: ReleasePlan) -> Any:
        """验证执行计划"""
        raise NotImplementedError


# 全局验证器实例（延迟初始化）
_validator_instance: ValidatorProtocol | None = None


def create_validator() -> ValidatorProtocol:
    """工厂函数：创建验证器实例（使用纯领域层实现）"""
    global _validator_instance
    if _validator_instance is None:
        from sprintcycle.domain.quality_spec.plan import ReleasePlanValidator

        _validator_instance = ReleasePlanValidator()
    return _validator_instance


def get_validator() -> ValidatorProtocol:
    """获取验证器实例"""
    return create_validator()


__all__ = [
    "ValidatorProtocol",
    "create_validator",
    "get_validator",
]
