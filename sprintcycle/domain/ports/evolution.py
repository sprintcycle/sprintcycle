"""Evolution 端口 - Domain 层与进化版本管理的接口

定义进化版本管理的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class EvolutionRegistryProtocol(ABC):
    """进化版本注册表协议"""

    @abstractmethod
    async def list_versions(self, target: Optional[str] = None, limit: int = 20) -> List[Any]:
        """列出版本"""
        ...

    @abstractmethod
    async def get_active(self, target: str) -> Optional[Any]:
        """获取活跃版本"""
        ...

    @abstractmethod
    async def export_manifest_index(self) -> Dict[str, Any]:
        """导出清单索引"""
        ...


class VersionManifestProtocol(ABC):
    """版本清单协议"""

    @abstractmethod
    async def get_version_manifest_summary(self, registry: Any, version_id: str) -> Dict[str, Any]:
        """获取版本清单摘要"""
        ...


# 工厂函数注册
_evolution_registry_factory: Optional[callable] = None
_version_manifest_factory: Optional[callable] = None


def register_evolution_registry_factory(factory: callable) -> None:
    """注册进化注册表工厂（由 Infrastructure 层调用）"""
    global _evolution_registry_factory
    _evolution_registry_factory = factory


def register_version_manifest_factory(factory: callable) -> None:
    """注册版本清单工厂（由 Infrastructure 层调用）"""
    global _version_manifest_factory
    _version_manifest_factory = factory


def create_evolution_registry(config: Any) -> EvolutionRegistryProtocol:
    """创建进化注册表实例"""
    if _evolution_registry_factory is not None:
        return _evolution_registry_factory(config)
    raise RuntimeError(
        "Evolution registry factory not registered. "
        "Please call register_evolution_registry_factory() from Infrastructure layer before using."
    )


def get_version_manifest_summary(registry: Any, version_id: str) -> Dict[str, Any]:
    """获取版本清单摘要"""
    if _version_manifest_factory is not None:
        return _version_manifest_factory(registry, version_id)
    raise RuntimeError(
        "Version manifest factory not registered. "
        "Please call register_version_manifest_factory() from Infrastructure layer before using."
    )


def evolution_sandbox_status(config: Any) -> Dict[str, Any]:
    """获取进化沙箱状态"""
    from sprintcycle.domain.ports.integrations import create_phoenix_exporter_spec, create_phoenix_trace_runtime
    
    try:
        exporter = create_phoenix_exporter_spec()
        runtime = create_phoenix_trace_runtime(exporter)
        return runtime.build()
    except Exception:
        return {"available": False, "message": "sandbox not configured"}


__all__ = [
    "EvolutionRegistryProtocol",
    "VersionManifestProtocol",
    "register_evolution_registry_factory",
    "register_version_manifest_factory",
    "create_evolution_registry",
    "get_version_manifest_summary",
    "evolution_sandbox_status",
]
