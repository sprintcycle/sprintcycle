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


# 工厂函数注册
_archguard_adapter_factory: Optional[callable] = None
_grimp_adapter_factory: Optional[callable] = None
_import_linter_adapter_factory: Optional[callable] = None
_ruff_adapter_factory: Optional[callable] = None
_typecheck_adapter_factory: Optional[callable] = None


def register_archguard_adapter_factory(factory: callable) -> None:
    global _archguard_adapter_factory
    _archguard_adapter_factory = factory


def register_grimp_adapter_factory(factory: callable) -> None:
    global _grimp_adapter_factory
    _grimp_adapter_factory = factory


def register_import_linter_adapter_factory(factory: callable) -> None:
    global _import_linter_adapter_factory
    _import_linter_adapter_factory = factory


def register_ruff_adapter_factory(factory: callable) -> None:
    global _ruff_adapter_factory
    _ruff_adapter_factory = factory


def register_typecheck_adapter_factory(factory: callable) -> None:
    global _typecheck_adapter_factory
    _typecheck_adapter_factory = factory


def get_archguard_adapter() -> ArchGuardAdapterProtocol:
    if _archguard_adapter_factory is not None:
        return _archguard_adapter_factory()
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import ArchonAdapter
    return ArchonAdapter()


def get_grimp_adapter() -> GrimpAdapterProtocol:
    if _grimp_adapter_factory is not None:
        return _grimp_adapter_factory()
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import GrimpAdapter
    return GrimpAdapter()


def get_import_linter_adapter() -> ImportLinterAdapterProtocol:
    if _import_linter_adapter_factory is not None:
        return _import_linter_adapter_factory()
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import ImportLinterAdapter
    return ImportLinterAdapter()


def get_ruff_adapter() -> RuffAdapterProtocol:
    if _ruff_adapter_factory is not None:
        return _ruff_adapter_factory()
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import RuffAdapter
    return RuffAdapter()


def get_typecheck_adapter() -> TypeCheckAdapterProtocol:
    if _typecheck_adapter_factory is not None:
        return _typecheck_adapter_factory()
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import TypeCheckAdapter
    return TypeCheckAdapter()


__all__ = [
    "GuardFindingLike",
    "ArchGuardAdapterProtocol",
    "GrimpAdapterProtocol",
    "ImportLinterAdapterProtocol",
    "RuffAdapterProtocol",
    "TypeCheckAdapterProtocol",
    "register_archguard_adapter_factory",
    "register_grimp_adapter_factory",
    "register_import_linter_adapter_factory",
    "register_ruff_adapter_factory",
    "register_typecheck_adapter_factory",
    "get_archguard_adapter",
    "get_grimp_adapter",
    "get_import_linter_adapter",
    "get_ruff_adapter",
    "get_typecheck_adapter",
]
