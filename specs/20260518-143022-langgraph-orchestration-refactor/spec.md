# Feature Specification: LangGraph Orchestration Refactor（LangGraph 编排重构）

**Feature Branch**: `20260518-143022-langgraph-orchestration-refactor`（功能分支：`20260518-143022-langgraph-orchestration-refactor`）

**Created**: 2026-05-18（创建时间：2026-05-18）

**Status**: Draft（状态：草稿）

**Input**: User request: "参考 SprintCycle LangGraph 改造方案，以 SprintCycle 代码为基准，校准改造方案实现目标架构（LangGraph 真正驱动）"（输入：用户需求：“参考 SprintCycle LangGraph 改造方案，以 SprintCycle 代码为基准，校准改造方案实现目标架构（LangGraph 真正驱动）”）

## Clarifications（澄清）

### Session 2026-05-18
- Q: 这次改造应落在哪一层？ → A: 完整结构梳理，覆盖 LangGraph 层、application 协调层，以及相关 facade / hook / registry 边界。
- Q: LangGraph 真正驱动要求到什么程度？ → A: 编译 + LLM + checkpoint + 现有执行器闭环重构都要纳入目标架构。
- Q: 断点恢复采用什么方式？ → A: 方案里同时定义抽象接口 + 一个默认本地实现，后续可替换成正式存储。
- Q: 功能名是什么？ → A: `langgraph-orchestration-refactor`。

## User Scenarios & Testing *(mandatory)*（用户场景与测试 *（必填）*）

### User Story 1 - Compile real LangGraph runtimes（编译真正的 LangGraph 运行时） (Priority: P1)（用户故事 1 - 编译真正的 LangGraph 运行时（优先级：P1））

As a maintainer, I want the SprintCycle LangGraph layer to compile real executable graphs so that orchestration is driven by LangGraph instead of method chaining.（作为维护者，我希望 SprintCycle 的 LangGraph 层能够编译为真正可执行的图，这样编排就由 LangGraph 驱动，而不是由方法串联驱动。）

**Why this priority**: Without compiled graphs, the LangGraph layer is only descriptive and cannot own routing, recovery, or execution flow.（为什么是这个优先级：如果没有编译成图，LangGraph 层就只是描述性的，无法真正拥有路由、恢复或执行流。）

**Independent Test**: Instantiate the top-level and per-sprint graph runtimes, compile them, and verify the returned artifacts are executable graphs with the expected nodes and conditional edges.（独立测试：实例化顶层和每个 sprint 的图运行时，完成编译，并验证返回产物是带有预期节点和条件边的可执行图。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** a valid orchestration state, **When** the intent graph is built, **Then** the graph compiles into an executable LangGraph object with the expected flow.（**Given** 一个有效的编排状态，**When** 构建意图图，**Then** 图会编译为带有预期流程的可执行 LangGraph 对象。）
2. **Given** a sprint execution state, **When** the sprint graph is built, **Then** the graph compiles into an executable LangGraph object with prepare/execute/observe/repair/finalize stages.（**Given** 一个 sprint 执行状态，**When** 构建 sprint 图，**Then** 图会编译为带有 prepare/execute/observe/repair/finalize 阶段的可执行 LangGraph 对象。）

---

### User Story 2 - Route through LLM-backed intent and plan stages（通过 LLM 驱动意图与计划阶段路由） (Priority: P2)（用户故事 2 - 通过 LLM 驱动意图与计划阶段路由（优先级：P2））

As a maintainer, I want the intent graph to use LLM-backed understanding and plan generation so that release planning is not just static state mutation.（作为维护者，我希望意图图使用 LLM 驱动的理解与计划生成，这样发布计划就不再只是静态状态修改。）

**Why this priority**: The top-level graph must do more than route; it must interpret intent and produce a structured release plan before dispatching sprint work.（为什么是这个优先级：顶层图不能只负责路由，还必须解释意图并在派发 sprint 工作之前产出结构化发布计划。）

**Independent Test**: Stub the LLM collaborator, invoke the intent graph nodes, and verify intent understanding, release plan generation, sprint splitting, and dispatch decisions are based on graph state.（独立测试：stub LLM 协作者，调用意图图节点，并验证意图理解、发布计划生成、sprint 拆分和派发决策均基于图状态。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** user intent and context, **When** the intent graph runs, **Then** the graph produces an analyzed intent and a structured release plan before sprint dispatch.（**Given** 用户意图和上下文，**When** 意图图运行，**Then** 图会在 sprint 派发前生成分析后的意图和结构化发布计划。）
2. **Given** sprint execution results, **When** the intent graph evaluates them, **Then** it routes to retry or finalize using conditional edges rather than external if/else chaining.（**Given** sprint 执行结果，**When** 意图图评估它们，**Then** 它会通过条件边路由到重试或完成，而不是通过外部 if/else 串联。）

---

### User Story 3 - Preserve execution continuity with checkpoint-backed recovery（通过 checkpoint 恢复保持执行连续性） (Priority: P3)（用户故事 3 - 通过 checkpoint 恢复保持执行连续性（优先级：P3））

As an operator, I want graph checkpoints and recoverable state so that interrupted orchestration can resume without losing the execution chain or duplicating work.（作为运维人员，我希望图具备 checkpoint 和可恢复状态，这样中断的编排可以恢复，而不会丢失执行链或重复工作。）

**Why this priority**: Recovery is a core part of the goal architecture and is required to make LangGraph the real runtime driver rather than a one-shot wrapper.（为什么是这个优先级：恢复是目标架构的核心部分，必须让 LangGraph 成为真正的运行时驱动，而不是一次性包装器。）

**Independent Test**: Run the graphs with a mock or local checkpoint store, interrupt execution, reload the saved state, and verify the graph resumes from the expected stage without duplicate workers or bypassed routing.（独立测试：使用 mock 或本地 checkpoint 存储运行图，中断执行，重新加载已保存状态，并验证图会从预期阶段恢复，而不会出现重复 worker 或绕过路由。）

**Application Entry Point**: `sprintcycle/application/release/orchestrator.py` is the canonical thin application-layer entrypoint for invoking compiled graphs and aggregating results.（**应用入口**：`sprintcycle/application/release/orchestrator.py` 是调用已编译图并汇总结果的 canonical 薄 application 层入口。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** a compiled graph with checkpoint support, **When** execution is interrupted, **Then** the runtime can restore the last known state and continue from that state.（**Given** 一个带 checkpoint 支持的已编译图，**When** 执行被中断，**Then** 运行时可以恢复到最后已知状态并从该状态继续。）
2. **Given** a recovery attempt after an interruption, **When** the graph resumes, **Then** it reuses the existing state and avoids starting a parallel duplicate execution path.（**Given** 中断后的恢复尝试，**When** 图恢复运行，**Then** 它会复用现有状态并避免启动并行的重复执行路径。）

### Edge Cases（边界情况）

- What happens when the graph is invoked without a `thread_id` or recovery key?（当图在没有 `thread_id` 或恢复 key 的情况下被调用时会怎样？）
- What happens if the intent LLM returns malformed JSON or partial structured output?（当意图 LLM 返回格式错误的 JSON 或部分结构化输出时会怎样？）
- What happens if `SprintExecutor` is unavailable during sprint execution?（当 sprint 执行期间 `SprintExecutor` 不可用时会怎样？）
- What happens when checkpoint restore data is older than the current graph schema?（当 checkpoint 恢复数据比当前图 schema 更旧时会怎样？）

## Requirements *(mandatory)*（需求 *（必填）*）

### Functional Requirements（功能需求）

- **FR-001**: System MUST provide a compiled LangGraph-based intent runtime that owns the top-level orchestration flow from intent intake through finalize.（系统必须提供一个已编译的基于 LangGraph 的意图运行时，负责从意图接收到完成的顶层编排流程。）
- **FR-002**: System MUST provide a compiled LangGraph-based sprint runtime that owns the per-sprint flow from prepare through finalize.（系统必须提供一个已编译的基于 LangGraph 的 sprint 运行时，负责从准备到完成的每个 sprint 流程。）
- **FR-003**: System MUST replace method-chained orchestration with LangGraph `StateGraph.compile()` outputs for both top-level and per-sprint flows.（系统必须用 LangGraph `StateGraph.compile()` 的输出替换顶层和每个 sprint 流程中的方法串联式编排。）
- **FR-004**: System MUST route intent understanding and release plan generation through graph nodes that can call LLM collaborators.（系统必须通过能够调用 LLM 协作者的图节点来完成意图理解和发布计划生成。）
- **FR-005**: System MUST express sprint routing, retry, and finalize decisions via LangGraph conditional edges rather than external imperative branching.（系统必须通过 LangGraph 条件边表达 sprint 路由、重试和 finalize 决策，而不是通过外部命令式分支。）
- **FR-006**: System MUST preserve `SprintExecutor` as the concrete execution capability while ensuring it is only invoked from within the sprint graph execution path.（系统必须保留 `SprintExecutor` 作为具体执行能力，同时确保它只能在 sprint 图执行路径内被调用。）
- **FR-007**: System MUST provide an abstraction for checkpointing/recovery and a default local implementation suitable for development and testing.（系统必须提供 checkpoint/恢复抽象以及适合开发和测试的默认本地实现。）
- **FR-008**: System MUST surface explicit state, result, and error information from graph execution so application-layer orchestration can aggregate outcomes without duplicating routing logic.（系统必须从图执行中暴露显式状态、结果和错误信息，以便 application 层编排能够汇总结果而无需复制路由逻辑。）
- **FR-009**: System MUST keep LangGraph-specific logic isolated to `infrastructure/integrations/langgraph/` while preserving existing application/service/facade/hook/orchestrator boundaries.（系统必须将 LangGraph 相关逻辑隔离在 `infrastructure/integrations/langgraph/` 中，同时保持现有 application/service/facade/hook/orchestrator 边界。）
- **FR-010**: System MUST avoid introducing a parallel execution path that bypasses the graph runtime once the graph is compiled.（系统必须避免在图编译后引入绕过图运行时的平行执行路径。）

### Key Entities *(include if feature involves data)*（关键实体 *（如果功能涉及数据则填写）*）

- **IntentState**: Top-level state carrying intent, context, release plan, sprint results, evaluation, and timeline data.（`IntentState`：顶层状态，携带意图、上下文、发布计划、sprint 结果、评估和时间线数据。）
- **SprintState**: Per-sprint state carrying sprint input, sprint context, execution result, observation, repair decision, and timeline data.（`SprintState`：每个 sprint 的状态，携带 sprint 输入、sprint 上下文、执行结果、观测、修复决策和时间线数据。）
- **CompiledGraphRuntime**: An executable graph runtime returned by graph compiler helpers and used by application-layer orchestration.（`CompiledGraphRuntime`：由图编译器辅助函数返回并供 application 层编排使用的可执行图运行时。）
- **CheckpointStore**: An abstract storage contract for persisting and restoring graph checkpoints.（`CheckpointStore`：用于持久化和恢复图 checkpoint 的抽象存储契约。）
- **LLM Collaborator**: A graph-invoked collaborator responsible for intent analysis and release-plan generation.（`LLM Collaborator`：由图调用的协作者，负责意图分析和发布计划生成。）

## Success Criteria *(mandatory)*（成功标准 *（必填）*）

### Measurable Outcomes（可衡量结果）

- **SC-001**: Compiling the top-level and per-sprint graphs returns executable graph artifacts rather than descriptive specs only.（编译顶层和每个 sprint 的图会返回可执行的图产物，而不只是描述性规范。）
- **SC-002**: Intent analysis, plan generation, sprint splitting, dispatch, and finalize decisions are driven by graph state and conditional routing.（意图分析、计划生成、sprint 拆分、派发和完成决策由图状态和条件路由驱动。）
- **SC-003**: Sprint execution remains rooted in `SprintExecutor` but only through graph-mediated invocation.（sprint 执行仍然基于 `SprintExecutor`，但只能通过图介导的调用发生。）
- **SC-004**: Interrupted graph execution can be restored from a checkpoint and resumed without duplicating active execution paths.（中断的图执行可以从 checkpoint 恢复并继续，而不会重复活跃执行路径。）
- **SC-005**: Unit tests can validate graph compilation, conditional routing, LLM-backed stages, and checkpoint restoration using mocked collaborators.（单元测试可以使用 mock 协作者验证图编译、条件路由、LLM 驱动阶段和 checkpoint 恢复。）

## Assumptions（假设）

- The current SprintCycle architecture and layered boundaries remain the baseline and should not be replaced.（当前 SprintCycle 架构和分层边界仍然是基线，不应被替换。）
- Existing application/orchestrator services already contain the business operations that graph nodes should reuse or invoke.（现有 application/orchestrator 服务已经包含图节点应复用或调用的业务操作。）
- A lightweight local checkpoint implementation is sufficient for the first version, as long as an abstraction allows future storage replacement.（只要有抽象允许后续替换存储，轻量本地 checkpoint 实现就足够支持第一版。）
- LLM calls will be introduced through explicit collaborators and not hidden inside application-layer orchestration.（LLM 调用将通过显式协作者引入，而不会隐藏在 application 层编排中。）
