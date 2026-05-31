"""架构守卫端口 - Domain 层与治理检查工具的接口

定义架构守卫适配器的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class GuardFindingLike:
    """GuardFinding 类型协议"""
    rule_id: str
    severity: str
    message: str
    location: dict


class ArchGuardAdapterProtocol(ABC):
    """架构守卫适配器协议"""

    @abstractmethod
    def run(self, project_root: str) -> List[GuardFindingLike]:
        """运行架构检查"""
        ...


class GrimpAdapterProtocol(ABC):
    """Grimp 依赖分析适配器协议"""

    @abstractmethod
    def run(self, project_root: str) -> List[GuardFindingLike]:
        """运行依赖分析"""
        ...


class ImportLinterAdapterProtocol(ABC):
    """Import Linter 适配器协议"""

    @abstractmethod
    def run(self, project_root: str) -> List[GuardFindingLike]:
        """运行导入检查"""
        ...


class RuffAdapterProtocol(ABC):
    """Ruff 代码检查适配器协议"""

    @abstractmethod
    def run(self, project_root: str) -> List[GuardFindingLike]:
        """运行代码检查"""
        ...


class TypeCheckAdapterProtocol(ABC):
    """类型检查适配器协议"""

    @abstractmethod
    def run(self, project_root: str) -> List[GuardFindingLike]:
        """运行类型检查"""
        ...


__all__ = [
    "GuardFindingLike",
    "ArchGuardAdapterProtocol",
    "GrimpAdapterProtocol",
    "ImportLinterAdapterProtocol",
    "RuffAdapterProtocol",
    "TypeCheckAdapterProtocol",
]
