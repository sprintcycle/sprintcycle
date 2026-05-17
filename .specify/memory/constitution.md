<!--
Sync Impact Report
Version change: 1.0.0 → 1.0.1（1.0.0 → 1.0.1）
Modified principles:
- [PRINCIPLE_1_NAME] → I. Contract-Driven Lifecycle（契约驱动的生命周期）
- [PRINCIPLE_2_NAME] → II. Layered Architecture and Orchestration Boundaries（分层架构与编排边界）
- [PRINCIPLE_3_NAME] → III. Governance-First Quality Gates（以治理为先的质量门禁）
- [PRINCIPLE_4_NAME] → IV. Observable, Recoverable, and Replayable Execution（可观测、可恢复、可回放的执行）
- [PRINCIPLE_5_NAME] → V. Versioned Evolution and Safe Promotion（版本化演进与安全晋升）
Added sections:
- Technology and runtime constraints（技术与运行时约束）
- Development workflow and review gates（开发流程与评审门禁）
Removed sections:
- Template placeholders and example comments（模板占位符与示例注释）
Templates requiring updates:
- ✅ `.specify/templates/plan-template.md`（已更新）
- ✅ `.specify/templates/spec-template.md`（已更新）
- ✅ `.specify/templates/tasks-template.md`（已更新）
- ⚠ `.specify/templates/commands/*.md`（verify generic guidance across command templates）（需确认命令模板是否仍有专用措辞）
- ✅ `README.md`（已更新）
- ✅ `.cursor/rules/langgraph-orchestration.mdc`（已更新）
- ✅ `.cursor/rules/sprintcycle-architecture-orchestration.mdc`（已更新）
Follow-up TODOs:
- TODO(RATIFICATION_DATE): historical ratification date was not available; using initial adoption date from this update（历史采纳日期不可用，暂使用本次更新日期）
- TODO(BILINGUAL_REVIEW): review whether all remaining constitution sections should be expanded into fuller bilingual phrasing（检查宪法其余部分是否也需要扩展为更完整的中英双语表述）
-->
# SprintCycle Constitution（SprintCycle 宪法）

## Core Principles（核心原则）

### I. Contract-Driven Lifecycle（契约驱动的生命周期）
Every meaningful user request MUST enter, travel through, and exit the system as a
`LifecycleContract`.（每一个有意义的用户请求都必须以 `LifecycleContract` 的形式进入系统、贯穿系统并离开系统。） The contract is the single source of truth for intent,
plan, execution, repair, observability, governance, and versioning evidence.（该契约是意图、计划、执行、修复、可观测性、治理与版本化证据的唯一事实来源。）
All stage transitions, recoveries, and promotions MUST be representable in the
contract and reproducible from it.（所有阶段迁移、恢复和晋升都必须能够在契约中表达，并且能够从契约中复现。）

Rationale: SprintCycle is a lifecycle platform, not a collection of disconnected
utilities.（理由：SprintCycle 是一个生命周期平台，而不是一组彼此割裂的工具。） Shared contract state keeps the system auditable, replayable, and safe
for cross-surface use from Web Dashboard, REST API, and SDK.（共享契约状态使系统保持可审计、可回放，并且能够安全地在 Web Dashboard、REST API 和 SDK 之间协同使用。）

### II. Layered Architecture and Orchestration Boundaries（分层架构与编排边界）
The codebase MUST preserve a layered architecture: domain rules live in domain,
application, execution, governance, and infrastructure boundaries.（代码库必须保持分层架构：领域规则分布在 domain、application、execution、governance 和 infrastructure 的边界中。） Orchestration
lives in application and runtime adapters, and presentation or interface layers
must not own business policy.（编排位于 application 和运行时适配层，表现层或接口层不得持有业务策略。） LangGraph and similar orchestrators MAY coordinate flow, but
they MUST NOT embed business logic that belongs to services, facades, hooks, or
policies.（LangGraph 及类似编排器可以协调流程，但不得嵌入应归属于服务、门面、钩子或策略的业务逻辑。）

Rationale: SprintCycle’s architecture depends on clean separation between
workflow control and domain responsibility.（理由：SprintCycle 的架构依赖于工作流控制与领域责任之间的清晰分离。） This prevents graph sprawl, keeps
retry and repair paths consistent, and allows services to evolve without
rewriting orchestration graphs.（这可以防止图编排失控，保持重试与修复路径一致，并允许服务演进而无需重写编排图。）

### III. Governance-First Quality Gates（以治理为先的质量门禁）
Changes that affect planning, execution, recovery, observability, governance,
or versioning MUST pass explicit validation gates before promotion or release.（任何影响计划、执行、恢复、可观测性、治理或版本化的变更，在晋升或发布前都必须通过明确的验证门禁。）
Governance checks include contract validity, architecture boundary checks,
static analysis, schema validation, and any project-specific integrity checks
required by the active governance level.（治理检查包括契约有效性、架构边界检查、静态分析、模式校验，以及当前治理级别所要求的任何项目特定完整性检查。）

Rationale: The platform’s value depends on trustworthy automation.（理由：平台的价值依赖于可信的自动化。） A feature
that cannot be validated or audited is not shippable, because it weakens the
contract-driven lifecycle and undermines later promotion decisions.（无法被验证或审计的功能不可交付，因为它会削弱契约驱动的生命周期，并破坏后续晋升决策的可靠性。）

### IV. Observable, Recoverable, and Replayable Execution（可观测、可恢复、可回放的执行）
Every execution path MUST emit sufficient evidence to support tracing,
diagnosis, repair, replay, and audit.（每条执行路径都必须产出足够的证据，以支持追踪、诊断、修复、回放和审计。） Failed or partial work MUST be recoverable
through explicit repair flows, and the system MUST preserve enough state to
explain what happened, why it happened, and what was changed.（失败或部分完成的工作必须能够通过显式修复流程恢复，并且系统必须保留足够状态，以解释发生了什么、为什么发生以及发生了哪些变更。）

Rationale: SprintCycle is designed for closed-loop development, so visibility
and recovery are not optional diagnostics; they are first-class product
requirements.（理由：SprintCycle 是为闭环开发而设计的，因此可见性与恢复不是可选诊断能力，而是一等公民级的产品要求。）（理由：这也是为什么任何编排层都必须保留足够证据，以支持回放、诊断和修复。）

### V. Versioned Evolution and Safe Promotion（版本化演进与安全晋升）
A completed lifecycle MUST only become a promoted version when its final
snapshot, evidence, and governance checks are complete.（只有当最终快照、证据和治理检查全部完成时，完成的生命周期才可以成为已晋升版本。） Promotions MUST update
the version registry, preserve lineage to the originating contract, and keep
active versions distinguishable from historical versions.（晋升必须更新版本注册表，保留与原始契约之间的血缘关系，并使活动版本与历史版本能够区分。）

Rationale: The platform must support safe evolution without losing provenance.（理由：平台必须支持安全演进，同时不能丢失来源追踪。）
Versioning is not a separate concern; it is the output of a verified lifecycle.（版本化不是独立关注点；它是经过验证的生命周期输出。）

## Technology and Runtime Constraints（技术与运行时约束）

SprintCycle is implemented as a Python-first system with a modern web and API
stack.（SprintCycle 是一个以 Python 为核心实现、配备现代 Web 与 API 技术栈的系统。） The project MUST respect the following runtime expectations:（项目必须遵守以下运行时要求：）

- Python runtime MUST be compatible with Python 3.11 or newer.（Python 运行时必须兼容 Python 3.11 或更高版本。）
- The public application surface MUST remain consistent across Web Dashboard,
  REST API, and Python SDK entry points.（公共应用入口在 Web Dashboard、REST API 和 Python SDK 之间必须保持一致。）
- Vue 3 + Element Plus remain the approved Dashboard stack.（Vue 3 + Element Plus 仍然是批准的 Dashboard 技术栈。）
- FastAPI remains the approved backend HTTP framework.（FastAPI 仍然是批准的后端 HTTP 框架。）
- LangGraph MAY be used for orchestration, but only within the boundaries
  defined by the layered architecture principle.（LangGraph 可以用于编排，但只能在分层架构原则定义的边界内使用。）
- SQLite-backed versioning, artifact persistence, and local developer workflows
  MUST remain supported unless a migration plan explicitly replaces them.（基于 SQLite 的版本管理、产物持久化和本地开发流程必须继续支持，除非迁移方案明确替换它们。）

These constraints exist to keep the platform stable for both product usage and
local development while preserving the existing deployment and runtime model.（这些约束的目的是在保留现有部署与运行模型的同时，确保平台在产品使用与本地开发中保持稳定。）

## Development Workflow and Review Gates（开发流程与评审门禁）

All substantive changes MUST follow this workflow:（所有实质性变更都必须遵循以下流程：）

1. Confirm the change fits the contract-driven lifecycle and the layered
   architecture.（确认变更符合契约驱动的生命周期和分层架构。）
2. Update or create the relevant spec, plan, and task artifacts before coding.（在编码前更新或创建相关的 spec、plan 和 task 工件。）
3. Implement the smallest coherent change that satisfies the spec.（以满足 spec 为目标，实现最小且完整的一组变更。）
4. Add or update tests for contract changes, orchestration changes, or
   governance-sensitive behavior.（为契约变更、编排变更或对治理敏感的行为补充或更新测试。）
5. Run linting, validation, and any required integration or governance checks.（运行 lint、验证以及所需的集成或治理检查。）
6. Review the change for observability, recovery, and promotion impact before
   merging or releasing.（在合并或发布之前，审查该变更对可观测性、恢复能力和晋升流程的影响。）

Additional requirements:（附加要求：）

- Orchestration changes MUST be checked against the LangGraph boundary rule.（编排变更必须对照 LangGraph 边界规则进行检查。）
- Any change affecting promotion, final snapshot, or version registry behavior
  MUST include evidence that safe promotion still holds.（任何影响晋升、最终快照或版本注册表行为的变更，都必须附带证明其仍满足安全晋升要求的证据。）
- Documentation that describes runtime behavior, architecture, or governance
  MUST stay aligned with the implementation.（描述运行时行为、架构或治理的文档必须与实现保持一致。）
- If a change introduces new ambiguity in the lifecycle, the ambiguity MUST be
  resolved in the spec before implementation continues.（如果变更引入了生命周期中的新歧义，必须先在 spec 中消除该歧义，然后才能继续实现。）

## Governance（治理）

This constitution overrides lower-level conventions when they conflict.（当本宪法与更低层级的约定冲突时，本宪法优先。）
Amendments require a written rationale, an impact review across related specs
and templates, and an updated version number using semantic versioning:（修订需要书面理由、对相关 spec 和模板的影响评审，以及按照语义化版本号更新版本号：）

- MAJOR: breaking governance or principle redefinitions（MAJOR：治理规则或原则发生破坏性重定义）
- MINOR: new principle or materially expanded guidance（MINOR：新增原则或显著扩展指导）
- PATCH: wording, clarity, or non-semantic refinements（PATCH：措辞、清晰度或非语义性改进）

Every pull request or review that touches architecture, lifecycle flow,
governance, observability, or versioning MUST verify constitution compliance.（每一个涉及架构、生命周期流、治理、可观测性或版本化的 pull request 或评审，都必须验证是否符合本宪法。）
If a proposal cannot satisfy these principles, the work MUST be decomposed,
renamed, or rejected until it can.（如果某项提案无法满足这些原则，则工作必须被拆分、重命名或拒绝，直到满足为止。）

**Version**: 1.0.0 | **Ratified**: 2026-05-17 | **Last Amended**: 2026-05-17
