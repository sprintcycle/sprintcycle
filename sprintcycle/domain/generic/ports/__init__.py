"""Domain 层端口定义 - DDD 六边形架构的核心接口

定义 Domain 层与外部世界交互的协议，由 Infrastructure 层实现并通过工厂注入。

端口分类：
- 状态存储端口 (state_store.py)
- 缓存端口 (cache.py)
- 架构守卫端口 (governance.py)
- 配置端口 (config.py)
- 集成适配器端口 (integrations.py)
"""

from .state_store import StateStoreProtocol, ExecutionState
from .cache import CacheBackendProtocol
from .governance import (
    ArchGuardAdapterProtocol,
    GrimpAdapterProtocol,
    ImportLinterAdapterProtocol,
    RuffAdapterProtocol,
    TypeCheckAdapterProtocol,
)
from .config import RuntimeConfigProtocol
from .integrations import (
    AutoGPTComposeSpecProtocol,
    AutoGPTRuntimeSpecProtocol,
    LangGraphRuntimeAdapterProtocol,
    PhoenixExporterSpecProtocol,
    PhoenixTraceRuntimeProtocol,
)

__all__ = [
    # 状态存储端口
    "StateStoreProtocol",
    "ExecutionState",
    # 缓存端口
    "CacheBackendProtocol",
    # 架构守卫端口
    "ArchGuardAdapterProtocol",
    "GrimpAdapterProtocol",
    "ImportLinterAdapterProtocol",
    "RuffAdapterProtocol",
    "TypeCheckAdapterProtocol",
    # 配置端口
    "RuntimeConfigProtocol",
    # 集成适配器端口
    "AutoGPTComposeSpecProtocol",
    "AutoGPTRuntimeSpecProtocol",
    "LangGraphRuntimeAdapterProtocol",
    "PhoenixExporterSpecProtocol",
    "PhoenixTraceRuntimeProtocol",
]
