# SprintCycle 架构不变性文档

> 本文档记录 SprintCycle 代码库的架构不变性（Architecture Invariants），即不可变更的核心设计约束。  
> 任何代码变更必须遵守本文档规定的边界、职责和契约。

---

## 1. 代码库统计

| 指标 | 数值 |
|------|------|
| Python 文件总数 | 360+ |
| 总代码行数 | 38,000+ |
| 顶层模块数 | 6 |

### 1.1 模块分布

| 模块 | 文件数 | 说明 |
|------|--------|------|
| `domain/core/execution` | 80+ | 执行引擎、状态管理、事件总线、agents、hooks、orchestrator、聚合根 |
| `domain/core/governance` | 78+ | 治理、HITL、建议、版本控制、arch_guard、聚合根、验证引擎 |
| `domain/core/lifecycle` | 10+ | 生命周期契约、状态机、聚合根、值对象、领域服务 |
| `infrastructure` | 62+ | 配置、持久化、集成、部署、可观测性适配器 |
| `application` | 47 | 服务编排（按领域组织：lifecycle、governance、evolution、dashboard） |
| `interfaces/http` | 14 | HTTP 接口层（dashboard 按领域划分路由） |
| `composition` | 3 | 组合根层（依赖注入） |

---

## 2. 分层架构

### 2.1 层级定义（洋葱架构 - 从外到内）

```
┌─────────────────────────────────────────────────────────────┐
│                    interfaces/http/                        │
│   (HTTP API: dashboard/[execution, governance, lifecycle, │
│    hitl, suggestions] / public/ / middleware/)            │
│                       ↓                                   │
│              ┌─────────────────────┐                      │
│              │  HTTP 路由适配层    │                      │
│              └─────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│                     composition/                           │
│    (http_factory.py, evolution_factory.py,                │
│     orchestration_factory.py)                             │
│                       ↓                                   │
│              ┌─────────────────────┐                      │
│              │    组合根 - 依赖注入 │                      │
│              └─────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│                     application/                           │
│    (Services: execution, governance, lifecycle, evolution, │
│     dashboard, observability - organized by domain)        │
│                       ↓                                   │
│              ┌─────────────────────┐                      │
│              │  用例编排与服务层   │                      │
│              └─────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│                       domain/                              │
│   (Core: lifecycle, execution, evolution, governance;      │
│    Supporting: intent, fitness;                           │
│    Generic: errors, prompts, models, platform, ports,     │
│             interfaces)                                   │
│                       ↓                                   │
│              ┌─────────────────────┐                      │
│              │  领域模型与业务规则  │                      │
│              │  聚合根与值对象      │                      │
│              └─────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│                  infrastructure/                           │
│  (shared/persistence, adapters/core, adapters/generic)     │
│                       ↓                                   │
│              ┌─────────────────────┐                      │
│              │   基础设施适配层    │                      │
│              │   adapters/:实现   │                      │
│              └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**洋葱架构层次说明：**

| 层级 | 位置 | 职责 | 依赖方向 |
|------|------|------|----------|
| **interfaces** | 最外层 | HTTP 接口、请求路由、上下文传递、中间件 | 依赖 application |
| **composition** | 第二层 | 组合根、依赖注入、服务初始化 | 依赖 application 和 infrastructure |
| **application** | 第三层 | 用例编排、服务协调、事务边界 | 依赖 domain |
| **domain** | 第四层 | 领域模型、业务规则、聚合根、值对象、端口定义 | 无外部依赖 |
| **infrastructure** | 最内层 | 数据库、缓存、外部集成、适配器 | 被所有层依赖 |

**领域层子域划分：**
- **Core Domains（核心子域）**: lifecycle, execution, evolution, governance（含 verification）
- **Supporting Domains（支撑子域）**: intent, fitness  
- **Generic Domains（通用子域）**: errors, prompts, models, platform, ports, interfaces

### 2.2 各层职责

| 层级 | 核心职责 | 不变性约束 |
|------|----------|------------|
| **interfaces** | HTTP 请求路由、请求上下文、审计日志、中间件 | 仅做请求转发，不含业务逻辑 |
| **composition** | 依赖注入、服务组装、工厂注册 | 纯组装逻辑，不含业务实现 |
| **application** | 跨服务编排、生命周期管理、API 聚合 | 依赖 domain，不直接操作基础设施 |
| **domain** | 领域模型、业务规则、聚合根、值对象、领域服务、端口定义 | 无外部依赖，纯业务表达 |
| **infrastructure** | 配置、持久化、外部集成、可观测性 | 实现细节，不暴露给 domain |

### 2.3 跨层依赖规则

```
interfaces → composition → application → domain → infrastructure
```

**分层依赖说明（从外到内）：**
- **interfaces** 依赖 **application** 和 **composition**
- **composition** 依赖 **application** 和 **infrastructure**
- **application** 依赖 **domain**
- **domain** 无外部依赖（纯业务逻辑）
- **infrastructure** 被所有层依赖（不依赖任何层）

**domain 层内部子域依赖：**
```
core/ (lifecycle, execution, evolution, governance)
    ↓
supporting/ (intent, fitness)
    ↓
generic/ (errors, prompts, models, platform, ports, interfaces)
```

**禁止**：
- domain 层依赖 application 层或 interfaces 层
- infrastructure 层依赖任何业务层
- 任何层直接访问数据库实现细节
- **工厂层包含适配器实现**
- **composition 层包含业务逻辑**

---

## 3. DDD 聚合根设计

### 3.1 核心子域聚合根

| 子域 | 聚合根 | 值对象 | 领域服务 |
|------|--------|--------|----------|
| **lifecycle** | `LifecycleRoot` | `StageEvidence`, `CorrelationContext`, `LifecycleEvidence`, `FailureInfo`, `RuntimeRef`, `GovernanceRef`, `EvolutionRef` | `LifecycleStateMachineService` |
| **execution** | `SprintAggregate`, `ReleasePlanAggregate` | `TaskResult`, `SprintResult` | - |
| **evolution** | `EvolutionRequest`, `SandboxSession` | `VersionArtifact`, `EvolutionEvidence` | - |
| **governance** | `GovernanceSession`, `RuleSetAggregate` | `GovernanceRule`, `RuleEvaluation`, `Finding`, `VerificationFinding`, `VerificationRule`, `VerificationReport` | - |

### 3.2 聚合根设计原则

1. **不可变设计**：所有状态修改返回新实例，保证线程安全
2. **值对象**：无身份标识，通过属性值相等判断
3. **事件驱动**：子域间通过 `DomainEvent` 通信，解耦依赖
4. **ID 引用**：跨聚合引用使用 ID 而非直接对象引用，防止循环依赖

### 3.3 领域事件系统

| 事件基类 | 位置 | 说明 |
|----------|------|------|
| `DomainEvent` | `domain/core/events/common.py` | 所有领域事件的基类 |
| `EventBus` | `domain/core/events/handlers.py` | 事件发布/订阅机制 |

**事件驱动架构：**
```
Execution → Governance → Evolution
    ↓            ↓            ↓
SprintCompleted → GovernanceCompleted → EvolutionPromoted
```

---

## 4. 核心能力清单

SprintCycle 不可替代的核心功能：

### 4.1 执行生命周期管理

| 能力 | 位置 | 说明 |
|------|------|------|
| 阶段编排 | `application/services/execution/phase_workflow.py` | 统一执行流程编排 |
| 状态机 | `domain/core/lifecycle/services.py` | 15 个生命周期阶段定义 |
| 聚合根 | `domain/core/lifecycle/lifecycle_root.py` | `LifecycleRoot` 不可变聚合根 |
| 恢复机制 | `application/services/governance/repair_orchestration_service.py` | 失败自动恢复路由 |
| 证据收集 | `domain/core/lifecycle/values.py` | `StageEvidence` 值对象 |

### 4.2 质量治理

| 能力 | 位置 | 说明 |
|------|------|------|
| 规则引擎 | `domain/core/governance/quality_spec/rules/rule.py` | 规则定义与匹配 |
| 架构守卫 | `domain/core/governance/arch_guard/` | 架构约束检查 |
| 验证引擎 | `domain/core/governance/verification/` | 多源验证提供者 |
| 聚合根 | `domain/core/governance/aggregates/governance_aggregates.py` | `GovernanceSession`, `RuleSetAggregate` |

### 4.3 人类在环（HITL）

| 能力 | 位置 | 说明 |
|------|------|------|
| 决策请求 | `domain/core/governance/hitl/coordinator.py` | 人工决策协调 |
| 会话管理 | `domain/core/governance/hitl/session.py` | 决策上下文 |
| 策略评估 | `domain/core/governance/hitl/policy.py` | 自动决策策略 |

### 4.4 建议系统

| 能力 | 位置 | 说明 |
|------|------|------|
| 建议生成 | `domain/core/governance/suggestion/service.py` | 从执行事件生成建议 |
| 审批流程 | `domain/core/governance/suggestion/approval.py` | 建议审核 |
| HITL 提升 | `domain/core/governance/suggestion/bridge.py` | 建议转 HITL |

### 4.5 可观测性

| 能力 | 位置 | 说明 |
|------|------|------|
| 事件总线 | `domain/core/events/handlers.py` | 发布-订阅事件 |
| 追踪 | `infrastructure/adapters/generic/observability/facade.py` | 运行追踪 |
| 诊断 | `infrastructure/adapters/generic/observability/diagnostics/` | 健康报告 |
| 诊断类型 | `domain/generic/interfaces/diagnostics.py` | `DiagnoseResult` 类型定义 |

---

## 5. 扩展点清单

### 5.1 插件化扩展

| 扩展点 | 协议/接口 | 位置 |
|--------|-----------|------|
| 质量规则插件 | `QualityPlugin` | `domain/core/governance/quality_spec/plugin_protocols.py` |
| 治理 argv 插件 | `pluggy` | `domain/core/governance/pluggy_host.py` |
| 执行 hooks | `HookDefinition` | `domain/core/execution/hooks/` |
| 治理 hooks | `GovernanceHook` | `domain/core/governance/task_hooks.py`, `sprint_hooks.py` |

### 5.2 适配器扩展

| 扩展点 | 说明 | 位置 |
|--------|------|------|
| 质量适配器 | 集成 Bandit, Arch, Deal 等 | `domain/core/governance/quality_spec/adapters/` |
| 验证提供者 | Playwright, 视觉对比等 | `domain/core/governance/verification/providers/` |
| LLM 提供者 | 模型调用抽象 | `infrastructure/adapters/generic/llm_provider.py` |
| 事件后端 | SQLite, Memory 等 | `infrastructure/adapters/core/execution/state_store/sqlite_event_backend.py` |
| 编排适配器 | 端口实现 | `infrastructure/adapters/core/orchestration/adapters.py` |

---

## 6. 契约接口

### 6.1 生命周期契约

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

### 6.2 状态机契约

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

### 6.3 聚合根契约

```python
# LifecycleRoot 聚合根核心字段
@dataclass(frozen=True)
class LifecycleRoot:
    contract_id: str
    execution_id: str
    task_id: str
    project_path: str
    stage: LifecycleStage
    status: LifecycleStatus
    intent: str
    evidence: LifecycleEvidence
    stage_history: tuple[StageHistoryEntry, ...]
    metadata: frozendict[str, Any]
```

---

## 7. 架构治理规则

### 7.1 架构守卫（ArchGuard）

| 规则 ID | 检查内容 | 严重性 |
|---------|----------|--------|
| `planning:release_plan_empty` | ReleasePlan 不为空 | error |
| `planning:sprint_name_duplicate` | Sprint 名称唯一 | error |
| `review:extension_point_bypass` | 禁止绕过治理扩展点 | error |
| `review:adapter_in_factory` | 禁止在工厂中定义适配器 | error |

### 7.2 聚合根规则

| 规则 ID | 检查内容 | 严重性 |
|---------|----------|--------|
| `aggregate:immutable` | 聚合根必须使用不可变设计 | error |
| `aggregate:identity` | 聚合根必须有唯一标识 | error |
| `aggregate:value_object` | 值对象必须通过属性值相等判断 | error |

### 7.3 依赖规则

| 规则 ID | 检查内容 | 严重性 |
|---------|----------|--------|
| `dependency:domain_no_external` | domain 层不能有外部依赖 | error |
| `dependency:infrastructure_no_business` | infrastructure 不能依赖业务层 | error |
| `dependency:composition_only_wiring` | composition 层只能包含组装逻辑 | error |

---

## 8. 设计模式清单

### 8.1 聚合模式

**位置**：`domain/core/lifecycle/lifecycle_root.py`

```python
# 聚合根模式
class LifecycleRoot:
    def transition_to(self, stage: LifecycleStage) -> LifecycleRoot:
        # 返回新实例（不可变设计）
        return LifecycleRoot(..., stage=stage)
```

### 8.2 观察者模式（Event-Driven）

**位置**：`domain/core/events/handlers.py`

```python
class EventBus:
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable): ...
    def publish(self, event: DomainEvent): ...
```

### 8.3 策略模式（Policies）

| 策略 | 位置 | 说明 |
|------|------|------|
| `PromotionPolicy` | `application/services/governance/promotion_policy.py` | 晋升策略 |
| `HitlPolicy` | `domain/core/governance/hitl/policy.py` | HITL 决策策略 |

### 8.4 门面模式（Facade）

| Facade | 位置 | 封装 |
|--------|------|------|
| `GovernanceFacade` | `domain/core/governance/facade.py` | HITL/Runner/Suggestion |
| `ObservabilityFacade` | `infrastructure/adapters/generic/observability/facade.py` | Phoenix/Events |

### 8.5 端口-适配器模式

**位置**：`domain/generic/ports/` 和 `infrastructure/adapters/`

```python
# 端口定义（domain）
class RuntimeConfigPort(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...

# 适配器实现（infrastructure）
class RuntimeConfigAdapter(RuntimeConfigPort):
    def to_dict(self) -> Dict[str, Any]: ...
```

### 8.6 组合根模式

**位置**：`composition/`

```python
# 组合根 - 依赖注入组装
class HttpFactory:
    def create_app(self) -> FastAPI:
        # 注册基础设施适配器
        # 创建应用服务
        # 返回配置好的应用
```

---

## 9. API 设计规范

### 9.1 api.py 方法分类

**核心执行方法**（委托给 ExecutionLifecycleService）：
- `start_execution_run()`
- `execution_detail()`
- `execution_events()`
- `replay_execution()`

**治理方法**（委托给 GovernanceOrchestrationService）：
- `governance_check()`
- `review_suggestion()`, `approve_suggestion()`, `reject_suggestion()`

**生命周期方法**（委托给 LifecycleDeliveryService）：
- `runtime_lifecycle()`
- `lifecycle_contract()`

### 9.2 DDD 聚合根 API

```python
# 创建聚合根
lifecycle = create_lifecycle(
    execution_id="exec-123",
    task_id="task-456",
    project_path="/workspace",
    intent="优化代码"
)

# 状态转换（不可变）
lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
```

---

## 10. 必须遵循的设计规范

### 10.1 分层规范

1. **禁止**：domain 层依赖任何其他业务层
2. **禁止**：基础设施层暴露给应用层以外
3. **必须**：使用 Facade 封装复杂子域
4. **必须**：接口层只做转发，不含业务逻辑
5. **必须**：工厂层只做组装，不含适配器实现
6. **必须**：composition 层只做依赖注入，不含业务逻辑

### 10.2 聚合根规范

1. **必须**：聚合根使用不可变设计（frozen dataclass）
2. **必须**：状态修改返回新实例
3. **必须**：跨聚合引用使用 ID
4. **禁止**：聚合根直接引用其他聚合根

### 10.3 事件规范

1. **必须**：使用 `DomainEvent` 基类定义事件
2. **必须**：通过 `EventBus` 发布事件
3. **禁止**：直接在组件间耦合（通过事件解耦）

---

## 11. 禁止事项

### 11.1 架构破坏

| 禁止项 | 原因 |
|--------|------|
| 在 domain 层导入 execution | 违反分层原则 |
| 在 api.py 直接操作数据库 | 违反分层原则 |
| 绕过 Hook 直接修改状态 | 破坏扩展机制 |
| composition 层包含业务逻辑 | 违反组合根模式 |

### 11.2 聚合根破坏

| 禁止项 | 原因 |
|--------|------|
| 修改聚合根的可变字段 | 破坏不可变设计 |
| 跨聚合直接引用对象 | 破坏 ID 引用原则 |
| 删除聚合根必需字段 | 破坏聚合契约 |

### 11.3 事件破坏

| 禁止项 | 原因 |
|--------|------|
| 删除 `DomainEvent` 基类 | 破坏事件系统 |
| 修改 `EventBus` 接口 | 破坏发布/订阅机制 |

---

## 12. 附录：关键文件映射

| 功能 | 关键文件 |
|------|----------|
| 主入口 | `sprintcycle/api.py` |
| 组合根 | `sprintcycle/composition/http_factory.py` |
| 聚合根 | `sprintcycle/domain/core/lifecycle/lifecycle_root.py` |
| 领域服务 | `sprintcycle/domain/core/lifecycle/services.py` |
| 值对象 | `sprintcycle/domain/core/lifecycle/values.py` |
| 事件总线 | `sprintcycle/domain/core/events/handlers.py` |
| 执行聚合 | `sprintcycle/domain/core/execution/aggregates/execution_aggregates.py` |
| 治理聚合 | `sprintcycle/domain/core/governance/aggregates/governance_aggregates.py` |
| 演化聚合 | `sprintcycle/domain/core/evolution/aggregates/evolution_aggregates.py` |
| 验证引擎 | `sprintcycle/domain/core/governance/verification/engine.py` |

---

## 13. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v3.0 | 2026-05-26 | 引入 DDD 聚合根设计，重构 lifecycle、execution、governance、evolution 子域；新增 composition 层；verification 移入 governance |
| v2.1 | 2026-05-25 | 适配器与工厂分离 |
| v2.0 | 2026-05-20 | 引入洋葱架构分层 |

---

> **版本**：v3.0  
> **更新日期**：2026-05-26  
> **维护者**：架构团队  
> **变更说明**：引入 DDD 领域驱动设计，添加聚合根、值对象、领域服务、事件驱动架构和组合根模式