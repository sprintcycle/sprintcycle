# Implementation Plan: LangGraph Orchestration Refactor（LangGraph 编排重构实现计划）

**Branch**: `20260518-143022-langgraph-orchestration-refactor`（分支：`20260518-143022-langgraph-orchestration-refactor`） | **Date**: 2026-05-18（日期：2026-05-18） | **Spec**: `specs/20260518-143022-langgraph-orchestration-refactor/spec.md`（规格：`specs/20260518-143022-langgraph-orchestration-refactor/spec.md`）

**Input**: Feature specification from `/specs/20260518-143022-langgraph-orchestration-refactor/spec.md`（输入：来自 `/specs/20260518-143022-langgraph-orchestration-refactor/spec.md` 的功能规格）

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.（注意：此模板由 `/speckit-plan` 命令填写。有关执行流程，请参见 `.specify/templates/plan-template.md`。）

## Summary（摘要）

Refactor SprintCycle’s LangGraph integration so the top-level intent flow and per-sprint flow are backed by compiled LangGraph `StateGraph` runtimes instead of descriptive graph specs plus method chaining. The refactor keeps SprintCycle’s layered architecture intact: `infrastructure/integrations/langgraph/` owns graph compilation, routing, checkpoint abstractions, and LangGraph-specific state; application-level orchestration remains thin and delegates into the compiled graphs; `SprintExecutor` remains the concrete execution engine but is invoked only from inside the sprint graph.（重构 SprintCycle 的 LangGraph 集成，使顶层意图流程和每个 sprint 的流程由已编译的 LangGraph `StateGraph` 运行时支撑，而不是由描述性图规范加方法串联支撑。此次重构保持 SprintCycle 的分层架构不变：`infrastructure/integrations/langgraph/` 负责图编译、路由、checkpoint 抽象和 LangGraph 专用状态；application 层编排保持轻量并委派给已编译图；`SprintExecutor` 仍是具体执行引擎，但只能在 sprint 图内部被调用。）

## Technical Context（技术上下文）

**Language/Version**: Python 3.11+（语言/版本：Python 3.11 及以上）

**Primary Dependencies**: LangGraph, existing SprintCycle application/orchestrator/service layers, current self-evolution/execution runtime components, and a local checkpoint abstraction that can later be swapped for a persistent store（主要依赖：LangGraph、现有 SprintCycle application/orchestrator/service 层、当前自进化/执行运行时组件，以及可后续替换为持久化存储的本地 checkpoint 抽象）

**Storage**: Default local JSON/file-based checkpoint implementation for development and tests; the abstraction must allow a future persistent backend without graph changes（存储：开发与测试默认使用本地 JSON/文件型 checkpoint 实现；抽象必须允许后续切换到持久化后端而无需改图逻辑）

**Testing**: pytest, async unit tests, LangGraph compile-path verification, mocked LLM collaborator, mocked checkpoint store, mocked SprintExecutor（测试：pytest、异步单元测试、LangGraph 编译路径验证、mock 的 LLM 协作者、mock 的 checkpoint 存储、mock 的 SprintExecutor）

**Target Platform**: Backend Python runtime and local developer workflows（目标平台：后端 Python 运行时和本地开发工作流）

**Project Type**: Python backend orchestration/runtime refactor inside SprintCycle（项目类型：SprintCycle 内的 Python 后端编排/运行时重构）

**Performance Goals**: Preserve deterministic orchestration, avoid duplicate execution paths, and keep graph compile/invoke overhead bounded relative to the existing runtime path（性能目标：保持编排确定性，避免重复执行路径，并将图编译/调用开销控制在现有运行时路径的合理范围内）

**Constraints**: Preserve current architecture and core skeleton; keep orchestration thin; do not move domain policy into graph nodes; do not introduce a bypass path that directly calls SprintExecutor from application code once compiled graphs exist; keep observability/recovery state explicit; use `sprintcycle/application/release/orchestrator.py` as the canonical thin application entrypoint（约束：保留当前架构和核心骨架；保持编排薄；不要把领域策略移入图节点；一旦存在编译后的图，不要在 application 代码中引入直接调用 SprintExecutor 的旁路；保持可观测性/恢复状态显式；使用 `sprintcycle/application/release/orchestrator.py` 作为 canonical 薄 application 入口）

**Scale/Scope**: A focused refactor across the LangGraph integration package plus small coordination updates in the application orchestration boundary and tests（规模/范围：覆盖 LangGraph 集成包的聚焦重构，以及 application 编排边界和测试中的少量协调更新）

## Constitution Check（宪法检查）

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*（*门禁：必须在阶段 0 调研之前通过，并在阶段 1 设计后复查。*）

- The refactor preserves SprintCycle’s layered architecture and keeps LangGraph inside the orchestration boundary only.（此次重构保留 SprintCycle 的分层架构，并确保 LangGraph 仅位于编排边界内。）
- Application/public entry points remain thin and do not own workflow policy or graph routing logic.（application/公共入口保持薄，不拥有工作流策略或图路由逻辑。）
- Execution, observability, recovery, and retry flows remain explicit and recoverable through graph state and checkpoint abstractions.（执行、可观测性、恢复和重试流程通过图状态和 checkpoint 抽象保持显式且可恢复。）
- The refactor reuses the existing execution backbone, including SprintExecutor, instead of introducing a parallel execution pipeline.（此次重构复用现有执行主干，包括 SprintExecutor，而不是引入平行执行流水线。）

## Project Structure（项目结构）

### Documentation (this feature)（文档（本功能））

```text
specs/20260518-143022-langgraph-orchestration-refactor/
├── spec.md              # Feature specification（功能规格）
├── plan.md              # This file (/speckit-plan command output)（本文件（/speckit-plan 命令输出））
├── research.md          # Phase 0 output (/speckit-plan command)（阶段 0 输出（/speckit-plan 命令））
├── data-model.md        # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
├── quickstart.md        # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
├── contracts/           # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)（阶段 2 输出（/speckit-tasks 命令 - 不由 /speckit-plan 创建））
```

### Source Code (repository root)（源代码（仓库根目录））

```text
sprintcycle/
├── application/
│   └── release/
│       └── orchestrator.py            # Thin orchestration boundary that invokes compiled graphs（薄编排边界，调用已编译图）
├── infrastructure/
│   └── integrations/
│       └── langgraph/
│           ├── states.py              # IntentState / SprintState definitions（状态定义）
│           ├── intent_nodes.py        # Intent graph nodes and routing helpers（意图图节点与路由辅助）
│           ├── sprint_nodes.py        # Sprint graph nodes and routing helpers（sprint 图节点与路由辅助）
│           ├── compiler.py            # Graph compilation and singleton accessors（图编译与单例访问器）
│           ├── checkpoint.py          # CheckpointStore abstraction + default local implementation（checkpoint 抽象 + 默认本地实现）
│           ├── graph.py               # Existing graph spec types, updated to align with compiled graphs（现有图规范类型，更新以对齐编译图）
│           ├── graph_runtime.py       # Runtime wrapper updated to return compiled graph artifacts（运行时包装，更新为返回已编译图产物）
│           ├── runtime.py             # Thin adapter around graph/runtime spec and compiled graph access（围绕图/运行时规范与编译图访问的薄适配器）
│           ├── intent_graph.py        # Top-level intent runtime compatibility surface（顶层意图运行时兼容层）
│           ├── sprint_graph.py        # Per-sprint runtime compatibility surface（每个 sprint 的运行时兼容层）
│           ├── plan_runtime.py        # Planning/runtime coordination compatibility updates（计划/运行时协调兼容更新）
│           └── adapter.py             # Integration adapter surface aligned to compiled graph usage（与编译图使用对齐的集成适配器）
└── tests/
    ├── application/
    │   └── release/
    │       └── test_orchestrator.py    # Thin boundary / no bypass-path tests（薄边界 / 无旁路路径测试）
    └── infrastructure/
        └── integrations/
            └── langgraph/
                ├── test_compiler.py   # Graph compilation and edge/routing tests（图编译与边/路由测试）
                ├── test_states.py     # State shape tests（状态形状测试）
                ├── test_checkpoint.py # Checkpoint abstraction tests（checkpoint 抽象测试）
                └── test_nodes.py      # Node behavior tests with mocked collaborators（带 mock 协作者的节点行为测试）
```

**Structure Decision**: Keep the LangGraph refactor inside `sprintcycle/infrastructure/integrations/langgraph/` as the owning subsystem, update the thin application orchestration boundary only where needed to consume compiled graphs, and add focused tests that prove there is no direct application-layer bypass around the graphs. This preserves the current architecture while changing the execution mechanism from descriptive/method-chained runtime objects to real compiled graphs.（**结构决策**：将 LangGraph 重构保留在 `sprintcycle/infrastructure/integrations/langgraph/` 作为所属子系统，只在需要消费已编译图时更新薄的 application 编排边界，并增加聚焦测试来证明 application 层不存在绕过图的直接路径。这样可以在保持当前架构的同时，将执行机制从描述性/方法串联式运行时对象切换为真正的已编译图。）

## Phase 0 - Research（阶段 0 - 调研）

1. Audit the current LangGraph integration files (`graph.py`, `graph_runtime.py`, `runtime.py`, `intent_graph.py`, `sprint_graph.py`, `plan_runtime.py`, `adapter.py`) to map where descriptive graph specs and method chaining still exist.（审计当前 LangGraph 集成文件，映射描述性图规范和方法串联仍存在的位置。）
2. Identify the smallest viable compatibility surface needed in the application boundary so compiled graphs can be invoked without exposing workflow policy there.（识别 application 边界所需的最小兼容面，以便在不向外暴露工作流策略的情况下调用已编译图。）
3. Confirm how `SprintExecutor` is currently reached and define the graph-only invocation path that preserves the execution backbone while removing bypass routes.（确认 `SprintExecutor` 当前如何被触达，并定义仅通过图调用的路径，在去除旁路的同时保留执行主干。）
4. Define a checkpoint contract that supports local development recovery now and can later swap to a durable backend without graph rewrites; prefer LangGraph-native checkpointer injection at compile/runtime boundaries with a thin adapter interface above it.（定义一个 checkpoint 契约，既支持当前本地开发恢复，又能在未来无需重写图逻辑的情况下切换到持久化后端；优先在 compile/runtime 边界使用 LangGraph 原生 checkpointer 注入，并在其上方保持一个薄适配接口。）

## Phase 1 - Design（阶段 1 - 设计）

1. Design explicit `IntentState` and `SprintState` models that carry only orchestration-relevant data plus explicit error/timeline/evaluation fields.（设计显式的 `IntentState` 和 `SprintState` 模型，只携带与编排相关的数据以及显式错误/时间线/评估字段。）
2. Design the top-level graph node flow for intent understanding, plan generation, sprint splitting, sprint dispatch, evaluation, and finalization.（设计顶层图在意图理解、计划生成、sprint 拆分、sprint 派发、评估和完成方面的节点流。）
3. Design the per-sprint graph node flow for prepare, execute, observe, repair, and finalize, with `SprintExecutor` only reachable inside the execute node.（设计每个 sprint 在 prepare、execute、observe、repair 和 finalize 方面的节点流，并确保 `SprintExecutor` 只能在 execute 节点内部被触达。）
4. Design the graph compilation helpers and singleton accessors so application code receives compiled graph objects instead of descriptive graph specs.（设计图编译辅助函数与单例访问器，使 application 代码接收的是已编译图对象而非描述性图规范。）
5. Design a checkpoint abstraction plus default local implementation, including the `thread_id`/configurable key path used for restore.（设计 checkpoint 抽象及默认本地实现，包括用于恢复的 `thread_id`/configurable key 路径。）
6. Design the thin application-level orchestration update needed to invoke the compiled top-level graph without duplicating routing logic.（设计调用已编译顶层图所需的薄 application 层编排更新，同时不重复路由逻辑。）

## Phase 1 Output Artifacts（阶段 1 输出工件）

- `data-model.md`: Intent/Sprint state, checkpoint abstraction, runtime adapter output, and execution evidence structures.（`data-model.md`：意图/sprint 状态、checkpoint 抽象、运行时适配器输出和执行证据结构。）
- `quickstart.md`: Minimal local flow to compile graphs, invoke the intent graph, and verify checkpoint-backed recovery.（`quickstart.md`：编译图、调用意图图并验证 checkpoint 支持恢复的最小本地流程。）
- `contracts/`: Any runtime or orchestration contracts needed to keep the graph boundary explicit and testable.（`contracts/`：为保持图边界显式且可测试所需的任何运行时或编排契约。）

## Phase 1 Constitution Re-check（阶段 1 宪法复查）

After design, re-validate that graph logic remains inside the orchestration boundary, that no parallel execution pipeline has been introduced, and that the top-level application entry points remain thin while the graphs own flow control.（设计完成后，重新验证图逻辑是否仍位于编排边界内、是否未引入平行执行流水线，以及顶层 application 入口是否仍然保持薄而由图拥有流控制。）

## Complexity Tracking（复杂度追踪）

No constitution violations identified for the proposed scope.（所提范围未发现宪法违规项。）
