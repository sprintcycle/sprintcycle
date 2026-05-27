"""Domain 层端口定义 - DDD 六边形架构的核心接口

定义 Domain 层与外部世界交互的协议，由 Infrastructure 层实现并通过工厂注入。

端口分类：
- 状态存储端口 (state_store.py)
- 缓存端口 (cache.py)
- 架构守卫端口 (governance.py)
- 配置端口 (config.py)
- 集成适配器端口 (integrations.py)
- 限流端口 (rate_limit.py)
- 审计端口 (audit.py)
- LLM 引擎端口 (llm.py)
- 部署端口 (deploy.py)
- 诊断端口 (diagnostics.py)
- 演化端口 (evolution.py)
- 治理端口 (governance.py)
- HITL 端口 (hitl.py)
- 知识端口 (knowledge.py)
- 编排端口 (orchestration.py)
- 注册端口 (registry.py)
- 建议端口 (suggestion.py)
- 可观测性端口 (observability.py)
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
from .rate_limit import RateLimitPort, RateLimitState
from .audit import AuditPort, AuditRecord
from .diagnostics import DiagnosticPort
from .llm import (
    EngineResult,
    EngineAdapterConfig,
    EngineAdapterProtocol,
    register_engine_adapter_factory,
    resolve_engine_adapter,
)
from .deploy import PlatformLaunchServiceProtocol
from .evolution import EvolutionRegistryProtocol, VersionManifestProtocol
from .hitl import HitlStoreProtocol
from .knowledge import KnowledgeRepositoryProtocol, SprintOutcomeCardAdapter
from .orchestration import RuntimeConfigPort, TraceRuntimePort
from .registry import RuntimeRegistryProtocol
from .suggestion import SuggestionStoreProtocol
from .observability import ObservabilityFacadeProtocol

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
    # 限流端口
    "RateLimitPort",
    "RateLimitState",
    # 审计端口
    "AuditPort",
    "AuditRecord",
    # 诊断端口
    "DiagnosticPort",
    # LLM 引擎端口
    "EngineResult",
    "EngineAdapterConfig",
    "EngineAdapterProtocol",
    "register_engine_adapter_factory",
    "resolve_engine_adapter",
    # 部署端口
    "PlatformLaunchServiceProtocol",
    # 演化端口
    "EvolutionRegistryProtocol",
    "VersionManifestProtocol",
    # HITL 端口
    "HitlStoreProtocol",
    # 知识端口
    "KnowledgeRepositoryProtocol",
    "SprintOutcomeCardAdapter",
    # 编排端口
    "RuntimeConfigPort",
    "TraceRuntimePort",
    # 注册端口
    "RuntimeRegistryProtocol",
    # 建议端口
    "SuggestionStoreProtocol",
    # 可观测性端口
    "ObservabilityFacadeProtocol",
]