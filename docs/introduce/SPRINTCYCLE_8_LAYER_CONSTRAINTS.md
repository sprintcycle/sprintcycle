# SprintCycle 8-Layer Directory Constraints

## 中文

本文档定义 SprintCycle 最终稳定的目录约束。重构、迁移、扩展、收敛时，必须遵守以下规则。

### 1. 总原则
`sprintcycle/` 下只允许这 8 个顶层目录作为业务代码组织方式：

- `entrypoints/`
- `presentation/`
- `application/`
- `execution/`
- `governance/`
- `observability/`
- `domain/`
- `infrastructure/`

#### 约束
- 不允许再新增其他业务顶层目录。
- 不允许通过旧目录名作为公共 API 或兼容层。
- 不允许在根包 `sprintcycle/__init__.py` 中继续聚合旧结构导出。
- 不允许跨层直接调用绕过约定边界。

### 2. 各目录职责约束

#### `entrypoints/`
职责：
- CLI / MCP / HTTP / 各种入口适配
- 参数解析
- 命令分发
- 请求 / 响应转换

约束：
- 只能做入口适配，不写业务逻辑。
- 不直接访问数据库、执行器、状态机实现。
- 不直接拼装复杂业务对象，交给 `application/` 或 `presentation/`。

允许调用：
- `application/`
- `presentation/`
- `governance/` 的读取接口
- `observability/` 的读取接口
- `domain/` 的纯模型与接口

#### `presentation/`
职责：
- dashboard
- view / projection / view model
- 面向人类展示的聚合数据

约束：
- 只能做读模型和展示模型构建。
- 不修改业务状态。
- 不直接写持久化。
- 不直接驱动执行流程。
- 不承载策略判断。

允许调用：
- `application/` 的查询 / 编排结果
- `observability/` 的 trace / event / health 数据
- `governance/` 的审计 / 审批 / 建议数据
- `domain/` 的展示所需模型

#### `application/`
职责：
- use case
- orchestration
- workflow
- plan expansion
- 服务编排

约束：
- 负责“做什么”和“顺序如何”。
- 不直接实现底层执行细节。
- 不直接依赖 UI。
- 不直接操作外部 SDK 的具体实现。
- 不把领域规则写成硬编码流程。

允许调用：
- `domain/`
- `execution/`
- `governance/`
- `observability/`
- `infrastructure/` 的抽象接口或仓储 / 客户端门面

#### `execution/`
职责：
- executor / engine / worker
- state machine
- planners
- agents
- rollback / retry / hooks

约束：
- 负责“怎么执行”。
- 不决定业务策略。
- 不负责展示。
- 不直接拼 dashboard payload。
- 不直接从入口层接收原始请求。
- 状态机与执行流程是执行层核心，不可被 UI 层反向引用。

允许调用：
- `domain/`
- `infrastructure/`
- `governance/` 的约束判断结果
- `observability/` 的事件 / trace 记录接口

#### `governance/`
职责：
- policy
- approval
- audit
- versioning
- hitl
- arch guard
- suggestion / review / compliance

约束：
- 负责“允许不允许”和“是否合规”。
- 不做执行动作。
- 不写 UI 逻辑。
- 不直接操作 `dashboard` / `presentation`。
- 审批、审计、版本记录要可追溯。
- versioning 相关实现要区分“治理接口”与“基础设施实现”。

允许调用：
- `domain/`
- `observability/`
- `infrastructure/` 的版本库、存储、适配器实现
- 向 `application/` 提供审批结果或策略决策

#### `observability/`
职责：
- trace
- replay
- event
- metrics
- diagnostics
- health report

约束：
- 只负责观测与诊断。
- 不做业务决策。
- 不直接修改状态。
- 不直接驱动执行。
- 不能把观测数据和业务对象强耦合成流程逻辑。

允许调用：
- `domain/` 中的事件 / 模型定义
- `infrastructure/` 中的存储 / 导出实现
- 被 `presentation/`、`governance/`、`application/` 读取

#### `domain/`
职责：
- 核心业务模型
- value object
- entity
- protocol / interface
- domain rule
- spec / policy abstraction

约束：
- 尽量不依赖上层目录。
- 不依赖 `presentation/`、`application/`、`entrypoints/`。
- 不直接依赖具体 `infrastructure/` 实现。
- 只定义领域语义，不关心技术细节。

允许调用：
- 原则上只依赖标准库或非常稳定的基础类型
- 可定义抽象接口供上层实现
- 可被其他层引用，但本身不反向引用上层

#### `infrastructure/`
职责：
- DB
- MQ
- cache
- config
- logging
- sandbox
- third-party SDK implementations
- adapter / client / repository 实现

约束：
- 只放技术实现，不放业务决策。
- 不做领域编排。
- 不承载 UI / presentation 逻辑。
- 不直接依赖上层的业务服务实现。
- 对外暴露实现，供 `application/`、`execution/`、`governance/` 调用。

### 3. 调用关系约束

#### 推荐调用方向
- `entrypoints/` → `application/` / `presentation/` / `governance/` / `observability/`
- `presentation/` → `application/` / `observability/` / `governance/` / `domain/`
- `application/` → `domain/` / `execution/` / `governance/` / `observability/` / `infrastructure/`
- `execution/` → `domain/` / `governance/` / `observability/` / `infrastructure/`
- `governance/` → `domain/` / `observability/` / `infrastructure/`
- `observability/` → `domain/` / `infrastructure/`
- `domain/` → 尽量不依赖上层
- `infrastructure/` → 可依赖第三方 SDK，但不反向依赖上层业务入口

#### 明确禁止的调用
- `presentation/` 直接写数据库
- `entrypoints/` 直接调用 executor 内部实现
- `execution/` 直接构造 dashboard view model
- `governance/` 直接做 UI 展示
- `domain/` 直接依赖 `presentation/` 或 `entrypoints/`
- `infrastructure/` 直接承载业务流程编排
- 任何层通过旧路径回跳到已废弃目录结构

### 4. 根据当前代码实际情况，建议加的“特别约束”

#### A. 根包不做业务聚合
`sprintcycle/__init__.py` 只保留极少稳定信息，例如版本号、作者信息。
不再作为旧架构的公共导出入口。

规则建议：
- 不要在根包持续导出 `execution` / `release_plan` / `orchestration` / `evolution` 等内部结构。
- 对外 API 要尽量走明确子包，而不是根包大导出。

#### B. `presentation` 只做“读聚合”
你现在的 `view_service` 很像展示聚合层，建议明确规定：

- 只能拼读数据
- 不做业务判断
- 不发起执行
- 不写存储

#### C. `application` 承担业务编排
你现在原先分散在 `services/`、`orchestration/`、`release_plan/`、`evolution/` 的很多能力，最终更适合在 `application/` 下按 use case 收敛。

规则建议：
- use case 归 `application/`
- 业务流程归 `application/`
- 计划扩展与编排归 `application/`

#### D. `governance` 要显式分子域
建议在规则里要求治理域至少区分：

- policy
- approval
- audit
- versioning
- hitl
- arch guard
- suggestion

这样以后不会再混成“大治理包”。

#### E. `observability` 只做观测，不能做决策
建议明确：

- trace / replay / event / diagnostics 可以被读
- 不能反向驱动执行逻辑
- 不能被当成业务状态源头

### 5. 最终验收标准
当重构完成后，必须满足：

- `sprintcycle/` 顶层仅剩 8 个目录
- 不存在旧目录残留
- 不存在兼容层
- 不存在未经同步修复的旧引用
- lint 通过

---

## English

This document defines the final stable directory constraints for SprintCycle. Any refactor, migration, expansion, or consolidation must follow these rules.

### 1. Core principle
Only these 8 top-level directories are allowed as the business code organization model under `sprintcycle/`:

- `entrypoints/`
- `presentation/`
- `application/`
- `execution/`
- `governance/`
- `observability/`
- `domain/`
- `infrastructure/`

#### Constraints
- Do not introduce any other top-level business directories.
- Do not use legacy directory names as public APIs or compatibility layers.
- Do not keep aggregating legacy exports in `sprintcycle/__init__.py`.
- Do not bypass the agreed layer boundaries with cross-layer direct calls.

### 2. Directory responsibility constraints

#### `entrypoints/`
Responsibilities:
- CLI / MCP / HTTP / external entry adapters
- argument parsing
- command dispatch
- request / response translation

Constraints:
- Only entry adaptation; no business logic.
- Do not access databases, executors, or state machine implementations directly.
- Do not assemble complex business objects; hand off to `application/` or `presentation/`.

Allowed calls:
- `application/`
- `presentation/`
- read-only interfaces from `governance/`
- read-only interfaces from `observability/`
- pure models and interfaces from `domain/`

#### `presentation/`
Responsibilities:
- dashboard
- view / projection / view model
- human-facing aggregated data

Constraints:
- Only build read models and presentation models.
- Do not mutate business state.
- Do not write persistence.
- Do not drive execution flows directly.
- Do not own strategy decisions.

Allowed calls:
- query / orchestration results from `application/`
- trace / event / health data from `observability/`
- audit / approval / suggestion data from `governance/`
- display-oriented models from `domain/`

#### `application/`
Responsibilities:
- use cases
- orchestration
- workflows
- plan expansion
- service orchestration

Constraints:
- Own the "what" and the "sequence".
- Do not implement low-level execution details.
- Do not depend directly on UI.
- Do not directly call concrete external SDK implementations.
- Do not encode domain rules as hardcoded flows.

Allowed calls:
- `domain/`
- `execution/`
- `governance/`
- `observability/`
- abstract interfaces, repositories, or client facades from `infrastructure/`

#### `execution/`
Responsibilities:
- executor / engine / worker
- state machine
- planners
- agents
- rollback / retry / hooks

Constraints:
- Own the "how to execute".
- Do not decide business strategy.
- Do not own presentation.
- Do not construct dashboard payloads directly.
- Do not accept raw requests directly from entry layers.
- Execution state machine and flow are core execution-layer concerns and must not be reverse-referenced by UI layers.

Allowed calls:
- `domain/`
- `infrastructure/`
- decision results from `governance/`
- event / trace recording interfaces from `observability/`

#### `governance/`
Responsibilities:
- policy
- approval
- audit
- versioning
- HITL
- arch guard
- suggestion / review / compliance

Constraints:
- Own "allowed or not" and "is it compliant".
- Do not perform execution actions.
- Do not write UI logic.
- Do not manipulate `dashboard` / `presentation` directly.
- Approval, audit, and version records must remain traceable.
- Separate governance interfaces from infrastructure implementations for versioning.

Allowed calls:
- `domain/`
- `observability/`
- versioning, storage, and adapter implementations in `infrastructure/`
- can provide approval results or policy decisions to `application/`

#### `observability/`
Responsibilities:
- trace
- replay
- event
- metrics
- diagnostics
- health reports

Constraints:
- Observability and diagnostics only.
- Do not make business decisions.
- Do not mutate state directly.
- Do not drive execution directly.
- Do not couple observability data tightly with business objects into process logic.

Allowed calls:
- event / model definitions in `domain/`
- storage / export implementations in `infrastructure/`
- read by `presentation/`, `governance/`, and `application/`

#### `domain/`
Responsibilities:
- core business models
- value objects
- entities
- protocols / interfaces
- domain rules
- spec / policy abstractions

Constraints:
- Avoid depending on higher layers.
- Do not depend on `presentation/`, `application/`, or `entrypoints/`.
- Do not depend directly on concrete `infrastructure/` implementations.
- Define business semantics only; ignore technical concerns.

Allowed calls:
- primarily standard library or very stable base types
- may define abstract interfaces for upper layers to implement
- can be referenced by other layers, but must not reference upper layers

#### `infrastructure/`
Responsibilities:
- DB
- MQ
- cache
- config
- logging
- sandbox
- third-party SDK implementations
- adapters / clients / repositories

Constraints:
- Technical implementations only; no business decisions.
- Do not orchestrate domain flows.
- Do not host UI / presentation logic.
- Do not directly depend on upper-layer business services.
- Expose implementations for `application/`, `execution/`, and `governance/` to consume.

### 3. Call-path constraints

#### Recommended call direction
- `entrypoints/` → `application/` / `presentation/` / `governance/` / `observability/`
- `presentation/` → `application/` / `observability/` / `governance/` / `domain/`
- `application/` → `domain/` / `execution/` / `governance/` / `observability/` / `infrastructure/`
- `execution/` → `domain/` / `governance/` / `observability/` / `infrastructure/`
- `governance/` → `domain/` / `observability/` / `infrastructure/`
- `observability/` → `domain/` / `infrastructure/`
- `domain/` → should avoid depending on upper layers
- `infrastructure/` → may depend on third-party SDKs, but must not depend back on upper-layer business entry points

#### Explicitly forbidden calls
- `presentation/` writing directly to the database
- `entrypoints/` calling executor internals directly
- `execution/` constructing dashboard view models directly
- `governance/` rendering UI directly
- `domain/` depending on `presentation/` or `entrypoints/`
- `infrastructure/` hosting business flow orchestration
- any layer jumping back to legacy directory structures through old paths

### 4. Special constraints based on the current codebase

#### A. The root package is not for business aggregation
`sprintcycle/__init__.py` should keep only a minimal stable surface, such as version and author information.
It must no longer act as the public export hub for the old architecture.

Rule guidance:
- Do not keep exporting internal structures like `execution`, `release_plan`, `orchestration`, or `evolution` from the root package.
- Public APIs should prefer explicit subpackages instead of a large root-package export surface.

#### B. `presentation` is read-only aggregation
Your current `view_service` behaves like a presentation aggregation layer. Make this explicit:

- only aggregate read data
- do not make business decisions
- do not trigger execution
- do not write storage

#### C. `application` owns business orchestration
Many capabilities that were previously scattered across `services/`, `orchestration/`, `release_plan/`, and `evolution/` should converge under `application/` as use cases.

Rule guidance:
- use cases belong to `application/`
- business flows belong to `application/`
- plan expansion and orchestration belong to `application/`

#### D. `governance` should be split into explicit subdomains
At minimum, governance should be organized around:

- policy
- approval
- audit
- versioning
- HITL
- arch guard
- suggestion

This prevents governance from becoming one oversized mixed bag.

#### E. `observability` only observes; it does not decide
Be explicit that:

- trace / replay / event / diagnostics may be read
- observability must not drive execution logic backward
- observability must not be treated as the source of business state

### 5. Final acceptance criteria
When refactoring is complete, the project must satisfy all of the following:

- only 8 top-level directories remain under `sprintcycle/`
- no legacy top-level directories remain
- no compatibility layer exists
- no outdated references remain unrepaired
- lint passes
