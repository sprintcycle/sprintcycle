# SprintCycle 架构不变性文档

> 本文档记录 SprintCycle 代码库的架构不变性（Architecture Invariants），即不可变更的核心设计约束。  
> 任何代码变更必须遵守本文档规定的边界、职责和契约。

---

## 1. 代码库统计

| 指标 | 数值 |
|------|------|
| Python 文件总数 | 347+ |
| 总代码行数 | 35,300+ |
| 顶层模块数 | 5 |

### 1.1 模块分布

| 模块 | 文件数 | 说明 |
|------|--------|------|
| `domain/core/execution` | 78 | 执行引擎、状态管理、事件总线、agents、hooks、orchestrator |
| `domain/core/governance` | 77 | 治理、HITL、建议、版本控制、arch_guard |
| `infrastructure` | 62+ | 配置、持久化、集成、部署、可观测性适配器 |
| `application` | 47 | 服务编排（按领域组织：lifecycle、governance、evolution、dashboard） |
| `interfaces/http` | 14 | HTTP 接口层（dashboard 按领域划分路由） |
| `sprintcycle/` | 5 | 根模块（api.py, hooks.py 等） |

---

## 2. 分层架构

### 2.1 层级定义（洋葱架构 - 从外到内）

```
┌─────────────────────────────────────────────────────────────┐
│                    interfaces/                              │
│   (HTTP API: dashboard/[execution, governance, lifecycle,  │
│    hitl, suggestions] / public/)                           │
│                       ↓                                    │
│              ┌─────────────────────┐                       │
│              │  HTTP 路由适配层    │                       │
│              └─────────────────────┘                       │
├─────────────────────────────────────────────────────────────┤
│                     application/                            │
│    (Services: execution, governance, lifecycle, evolution, │
│     dashboard, observability - organized by domain)        │
│                       ↓                                    │
│              ┌─────────────────────┐                       │
│              │  用例编排与服务层   │                       │
│              │  factories/: 纯组装 │                       │
│              └─────────────────────┘                       │
├─────────────────────────────────────────────────────────────┤
│                       domain/                               │
│   (Core: lifecycle, execution, evolution, governance;      │
│    Supporting: intent, verification, fitness;              │
│    Generic: errors, prompts, models, platform, ports)      │
│                       ↓                                    │
│              ┌─────────────────────┐                       │
│              │  领域模型与业务规则  │                       │
│              └─────────────────────┘                       │
├─────────────────────────────────────────────────────────────┤
│                  infrastructure/                            │
│  (shared/persistence, adapters/core, adapters/generic)      │
│                       ↓                                    │
│              ┌─────────────────────┐                       │
│              │   基础设施适配层    │                       │
│              │   adapters/:实现   │                       │
│              └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

**洋葱架构层次说明：**

| 层级 | 位置 | 职责 | 依赖方向 |
|------|------|------|----------|
| **interfaces** | 最外层 | HTTP 接口、请求路由、上下文传递 | 依赖 application |
| **application** | 第二层 | 用例编排、服务协调、事务边界 | 依赖 domain |
| **domain** | 第三层 | 领域模型、业务规则、值对象 | 无外部依赖 |
| **infrastructure** | 最内层 | 数据库、缓存、外部集成、适配器 | 被所有层依赖 |

**领域层子域划分：**
- **Core Domains（核心子域）**: lifecycle, execution, evolution, governance
- **Supporting Domains（支撑子域）**: intent, verification, fitness  
- **Generic Domains（通用子域）**: errors, prompts, models, platform, ports

### 2.2 各层职责

| 层级 | 核心职责 | 不变性约束 |
|------|----------|------------|
| **interfaces** | HTTP 请求路由、请求上下文、审计日志 | 仅做请求转发，不含业务逻辑 |
| **application** | 跨服务编排、生命周期管理、API 聚合 | 依赖 domain，不直接操作基础设施 |
| **domain** | 领域模型、业务规则、质量规范<br>**核心子域**: lifecycle, execution, evolution, governance<br>**支撑子域**: intent, verification, fitness<br>**通用子域**: errors, prompts, models, platform, ports | 无外部依赖，纯业务表达 |
| **infrastructure** | 配置、持久化、外部集成、可观测性 | 实现细节，不暴露给 domain |

### 2.3 跨层依赖规则

```
interfaces → application → domain → infrastructure
```

**分层依赖说明（从外到内）：**
- **interfaces** 依赖 **application**
- **application** 依赖 **domain**
- **domain** 无外部依赖（纯业务逻辑）
- **infrastructure** 被所有层依赖（不依赖任何层）

**domain 层内部子域依赖：**
```
core/ (lifecycle, execution, evolution, governance)
    ↓
supporting/ (intent, verification, fitness)
    ↓
generic/ (errors, prompts, models, platform, ports)
```

**禁止**：
- domain 层依赖 application 层或 interfaces 层
- infrastructure 层依赖任何业务层
- 任何层直接访问数据库实现细节
- **工厂层包含适配器实现**

### 2.4 适配器与工厂分离原则

**工厂层（application/factories/）职责：**
- 仅负责依赖组装（wiring）
- 依赖注入配置
- 组合根模式实现
- **禁止包含适配器实现逻辑**

**适配器层（infrastructure/adapters/）职责：**
- 实现 domain 层定义的端口（Ports）
- 桥接领域抽象与具体技术实现
- 遵循依赖倒置原则
- **禁止包含组装逻辑**

**适配器位置规范：**
| 适配器类型 | 位置 | 示例 |
|-----------|------|------|
| 核心子域适配器 | `infrastructure/adapters/core/` | execution/, evolution/, governance/, **orchestration/** |
| 通用子域适配器 | `infrastructure/adapters/generic/` | config/, cache/, deploy/, integrations/ |

---

## 3. 核心能力清单

SprintCycle 不可替代的核心功能：

### 3.1 执行生命周期管理

| 能力 | 位置 | 说明 |
|------|------|------|
| 阶段编排 | `application/services/execution/phase_workflow.py` | 统一执行流程编排 |
| 状态机 | `application/services/lifecycle/lifecycle_state_machine.py` | 16 个生命周期阶段定义 |
| 恢复机制 | `application/services/governance/repair_orchestration_service.py` | 失败自动恢复路由 |
| 证据收集 | `application/services/lifecycle/lifecycle_contracts.py` | 阶段证据 schema |
| 依赖注入工厂 | `application/factories/orchestration.py` | 编排器依赖组装 |

### 3.2 质量治理

| 能力 | 位置 | 说明 |
|------|------|------|
| 规则引擎 | `domain/core/governance/quality_spec/rules/rule.py` | 规则定义与匹配 |
| 架构守卫 | `domain/core/governance/arch_guard/` | 架构约束检查 |
| 适配器系统 | `domain/core/governance/quality_spec/adapters/` | 外部工具集成 |
| 插件协议 | `domain/core/governance/quality_spec/plugin_protocols.py` | 可扩展质量规则 |

### 3.3 人类在环（HITL）

| 能力 | 位置 | 说明 |
|------|------|------|
| 决策请求 | `domain/core/governance/hitl/coordinator.py` | 人工决策协调 |
| 会话管理 | `domain/core/governance/hitl/session.py` | 决策上下文 |
| 策略评估 | `domain/core/governance/hitl/policy.py` | 自动决策策略 |

### 3.4 建议系统

| 能力 | 位置 | 说明 |
|------|------|------|
| 建议生成 | `domain/core/governance/suggestion/service.py` | 从执行事件生成建议 |
| 审批流程 | `domain/core/governance/suggestion/approval.py` | 建议审核 |
| HITL 提升 | `domain/core/governance/suggestion/bridge.py` | 建议转 HITL |

### 3.5 可观测性

| 能力 | 位置 | 说明 |
|------|------|------|
| 事件总线 | `domain/core/execution/core/events.py` | 发布-订阅事件 |
| 追踪 | `infrastructure/adapters/generic/observability/facade.py` | 运行追踪 |
| 诊断 | `infrastructure/adapters/generic/observability/diagnostics/` | 健康报告 |

---

## 4. 扩展点清单

### 4.1 插件化扩展

| 扩展点 | 协议/接口 | 位置 |
|--------|-----------|------|
| 质量规则插件 | `QualityPlugin` | `domain/core/governance/quality_spec/plugin_protocols.py` |
| 治理 argv 插件 | `pluggy` | `domain/core/governance/pluggy_host.py` |
| 执行 hooks | `HookDefinition` | `domain/core/execution/hooks/` |
| 治理 hooks | `GovernanceHook` | `domain/core/governance/task_hooks.py`, `sprint_hooks.py` |

### 4.2 适配器扩展

| 扩展点 | 说明 | 位置 |
|--------|------|------|
| 质量适配器 | 集成 Bandit, Arch, Deal 等 | `domain/core/governance/quality_spec/adapters/` |
| 验证提供者 | Playwright, 视觉对比等 | `domain/supporting/verification/providers/` |
| LLM 提供者 | 模型调用抽象 | `infrastructure/adapters/generic/llm_provider.py` |
| 事件后端 | SQLite, Memory 等 | `infrastructure/adapters/core/execution/state_store/sqlite_event_backend.py` |
| 编排适配器 | 端口实现 | `infrastructure/adapters/core/orchestration/adapters.py` |

### 4.3 可配置扩展

| 扩展点 | 配置项 | 位置 |
|--------|--------|------|
| 事件后端 | `SPRINTCYCLE_EXECUTION_EVENT_BACKEND` | `infrastructure/adapters/core/execution/state_store/state_store.py` |
| 状态存储 | `RuntimeConfig.state_store` | `infrastructure/adapters/core/execution/state_store/` |
| 治理规则 | `sprintcycle.toml` | `domain/core/governance/runner.py` |

---

## 5. 契约接口

### 5.1 生命周期契约

```python
# 阶段序列（不可更改顺序）
REQUIRED_STAGE_SEQUENCE = (
    "new", "normalized", "planned", "prepared", "decomposed",
    "executing", "observing", "diagnosed", "repairing", "verifying",
    "delivering", "runtime_linked", "governing", "promotion_ready", "promoted"
)

# 阶段证据 schema
STAGE_EVIDENCE_SCHEMA = {
    "normalized": ("normalized",),
    "planned": ("plan",),
    "prepared": ("prepared",),
    "executing": ("trace",),
    "diagnosed": ("root_causes", "repair_ready", "confidence", "recommendations"),
    ...
}
```

### 5.2 治理契约

```python
# 治理门
GATES = ("planning", "review", "delivery", "production")

# 规则结构
@dataclass
class Rule:
    id: str
    name: str
    category: str
    severity: str  # "error", "warning", "info"
    enabled: bool
    thresholds: Dict[str, Any]
    applies_to: List[str]  # gates
```

### 5.3 Hook 契约

```python
# Hook 事件定义
HOOK_EVENTS = {
    "execution.start": ("execution.started", "execution.start_failed"),
    "suggestion.review": ("suggestion.reviewed",),
    "governance.check": ("governance.checked", "governance.check_failed"),
    ...
}

# Hook 上下文
@dataclass
class HookContext:
    domain: str
    action: str
    subject_id: str
    execution_id: str
    project_path: str
    payload: Dict[str, Any]
    trace_id: str
```

### 5.4 事件契约

```python
# 事件类型枚举
class EventType(Enum):
    EXECUTION_START = "execution_start"
    SPRINT_START = "sprint_start"
    TASK_COMPLETE = "task_complete"
    GOVERNANCE_GATE = "governance_gate"
    HITL_REQUEST_OPEN = "hitl_request_open"
    ...
```

### 5.5 状态机契约

```python
# 状态转移规则（部分）
STAGE_TRANSITIONS = {
    "new": ("normalized", "failed", "cancelled"),
    "executing": ("observing", "diagnosed", "delivering", "failed", "cancelled"),
    "governing": ("promotion_ready", "failed", "cancelled"),
    "promotion_ready": ("promoted", "failed", "cancelled"),
    ...
}

# 恢复路由
RECOVERY_TARGETS = {
    "executing": "repairing",
    "observing": "repairing",
    "failed": "repairing",
    ...
}
```

### 5.6 端口-适配器契约

| 端口 | 适配器实现 | 位置 |
|------|-----------|------|
| `GraphCompilerPort` | `GraphCompilerAdapter` | `infrastructure/adapters/core/orchestration/adapters.py` |
| `KnowledgeRepositoryPort` | `KnowledgeRepositoryAdapter` | `infrastructure/adapters/core/orchestration/adapters.py` |
| `KnowledgeInjectionHookPort` | `KnowledgeInjectionHookAdapter` | `infrastructure/adapters/core/orchestration/adapters.py` |
| `RuntimeConfigPort` | `RuntimeConfigAdapter` | `infrastructure/adapters/core/orchestration/adapters.py` |
| `TraceRuntimePort` | `TraceRuntimeAdapter` | `infrastructure/adapters/core/orchestration/adapters.py` |
| `StateStorePort` | `StateStoreAdapter` | `infrastructure/adapters/core/orchestration/adapters.py` |
| `QualityConfigPort` | `QualityConfigAdapter` | `infrastructure/adapters/core/orchestration/adapters.py` |

---

## 6. 架构治理规则

### 6.1 架构守卫（ArchGuard）

| 规则 ID | 检查内容 | 严重性 |
|---------|----------|--------|
| `planning:release_plan_empty` | ReleasePlan 不为空 | error |
| `planning:sprint_name_duplicate` | Sprint 名称唯一 | error |
| `planning:spec_ref_missing` | spec_ref 文件存在 | warning |
| `review:extension_point_bypass` | 禁止绕过治理扩展点 | error |
| `review:hook_context_invalid` | hook context 格式正确 | warning |
| `review:adapter_in_factory` | 禁止在工厂中定义适配器 | error |

### 6.2 架构分层规则

```python
# 分层定义
LAYER_NAMES = (
    "domain",
    "application",
    "execution",
    "governance",
    "infrastructure",
    "interfaces"
)

# 允许的跨层依赖
ALLOWED_DEPENDENCIES = {
    "interfaces": ["application"],
    "application": ["domain"],
    "domain": [],  # 无外部依赖
    "infrastructure": [],  # 无外部依赖（被其他层依赖）
}
```

### 6.3 质量门（Quality Gates）

| Gate | 阶段 | 规则集 |
|------|------|--------|
| `planning` | 规划期 | Planning Rules |
| `review` | 代码评审 | Review Rules |
| `delivery` | 交付期 | Delivery Rules |
| `production` | 生产期 | Production Rules |

---

## 7. 设计模式清单

### 7.1 观察者模式（Event-Driven）

**位置**：`domain/core/execution/core/events.py`

```python
# 发布-订阅契约
class ExecutionEventBackend(Protocol):
    def on(self, event_type: EventType, handler: Callable) -> Self: ...
    async def emit(self, event: Event) -> None: ...
    def emit_sync(self, event: Event) -> None: ...

# 默认实现：SQLiteMQEventBackend
# 进程内测试实现：EventBus
```

**关键特性**：
- 异步/同步双模式
- 一次性监听器（once）
- 安全错误处理（不阻断主流程）

### 7.2 契约式设计（Contracts）

**位置**：`domain/core/governance/quality_spec/`

```python
# 规则契约
class Rule:
    id: str
    name: str
    category: str
    severity: str
    applies_to_gate(gate: str) -> bool

# 适配器契约
class QualityAdapter(Protocol):
    def check(self, context: QualityContext) -> List[Finding]: ...
    def applies_to_gate(self, gate: str) -> bool: ...
```

### 7.3 策略模式（Policies）

| 策略 | 位置 | 说明 |
|------|------|------|
| `PromotionPolicy` | `application/services/governance/promotion_policy.py` | 晋升策略 |
| `HitlPolicy` | `domain/core/governance/hitl/policy.py` | HITL 决策策略 |
| `TaskRetryPolicy` | `domain/core/execution/policies.py` | 重试策略 |

### 7.4 委托模式（Delegation）

**api.py 委托结构**：

```
SprintCycle (api.py)
    ├── _execution_lifecycle (ExecutionLifecycleService)
    ├── _governance_orchestration (GovernanceOrchestrationService)
    ├── _lifecycle_delivery (LifecycleDeliveryService)
    ├── _lifecycle_assembly (LifecycleContractAssemblyService)
    └── _suggestion_application (SuggestionApplicationService)
```

### 7.5 门面模式（Facade）

| Facade | 位置 | 封装 |
|--------|------|------|
| `GovernanceFacade` | `domain/core/governance/facade.py` | HITL/Runner/Suggestion |
| `ObservabilityFacade` | `infrastructure/adapters/generic/observability/facade.py` | Phoenix/Events |
| `SuggestionFacade` | `domain/core/governance/suggestion/facade.py` | 建议操作 |
| `HitlFacade` | `domain/core/governance/hitl/facade.py` | HITL 协调 |

### 7.6 状态机模式

**位置**：`application/services/lifecycle/lifecycle_state_machine.py`

```python
class LifecycleStateMachine:
    stage: str = "new"
    can_transition(from_stage, to_stage) -> bool
    validate_transition(from_stage, to_stage) -> Optional[str]
    next_stages(stage) -> tuple[str, ...]
```

### 7.7 端口-适配器模式

**位置**：`domain/generic/ports/` 和 `infrastructure/adapters/`

```python
# 端口定义（domain）
@runtime_checkable
class RuntimeConfigPort(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...
    @property
    def dry_run(self) -> bool: ...

# 适配器实现（infrastructure）
class RuntimeConfigAdapter(RuntimeConfigPort):
    def __init__(self):
        self._config = RuntimeConfig()
    def to_dict(self) -> Dict[str, Any]:
        return self._config.to_dict()
```

---

## 8. API 设计规范

### 8.1 api.py 方法分类

**核心执行方法**（委托给 ExecutionLifecycleService）：
- `start_execution_run()`
- `execution_detail()`
- `execution_events()`
- `replay_execution()`

**治理方法**（委托给 GovernanceOrchestrationService）：
- `governance_check()`
- `observability_*`
- `review_suggestion()`, `approve_suggestion()`, `reject_suggestion()`

**生命周期方法**（委托给 LifecycleDeliveryService）：
- `runtime_lifecycle()`
- `lifecycle_contract()`
- `lifecycle_recovery_and_promotion()`

**视图方法**（委托给 PlatformSummaryService）：
- `fitness_view()`
- `deploy_view()`
- `platform_overview()`

### 8.2 接口层规范

**Internal API** (`interfaces/http/dashboard/`)：
- 仪表盘专用
- 审计日志
- 速率限制
- 请求上下文传递

**Public API** (`interfaces/http/public/`)：
- 外部集成
- `/api/v1` 前缀
- 标准化请求/响应

### 8.3 工厂层规范

**工厂职责**：
- 仅做依赖组装
- 使用延迟导入避免循环依赖
- 依赖端口而非具体实现

**禁止**：
- 在工厂中定义适配器类
- 在工厂中包含业务逻辑
- 直接依赖基础设施实现

---

## 9. 必须遵循的设计规范

### 9.1 分层规范

1. **禁止**：domain 层依赖任何其他业务层
2. **禁止**：基础设施层暴露给应用层以外
3. **必须**：使用 Facade 封装复杂子域
4. **必须**：接口层只做转发，不含业务逻辑
5. **必须**：工厂层只做组装，不含适配器实现

### 9.2 扩展性规范

1. **必须**：新功能通过 Hook 扩展
2. **必须**：新工具集成通过 Adapter 实现
3. **必须**：新治理规则实现 Rule 接口
4. **鼓励**：使用 pluggy 插件协议
5. **必须**：适配器放在 infrastructure/adapters/ 中

### 9.3 状态管理规范

1. **必须**：使用 LifecycleStateMachine 验证转移
2. **禁止**：直接修改 stage 而不经过状态机
3. **必须**：阶段转换记录 evidence
4. **必须**：失败状态路由到 recovery

### 9.4 事件规范

1. **必须**：使用 EventType 枚举定义事件
2. **必须**：通过 ExecutionEventBackend 发布事件
3. **禁止**：直接在组件间耦合（通过事件解耦）
4. **建议**：使用 Hook 拦截关键操作点

### 9.5 治理规范

1. **必须**：所有治理检查通过 GovernanceRunner
2. **必须**：治理结果持久化
3. **禁止**：绕过 ArchGuard 直接访问内部实现
4. **必须**：HITL 决策有超时机制

### 9.6 适配器规范

1. **必须**：适配器实现对应的 domain 端口
2. **必须**：适配器放在 infrastructure/adapters/ 目录
3. **禁止**：适配器包含组装逻辑
4. **必须**：适配器遵循依赖倒置原则

---

## 10. 禁止事项

### 10.1 架构破坏

| 禁止项 | 原因 |
|--------|------|
| 在 domain 层导入 execution | 违反分层原则 |
| 在 api.py 直接操作数据库 | 违反分层原则 |
| 绕过 Hook 直接修改状态 | 破坏扩展机制 |
| 绕过 GovernanceFacade 直接调用治理服务 | 破坏治理一致性 |
| **在工厂层定义适配器** | 违反职责分离原则 |

### 10.2 状态破坏

| 禁止项 | 原因 |
|--------|------|
| 直接修改 execution.state | 必须通过 StateStore |
| 跳过 STAGE_TRANSITIONS 直接转移 | 违反状态机契约 |
| 删除 REQUIRED_STAGE_SEQUENCE 任意阶段 | 破坏生命周期完整性 |
| 修改 STAGE_EVIDENCE_SCHEMA 移除必需字段 | 破坏证据契约 |

### 10.3 扩展点破坏

| 禁止项 | 原因 |
|--------|------|
| 删除 QualityPlugin 接口 | 破坏插件机制 |
| 移除 HookRegistry | 破坏钩子系统 |
| 修改 pluggy 协议 group 名称 | 破坏插件发现 |
| 删除 ExecutionEventBackend Protocol | 破坏事件后端可插拔 |

### 10.4 契约破坏

| 禁止项 | 原因 |
|--------|------|
| 修改 Rule 必需字段 | 破坏规则引擎 |
| 删除或重命名 EventType 枚举值 | 破坏事件类型一致性 |
| 修改 RECOVERY_TARGETS 默认映射 | 破坏恢复路由 |
| 修改 LIFECYCLE_STAGES 顺序 | 破坏生命周期定义 |

### 10.5 适配器-工厂分离破坏

| 禁止项 | 原因 |
|--------|------|
| 在 factories/ 中定义适配器类 | 违反职责分离 |
| 在 adapters/ 中定义组装逻辑 | 违反职责分离 |
| 适配器不实现 domain 端口 | 违反依赖倒置 |

---

## 11. API 端点清单

### 11.1 Dashboard API（按领域划分）

#### Execution 领域
| 端点 | 方法 | 服务 | 说明 |
|------|------|------|------|
| `/api/execution/trace` | GET | Observability | 执行追踪 |
| `/api/execution/{id}/detail` | GET | Execution | 执行详情 |
| `/api/execution/{id}/replay` | GET | Observability | 执行回放 |

#### Governance 领域
| 端点 | 方法 | 服务 | 说明 |
|------|------|------|------|
| `/api/governance/latest` | GET | Governance | 最新治理报告 |
| `/api/governance/history` | GET | Governance | 治理历史 |
| `/api/governance/check` | POST | Governance | 执行治理检查 |

#### Lifecycle 领域
| 端点 | 方法 | 服务 | 说明 |
|------|------|------|------|
| `/api/lifecycle/contract` | GET | Lifecycle | 生命周期契约 |
| `/api/lifecycle/contract/{id}/review` | POST | Lifecycle | 契约评审 |
| `/api/lifecycle/delivery` | GET | Lifecycle | 交付状态 |

#### HITL 领域
| 端点 | 方法 | 服务 | 说明 |
|------|------|------|------|
| `/api/hitl/pending` | GET | HITL | 待处理决策列表 |
| `/api/hitl/history` | GET | HITL | 决策历史 |
| `/api/hitl/{id}/decision` | POST | HITL | 提交决策 |

#### Suggestions 领域
| 端点 | 方法 | 服务 | 说明 |
|------|------|------|------|
| `/api/suggestions/{id}/approve` | POST | Suggestions | 批准建议 |
| `/api/suggestions/{id}/reject` | POST | Suggestions | 拒绝建议 |
| `/api/suggestions/promoted` | GET | Suggestions | 已晋升建议 |

### 11.2 Public API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/plan` | POST | 规划执行 |
| `/api/v1/run` | POST | 启动执行 |
| `/api/v1/diagnose` | GET | 诊断执行 |
| `/api/v1/status` | POST | 查询状态 |
| `/api/v1/rollback` | POST | 回滚执行 |
| `/api/v1/stop` | POST | 停止执行 |

---

## 12. 配置契约

### 12.1 RuntimeConfig

```python
@dataclass
class RuntimeConfig:
    project_path: str
    execution_event_backend: str  # "sqlite" | "memory"
    state_store: str  # "sqlite" | "memory"
    governance_enabled: bool
    hitl_enabled: bool
    observability_enabled: bool
    # ... 更多配置
```

### 12.2 sprintcycle.toml 结构

```toml
[governance]
enabled = true
gate = "review"
rules = []

[hitl]
enabled = true
timeout = 300

[observability]
enabled = true
event_backend = "sqlite"
```

---

## 附录 A：关键文件映射

| 功能 | 关键文件 |
|------|----------|
| 主入口 | `sprintcycle/api.py` |
| 状态机 | `sprintcycle/application/services/lifecycle/lifecycle_state_machine.py` |
| 事件总线 | `sprintcycle/domain/core/execution/core/events.py` |
| 治理运行器 | `sprintcycle/domain/core/governance/runner.py` |
| 质量规则 | `sprintcycle/domain/core/governance/quality_spec/rules/rule.py` |
| Hook 系统 | `sprintcycle/domain/core/execution/hooks/` |
| 插件协议 | `sprintcycle/domain/core/governance/quality_spec/plugin_protocols.py` |
| HITL 协调 | `sprintcycle/domain/core/governance/hitl/coordinator.py` |
| 建议服务 | `sprintcycle/domain/core/governance/suggestion/service.py` |
| 组合根 | `sprintcycle/application/factories/http.py` |
| 编排依赖工厂 | `sprintcycle/application/factories/orchestration.py` |
| 编排适配器 | `sprintcycle/infrastructure/adapters/core/orchestration/adapters.py` |

---

## 附录 B：变更流程

### B.1 添加新功能

1. 确认功能属于哪一层
2. 如果需要扩展，添加到对应扩展点
3. 更新本文档的对应章节
4. 如果涉及适配器，放在 infrastructure/adapters/ 中

### B.2 添加新治理规则

1. 实现 `Rule` 接口
2. 注册到 `RuleRegistry`
3. 更新 `sprintcycle.toml` 中的 rules 配置

### B.3 添加新适配器

1. 在 `domain/generic/ports/` 定义端口（如果需要）
2. 在 `infrastructure/adapters/` 实现适配器类
3. 在工厂层添加组装逻辑

---

## 附录 C：洋葱架构依赖关系图

```
┌─────────────────────────────────────────────────────┐
│              interfaces/http/                       │ ← 依赖 application
│  (Dashboard Routes, Public API)                    │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│              application/                           │ ← 依赖 domain
│  (services/, orchestration/, factories/)           │
│  factories/: 纯组装逻辑                            │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                domain/                              │ ← 无外部依赖
│  (core/, supporting/, generic/ports/)              │
│  ports/: 端口定义                                   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│            infrastructure/                         │ ← 依赖 domain 端口
│  (adapters/core/, adapters/generic/)               │
│  adapters/: 适配器实现                              │
└─────────────────────────────────────────────────────┘
```

---

> **版本**：v2.1  
> **更新日期**：2026-05-25  
> **维护者**：架构团队  
> **变更说明**：重构适配器与工厂分离，适配器统一放在 infrastructure/adapters/core/orchestration/，工厂层仅保留组装逻辑，符合 DDD 洋葱架构原则
