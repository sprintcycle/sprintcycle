"""
Domain 层验证器接口定义

使用工厂模式消除 Domain → Application 的运行时依赖。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sprintcycle.domain.models import ReleasePlan


class ValidatorProtocol(ABC):
    """验证器抽象基类"""

    @abstractmethod
    def validate(self, plan: "ReleasePlan") -> Any:
        """验证执行计划"""
        raise NotImplementedError


# 全局验证器实例（延迟初始化）
_validator_instance: ValidatorProtocol | None = None


def create_validator() -> ValidatorProtocol:
    """工厂函数：创建验证器实例（延迟导入 Application 实现）"""
    global _validator_instance
    if _validator_instance is None:
        from sprintcycle.application.release_plan.validator import ReleasePlanValidator

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
