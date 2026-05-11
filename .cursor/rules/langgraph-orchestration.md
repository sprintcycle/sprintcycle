# SprintCycle LangGraph Orchestration Rule / SprintCycle LangGraph 编排规则

## English

### LangGraph orchestration rule
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

### Implementation guidance
- Treat graph nodes as orchestration units, not as domain service replacements.
- Keep graph transitions explicit and minimal.
- If a node needs business behavior, move that behavior into the owning service/facade/hook and let the graph call it.
- Avoid hardcoding workflow policy inside graph construction when the policy already exists in the domain layer.
- Keep graph-based changes aligned with the end-to-end lifecycle and the current execution backbone.

### 补充稳定性规则
- 禁止平行流程：不要用 graph 构造一条绕开主编排层的并行执行链。
- 扩展优先、替换禁止：优先在现有 graph 节点、边、hook、service 上扩展能力，不要重建整套编排。
- 状态只允许通过正式通道变更：graph 中的状态推进必须依赖既有服务和正式状态通道，不得直接污染领域状态。
- 端到端闭环优先：graph 改动必须保证 Web 任务仍可完整穿过请求、执行、修复、交付和后续治理链路。
- 图编排与领域逻辑分离：graph 只负责流程与状态迁移，业务规则仍归属 service / facade / hook / orchestrator。

## 中文

### LangGraph 编排规则
- LangGraph 是规划与 Sprint 级调度的核心编排骨架。
- 当前 LangGraph 作用范围是 `plan / run / observe / repair`。
- 应使用 LangGraph 来结构化 plan 拆分为 sprint，以及管理每个 sprint 内部的调度。
- LangGraph 只应聚焦于编排流程、状态转移和阶段间路由。
- 不要把领域业务规则直接写进 graph 节点，除非这些逻辑本来就属于 application service、facade、hook 或 orchestrator。
- 不要把 LangGraph 当成绕过现有架构边界的捷径。
- plan 拆分、sprint 创建、sprint 排序、修复重试路由、sprint 内部派发，都必须与分层架构保持一致。
- 优先复用现有扩展点、hook phase、registry 和 service 方法，而不是引入平行的 graph 专用业务逻辑。
- 必须保持编排与领域责任的清晰分离。
- 任何 LangGraph 变更都必须保持端到端生命周期完整，不能削弱治理、可观测性、建议处理或自进化流程。

### 实现指引
- 把 graph node 视为编排单元，而不是领域服务替代品。
- 保持 graph transition 显式且最小化。
- 如果某个节点需要业务行为，应把该行为移到对应的 service/facade/hook 中，再由 graph 调用。
- 当领域层已经存在策略时，不要在 graph 构造中硬编码工作流策略。
