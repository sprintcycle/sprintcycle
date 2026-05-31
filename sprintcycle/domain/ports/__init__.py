"""Domain 层端口定义 - DDD 六边形架构的外部端口 (Ports)

**职责边界:**
- 定义 Domain 层与外部世界交互的协议
- 六边形架构的输入/输出端口
- 由 Infrastructure 层实现并通过 Container 注入

**与 domain/generic/interfaces 的区别:**
- `domain/ports/`: 外部端口，定义与外部系统的交互协议（如数据库、缓存、LLM、第三方服务）
- `domain/generic/interfaces/`: 领域层内部的通用接口，定义子域间的协作契约

**端口分类:**
- 状态存储端口 (state_store.py): 持久化存储
- 缓存端口 (cache.py): 缓存服务
- 架构守卫端口 (governance.py): 架构检查工具适配器
- 配置端口 (config.py): 运行时配置
- 集成适配器端口 (integrations.py): 第三方服务集成（LangGraph、Phoenix 等）
- 限流端口 (rate_limit.py): 限流服务
- 审计端口 (audit.py): 审计日志
- LLM 引擎端口 (llm.py): LLM 引擎调用
- 部署端口 (deploy.py): 部署服务
- 诊断端口 (diagnostics.py): 诊断服务
- 演化端口 (evolution.py): 版本演化
- HITL 端口 (hitl.py): 人类在环服务
- 知识端口 (knowledge.py): 知识管理
- 编排端口 (orchestration.py): 执行编排
- 注册端口 (registry.py): 运行时注册
- 建议端口 (suggestion.py): 建议存储
- 可观测性端口 (observability.py): 可观测性集成
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
