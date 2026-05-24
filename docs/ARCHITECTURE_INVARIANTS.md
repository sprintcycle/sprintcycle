# SprintCycle 架构不变性文档

> 本文档记录 SprintCycle 代码库的架构不变性（Architecture Invariants），即不可变更的核心设计约束。  
> 任何代码变更必须遵守本文档规定的边界、职责和契约。

---

## 1. 代码库统计

| 指标 | 数值 |
|------|------|
| Python 文件总数 | 345 |
| 总代码行数 | 35,170 |
| 顶层模块数 | 8 |

### 1.1 模块分布

| 模块 | 文件数 | 说明 |
|------|--------|------|
| `execution` | 78 | 执行引擎、状态管理、事件总线 |
| `governance` | 77 | 治理、HITL、建议、版本控制 |
| `domain` | 62 | 领域模型、质量规范、验证 |
| `infrastructure` | 60+ | 配置、持久化、集成、部署、可观测性 |
| `application` | 47 | 服务编排、API 封装 |
| `interfaces` | 4 | HTTP 接口层 |
| `sprintcycle/` | 5 | 根模块（api.py, hooks.py 等） |

---

## 2. 分层架构

### 2.1 层级定义

```
┌─────────────────────────────────────────────────────────────┐
│                    interfaces/http/                         │
│                  (HTTP API: internal.py, public.py)         │
├─────────────────────────────────────────────────────────────┤
│                     application/                            │
│    (Services: lifecycle, governance, evolution, etc.)      │
├─────────────────────────────────────────────────────────────┤
│                       domain/                               │
│   (Models: fitness, intent, platform, quality_spec, etc.)  │
├─────────────────────────────────────────────────────────────┤
│                      execution/                             │
│    (Execution: engine, state, events, hooks, etc.)          │
├─────────────────────────────────────────────────────────────┤
│                      governance/                            │
│      (Policy: hitl, arch_guard, suggestion, versioning)    │
├─────────────────────────────────────────────────────────────┤
│                    infrastructure/                          │
│  (Config, persistence, integrations, deployment, sandbox,   │
│   observability: trace, replay, diagnostics, runtime)       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 各层职责

| 层级 | 核心职责 | 不变性约束 |
|------|----------|------------|
| **interfaces** | HTTP 请求路由、请求上下文、审计日志 | 仅做请求转发，不含业务逻辑 |
| **application** | 跨服务编排、生命周期管理、API 聚合 | 依赖 domain，不直接操作基础设施 |
| **domain** | 领域模型、业务规则、质量规范 | 无外部依赖，纯业务表达 |
| **execution** | 执行引擎、状态机、事件发布 | 可观测性边界，不做治理决策 |
| **governance** | 策略检查、HITL、建议管理、架构守卫 | 不直接操作执行引擎 |
| **infrastructure** | 配置、持久化、外部集成 | 实现细节，不暴露给 domain |

### 2.3 跨层依赖规则

```
interfaces → application → domain
                         ↓
                   execution
                         ↓
                   infrastructure (包含 observability)

governance → domain (仅读)
governance → infrastructure (通过 runner)
```

**禁止**：
- domain 层依赖 application 层
- domain 层依赖 execution 层
- infrastructure 层依赖 governance 层
- 任何层直接访问数据库实现细节

---

## 3. 核心能力清单

SprintCycle 不可替代的核心功能：

### 3.1 执行生命周期管理

| 能力 | 位置 | 说明 |
|------|------|------|
| 阶段编排 | `application/services/phase_workflow.py` | 统一执行流程编排 |
| 状态机 | `application/services/lifecycle_state_machine.py` | 16 个生命周期阶段定义 |
| 恢复机制 | `application/services/repair_orchestration_service.py` | 失败自动恢复路由 |
| 证据收集 | `application/services/lifecycle_contracts.py` | 阶段证据 schema |

### 3.2 质量治理

| 能力 | 位置 | 说明 |
|------|------|------|
| 规则引擎 | `domain/quality_spec/rules/rule.py` | 规则定义与匹配 |
| 架构守卫 | `governance/arch_guard/` | 架构约束检查 |
| 适配器系统 | `domain/quality_spec/adapters/` | 外部工具集成 |
| 插件协议 | `domain/quality_spec/plugin_protocols.py` | 可扩展质量规则 |

### 3.3 人类在环（HITL）

| 能力 | 位置 | 说明 |
|------|------|------|
| 决策请求 | `governance/hitl/coordinator.py` | 人工决策协调 |
| 会话管理 | `governance/hitl/session.py` | 决策上下文 |
| 策略评估 | `governance/hitl/policy.py` | 自动决策策略 |

### 3.4 建议系统

| 能力 | 位置 | 说明 |
|------|------|------|
| 建议生成 | `governance/suggestion/service.py` | 从执行事件生成建议 |
| 审批流程 | `governance/suggestion/approval.py` | 建议审核 |
| HITL 提升 | `governance/suggestion/bridge.py` | 建议转 HITL |

### 3.5 可观测性

| 能力 | 位置 | 说明 |
|------|------|------|
| 事件总线 | `execution/events.py` | 发布-订阅事件 |
| 追踪 | `observability/facade.py` | 运行追踪 |
| 诊断 | `observability/diagnostics/` | 健康报告 |

---

## 4. 扩展点清单

### 4.1 插件化扩展

| 扩展点 | 协议/接口 | 位置 |
|--------|-----------|------|
| 质量规则插件 | `QualityPlugin` | `domain/quality_spec/plugin_protocols.py` |
| 治理 argv 插件 | `pluggy` | `governance/pluggy_host.py` |
| 执行 hooks | `HookDefinition` | `execution/hooks/` |
| 治理 hooks | `GovernanceHook` | `governance/task_hooks.py`, `sprint_hooks.py` |

### 4.2 适配器扩展

| 扩展点 | 说明 | 位置 |
|--------|------|------|
| 质量适配器 | 集成 Bandit, Arch, Deal 等 | `domain/quality_spec/adapters/` |
| 验证提供者 | Playwright, 视觉对比等 | `domain/verification/providers/` |
| LLM 提供者 | 模型调用抽象 | `infrastructure/llm_provider.py` |
| 事件后端 | SQLite, Memory 等 | `execution/events.py` |

### 4.3 可配置扩展

| 扩展点 | 配置项 | 位置 |
|--------|--------|------|
| 事件后端 | `SPRINTCYCLE_EXECUTION_EVENT_BACKEND` | `execution/events.py` |
| 状态存储 | `RuntimeConfig.state_store` | `execution/state/` |
| 治理规则 | `sprintcycle.toml` | `governance/runner.py` |

---

## 5. 契约接口

### 5.1 生命周期契约

```python
# 阶段序列（不可更改顺序）
REQUIRED_STAGE_SEQUENCE = (
    "normalized", "plan", "prepare", "decompose",
    "execute", "observe", "diagnose", "repair",
    "verify", "deliver", "runtime", "governance",
    "promotion", "evolution"
)

# 阶段证据 schema
STAGE_EVIDENCE_SCHEMA = {
    "normalized": ("normalized",),
    "plan": ("objective", "present"),
    "execute": ("trace", "present"),
    "diagnose": ("root_causes", "repair_ready", "confidence", "recommendations", "present"),
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
    "application": ["domain", "execution", "governance"],
    "domain": [],  # 无外部依赖
    "execution": ["domain", "infrastructure"],
    "governance": ["domain"],
    "infrastructure": ["domain"],
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

**位置**：`execution/events.py`

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

**位置**：`domain/quality_spec/`

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
| `PromotionPolicy` | `application/services/promotion_policy.py` | 晋升策略 |
| `HitlPolicy` | `governance/hitl/policy.py` | HITL 决策策略 |
| `TaskRetryPolicy` | `execution/policies.py` | 重试策略 |
| `HookPolicy` | `hooks.py` | Hook 失败策略 |

### 7.4 委托模式（Delegation）

**api.py 委托结构**：

```
SprintCycle (api.py)
    ├── _execution_service (ExecutionLifecycleService)
    ├── _governance_orchestration (GovernanceOrchestrationService)
    ├── _lifecycle_delivery (LifecycleDeliveryService)
    ├── _lifecycle_assembly (LifecycleContractAssemblyService)
    ├── _evolution_promotion (EvolutionPromotionService)
    └── _suggestion_application (SuggestionApplicationService)
```

**接口层委托**：

```
build_internal_router()
    └── InternalAPIService
            ├── governance_*
            ├── dashboard_*
            └── execution_*

build_public_router()
    └── PublicAPIService
            ├── plan()
            ├── run()
            └── diagnose()
```

### 7.5 门面模式（Facade）

| Facade | 位置 | 封装 |
|--------|------|------|
| `GovernanceFacade` | `governance/facade.py` | HITL/Runner/Suggestion |
| `ObservabilityFacade` | `observability/facade.py` | Phoenix/Events |
| `SuggestionFacade` | `governance/suggestion/facade.py` | 建议操作 |
| `HitlFacade` | `governance/hitl/facade.py` | HITL 协调 |

### 7.6 状态机模式

**位置**：`application/services/lifecycle_state_machine.py`

```python
class LifecycleStateMachine:
    stage: str = "new"
    can_transition(from_stage, to_stage) -> bool
    validate_transition(from_stage, to_stage) -> Optional[str]
    next_stages(stage) -> tuple[str, ...]
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

**Internal API** (`interfaces/http/internal.py`)：
- 仪表盘专用
- 审计日志
- 速率限制
- 请求上下文传递

**Public API** (`interfaces/http/public.py`)：
- 外部集成
- `/api/v1` 前缀
- 标准化请求/响应

---

## 9. 必须遵循的设计规范

### 9.1 分层规范

1. **禁止**：domain 层依赖任何其他业务层
2. **禁止**：基础设施层暴露给应用层以外
3. **必须**：使用 Facade 封装复杂子域
4. **必须**：接口层只做转发，不含业务逻辑

### 9.2 扩展性规范

1. **必须**：新功能通过 Hook 扩展
2. **必须**：新工具集成通过 Adapter 实现
3. **必须**：新治理规则实现 Rule 接口
4. **鼓励**：使用 pluggy 插件协议

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

---

## 10. 禁止事项

### 10.1 架构破坏

| 禁止项 | 原因 |
|--------|------|
| 在 domain 层导入 execution | 违反分层原则 |
| 在 api.py 直接操作数据库 | 违反分层原则 |
| 绕过 Hook 直接修改状态 | 破坏扩展机制 |
| 绕过 GovernanceFacade 直接调用治理服务 | 破坏治理一致性 |

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

---

## 11. API 端点清单

### 11.1 Internal API

| 端点 | 方法 | 服务 | 说明 |
|------|------|------|------|
| `/api/governance/latest` | GET | Governance | 最新治理报告 |
| `/api/governance/history` | GET | Governance | 治理历史 |
| `/api/governance/check` | POST | Governance | 执行治理检查 |
| `/api/dashboard/governance` | GET | Dashboard | 仪表盘治理视图 |
| `/api/dashboard/platform` | GET | Dashboard | 平台工作区 |
| `/api/dashboard/trace` | GET | Dashboard | 执行追踪 |
| `/api/dashboard/fitness` | GET | Dashboard | 适配度视图 |
| `/api/dashboard/deploy` | GET | Dashboard | 部署视图 |
| `/api/dashboard/lifecycle-contract` | GET | Dashboard | 生命周期契约 |
| `/api/console/overview` | GET | Console | 控制台概览 |

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
| 状态机 | `sprintcycle/application/services/lifecycle_state_machine.py` |
| 事件总线 | `sprintcycle/execution/events.py` |
| 治理运行器 | `sprintcycle/governance/runner.py` |
| 质量规则 | `sprintcycle/domain/quality_spec/rules/rule.py` |
| Hook 系统 | `sprintcycle/hooks.py` |
| 插件协议 | `sprintcycle/domain/quality_spec/plugin_protocols.py` |
| HITL 协调 | `sprintcycle/governance/hitl/coordinator.py` |
| 建议服务 | `sprintcycle/governance/suggestion/service.py` |

---

## 附录 B：变更流程

### B.1 添加新功能

1. 确认功能属于哪一层
2. 如果需要扩展，添加到对应扩展点
3. 更新本文档的对应章节

### B.2 添加新治理规则

1. 实现 `Rule` 接口
2. 注册到 `RuleRegistry`
3. 更新 `sprintcycle.toml` 中的 rules 配置

### B.3 添加新适配器

1. 实现 `QualityAdapter` 接口
2. 注册到 `QualityRegistry`
3. 添加到 `sprintcycle.toml` 的 adapters 配置

---

> **版本**：v1.0  
> **更新日期**：2024-01-20  
> **维护者**：架构团队
