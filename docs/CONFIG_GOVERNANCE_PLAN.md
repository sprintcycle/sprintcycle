# 配置管理统一治理方案

> 遵循 DDD + 六边形架构原则

---

## 1. 现状分析

### 1.1 当前架构

当前配置管理分散在以下多个位置：

```
├── domain/
│   ├── ports/
│   │   └── config.py          # RuntimeConfigProtocol 协议
│   └── generic/
│       └── interfaces/
│           └── config.py      # ConfigProtocol 协议 + load_project_config() 工厂
├── application/
│   ├── services/
│   │   └── config_service.py  # ConfigService 服务
│   └── composition/
│       └── di_container.py    # container.runtime_config_container.runtime_config()
└── infrastructure/
    └── adapters/generic/config/  # 11个文件
        ├── __init__.py
        ├── dynaconf_app.py
        ├── flatten.py
        ├── llm_config.py
        ├── logging_setup.py
        ├── manager.py         # ConfigManager
        ├── platform_state.py
        ├── quality.py
        ├── rate_limit.py
        ├── runtime_config.py  # RuntimeConfig
        ├── runtime_registry.py
        └── sprintcycle_config.py
```

### 1.2 存在的问题

1. **协议重复定义**
   - `domain/ports/config.py` 定义了 `RuntimeConfigProtocol`
   - `domain/generic/interfaces/config.py` 定义了 `ConfigProtocol`
   - 两者功能重叠，存在冗余

2. **多层包装，增加复杂度**
   ```
   ConfigService 
     → DI Container 
       → ConfigManager 
         → RuntimeConfig 
           → Dynaconf
   ```

3. **职责不清**
   - `ConfigService`、`ConfigManager`、`RuntimeConfig` 功能有重叠
   - `domain/generic/interfaces/config.py` 既定义协议又提供工厂函数，违反单一职责

4. **配置模块文件过多**
   - `infrastructure/adapters/generic/config/` 有 11 个文件
   - 部分文件功能单一，缺乏必要的聚合

5. **访问方式不统一**
   - 有些通过 DI Container 访问
   - 有些通过 `load_project_config()` 访问
   - 有些直接使用 `RuntimeConfig`

---

## 2. 治理方案

### 2.1 架构目标

遵循 DDD + 六边形架构原则：

1. **统一协议**：合并重复的协议定义
2. **清晰分层**：明确 Domain、Application、Infrastructure 层的职责
3. **单一入口**：通过 DI Container 统一访问配置
4. **保持向后兼容**：避免破坏性变更

### 2.2 目标架构

```
├── domain/
│   └── ports/
│       └── config.py          # 统一的 ConfigProtocol 协议
├── application/
│   ├── services/
│   │   └── config_service.py  # ConfigService（精简，专注业务逻辑）
│   └── composition/
│       └── di_container.py    # container.config() 单一入口
└── infrastructure/
    └── adapters/generic/config/  # 合并后的实现
        ├── __init__.py
        ├── config_impl.py     # 统一的 ConfigImpl（合并 RuntimeConfig + ConfigManager）
        ├── dynaconf_loader.py # Dynaconf 加载逻辑
        └── config_helpers.py  # 辅助函数（quality、rate_limit、llm_config 等）
```

---

## 3. 详细设计

### 3.1 Domain 层：统一协议

**文件**：`domain/ports/config.py`

**内容**：保留 `RuntimeConfigProtocol`，删除 `ConfigProtocol`（前者功能更全）

```python
class ConfigProtocol(ABC):
    """统一的配置协议接口
    
    整合原 RuntimeConfigProtocol 的功能
    """
    
    @abstractmethod
    def __getattr__(self, item: str) -> Any: ...
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any: ...
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None: ...
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]: ...
    
    @abstractmethod
    def effective_quality_level(self) -> str: ...
    
    @classmethod
    @abstractmethod
    def from_project(cls, project_path: str) -> "ConfigProtocol": ...
```

**删除文件**：`domain/generic/interfaces/config.py`（功能合并到 ports）

---

### 3.2 Infrastructure 层：统一实现

**合并策略**：

1. **主实现**：`config_impl.py`
   - 合并 `RuntimeConfig` 和 `ConfigManager` 的功能
   - 实现统一的 `ConfigProtocol`
   
2. **加载器**：`dynaconf_loader.py`
   - 从 `dynaconf_app.py` 迁移
   - 负责构建 Dynaconf 实例

3. **辅助模块**：`config_helpers.py`
   - 合并 `quality.py`、`rate_limit.py`、`llm_config.py`、`platform_state.py` 等
   - 提供特定领域的配置辅助函数

**文件结构**：
```
infrastructure/adapters/generic/config/
├── __init__.py
├── config_impl.py        # 主实现
├── dynaconf_loader.py    # Dynaconf 加载
├── config_helpers.py     # 辅助函数
└── flatten.py            # （保留，辅助工具）
```

---

### 3.3 Application 层：精简服务

**文件**：`application/services/config_service.py`

**精简策略**：
- 专注于业务逻辑（历史记录、保存、验证）
- 通过 DI Container 获取配置实现
- 移除对具体实现的直接依赖

---

### 3.4 DI Container：统一入口

**文件**：`application/composition/di_container.py`

**简化**：
- 移除 `runtime_config_container` 中间层
- 提供 `config()` 单一入口
- 保持向后兼容的 `runtime_config()` 别名

---

## 4. 实施步骤

### Phase 1：准备（保持向后兼容）
1. 创建新的统一协议和实现
2. 保留现有文件，添加弃用警告
3. 更新 DI Container 提供新接口

### Phase 2：迁移内部使用
1. 逐步更新内部模块使用新接口
2. 添加迁移指南
3. 确保测试通过

### Phase 3：清理（可选）
1. 在主要版本更新时移除废弃文件
2. 完成文档更新

---

## 5. 向后兼容性策略

1. **保留现有 API**
   - 所有现有导入路径保持工作
   - 添加 `DeprecationWarning` 警告
   
2. **提供兼容层**
   - `ConfigService` 保持现有接口
   - `RuntimeConfig` 作为新实现的别名
   
3. **渐进式迁移**
   - 分阶段迁移，不一次性破坏现有代码

---

## 6. 预期效果

| 指标 | 当前 | 目标 |
|------|------|------|
| 协议定义文件 | 2 | 1 |
| 配置相关文件 | 11+ | 4-5 |
| 访问路径 | 多种 | 1种（DI Container） |
| 抽象层数 | 5 | 3 |

---

## 7. 相关参考

- [ARCHITECTURE_SIMPLIFICATION.md](./ARCHITECTURE_SIMPLIFICATION.md)
- [AGENTS.md](../AGENTS.md)
