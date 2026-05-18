# Implementation Plan: LangGraph Orchestration Cleanup（LangGraph 编排清理实现计划）

**Branch**: `20260518-143022-langgraph-orchestration-refactor`（分支：`20260518-143022-langgraph-orchestration-refactor`） | **Date**: 2026-05-18（日期：2026-05-18） | **Spec**: `specs/20260518-143022-langgraph-orchestration-refactor/spec.md`（规格：`specs/20260518-143022-langgraph-orchestration-refactor/spec.md`）

**Input**: Feature specification from `/specs/20260518-143022-langgraph-orchestration-refactor/spec.md`（输入：来自 `/specs/20260518-143022-langgraph-orchestration-refactor/spec.md` 的功能规格）

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.（注意：此模板由 `/speckit-plan` 命令填写。有关执行流程，请参见 `.specify/templates/plan-template.md`。）

## Summary（摘要）

Remove the old LangGraph runtime entry points and switch `SprintOrchestrator` to the compiler-backed `StateGraph.compile()` path as the only supported orchestration route. The refactor preserves SprintCycle’s layered architecture: `sprintcycle/infrastructure/integrations/langgraph/` owns graph compilation, state, checkpoint abstraction, and LangGraph-specific helpers; application-layer orchestration remains thin and consumes compiled graph artifacts; `SprintExecutor` remains the concrete sprint execution engine but is only reachable through the sprint graph.（移除旧的 LangGraph 运行时入口，并将 `SprintOrchestrator` 切换到基于 compiler 的 `StateGraph.compile()` 路径，作为唯一受支持的编排路线。此次重构保留 SprintCycle 的分层架构：`sprintcycle/infrastructure/integrations/langgraph/` 负责图编译、状态、checkpoint 抽象和 LangGraph 专用辅助；application 层编排保持轻量并消费已编译图产物；`SprintExecutor` 仍是具体 sprint 执行引擎，但只能通过 sprint 图触达。）

## Technical Context（技术上下文）

**Language/Version**: Python 3.11+（语言/版本：Python 3.11 及以上）

**Primary Dependencies**: LangGraph, existing SprintCycle application/orchestrator/service layers, current execution runtime components, and a local checkpoint abstraction that can later be replaced with durable storage（主要依赖：LangGraph、现有 SprintCycle application/orchestrator/service 层、当前执行运行时组件，以及可后续替换为持久化存储的本地 checkpoint 抽象）

**Storage**: Default local JSON/file-based checkpoint implementation for development and tests; abstraction must allow future persistent backend replacement without graph rewrites（存储：开发与测试默认使用本地 JSON/文件型 checkpoint 实现；抽象必须允许未来替换为持久化后端而无需重写图逻辑）

**Testing**: pytest, async unit tests, LangGraph compile-path verification, mocked LLM collaborator, mocked checkpoint store, mocked SprintExecutor（测试：pytest、异步单元测试、LangGraph 编译路径验证、mock 的 LLM 协作者、mock 的 checkpoint 存储、mock 的 SprintExecutor）

**Target Platform**: Backend Python runtime and local developer workflows（目标平台：后端 Python 运行时和本地开发工作流）

**Project Type**: Python backend orchestration/runtime refactor inside SprintCycle（项目类型：SprintCycle 内的 Python 后端编排/运行时重构）

**Performance Goals**: Preserve deterministic orchestration, avoid duplicate execution paths, and keep graph compile/invoke overhead bounded relative to the existing runtime path（性能目标：保持编排确定性，避免重复执行路径，并将图编译/调用开销控制在现有运行时路径的合理范围内）

**Constraints**: Preserve current architecture and core skeleton; keep orchestration thin; do not move domain policy into graph nodes; do not introduce a bypass path that directly calls `SprintExecutor` from application code once compiled graphs exist; keep observability/recovery state explicit; use `sprintcycle/application/release/orchestrator.py` as the canonical thin application entrypoint（约束：保留当前架构和核心骨架；保持编排薄；不要把领域策略移入图节点；一旦存在编译后的图，不要在 application 代码中引入直接调用 `SprintExecutor` 的旁路；保持可观测性/恢复状态显式；使用 `sprintcycle/application/release/orchestrator.py` 作为 canonical 薄 application 入口）

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
├── research.md          # Phase 0 output（阶段 0 输出）
├── data-model.md        # Phase 1 output（阶段 1 输出）
├── quickstart.md        # Phase 1 output（阶段 1 输出）
└── contracts/           # Phase 1 output（阶段 1 输出）
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
│           ├── compiler.py            # Graph compilation and singleton accessors（图编译与单例访问器）
│           ├── states.py              # IntentState / SprintState definitions（状态定义）
│           ├── intent_nodes.py        # Intent graph nodes and routing helpers（意图图节点与路由辅助）
│           ├── sprint_nodes.py        # Sprint graph nodes and routing helpers（sprint 图节点与路由辅助）
│           ├── checkpoint.py          # CheckpointStore abstraction + default local implementation（checkpoint 抽象 + 默认本地实现）
│           ├── graph.py               # Graph spec metadata aligned with compiled graphs（与编译图对齐的图元数据）
│           ├── runtime.py             # Thin adapter around compiled graph access（围绕编译图访问的薄适配器）
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

1. Audit the current LangGraph integration files to map where descriptive graph specs and legacy runtime wrappers still exist, and identify all references that must be removed or updated.（审计当前 LangGraph 集成文件，映射描述性图规范和旧运行时包装器仍存在的位置，并识别所有必须删除或更新的引用。）
2. Confirm the compiled graph contract exposed by `compiler.py`, including graph object shape, state inputs/outputs, and checkpoint injection points.（确认 `compiler.py` 暴露的已编译图契约，包括图对象形状、状态输入/输出和 checkpoint 注入点。）
3. Identify the minimal application-layer update required for `SprintOrchestrator` to consume compiled graphs without duplicating routing logic or touching `SprintExecutor` directly.（识别 `SprintOrchestrator` 消费已编译图所需的最小 application 层更新，且不重复路由逻辑或直接触碰 `SprintExecutor`。）
4. Determine the cleanest retirement path for `intent_graph.py`, `sprint_graph.py`, and `graph_runtime.py` so no production code continues importing them.（确定 `intent_graph.py`、`sprint_graph.py` 和 `graph_runtime.py` 最干净的退役路径，使生产代码不再导入它们。）

## Phase 1 - Design（阶段 1 - 设计）

1. Design explicit `IntentState` and `SprintState` models that carry orchestration-relevant data plus explicit error, retry, and timing fields.（设计显式的 `IntentState` 和 `SprintState` 模型，只携带与编排相关的数据以及显式错误、重试和时间字段。）
2. Design the top-level graph node flow for intent understanding, plan generation, sprint splitting, sprint dispatch, evaluation, and finalization using the compiled graph path.（设计顶层图在意图理解、计划生成、sprint 拆分、sprint 派发、评估和完成方面的节点流，并使用已编译的图路径。）
3. Design the per-sprint graph node flow for prepare, execute, observe, repair, and finalize, with `SprintExecutor` only reachable inside the execute node.（设计每个 sprint 在 prepare、execute、observe、repair 和 finalize 方面的节点流，并确保 `SprintExecutor` 只能在 execute 节点内部被触达。）
4. Design the graph compilation helpers so application code receives compiled graph objects instead of descriptive graph specs or legacy runtime wrappers.（设计图编译辅助函数，使 application 代码接收的是已编译图对象，而不是描述性图规范或旧运行时包装器。）
5. Design the checkpoint abstraction plus default local implementation, including the restore key path used by compiled graph invocation.（设计 checkpoint 抽象及默认本地实现，包括已编译图调用使用的恢复 key 路径。）
6. Design the thin application-level orchestration update needed to invoke the compiled top-level graph and consume its results without duplicating orchestration policy.（设计调用已编译顶层图并消费其结果所需的薄 application 层编排更新，同时不重复编排策略。）

## Phase 1 Output Artifacts（阶段 1 输出工件）

- `data-model.md`: Intent/Sprint state, checkpoint abstraction, compiled runtime output, and execution evidence structures.（`data-model.md`：意图/sprint 状态、checkpoint 抽象、已编译运行时输出和执行证据结构。）
- `quickstart.md`: Minimal local flow to compile graphs, invoke the intent graph, and verify checkpoint-backed recovery.（`quickstart.md`：编译图、调用意图图并验证 checkpoint 支持恢复的最小本地流程。）
- `contracts/`: Any runtime or orchestration contracts needed to keep the graph boundary explicit and testable.（`contracts/`：为保持图边界显式且可测试所需的任何运行时或编排契约。）

## Phase 1 Constitution Re-check（阶段 1 宪法复查）

After design, re-validate that graph logic remains inside the orchestration boundary, that no parallel execution pipeline has been introduced, and that the top-level application entry points remain thin while the graphs own flow control.（设计完成后，重新验证图逻辑是否仍位于编排边界内、是否未引入平行执行流水线，以及顶层 application 入口是否仍然保持薄而由图拥有流控制。）

## Complexity Tracking（复杂度追踪）

No constitution violations identified for the proposed scope.（所提范围未发现宪法违规项。）
