# SprintCycle Architecture and Orchestration Rule / 架构与编排规则

## English

You are working on SprintCycle, a layered orchestration system with a stable core architecture.

### 1. System constitution
- Preserve the current architecture and core skeleton.
- Keep the public API thin: it may normalize, route, delegate, and aggregate, but it must not own workflow logic.
- Keep execution, governance, observability, suggestion handling, deployment/runtime, and evolution strictly separated.
- Prefer existing services, facades, hooks, registries, adapters, and event backends over introducing parallel paths.
- During refactoring, file path adjustments, or folder structure adjustments, treat code preservation as a hard requirement: do not lose existing code, do not accidentally remove necessary call chains or dependencies, do not break any logic that should continue to exist after the move or cleanup, and make sure all references are handled correctly.
- Any new feature must land in the correct layer and use the smallest possible change.

### 2. Non-negotiable boundaries
- Do not move domain rules into the public API or presentation layer.
- Do not bypass hooks when lifecycle interception, compensation, or policy control is needed.
- Do not bypass facades when domain coordination already exists.
- Do not duplicate observability, governance, or suggestion logic inside execution code.
- Do not mutate suggestion or governance state outside their designated workflows.
- Do not introduce competing pipelines that weaken the current skeleton.

### 3. Layer ownership
- API layer: request normalization, thin routing, compatibility, and result aggregation.
- Service layer: workflow logic and orchestration of domain behavior.
- Facade layer: stable domain-facing coordination and compatibility.
- Hook layer: lifecycle interception, before/after/failed behavior, policy gating, and annotations.
- Orchestration/execution layer: runtime execution mechanics, scheduling, and execution lifecycle.
- Governance layer: checks, review, approval, and policy decisions.
- Observability layer: trace, replay, event capture, inspection, and read models.
- Suggestion layer: review, approval, rejection, archival, promotion, and replay linkage.
- Evolution layer: version growth, memory, knowledge capture, and iterative self-improvement.
- Registry/adapter layer: plugin lookup and environment-specific integration.

### 4. Web end-to-end stability guarantee
- For any task initiated from the Web platform, the system must be able to complete the full lifecycle stably.
- This applies equally to self-evolution tasks and user project optimization tasks.
- Based on the current implementation, the core chain should be understood as:
  request normalization / intent entry → plan and execution preparation → sprint orchestration and decomposition → SprintOrchestrator execution → execution observation and repair → result delivery and summary generation → deployment / runtime coordination → suggestion capture and governance → self-evolution and version evolution
- `SprintCycle` is the public coordination layer and must remain thin.
- The execution backbone centers on `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor`.
- LangGraph currently serves as the orchestration skeleton for `plan / run / observe / repair`.
- Suggestions, governance, observability, and evolution are coordinated capabilities around the execution backbone and must be integrated through existing services, facades, hooks, registries, and orchestrators.
- Any implementation change must preserve the continuity of this chain and must not weaken the ability to progress stably from one stage to the next.

### 4.1 Console Web boundary rule
- The Console Web is the human-machine entry, contract visualization surface, and operation panel.
- The backend is the contract-driven closed-loop orchestration system.
- The Console Web may create, submit, display, inspect, and operate on a lifecycle contract, but it must not become the orchestrator itself.
- The Console Web must not own stage transitions, recovery branching, governance decisions, promotion decisions, or version evolution logic.
- The Console Web must not duplicate runtime, suggestion, governance, promotion, or repair workflows that already belong to the backend contract flow.
- The Console Web should stay thin and stateless with respect to orchestration, and should only translate user intent into contract operations.
- All stable lifecycle completion guarantees must be implemented by the backend contract, stage machine, services, facades, hooks, registries, and orchestrators.
- If the Console Web needs additional capability, prefer adding contract fields, backend lifecycle states, or operation APIs rather than embedding business logic in the UI layer.
- Any change that affects recovery, promotion, execution, or evolution must keep the Console Web as an entry and control surface only, not as the source of orchestration truth.

### 5. LangGraph orchestration rule
- LangGraph is the core orchestration skeleton for planning and sprint-level scheduling.
- Current LangGraph scope is `plan / run / observe / repair`.
- Use LangGraph to structure plan decomposition into sprints and to manage internal scheduling within each sprint.
- Keep LangGraph focused on orchestration flow, state transitions, and routing between stages.
- Do not put domain business rules directly inside graph nodes when the logic belongs to application services, facades, hooks, or orchestrators.
- Do not use LangGraph as a shortcut to bypass existing architecture boundaries.
- Plan splitting, sprint creation, sprint sequencing, retry/fix routing, and intra-sprint dispatch must remain aligned with the layered architecture.
- Prefer reusing existing extension points, hook phases, registries, and service methods rather than introducing parallel graph-specific business logic.
- Preserve the clean separation between orchestration and domain responsibility.
- Any LangGraph change must keep the end-to-end lifecycle intact and must not weaken governance, observability, suggestion handling, or evolution flows.

### 6. Interaction rules
- For every request, first identify the owning subsystem.
- Determine whether the change is additive, behavioral, or structural.
- Reuse the nearest existing extension point before introducing new abstractions.
- Keep changes localized to the smallest responsible layer.
- If a request touches multiple subsystems, keep boundaries explicit and coordinate through services rather than direct coupling.
- Prefer explicit lifecycle steps over implicit side effects.
- Treat any repository change that could affect architecture, orchestration, lifecycle continuity, or layer ownership as a valid trigger for this rule.
- When code, docs, configs, tests, or dependency files change, re-check whether the web end-to-end chain and the public coordination layer remain intact.

### 7. Change strategy
1. Identify the owning subsystem.
2. Check whether an existing service, facade, hook, registry, or adapter can express the change.
3. Implement the smallest possible change in the correct layer.
4. Keep the public API thin.
5. Keep orchestration clean and domain logic localized.
6. Verify that the web-triggered end-to-end lifecycle still remains intact.
7. Verify that governance, observability, suggestion, and evolution flows remain consistent.

### 8. Default decision policy
- When in doubt, preserve the current architecture.
- Prefer extension over replacement.
- Prefer composition over coupling.
- Prefer service-level changes over API-level complexity.
- Prefer explicit flow over hidden behavior.
- Avoid speculative abstractions and avoid duplicating logic across layers.
- If behavior belongs to a hook, facade, service, registry, or LangGraph orchestration stage, implement it there rather than inline.

## 中文

你正在 SprintCycle 中工作。SprintCycle 是一个分层的编排系统，必须保持稳定的核心架构。

### 1. 系统总则
- 必须保留当前架构和核心骨架。
- 公共 API 必须保持“薄”：只负责归一化、路由、委派和结果汇总，不得承载工作流业务逻辑。
- 执行、治理、可观测性、建议处理、部署/运行时、自进化等职责必须严格分离。
- 优先复用现有的 service、facade、hook、registry、adapter 和 event backend，不要引入平行路径。
- 在重构、文件路径调整或文件夹结构调整过程中，代码保留必须作为硬性要求：不要丢失现有代码，不要误删必要的调用链或依赖关系，也不要破坏本来应该继续存在的逻辑，并且要处理好所有引用问题。
- 任何新功能都必须落到正确的层，并采用最小改动原则。

### 2. 不可破坏的边界
- 不要把领域规则塞进公共 API 或展示层。
- 当需要生命周期拦截、补偿或策略控制时，不要绕过 hook。
- 当已有 domain coordination 存在时，不要绕过 facade。
- 不要在执行代码里重复实现可观测性、治理或建议逻辑。
- 不要在建议或治理流程之外修改它们的状态。
- 不要引入会破坏当前骨架的竞争性流程或平行流水线。

### 3. 分层职责
- API 层：请求归一化、薄路由、兼容性处理、结果汇总。
- Service 层：工作流逻辑和领域行为编排。
- Facade 层：稳定的领域协调入口和兼容层。
- Hook 层：生命周期拦截、before/after/failed 行为、策略门控和注解。
- 编排/执行层：运行时执行机制、调度和执行生命周期。
- 治理层：检查、审核、批准和策略决策。
- 可观测性层：trace、replay、事件采集、检查和读模型。
- 建议层：审核、批准、拒绝、归档、晋升和 replay 关联。
- 自进化层：版本增长、记忆、知识捕获和迭代式自我改进。
- Registry/Adapter 层：插件查找和环境相关集成。

### 4. Web 端到端稳定性保障
- 对于任何从 Web 平台发起的任务，系统都必须能够稳定完成完整生命周期。
- 这同样适用于自进化任务和用户项目优化任务。
- 以当前实现为准，核心链路应理解为：
  请求归一化 / 意图入口 → 计划与执行准备 → Sprint 编排与拆分 → SprintOrchestrator 执行 → 执行观测与修复 → 结果交付与摘要生成 → 部署 / 运行时联动 → 建议捕获与治理 → 自进化与版本演化
- `SprintCycle` 是公共协调层，只负责归一化、路由、委派和结果汇总，不承载核心工作流逻辑。
- 执行主干当前以 `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor` 为核心。
- 当前 LangGraph 以 `plan / run / observe / repair` 为主要编排骨架，负责计划、执行、观测和修复的流程组织，不替代领域服务、治理流程或自进化逻辑。
- 建议、治理、可观测性和自进化是围绕执行主干协同工作的系统能力，应通过现有 service、facade、hook、registry 和 orchestrator 接入，不得破坏主干架构。
- 任何实现修改都必须保持这条闭环的连贯性，不能削弱 Web 发起任务后的稳定推进能力，也不能绕过现有服务层、门面层、hook 或编排层。

### 4.1 控制台 Web 边界规则
- 控制台 Web 是人机入口、contract 可视化层和操作面板。
- 后端是 contract 驱动的闭环编排系统。
- 控制台 Web 可以创建、提交、展示、查看和操作 lifecycle contract，但不能演化成编排器本身。
- 控制台 Web 不能拥有阶段流转、恢复分支、治理决策、promotion 决策或版本演化逻辑。
- 控制台 Web 不能复制已属于后端 contract 流程的 runtime、suggestion、governance、promotion 或 repair 工作流。
- 控制台 Web 应保持薄且尽量无状态，只负责把用户意图翻译成 contract 操作。
- 所有稳定完成生命周期的能力都必须由后端 contract、阶段机、service、facade、hook、registry 和 orchestrator 实现。
- 如果控制台 Web 需要新增能力，应优先增加 contract 字段、后端生命周期状态或操作 API，而不是把业务逻辑塞进 UI 层。
- 任何影响恢复、promotion、执行或演化的变更，都必须保持控制台 Web 只作为入口和控制面，而不是编排事实来源。

### 5. LangGraph 编排规则
- LangGraph 是规划与 Sprint 级调度的核心编排骨架。
- 当前 LangGraph 的范围是 `plan / run / observe / repair`。
- 应使用 LangGraph 来组织 plan 拆分为 sprint，以及管理每个 sprint 内部的调度。
- LangGraph 只应聚焦于编排流程、状态转移和阶段间路由。
- 不要把领域业务规则直接写进 graph 节点，除非这些逻辑本来就属于 application service、facade、hook 或 orchestrator。
- 不要把 LangGraph 当成绕过现有架构边界的捷径。
- plan 拆分、sprint 创建、sprint 排序、修复重试路由、sprint 内部派发，都必须与分层架构保持一致。
- 优先复用现有扩展点、hook phase、registry 和 service 方法，而不是引入平行的 graph 专用业务逻辑。
- 必须保持编排与领域责任的清晰分离。
- 任何 LangGraph 变更都必须保持端到端生命周期完整，不能削弱治理、可观测性、建议处理或自进化流程。

### 6. 交互规则
- 对于每个需求，先识别所属子系统。
- 判断这次修改是新增、行为变更还是结构调整。
- 优先复用最近的现有扩展点，再考虑新增抽象。
- 把改动限制在最小的责任层中。
- 如果一个需求涉及多个子系统，必须保持边界清晰，通过 service 协调，而不是直接耦合。
- 优先使用显式生命周期步骤，避免隐式副作用。

### 7. 修改策略
1. 识别所属子系统。
2. 检查现有 service、facade、hook、registry 或 adapter 是否能表达该变化。
3. 在正确层中实现最小改动。
4. 保持公共 API 薄。
5. 保持编排简洁，领域逻辑局部化。
6. 验证 Web 触发的端到端生命周期仍然完整。
7. 验证治理、可观测性、建议和自进化流程保持一致。

### 8. 默认决策原则
- 有疑问时，优先保留当前架构。
- 优先扩展而不是替换。
- 优先组合而不是耦合。
- 优先在 service 层修改，而不是增加 API 层复杂度。
- 优先显式流程，而不是隐藏行为。
- 避免投机性的抽象，也避免在多层重复逻辑。
- 如果行为属于 hook、facade、service、registry 或 LangGraph 编排阶段，就应在那个位置实现，而不是内联实现。
