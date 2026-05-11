# SprintCycle Core Architecture Rule / SprintCycle 核心架构规则

## English

You are working on SprintCycle, a layered orchestration system with a stable core architecture.

### System constitution
- Preserve the current architecture and core skeleton.
- Keep the public API thin: it may normalize, route, delegate, and aggregate, but it must not own workflow logic.
- Keep execution, governance, observability, suggestion handling, deployment/runtime, and evolution strictly separated.
- Prefer existing services, facades, hooks, registries, adapters, and event backends over introducing parallel paths.
- Any new feature must land in the correct layer and use the smallest possible change.

### Key component ownership
- AutoGPT is responsible for deployment specifications and platformized startup.
- LangGraph is responsible for execution graph adaptation.
- Phoenix is responsible for trace / replay observability adaptation.
- SprintCycle Core must continue to own business orchestration and the repair/fix closed loop.
- Do not move these responsibilities across layers unless the architecture is explicitly being redefined.

### Non-negotiable boundaries
- Do not move domain rules into the public API or presentation layer.
- Do not bypass hooks when lifecycle interception, compensation, or policy control is needed.
- Do not bypass facades when domain coordination already exists.
- Do not duplicate observability, governance, or suggestion logic inside execution code.
- Do not mutate suggestion or governance state outside their designated workflows.
- Do not introduce competing pipelines that weaken the current skeleton.

### Layer ownership
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

### Interaction rules
- For every request, first identify the owning subsystem.
- Determine whether the change is additive, behavioral, or structural.
- Reuse the nearest existing extension point before introducing new abstractions.
- Keep changes localized to the smallest responsible layer.
- If a request touches multiple subsystems, keep boundaries explicit and coordinate through services rather than direct coupling.
- Prefer explicit lifecycle steps over implicit side effects.

### Change strategy
1. Identify the owning subsystem.
2. Check whether an existing service, facade, hook, registry, or adapter can express the change.
3. Implement the smallest possible change in the correct layer.
4. Keep the public API thin.
5. Keep orchestration clean and domain logic localized.
6. Verify that the web-triggered end-to-end lifecycle still remains intact.
7. Verify that governance, observability, suggestion, and evolution flows remain consistent.

### Default decision policy
- When in doubt, preserve the current architecture.
- Prefer extension over replacement.
- Prefer composition over coupling.
- Prefer service-level changes over API-level complexity.
- Prefer explicit flow over hidden behavior.
- Avoid speculative abstractions and avoid duplicating logic across layers.
- If behavior belongs to a hook, facade, service, registry, or orchestration stage, implement it there rather than inline.

### Additional stability rules / 补充稳定性规则
- No parallel workflows: do not create competing pipelines or bypass the established orchestration path.
- Extension first, replacement last: prefer extending existing services, facades, hooks, registries, and adapters over replacing core flows.
- State changes must go through official channels: execution, governance, suggestion, and evolution state must be mutated only through their designated services or facades.
- End-to-end closure first: every change must preserve the web-triggered lifecycle from start to finish and keep downstream handoffs intact.
- Separate graph orchestration from domain logic: LangGraph or other orchestration graphs must remain flow coordination layers, not domain rule containers.

### 补充稳定性规则
- 禁止平行流程：不要创建竞争性的工作流，也不要绕过既定编排路径。
- 扩展优先、替换最后：优先扩展现有的 service、facade、hook、registry 和 adapter，而不是替换核心流程。
- 状态只允许通过正式通道变更：execution、governance、suggestion、evolution 的状态只能通过各自指定的 service 或 facade 变更。
- 端到端闭环优先：任何改动都必须保持 Web 触发后的生命周期从开始到结束完整可达，并保持下游交接连续。
- 图编排与领域逻辑分离：LangGraph 或其他编排图只能作为流程协调层，不能承载领域规则容器。

## 中文

你正在 SprintCycle 中工作。SprintCycle 是一个分层的编排系统，必须保持稳定的核心架构。

### 系统总则
- 必须保留当前架构和核心骨架。
- 公共 API 必须保持“薄”：只负责归一化、路由、委派和结果汇总，不得承载工作流业务逻辑。
- 执行、治理、可观测性、建议处理、部署/运行时、自进化等职责必须严格分离。
- 优先复用现有的 service、facade、hook、registry、adapter 和 event backend，不要引入平行路径。
- 任何新功能都必须落到正确的层，并采用最小改动原则。

### 关键组件职责限定
- AutoGPT 负责部署规格和平台化启动。
- LangGraph 负责执行图适配。
- Phoenix 负责 trace / replay 可观测性适配。
- SprintCycle Core 继续负责业务编排和修复闭环。
- 除非架构被明确重新定义，否则不要把这些职责迁移到别的层。

### 不可破坏的边界
- 不要把领域规则塞进公共 API 或展示层。
- 当需要生命周期拦截、补偿或策略控制时，不要绕过 hook。
- 当已有 domain coordination 存在时，不要绕过 facade。
- 不要在执行代码里重复实现可观测性、治理或建议逻辑。
- 不要在建议或治理流程之外修改它们的状态。
- 不要引入会破坏当前骨架的竞争性流程或平行流水线。

### 分层职责
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

### 交互规则
- 对于每个需求，先识别所属子系统。
- 判断这次修改是新增、行为变更还是结构调整。
- 优先复用最近的现有扩展点，再考虑新增抽象。
- 把改动限制在最小的责任层中。
- 如果一个需求涉及多个子系统，必须保持边界清晰，通过 service 协调，而不是直接耦合。
- 优先使用显式生命周期步骤，避免隐式副作用。

### 修改策略
1. 识别所属子系统。
2. 检查现有 service、facade、hook、registry 或 adapter 是否能表达该变化。
3. 在正确层中实现最小改动。
4. 保持公共 API 薄。
5. 保持编排简洁，领域逻辑局部化。
6. 验证 Web 触发的端到端生命周期仍然完整。
7. 验证治理、可观测性、建议和自进化流程保持一致。

### 默认决策原则
- 有疑问时，优先保留当前架构。
- 优先扩展而不是替换。
- 优先组合而不是耦合。
- 优先在 service 层修改，而不是增加 API 层复杂度。
- 优先显式流程，而不是隐藏行为。
- 避免投机性的抽象，也避免在多层重复逻辑。
- 如果行为属于 hook、facade、service、registry 或编排阶段，就应在那个位置实现，而不是内联实现。
