# SprintCycle 依赖注入重构指南

## 📋 重构概览

本次重构引入了 **dependency-injector** 框架，实现了声明式依赖注入管理。

### 主要变化

| 方面 | 重构前 | 重构后 |
|------|--------|--------|
| **依赖管理** | 手动工厂注册 + 全局变量 | 声明式 Container |
| **代码量** | 每个端口约 35 行样板 | 每个端口约 1-2 行配置 |
| **依赖关系** | 分散在多个文件 | 集中在 Container |
| **测试 Mock** | 手动替换全局变量 | Container.override() |
| **生命周期** | 手动管理 | 自动 Singleton/Factory |

### 文件结构变化

```
重构前:
├── domain/ports/
│   ├── cache.py (Protocol + 全局工厂)
│   ├── state_store.py (Protocol + 全局工厂)
│   └── ... (每个端口都有工厂注册代码)
└── infrastructure/
    └── factory.py (注册所有工厂)

重构后:
├── domain/ports/
│   ├── cache.py (仅 Protocol)
│   ├── state_store.py (仅 Protocol)
│   └── ... (仅定义接口)
├── application/composition/
│   ├── di_container.py (新的 Container)
│   └── di_bridge.py (向后兼容桥接)
└── infrastructure/
    └── (不再需要 factory.py)
```

## 🚀 快速开始

### 1. 安装依赖

```bash
uv pip install "dependency-injector>=4.40.0"
```

### 2. 基本使用

```python
from sprintcycle.application.composition.di_container import container

# 获取单例服务
cache = container.cache_backend()
state_store = container.state_store()

# 获取应用服务
service = container.my_application_service()
```

### 3. 配置注入

```python
from sprintcycle.application.composition.di_container import create_container

# 创建并配置容器
container = create_container(
    project_path="/path/to/project",
    state_store_dir="/path/to/state",
)

# 使用配置好的容器
config = container.runtime_config()
```

### 4. 测试 Mock

```python
from sprintcycle.application.composition.di_container import container

def test_my_service():
    # 创建一个简单的 Mock
    class MockCache:
        def get(self, key):
            return "mocked_value"
        # ... 实现其他方法

    # Override 替换真实实现
    with container.cache_backend.override(MockCache()):
        # 在这个上下文中，所有获取 cache_backend 的代码都会得到 MockCache
        service = MyService()
        result = service.do_something()
        assert result == "mocked_value"

    # 退出上下文后，自动恢复真实实现
```

## 📖 迁移指南

### 旧代码 → 新代码

#### 1. 导入变化

```python
# ❌ 旧代码（不再推荐）
from sprintcycle.domain.ports.cache import get_cache_backend, register_cache_backend_factory
cache = get_cache_backend()

# ✅ 新代码（推荐）
from sprintcycle.application.composition.di_container import container
cache = container.cache_backend()
```

#### 2. 应用服务获取

```python
# ❌ 旧代码
from sprintcycle.interfaces.http.handlers.services import ServiceAggregator
aggregator = ServiceAggregator(project_path)
execution_service = aggregator._execution_lifecycle

# ✅ 新代码
from sprintcycle.application.composition.di_container import container
service = container.execution_service()
```

#### 3. 工厂注册（基础设施层）

```python
# ❌ 旧代码（infrastructure/factory.py）
def register_all_infrastructure(project_path: str, config: Any) -> None:
    register_cache_backend_factory(_cache_factory)
    register_state_store_factory(_state_store_factory)
    # ... 每个端口都要注册

# ✅ 新代码（application/composition/di_container.py）
class CoreInfrastructureContainer(containers.DeclarativeContainer):
    cache_backend = providers.Singleton(CacheBackend)
    state_store = providers.Singleton(get_state_store)
```

### 向后兼容

对于暂时无法修改的代码，提供了桥接模块：

```python
from sprintcycle.application.composition.di_bridge import (
    get_cache_backend,      # 等同于 container.cache_backend()
    get_state_store,         # 等同于 container.state_store()
    get_runtime_config,      # 等同于 container.runtime_config()
    # ... 其他端口
)

# 旧代码可以直接使用，不需要修改
cache = get_cache_backend()  # ✅ 正常工作
```

## 🎯 核心概念

### Container

主容器，管理所有依赖：

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Singleton: 共享实例
    cache_backend = providers.Singleton(CacheBackend)

    # Factory: 每次创建新实例
    state_store = providers.Singleton(StateStore)

    # Callable: 工具函数
    compiled_graph = providers.Callable(compile_intent_graph)

    # Dict: 配置字典
    governance_adapters = providers.Dict({
        "archguard": providers.Singleton(ArchonAdapter),
        "ruff": providers.Singleton(RuffAdapter),
    })
```

### Provider 类型

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| `Singleton` | 共享单例 | 数据库连接、缓存、配置 |
| `Factory` | 每次新建 | 无状态服务 |
| `Callable` | 工具函数 | 编译、转换 |
| `Configuration` | 配置注入 | 运行时配置 |
| `Dict` | 字典配置 | 多适配器配置 |

### Override（测试关键）

```python
from sprintcycle.application.composition.di_container import container

# 替换为 Mock
with container.cache_backend.override(MockCacheBackend()):
    # 所有在这个上下文中获取的 cache_backend 都是 Mock
    service = MyService()
    service.test_method()

# 支持嵌套 Override
with container.cache_backend.override(MockCache()):
    with container.state_store.override(MockStateStore()):
        # 两个都被替换
        integration_test()
```

## 📊 收益分析

### 代码量对比

**重构前**（每个端口）：
```python
# domain/ports/cache.py (约 20 行)
_cache_backend_factory = None

def register_cache_backend_factory(factory):
    global _cache_backend_factory
    _cache_backend_factory = factory

def get_cache_backend(...):
    if _cache_backend_factory is not None:
        return _cache_backend_factory(...)
    raise RuntimeError(...)

# infrastructure/factory.py (约 5 行)
def register_all_infrastructure(...):
    register_cache_backend_factory(_cache_factory)
    # ... 每个端口都要写

# application/composition/http_factory.py (约 10 行)
def create_cache_backend(...):
    return build_cache_backend(...)

register_cache_backend_factory(create_cache_backend)
```

**重构后**（每个端口）：
```python
# application/composition/di_container.py (约 1 行)
cache_backend = providers.Singleton(CacheBackend)
```

### 可维护性提升

1. **依赖关系一目了然**：所有依赖在 Container 中集中声明
2. **生命周期自动管理**：Singleton/Factory 由框架管理
3. **测试更简单**：Override 替换，无需修改生产代码
4. **配置更灵活**：支持环境变量、配置文件、代码配置

## 🔄 迁移计划

### Phase 1: 基础设施（已完成）
- ✅ 添加 dependency-injector 依赖
- ✅ 创建 SprintCycleContainer
- ✅ 保留 Protocol 定义
- ✅ 创建向后兼容桥接

### Phase 2: 核心模块（进行中）
- 🔄 更新 interfaces/http 层
- 🔄 更新 application/services 层
- 🔄 更新 domain/core 层

### Phase 3: 测试适配
- 🔄 重写测试使用 Override
- 🔄 添加集成测试
- 🔄 移除旧工厂注册代码

### Phase 4: 清理
- 📋 移除 di_bridge.py（可选）
- 📋 删除 infrastructure/factory.py
- 📋 清理旧端口文件中的工厂代码

## ⚠️ 注意事项

### 1. 全局容器 vs 本地容器

```python
# 全局容器（推荐用于单例应用）
from sprintcycle.application.composition.di_container import container

# 本地容器（推荐用于多租户/测试）
from sprintcycle.application.composition.di_container import create_container

def test_multi_tenant():
    tenant_a = create_container(project_path="/tenant/a")
    tenant_b = create_container(project_path="/tenant/b")

    # 两个租户隔离
    cache_a = tenant_a.cache_backend()
    cache_b = tenant_b.cache_backend()
```

### 2. 避免循环依赖

Container 会自动检测循环依赖，但应尽量避免：

```python
# ❌ 避免
class A:
    def __init__(self, b: B): ...
class B:
    def __init__(self, a: A): ...

# ✅ 推荐
class A:
    def __init__(self, config: Config): ...
class B:
    def __init__(self, a: A, config: Config): ...
```

### 3. 延迟初始化

Container 支持延迟初始化以提升启动性能：

```python
class Container(containers.DeclarativeContainer):
    # 使用 lazy 延迟初始化
    heavy_service = providers.Singleton(
        HeavyService,
        deps=providers.Object("placeholder")
    )
```

## 📚 参考资料

- [dependency-injector 官方文档](https://python-dependency-injector.ets-labs.org/)
- [DDD 六边形架构](https://alistair.cockburn.us/hexagonal-architecture/)
- [SprintCycle 架构规范](../.cursor/rules/sprintcycle-architecture-orchestration.mdc)

## 🆘 常见问题

### Q: 如何调试依赖问题？

```python
# 查看容器配置
from sprintcycle.application.composition.di_container import container

# 打印依赖图
print(container.as_dict())

# 检查 wiring
container.check_wiring()
```

### Q: 如何处理可选依赖？

```python
class Container(containers.DeclarativeContainer):
    # 使用 union 类型
    optional_service = providers.Optional(
        providers.Singleton(RedisCache),
        default=providers.Singleton(DiskCache),
    )
```

### Q: 如何在不同环境使用不同实现？

```python
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # 开发环境使用内存缓存
    cache_backend = providers.Selector(
        config.environment,
        development=providers.Singleton(MemoryCache),
        production=providers.Singleton(RedisCache),
    )
```

## ✨ 总结

这次重构将 SprintCycle 的依赖注入从手动模式升级到声明式模式，大幅提升了：

- ✅ **代码可读性**：依赖关系一目了然
- ✅ **可维护性**：集中管理，修改一处即可
- ✅ **测试友好**：Override 让 Mock 变得简单
- ✅ **代码量**：减少 80%+ 样板代码
- ✅ **类型安全**：自动依赖图验证

建议采用渐进式迁移，优先在新代码中使用新模式，逐步改造旧代码。
