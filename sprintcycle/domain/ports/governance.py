"""架构守卫端口 - Domain 层与治理检查工具的接口

定义架构守卫适配器的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class GuardFindingLike:
    """GuardFinding 类型协议"""
    rule_id: str
    severity: str
    message: str
    location: dict


class LinterAdapterProtocol(ABC):
    """统一的代码检查/架构分析适配器协议
    
    合并了原来的 5 个相似协议，简化为一个通用接口
    """

    @abstractmethod
    def run(self, project_root: str) -> List[GuardFindingLike]:
        """运行检查或分析"""
        ...


__all__ = [
    "GuardFindingLike",
    "LinterAdapterProtocol",
]
