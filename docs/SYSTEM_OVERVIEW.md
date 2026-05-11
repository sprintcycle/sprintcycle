# SprintCycle System Overview / 系统总览

This document is a current snapshot of the system based on the latest implementation in the repository.
本文档基于仓库最新实现生成，作为系统当前快照使用。

---

## English

### 1. What SprintCycle is

SprintCycle is an orchestration platform that connects the full loop from intent understanding to final delivery, deployment, governance, suggestion handling, observability, and evolution.

The current implementation centers on a public facade plus workflow-specific application services. The public API coordinates, normalizes, and routes requests; the services own the actual workflow logic.

### 2. Architecture diagram

```mermaid
graph TD
  U[Users / CLI / Dashboard / MCP / SDK] --> A[SprintCycle API]
  A --> E[ExecutionLifecycleService]
  A --> G[GovernanceOrchestrationService]
  A --> S[SuggestionApplicationService]
  A --> O[ObservabilityService]
  A --> P[PlatformSummaryService]
  A --> F[Domain Facades]

  E --> OR[SprintOrchestrator]
  E --> EX[Execution Engine]
  E --> ST[Execution State / Store]
  E --> R[Runtime Registry]
  E --> HB[Execution Event Backend]
  E --> H[Hook Registry]

  G --> GF[GovernanceFacade]
  G --> AG[ArchGuard / Governance Checks]
  G --> H

  S --> SF[SuggestionFacade]
  S --> GV[Governance Facade]
  S --> H

  O --> OB[Observability Facade]
  O --> TR[Trace / Replay Payloads]

  P --> DV[Dashboard Views]
  P --> WV[Workbench / Platform Views]

  F --> GO[Governance]
  F --> SU[Suggestion]
  F --> OB
```

### 3. Data flow diagram

```mermaid
flowchart LR
  I[Intent / Workspace Context] --> N[Input Normalization]
  N --> R[Release Plan / Sprint Request]
  R --> T[Task Decomposition]
  T --> X[Sprint Execution]
  X --> Q[Evaluation / Fix]
  Q --> D[Final Delivery]
  D --> U[Deployment / Runtime Operation]
  X --> O[Observability]
  Q --> O
  O --> V[Suggestion Capture]
  V --> G[Governance Review]
  G --> E[Self-Evolution / Versioning]
  E --> R
```

### 4. Processing flow diagram

```mermaid
flowchart TD
  A[1. Intent parsing] --> B[2. Plan generation]
  B --> C[3. Task decomposition]
  C --> D[4. Sprint execution]
  D --> E[5. Evaluation and fix]
  E --> F[6. Final delivery]
  F --> G[7. Automatic deployment and runtime operation]
  G --> H[8. Suggestion capture and review]
  H --> I[9. Self-evolution / version growth]
```

### 5. Core end-to-end flow

The system is designed around the following lifecycle:

1. **Intent parsing**
2. **Plan generation**
3. **Task decomposition**
4. **Sprint execution**
5. **Evaluation and fix**
6. **Final delivery**
7. **Automatic deployment and runtime operation**
8. **Suggestion capture and review**
9. **Self-evolution / version growth**

This is not a single monolithic pipeline inside one class. It is a set of connected capabilities distributed across the API, services, facades, execution engine, governance layer, observability layer, and evolution/versioning layer.

### 6. Core multi-round sprint execution flow

A single sprint run is usually only one round in a longer loop. The current implementation supports a repeated cycle of execution, feedback, and follow-up work.

```mermaid
flowchart TD
  A[Start run] --> B[Build execution context]
  B --> C[Pre-run gate]
  C -->|pass| D[Start execution]
  C -->|blocked| Z[Return blocked result]
  D --> E[Collect execution events]
  E --> F[Observe results]
  F --> G{Needs fix?}
  G -->|yes| H[Create fix / follow-up tasks]
  H --> I[Update plan / release plan]
  I --> J[Next sprint round]
  J --> B
  G -->|no| K[Finalize delivery]
  K --> L[Auto deploy / runtime operation]
  L --> M[Capture suggestions]
  M --> N[Governance review]
  N --> O[Promote approved changes to evolution]
```

### 7. Intent parsing

Intent parsing turns user goals, workspace context, and existing project state into a structured starting point for execution.

Current implementation areas involved in this stage include:

- intent and memory handling in the evolution layer
- prompt / intent support utilities
- public API entry points that normalize input before delegation

Intent parsing is not implemented as a separate standalone monolith. It is distributed across the intent-related helpers and the public orchestration layer.

### 8. Plan generation

Plan generation converts the parsed intent into an executable release plan or sprint-oriented execution structure.

Current implementation areas involved in this stage include:

- execution planning utilities
- release plan parsing and orchestration paths
- sprint orchestration entry points exposed through `SprintCycle`
- downstream execution engine adapters

The public API coordinates plan-related inputs and delegates actual planning behavior to the orchestrator and execution stack.

### 9. Task decomposition

Task decomposition breaks a higher-level plan into workable execution units that can be run by sprint execution.

Current implementation areas involved in this stage include:

- task and sprint planning models
- execution planners and builders
- orchestrator logic that prepares runnable execution units
- runtime and state helpers that persist execution structure

Task decomposition is part of the execution workflow rather than a separate user-facing product surface.

### 10. Sprint execution

Sprint execution is the runtime path that actually runs the planned work.

Current implementation areas involved in this stage include:

- `SprintCycle.run(...)` as the public entry point
- `ExecutionLifecycleService` for execution startup and lifecycle coordination
- `SprintOrchestrator` and execution engine components for actual run behavior
- execution state, event backend, rollback, cache, and runtime registry helpers

Typical responsibilities in this stage include:

- creating an execution context
- applying pre-run gates
- starting execution runs
- updating execution state
- recording execution events
- exposing execution details and replay data

### 11. Evaluation and fix

After or during execution, the system can evaluate results and surface fix-oriented views and workflows.

Current implementation areas involved in this stage include:

- observability trace and replay data
- dashboard views for fix / fitness / execution status
- governance and policy checks that can feed back into execution quality
- report and summary helpers in the service layer

Evaluation is not a single isolated engine. It is a collection of read-side summaries and workflow feedback paths.

### 12. Final delivery

Final delivery represents the point where execution output becomes a usable result for the workspace, dashboard, or downstream automation.

Current implementation areas involved in this stage include:

- execution result objects
- platform and dashboard summary services
- deployment-related helpers and views
- observability payloads for final inspection

In the current codebase, “final delivery” is best understood as the combination of successful execution result materialization, summary generation, and downstream presentation.

### 13. Automatic deployment and runtime operation

SprintCycle also includes deployment-oriented and runtime-oriented support.

Current implementation areas involved in this stage include:

- deployment helpers
- runtime registry management
- dashboard deploy views
- compose and sandbox utilities
- integration adapters for environment-specific runtime behavior

The public API coordinates these capabilities but does not own the deployment internals.

### 14. Suggestions

Suggestion handling is a first-class governance workflow.

Current capabilities include:

- review
- approve
- reject
- archive
- promotion to HITL
- replay attachment
- capture of execution events into suggestion records

Current implementation centers on `SuggestionApplicationService`, `SuggestionFacade`, and the governance suggestion modules.

### 15. Self-evolution

SprintCycle includes evolution-oriented support for version growth, knowledge capture, and intent-driven iteration.

Current implementation areas involved in this stage include:

- version registry access
- evolution summary and index support
- memory store and knowledge repository integration
- evolution workflow helpers and controllers

Self-evolution is implemented as an explicit capability layer rather than as an implicit side effect of execution.

### 16. Governance and human-in-the-loop

Governance ensures that execution and suggestion flows can be checked, reviewed, and controlled.

Current implementation areas include:

- governance checks for planning and review gates
- pending / history / summary / request lookup
- suggestion review and approval flows
- HITL orchestration
- hook-based callbacks around governance actions

### 17. Observability

Observability is a separate read-side capability that keeps trace and replay concerns out of the main execution and governance workflows.

Current implementation areas include:

- event recording
- event listing
- trace payload generation
- replay payload generation
- execution detail views based on observability data

### 18. Hook and event protocol

The hook system is centralized in `sprintcycle/hooks.py`.

Current protocol:

- phases: `before`, `after`, `failed`
- policies: `fail_open`, `fail_closed`, `compensate`
- context objects: carry domain, action, subject, execution, project path, payload, metadata, and trace id
- result objects: can block, mutate, or annotate execution
- domain events: registered and emitted through the hook registry

Current hook domains include execution, suggestion, and governance.

### 19. Public API role

`SprintCycle` is the public coordination layer for CLI, dashboard, MCP, and SDK usage.

It is responsible for:

- initialization and dependency wiring
- parameter normalization
- thin cross-layer delegation
- result aggregation
- compatibility adapters when old behavior still needs to be supported

It is not responsible for owning the workflow rules themselves.

### 20. Main source-of-truth files

For the most accurate behavior, inspect these files first:

- `sprintcycle/api.py`
- `sprintcycle/hooks.py`
- `sprintcycle/services/execution_lifecycle_service.py`
- `sprintcycle/services/governance_orchestration_service.py`
- `sprintcycle/services/suggestion_application_service.py`
- `sprintcycle/services/observability_service.py`
- `sprintcycle/services/platform_summary_service.py`
- `sprintcycle/governance/facade.py`
- `sprintcycle/governance/suggestion/facade.py`
- `sprintcycle/observability/facade.py`
- `sprintcycle/orchestration/sprint_orchestrator.py`
- `sprintcycle/execution/`
- `sprintcycle/evolution/`

### 21. Chinese diagram summary

#### 架构图

```mermaid
graph TD
  U[用户 / CLI / Dashboard / MCP / SDK] --> A[SprintCycle API]
  A --> E[执行生命周期服务]
  A --> G[治理编排服务]
  A --> S[建议应用服务]
  A --> O[可观测性服务]
  A --> P[平台汇总服务]
  A --> F[领域门面]

  E --> OR[SprintOrchestrator]
  E --> EX[执行引擎]
  E --> ST[执行状态 / 存储]
  E --> R[运行时注册表]
  E --> HB[执行事件后端]
  E --> H[Hook 注册中心]

  G --> GF[GovernanceFacade]
  G --> AG[ArchGuard / 治理检查]
  G --> H

  S --> SF[SuggestionFacade]
  S --> GV[治理门面]
  S --> H

  O --> OB[ObservabilityFacade]
  O --> TR[Trace / Replay Payload]

  P --> DV[Dashboard 视图]
  P --> WV[Workbench / 平台视图]

  F --> GO[治理]
  F --> SU[建议]
  F --> OB
```

#### 数据流图

```mermaid
flowchart LR
  I[意图 / 工作区上下文] --> N[输入归一化]
  N --> R[Release Plan / Sprint 请求]
  R --> T[任务拆解]
  T --> X[Sprint 执行]
  X --> Q[评估 / 修复]
  Q --> D[最终交付]
  D --> U[部署 / 运行时操作]
  X --> O[可观测性]
  Q --> O
  O --> V[建议捕获]
  V --> G[治理审核]
  G --> E[自进化 / 版本管理]
  E --> R
```

#### 处理流程图

```mermaid
flowchart TD
  A[1. 意图解析] --> B[2. 计划生成]
  B --> C[3. 任务拆解]
  C --> D[4. Sprint 执行]
  D --> E[5. 评估修复]
  E --> F[6. 最终交付]
  F --> G[7. 自动部署运行]
  G --> H[8. 建议收集与审核]
  H --> I[9. 自进化 / 版本增长]
```

#### 完整的多轮 Sprint 执行流程图

```mermaid
flowchart TD
  A[开始运行] --> B[构建执行上下文]
  B --> C[Pre-run Gate]
  C -->|通过| D[开始执行]
  C -->|阻断| Z[返回阻断结果]
  D --> E[收集执行事件]
  E --> F[观察结果]
  F --> G{需要修复?}
  G -->|是| H[创建修复 / 后续任务]
  H --> I[更新计划 / Release Plan]
  I --> J[下一轮 Sprint]
  J --> B
  G -->|否| K[完成交付]
  K --> L[自动部署 / 运行时操作]
  L --> M[捕获建议]
  M --> N[治理审核]
  N --> O[批准变更进入自进化]
```

---

## 中文

### 1. SprintCycle 是什么

SprintCycle 是一个编排平台，连接从意图理解、计划生成、任务拆解、Sprint 执行、评估修复、最终交付，到自动部署运行、建议处理、治理控制和自进化的完整闭环。

当前实现以“公共门面 + 具体工作流应用服务”为中心。公共 API 负责协调、归一化和路由；真正的工作流逻辑由各个 service 负责。

### 2. 核心端到端流程

系统围绕以下生命周期设计：

1. **意图解析**
2. **计划生成**
3. **任务拆解**
4. **Sprint 执行**
5. **评估修复**
6. **最终交付**
7. **自动部署运行**
8. **建议收集与审核**
9. **自进化 / 版本增长**

它不是一个写死在单个类里的大流水线，而是分布在 API、服务层、门面层、执行引擎、治理层、可观测性层和演化/版本管理层中的多个能力组合。

### 3. 意图解析

意图解析的目标，是把用户目标、工作区上下文和已有项目状态，转成一个可执行的起点。

当前参与这一阶段的实现主要包括：

- 演化层中的 intent 和 memory 处理
- prompt / intent 相关工具
- 公共 API 在分发前做输入归一化

意图解析并不是一个单独的大模块，而是分散在 intent 相关工具和公共编排层中。

### 4. 计划生成

计划生成会把解析后的意图转换成可执行的 release plan 或 sprint 执行结构。

当前参与这一阶段的实现主要包括：

- 执行规划工具
- release plan 的解析和编排路径
- 通过 `SprintCycle` 暴露的 sprint 编排入口
- 下游执行引擎适配器

公共 API 负责接收计划相关输入，并把真正的规划行为委派给 orchestrator 和执行栈。

### 5. 任务拆解

任务拆解会把高层计划拆成可执行单元，供 sprint 执行运行。

当前参与这一阶段的实现主要包括：

- task 和 sprint 的规划模型
- execution planners 和 builders
- 准备可运行执行单元的 orchestrator 逻辑
- 持久化执行结构的 runtime / state 辅助工具

任务拆解属于执行工作流的一部分，而不是单独对外暴露的产品表面。

### 6. Sprint 执行

Sprint 执行是实际运行计划工作的运行时路径。

当前参与这一阶段的实现主要包括：

- 作为公共入口的 `SprintCycle.run(...)`
- 负责执行启动与生命周期协调的 `ExecutionLifecycleService`
- 负责真实运行行为的 `SprintOrchestrator` 和执行引擎组件
- execution state、事件后端、回滚、缓存和运行时注册表辅助工具

这一阶段通常负责：

- 创建 execution context
- 应用 pre-run gate
- 启动执行
- 更新执行状态
- 记录执行事件
- 暴露执行详情与 replay 数据

### 7. 评估修复

执行完成后或执行过程中，系统可以对结果进行评估，并提供修复导向的视图和工作流。

当前参与这一阶段的实现主要包括：

- observability 的 trace / replay 数据
- dashboard 中的 fix / fitness / execution 状态视图
- 会反向影响执行质量的治理和 policy 检查
- service 层中的 report 和 summary 辅助工具

评估不是一个单独孤立的引擎，而是一组读侧摘要和反馈路径的组合。

### 8. 最终交付

最终交付表示执行结果已经变成工作区、仪表盘或下游自动化可以使用的成果。

当前参与这一阶段的实现主要包括：

- 执行结果对象
- 平台和 dashboard summary service
- 与部署相关的辅助工具和视图
- 便于最终检查的 observability payload

在当前代码库里，“最终交付”更适合理解为：成功执行结果的落地、摘要生成与下游呈现的组合。

### 9. 自动部署运行

SprintCycle 也包含部署导向和运行时导向的支持。

当前参与这一阶段的实现主要包括：

- deployment 辅助工具
- runtime registry 管理
- dashboard deploy 视图
- compose 和 sandbox 工具
- 面向环境差异的集成适配器

公共 API 会协调这些能力，但不会自己承载部署内部机制。

### 10. 建议

Suggestion 处理是一个一等治理工作流。

当前能力包括：

- review
- approve
- reject
- archive
- promote 到 HITL
- attach replay
- 将 execution event 捕获为 suggestion 记录

当前实现主要集中在 `SuggestionApplicationService`、`SuggestionFacade` 和 governance suggestion 相关模块。

### 11. 自进化

SprintCycle 包含面向版本增长、知识捕获和意图驱动迭代的演化能力。

当前参与这一阶段的实现主要包括：

- version registry 访问
- evolution summary 和 index 支持
- memory store 与 knowledge repository 集成
- 演化工作流辅助器和控制器

自进化是一个明确的能力层，而不是执行过程中的隐式副作用。

### 12. 治理与 HITL

治理负责确保执行和建议流程可以被检查、审核和控制。

当前实现包括：

- 对 planning / review gate 的治理检查
- pending / history / summary / request 查询
- suggestion 的 review / approval 流程
- HITL 编排
- 围绕治理动作的 hook 回调

### 13. 可观测性

可观测性是一个独立的读侧能力，把 trace 和 replay 的关注点从主执行和治理流程中剥离出去。

当前实现包括：

- 事件记录
- 事件列表
- trace payload 生成
- replay payload 生成
- 基于 observability 数据的 execution detail 视图

### 14. Hook 与事件协议

hook 系统集中在 `sprintcycle/hooks.py`。

当前协议：

- phase：`before`、`after`、`failed`
- policy：`fail_open`、`fail_closed`、`compensate`
- context 对象：携带 domain、action、subject、execution、project path、payload、metadata、trace id
- result 对象：可以阻断、修改或补充执行上下文
- domain event：通过 hook registry 注册和发布

当前 hook domain 覆盖 execution、suggestion 和 governance。

### 15. 公共 API 的角色

`SprintCycle` 是 CLI、dashboard、MCP 和 SDK 使用的公共协调层。

它负责：

- 初始化与依赖装配
- 参数归一化
- 跨层薄转发
- 结果汇总
- 在需要时保留兼容适配器

它不负责直接拥有工作流规则本身。

### 16. 主要源码参考

若要查看最准确的行为，请优先阅读以下文件：

- `sprintcycle/api.py`
- `sprintcycle/hooks.py`
- `sprintcycle/services/execution_lifecycle_service.py`
- `sprintcycle/services/governance_orchestration_service.py`
- `sprintcycle/services/suggestion_application_service.py`
- `sprintcycle/services/observability_service.py`
- `sprintcycle/services/platform_summary_service.py`
- `sprintcycle/governance/facade.py`
- `sprintcycle/governance/suggestion/facade.py`
- `sprintcycle/observability/facade.py`
- `sprintcycle/orchestration/sprint_orchestrator.py`
- `sprintcycle/execution/`
- `sprintcycle/evolution/`