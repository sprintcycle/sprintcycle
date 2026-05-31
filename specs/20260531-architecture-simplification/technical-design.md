# SprintCycle 架构精简 - 技术方案设计

**版本：** v1.0
**日期：** 2026-05-31
**状态：** 待 HITL 确认

---

## 一、架构合规性检查

### 1.1 DDD 六边形架构检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 领域层纯粹性 | ✅ | 不受影响 |
| 聚合根不可变性 | ✅ | 不受影响 |
| Port/Adapter 分离 | ✅ | 保持不变 |
| Composition Root 模式 | 🔄 | 将优化组合根实现 |
| 单层依赖规则 | ✅ | 保持不变 |

### 1.2 合规性结论

✅ **符合 DDD 六边形架构要求**
- 优化仅涉及 Composition Root 层的实现方式
- 不改变架构边界和依赖关系
- 不影响领域层纯粹性

---

## 二、方案设计原则

> **核心要求：直接实现终态方案，不添加过渡或兼容代码**

### 2.1 废弃模块清理策略

**直接删除，不保留任何兼容层：**

```
删除文件：
├── sprintcycle/application/composition/di_bridge.py
├── sprintcycle/application/composition/http_factory.py
├── sprintcycle/domain/core/governance/hitl/context.py
├── sprintcycle/domain/core/governance/hitl/config.py
└── sprintcycle/domain/core/governance/hitl/utils.py
```

**更新导入：**
- 更新 `sprintcycle/application/composition/__init__.py` - 直接从 di_container 导出
- 更新 `sprintcycle/domain/core/governance/hitl/__init__.py` - 移除兼容层导出

### 2.2 DI 容器重构策略

**使用 dependency-injector 库替换自定义容器：**

**现有结构（过度设计）：**
```python
# 431 行自定义代码，包含：
class SprintCycleContainer:
    - 5 个子容器类
    - OverrideProvider
    - OverrideContext
    - 4 层 DI 抽象
```

**终态结构（简化）：**
```python
# 使用 dependency-injector，提供统一的容器接口
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    lifecycle_service = providers.Factory(LifecycleService)
    cache_backend = providers.Singleton(CacheBackend)
    state_store = providers.Singleton(StateStore)
    runtime_config = providers.Singleton(RuntimeConfig)
    # ... 其他服务
```

**兼容性保持：**
- 保留 `container` 全局实例
- 保留 `get_container()` 函数
- 保留 `create_container()` 函数
- 更新 `lifecycle_service()` 等便捷函数

---

## 三、详细变更清单

### 3.1 Phase 1: 废弃模块清理

#### 步骤 1.1: 删除废弃文件

**文件清单：**
```bash
# 删除以下文件：
sprintcycle/application/composition/di_bridge.py
sprintcycle/application/composition/http_factory.py
sprintcycle/domain/core/governance/hitl/context.py
sprintcycle/domain/core/governance/hitl/config.py
sprintcycle/domain/core/governance/hitl/utils.py
```

#### 步骤 1.2: 更新 HITL __init__.py

**变更前：**
```python
# 从兼容层重新导出
from .config import get_hitl_timeout_seconds, is_hitl_enabled
from .context import (
    build_hitl_context,
    build_replay_context,
    ...
)
from .utils import compact_dict
```

**变更后：**
```python
# 直接从实际实现导入
from .types import (
    get_hitl_timeout_seconds,
    is_hitl_enabled,
    HitlGate,
    ...
)
from .coordinator import (
    build_hitl_context,
    build_replay_context,
    compact_dict,
    ...
)
```

#### 步骤 1.3: 更新 composition __init__.py

**变更前：**
```python
from sprintcycle.application.composition.http_factory import (
    InfrastructureFactory,
    initialize_http_infrastructure,
)
from sprintcycle.application.composition.di_container import (
    Container,
    container,
    create_container,
    get_container,
)
```

**变更后：**
```python
from sprintcycle.application.composition.di_container import (
    Container,
    container,
    create_container,
    get_container,
    initialize_http_infrastructure,
)

# 移除 InfrastructureFactory（空壳）
```

### 3.2 Phase 2: DI 容器重构

#### 步骤 2.1: 创建新的 Container 类

**新文件：** `sprintcycle/application/composition/di_container.py`

```python
"""Dependency injection container using dependency-injector.

This module provides centralized dependency injection using the
dependency-injector library, replacing the custom container.
"""

from __future__ import annotations

from dependency_injector import containers, providers
from typing import Optional, Any


class Container(containers.DeclarativeContainer):
    """Main DI container for SprintCycle."""

    # Infrastructure
    cache_backend = providers.Singleton(
        "cache_backend_provider"
    )
    state_store = providers.Singleton(
        "state_store_provider"
    )
    runtime_config = providers.Singleton(
        "runtime_config_provider"
    )
    rate_limit_adapter = providers.Singleton(
        RateLimitAdapter
    )
    audit_adapter = providers.Singleton(
        AuditAdapter
    )

    # Governance
    archguard_adapter = providers.Singleton(
        ArchGuardAdapter
    )
    grimp_adapter = providers.Singleton(
        GrimpAdapter
    )
    import_linter_adapter = providers.Singleton(
        ImportLinterAdapter
    )
    ruff_adapter = providers.Singleton(
        RuffAdapter
    )
    typecheck_adapter = providers.Singleton(
        TypecheckAdapter
    )

    # Observability
    observability_facade = providers.Singleton(
        ObservabilityFacade
    )
    diagnostic_adapter = providers.Singleton(
        DiagnosticAdapter
    )

    # Lifecycle
    lifecycle_state_machine = providers.Singleton(
        get_lifecycle_state_machine
    )
    lifecycle_service = providers.Factory(
        LifecycleService,
        state_machine=lifecycle_state_machine
    )


# Global container instance
_container_instance: Optional[Container] = None


def get_container() -> Container:
    """Get the singleton container instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = Container()
    return _container_instance


def create_container(project_path: str = ".") -> Container:
    """Create and initialize a new container instance."""
    global _container_instance
    _container_instance = Container()
    return _container_instance


def initialize_http_infrastructure(project_path: str) -> None:
    """Initialize HTTP layer infrastructure."""
    create_container(project_path=project_path)


# Backward-compatible convenience functions
def lifecycle_service() -> Any:
    """Get lifecycle service instance."""
    return get_container().lifecycle_service()


def lifecycle_state_machine() -> Any:
    """Get lifecycle state machine instance."""
    return get_container().lifecycle_state_machine()


# Module exports
container = get_container()

__all__ = [
    "Container",
    "container",
    "get_container",
    "create_container",
    "initialize_http_infrastructure",
    "lifecycle_service",
    "lifecycle_state_machine",
]
```

#### 步骤 2.2: 定义 Provider 函数

在容器初始化时注册实际的 provider 实现：

```python
def _register_providers(container: Container, project_path: str) -> None:
    """Register actual provider implementations."""
    from sprintcycle.infrastructure.adapters.generic.cache.factory import (
        create_cache_backend
    )
    from sprintcycle.infrastructure.adapters.core.execution.state_store import (
        create_state_store
    )

    # Cache backend
    container.cache_backend.override(
        providers.Factory(
            create_cache_backend,
            project_path=project_path
        )
    )

    # State store
    container.state_store.override(
        providers.Factory(create_state_store)
    )
```

#### 步骤 2.3: 更新向后兼容接口

**保留的接口：**
- `container.lifecycle_service()` → 委托给 `Container().lifecycle_service()`
- `container.lifecycle_state_machine()` → 委托给 `Container().lifecycle_state_machine()`
- `container.infrastructure.cache_backend()` → 委托给 `Container().cache_backend()`
- 等等

---

## 四、实施顺序

```
Phase 1: 废弃模块清理
├─ 步骤 1.1: 删除废弃文件
├─ 步骤 1.2: 更新 HITL __init__.py
└─ 步骤 1.3: 更新 composition __init__.py
    ↓
Phase 2: DI 容器重构
├─ 步骤 2.1: 创建新的 Container 类
├─ 步骤 2.2: 定义 Provider 函数
├─ 步骤 2.3: 更新向后兼容接口
└─ 步骤 2.4: 验证所有导入
    ↓
Phase 3: 测试验证
├─ 步骤 3.1: 运行后端测试
├─ 步骤 3.2: 验证导入
└─ 步骤 3.3: 集成测试
    ↓
Phase 4: 文档同步
└─ 更新相关文档
```

---

## 五、兼容性保持清单

| 接口 | 保留 | 说明 |
|------|------|------|
| `from sprintcycle.application.composition import container` | ✅ | 全局容器实例 |
| `from sprintcycle.application.composition import get_container` | ✅ | 获取容器函数 |
| `from sprintcycle.application.composition import create_container` | ✅ | 创建容器函数 |
| `container.lifecycle_service()` | ✅ | 生命周期服务 |
| `container.infrastructure.cache_backend()` | ✅ | 缓存后端 |
| `from sprintcycle.domain.core.governance.hitl import HitlFacade` | ✅ | HITL 门面 |
| `from sprintcycle.domain.core.governance.hitl import is_hitl_enabled` | ✅ | HITL 配置 |

---

## 六、风险缓解措施

### 6.1 示例代码失效

**影响：** 5 个示例/脚本文件引用 di_bridge

**措施：** 更新示例代码使用新路径
```python
# 变更前
from sprintcycle.application.composition.di_bridge import get_cache_backend

# 变更后
from sprintcycle.application.composition.di_container import container
cache = container.infrastructure.cache_backend()
```

### 6.2 DI 变更引入 bug

**影响：** 所有使用 container 的地方

**措施：**
1. 保留相同的公共接口
2. 逐步替换内部实现
3. 充分测试覆盖

### 6.3 文档过期

**影响：** DI 相关的迁移指南

**措施：** 删除或更新以下文档：
- `docs/DI_CONTAINER_MIGRATION_GUIDE.md` → 删除
- `docs/DI_REFACTORING_SUMMARY.md` → 删除
- `docs/ARCHITECTURE_SIMPLIFICATION.md` → 更新

---

## 七、预期效果

| 指标 | 变更前 | 变更后 | 改善 |
|------|--------|--------|------|
| DI 抽象层数 | 4 层 | 1 层 | ↓ 75% |
| 自定义容器代码 | 431 行 | ~100 行 | ↓ 77% |
| 废弃模块数 | 5 个 | 0 个 | ↓ 100% |
| 维护成本 | 高 | 低 | ↓ 明显 |

---

## 八、验证标准

- [ ] 所有废弃文件已删除
- [ ] DI 容器使用 dependency-injector
- [ ] 公共接口保持不变
- [ ] 所有测试通过
- [ ] 示例代码更新
- [ ] 文档同步更新
- [ ] 无导入错误

---

**技术方案生成时间：** 2026-05-31
**待 HITL 确认后执行**
