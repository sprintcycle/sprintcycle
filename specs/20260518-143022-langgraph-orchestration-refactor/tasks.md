# Tasks: LangGraph Orchestration Refactor（LangGraph 编排重构）

**Input**: Design documents from `/specs/20260518-143022-langgraph-orchestration-refactor/`（输入：来自 `/specs/20260518-143022-langgraph-orchestration-refactor/` 的设计文档）

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/（前置条件：plan.md（必需）、spec.md（用户故事必需）、research.md、data-model.md、contracts/）

**Tests**: Included because the feature specification explicitly requires unit tests for graph compilation, conditional routing, LLM-backed stages, and checkpoint restoration.（**测试**：已包含，因为功能规格明确要求对图编译、条件路由、LLM 驱动阶段和 checkpoint 恢复进行单元测试。）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.（**组织方式**：任务按用户故事分组，以便每个故事都能独立实现和独立测试。）

## Format: `[ID] [P?] [Story] Description`（格式：`[ID] [P?] [Story] 描述`）

- **[P]**: Can run in parallel (different files, no dependencies)（**[P]**：可并行执行（不同文件、无依赖））
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)（**[Story]**：该任务所属的用户故事（例如 US1、US2、US3））
- Include exact file paths in descriptions（描述中需包含精确文件路径）

## Phase 1: Setup (Shared Infrastructure)（阶段 1：初始化（共享基础设施））

**Purpose**: Create the LangGraph feature scaffolding and align the implementation with the existing orchestration boundary.（**目的**：创建 LangGraph 功能脚手架，并使实现与现有编排边界保持一致。）

- [X] T001 Create `specs/20260518-143022-langgraph-orchestration-refactor/research.md` with current-code audit notes for `sprintcycle/infrastructure/integrations/langgraph/{graph.py,graph_runtime.py,runtime.py,intent_graph.py,sprint_graph.py,plan_runtime.py,adapter.py}`（创建 `specs/20260518-143022-langgraph-orchestration-refactor/research.md`，记录对 `sprintcycle/infrastructure/integrations/langgraph/{graph.py,graph_runtime.py,runtime.py,intent_graph.py,sprint_graph.py,plan_runtime.py,adapter.py}` 的现有代码审计笔记）
- [X] T002 Create `specs/20260518-143022-langgraph-orchestration-refactor/data-model.md` documenting `IntentState`, `SprintState`, `CheckpointStore`, and compiled graph runtime outputs（创建 `specs/20260518-143022-langgraph-orchestration-refactor/data-model.md`，记录 `IntentState`、`SprintState`、`CheckpointStore` 和已编译图运行时输出）
- [X] T003 Create `specs/20260518-143022-langgraph-orchestration-refactor/quickstart.md` with a minimal compile/invoke/recover flow for the LangGraph refactor（创建 `specs/20260518-143022-langgraph-orchestration-refactor/quickstart.md`，写出 LangGraph 重构的最小编译/调用/恢复流程）
- [X] T004 [P] Create `specs/20260518-143022-langgraph-orchestration-refactor/contracts/` artifacts for graph runtime invocation and checkpoint access contracts（[P] 创建 `specs/20260518-143022-langgraph-orchestration-refactor/contracts/` 工件，用于图运行时调用和 checkpoint 访问契约）

---

## Phase 2: Foundational (Blocking Prerequisites)（阶段 2：基础层（阻塞性前置条件））

**Purpose**: Core graph state, checkpoint abstraction, and compilation helpers that all graph flows depend on before any story can be implemented.（**目的**：在实现任何用户故事之前，先建立所有图流程依赖的核心图状态、checkpoint 抽象和编译辅助函数。）

**⚠️ CRITICAL**: No user story work can begin until this phase is complete（**⚠️ 关键**：在本阶段完成前，不能开始任何用户故事工作）

- [X] T005 Define `IntentState`, `SprintState`, and timeline/error/evaluation fields in `sprintcycle/infrastructure/integrations/langgraph/states.py`（在 `sprintcycle/infrastructure/integrations/langgraph/states.py` 中定义 `IntentState`、`SprintState` 以及 timeline/error/evaluation 字段）
- [X] T006 Define `CheckpointStore` abstraction and default local JSON/file implementation in `sprintcycle/infrastructure/integrations/langgraph/checkpoint.py`（在 `sprintcycle/infrastructure/integrations/langgraph/checkpoint.py` 中定义 `CheckpointStore` 抽象和默认本地 JSON/文件实现）
- [X] T007 [P] Add graph compilation helpers and singleton accessors in `sprintcycle/infrastructure/integrations/langgraph/compiler.py` for `compile_intent_graph()`, `compile_sprint_graph()`, `get_intent_graph()`, and `get_sprint_graph()`（[P] 在 `sprintcycle/infrastructure/integrations/langgraph/compiler.py` 中添加图编译辅助函数和单例访问器：`compile_intent_graph()`、`compile_sprint_graph()`、`get_intent_graph()`、`get_sprint_graph()`）
- [X] T008 [P] Update `sprintcycle/infrastructure/integrations/langgraph/graph.py` to align node/edge specs with compiled graph runtime metadata instead of descriptive-only flow objects（[P] 更新 `sprintcycle/infrastructure/integrations/langgraph/graph.py`，使节点/边规范与已编译图运行时元数据对齐，而不是仅保留描述性流程对象）
- [X] T009 Update `sprintcycle/infrastructure/integrations/langgraph/graph_runtime.py` so it returns compiled graph artifacts and not just stringified graph descriptions（更新 `sprintcycle/infrastructure/integrations/langgraph/graph_runtime.py`，使其返回已编译图产物，而不是仅返回字符串化的图描述）
- [X] T010 Update `sprintcycle/infrastructure/integrations/langgraph/runtime.py` and compatibility surfaces in `intent_graph.py`, `sprint_graph.py`, `plan_runtime.py`, and `adapter.py` to consume the compiled graph accessors without reintroducing bypass logic（更新 `sprintcycle/infrastructure/integrations/langgraph/runtime.py` 以及 `intent_graph.py`、`sprint_graph.py`、`plan_runtime.py`、`adapter.py` 中的兼容层，使其消费已编译图访问器而不重新引入旁路逻辑）

**Checkpoint**: Foundation ready - graph compilation, state modeling, and checkpoint abstraction can now support independent story work.（**检查点**：基础能力已就绪——图编译、状态建模和 checkpoint 抽象现在可以支持独立的用户故事工作。）

---

## Phase 3: User Story 1 - Compile real LangGraph runtimes（编译真正的 LangGraph 运行时） (Priority: P1) 🎯 MVP（阶段 3：用户故事 1 - 编译真正的 LangGraph 运行时（优先级：P1）🎯 MVP）

**Goal**: Replace descriptive/method-chained graph runtime behavior with compiled LangGraph `StateGraph` runtimes for both the top-level intent flow and the per-sprint flow.（**目标**：将描述性/方法串联式图运行时行为替换为真正编译后的 LangGraph `StateGraph` 运行时，覆盖顶层意图流和每个 sprint 的流。）

**Independent Test**: Instantiate and compile both graphs, then assert that the resulting artifacts contain the expected nodes, edges, entry points, and finish points.（**独立测试**：实例化并编译两个图，然后断言结果产物包含预期的节点、边、入口点和结束点。）

### Tests for User Story 1（用户故事 1 的测试）

- [X] T011 [P] [US1] Add unit tests for compiled intent graph structure in `tests/infrastructure/integrations/langgraph/test_compiler.py`（[P] [US1] 在 `tests/infrastructure/integrations/langgraph/test_compiler.py` 中添加已编译意图图结构单元测试）
- [X] T012 [P] [US1] Add unit tests for compiled sprint graph structure in `tests/infrastructure/integrations/langgraph/test_compiler.py`（[P] [US1] 在 `tests/infrastructure/integrations/langgraph/test_compiler.py` 中添加已编译 sprint 图结构单元测试）
- [X] T013 [P] [US1] Add unit tests for graph state shapes in `tests/infrastructure/integrations/langgraph/test_states.py`（[P] [US1] 在 `tests/infrastructure/integrations/langgraph/test_states.py` 中添加图状态形状单元测试）

### Implementation for User Story 1（用户故事 1 的实现）

- [X] T014 [US1] Implement `sprintcycle/infrastructure/integrations/langgraph/intent_nodes.py` for top-level orchestration nodes and conditional routing helpers（[US1] 实现 `sprintcycle/infrastructure/integrations/langgraph/intent_nodes.py`，用于顶层编排节点和条件路由辅助函数）
- [X] T015 [US1] Implement `sprintcycle/infrastructure/integrations/langgraph/sprint_nodes.py` for per-sprint prepare/execute/observe/repair/finalize nodes and retry routing helpers（[US1] 实现 `sprintcycle/infrastructure/integrations/langgraph/sprint_nodes.py`，用于每个 sprint 的 prepare/execute/observe/repair/finalize 节点和重试路由辅助函数）
- [X] T016 [US1] Implement `sprintcycle/infrastructure/integrations/langgraph/compiler.py` to compile both graphs with `StateGraph.compile()` and expose graph singletons（[US1] 实现 `sprintcycle/infrastructure/integrations/langgraph/compiler.py`，使用 `StateGraph.compile()` 编译两个图并暴露图单例）
- [X] T017 [US1] Update `sprintcycle/infrastructure/integrations/langgraph/graph_runtime.py` and `runtime.py` to surface compiled graph artifacts through the existing runtime adapter surface（[US1] 更新 `sprintcycle/infrastructure/integrations/langgraph/graph_runtime.py` 和 `runtime.py`，通过现有运行时适配器表面暴露已编译图产物）

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.（**检查点**：到这里，用户故事 1 应已完全可用并可独立测试。）

---

## Phase 4: User Story 2 - Route through LLM-backed intent and plan stages（通过 LLM 驱动意图与计划阶段路由） (Priority: P2)（阶段 4：用户故事 2 - 通过 LLM 驱动意图与计划阶段路由（优先级：P2））

**Goal**: Make the intent graph actually understand user intent and generate a structured release plan using LLM collaborators, then route sprint decomposition and dispatch through graph state and conditional edges.（**目标**：让意图图真正理解用户意图并使用 LLM 协作者生成结构化发布计划，然后通过图状态和条件边完成 sprint 拆分与派发路由。）

**Independent Test**: Stub the LLM collaborator and verify the intent graph nodes produce analyzed intent, generated release plans, sprint decomposition, dispatch results, and retry/finalize decisions from graph state alone.（**独立测试**：stub LLM 协作者，并验证意图图节点仅凭图状态就能产出意图分析、发布计划、sprint 拆分、派发结果以及重试/完成决策。）

### Tests for User Story 2（用户故事 2 的测试）

- [X] T018 [P] [US2] Add unit tests for LLM-backed intent understanding in `tests/infrastructure/integrations/langgraph/test_nodes.py`（[P] [US2] 在 `tests/infrastructure/integrations/langgraph/test_nodes.py` 中添加 LLM 驱动的意图理解单元测试）
- [X] T019 [P] [US2] Add unit tests for release plan generation and sprint splitting in `tests/infrastructure/integrations/langgraph/test_nodes.py`（[P] [US2] 在 `tests/infrastructure/integrations/langgraph/test_nodes.py` 中添加发布计划生成与 sprint 拆分单元测试）
- [X] T020 [P] [US2] Add unit tests for dispatch evaluation and retry/finalize conditional routing in `tests/infrastructure/integrations/langgraph/test_nodes.py`（[P] [US2] 在 `tests/infrastructure/integrations/langgraph/test_nodes.py` 中添加派发评估与重试/完成条件路由单元测试）

### Implementation for User Story 2（用户故事 2 的实现）

- [X] T021 [US2] Implement LLM-collaborator integration in `sprintcycle/infrastructure/integrations/langgraph/intent_nodes.py` for `intent_understand()` and `plan_generate()`（[US2] 在 `sprintcycle/infrastructure/integrations/langgraph/intent_nodes.py` 中实现 LLM 协作者集成，用于 `intent_understand()` 和 `plan_generate()`）
- [X] T022 [US2] Implement sprint splitting, dispatch, evaluation, and finalize state transitions in `sprintcycle/infrastructure/integrations/langgraph/intent_nodes.py` using graph state only（[US2] 在 `sprintcycle/infrastructure/integrations/langgraph/intent_nodes.py` 中仅使用图状态实现 sprint 拆分、派发、评估和 finalize 状态转换）
- [X] T023 [US2] Ensure `SprintExecutor` is invoked only from `sprintcycle/infrastructure/integrations/langgraph/sprint_nodes.py` execute node and not from application-layer bypass code（[US2] 确保 `SprintExecutor` 只能从 `sprintcycle/infrastructure/integrations/langgraph/sprint_nodes.py` 的 execute 节点中被调用，而不能由 application 层旁路代码调用）
- [X] T024 [US2] Update `sprintcycle/application/release/orchestrator.py` as the canonical thin orchestration entry to call compiled intent graph and aggregate results without owning routing logic（[US2] 更新 `sprintcycle/application/release/orchestrator.py` 作为 canonical 薄编排入口，使其调用已编译的意图图并汇总结果，但不拥有路由逻辑）

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.（**检查点**：到这里，用户故事 1 和 2 都应可独立工作。）

---

## Phase 5: User Story 3 - Preserve execution continuity with checkpoint-backed recovery（通过 checkpoint 恢复保持执行连续性） (Priority: P3)（阶段 5：用户故事 3 - 通过 checkpoint 恢复保持执行连续性（优先级：P3））

**Goal**: Add checkpoint-backed recovery so interrupted orchestration can resume from the saved graph state without duplicating execution paths or bypassing graph routing.（**目标**：增加基于 checkpoint 的恢复，使中断的编排可以从已保存的图状态恢复，而不会重复执行路径或绕过图路由。）

**Independent Test**: Use a mock or local checkpoint store, interrupt graph execution, restore from the saved state, and verify the graph resumes at the expected stage without duplicate active workers.（**独立测试**：使用 mock 或本地 checkpoint 存储，中断图执行，从已保存状态恢复，并验证图会从预期阶段继续，而不会产生重复的活跃 worker。）

### Tests for User Story 3（用户故事 3 的测试）

- [X] T025 [P] [US3] Add unit tests for checkpoint save/restore behavior in `tests/infrastructure/integrations/langgraph/test_checkpoint.py`（[P] [US3] 在 `tests/infrastructure/integrations/langgraph/test_checkpoint.py` 中添加 checkpoint 保存/恢复行为单元测试）
- [X] T026 [P] [US3] Add unit tests for recovery after interrupted intent graph execution in `tests/infrastructure/integrations/langgraph/test_nodes.py`（[P] [US3] 在 `tests/infrastructure/integrations/langgraph/test_nodes.py` 中添加意图图中断后恢复的单元测试）
- [X] T027 [P] [US3] Add unit tests for recovery after interrupted sprint graph execution in `tests/infrastructure/integrations/langgraph/test_nodes.py`（[P] [US3] 在 `tests/infrastructure/integrations/langgraph/test_nodes.py` 中添加 sprint 图中断后恢复的单元测试）

### Implementation for User Story 3（用户故事 3 的实现）

- [X] T028 [US3] Implement checkpoint save/load logic and `thread_id`-based restore path in `sprintcycle/infrastructure/integrations/langgraph/checkpoint.py`（[US3] 在 `sprintcycle/infrastructure/integrations/langgraph/checkpoint.py` 中实现 checkpoint 保存/加载逻辑和基于 `thread_id` 的恢复路径）
- [X] T029 [US3] Wire checkpoint support into graph compilation or runtime accessors in `sprintcycle/infrastructure/integrations/langgraph/compiler.py` so compiled graphs can restore state（[US3] 在 `sprintcycle/infrastructure/integrations/langgraph/compiler.py` 中把 checkpoint 支持接入图编译或运行时访问器，使已编译图可以恢复状态）
- [X] T030 [US3] Update `sprintcycle/application/release/orchestrator.py` as the canonical thin application orchestration entrypoint to pass recovery keys/config through to compiled graph invocations（[US3] 更新 `sprintcycle/application/release/orchestrator.py` 作为 canonical 薄 application 编排入口，将恢复 key/config 传递给已编译图调用）
- [X] T031 [US3] Add guard rails to prevent duplicate workers or concurrent activation sessions during recovery in `sprintcycle/infrastructure/integrations/langgraph/runtime.py` and/or `checkpoint.py`（[US3] 在 `sprintcycle/infrastructure/integrations/langgraph/runtime.py` 和/或 `checkpoint.py` 中添加防护，避免恢复期间出现重复 worker 或并发激活会话）

**Checkpoint**: All user stories should now be independently functional.（**检查点**：所有用户故事现在都应可独立运行。）

---

## Phase 6: Polish & Cross-Cutting Concerns（阶段 6：润色与跨切关注点）

**Purpose**: Improvements that affect multiple user stories.（**目的**：影响多个用户故事的改进。）

- [X] T032 [P] Update `specs/20260518-143022-langgraph-orchestration-refactor/quickstart.md` with validation steps for compile/invoke/recover flow（[P] 更新 `specs/20260518-143022-langgraph-orchestration-refactor/quickstart.md`，补充编译/调用/恢复流程的验证步骤）
- [X] T033 [P] Update `specs/20260518-143022-langgraph-orchestration-refactor/data-model.md` and `contracts/` to reflect finalized runtime and checkpoint contracts（[P] 更新 `specs/20260518-143022-langgraph-orchestration-refactor/data-model.md` 和 `contracts/`，反映最终的运行时与 checkpoint 契约）
- [X] T034 [P] Add or update docs in `specs/20260518-143022-langgraph-orchestration-refactor/research.md` to record any final graph/runtime trade-offs and architecture notes（[P] 在 `specs/20260518-143022-langgraph-orchestration-refactor/research.md` 中补充或更新文档，记录最终的图/运行时权衡与架构笔记）
- [X] T035 Run targeted lint and unit tests for `sprintcycle/infrastructure/integrations/langgraph/` and the thin application orchestration entrypoints（运行针对 `sprintcycle/infrastructure/integrations/langgraph/` 和薄 application 编排入口的定向 lint 与单元测试）
- [X] T036 Verify `SprintExecutor` is not called from any bypass path outside the sprint graph execution node and that the LangGraph boundary remains thin and authoritative（验证 `SprintExecutor` 没有在 sprint 图执行节点之外的任何旁路路径中被调用，并确保 LangGraph 边界保持薄且具有权威性）

---

## Dependencies & Execution Order（依赖关系与执行顺序）

### Phase Dependencies（阶段依赖）

- **Setup (Phase 1)**: No dependencies - can start immediately（**初始化（阶段 1）**：无依赖——可立即开始）
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories（**基础层（阶段 2）**：依赖初始化完成——阻塞所有用户故事）
- **User Stories (Phase 3+)**: All depend on Foundational phase completion（**用户故事（阶段 3+）**：都依赖基础层完成）
  - User stories can then proceed in parallel (if staffed)（用户故事随后可并行推进（如果资源允许））
  - Or sequentially in priority order (P1 → P2 → P3)（或者按优先级顺序推进（P1 → P2 → P3））
- **Polish (Final Phase)**: Depends on all desired user stories being complete（**润色（最终阶段）**：依赖所有目标用户故事完成）

### User Story Dependencies（用户故事依赖）

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories（**用户故事 1（P1）**：可在基础层（阶段 2）后开始——不依赖其他故事）
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable（**用户故事 2（P2）**：可在基础层（阶段 2）后开始——可与 US1 集成，但应保持可独立测试）
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable（**用户故事 3（P3）**：可在基础层（阶段 2）后开始——可与 US1/US2 集成，但应保持可独立测试）

### Within Each User Story（每个用户故事内部）

- Tests (if included) MUST be written and FAIL before implementation（测试（如包含）必须先编写并在实现前失败）
- Models/state before graph wiring and runtime changes（先模型/状态，后图接线和运行时变更）
- Services/nodes before orchestration entrypoint updates（先服务/节点，后编排入口更新）
- Core graph implementation before integration cleanup（先核心图实现，后集成清理）
- Story complete before moving to next priority（完成当前故事后再进入下一个优先级）

### Parallel Opportunities（并行机会）

- All Setup tasks marked [P] can run in parallel（所有标记为 [P] 的初始化任务可并行执行）
- All Foundational tasks marked [P] can run in parallel (within Phase 2)（所有标记为 [P] 的基础任务可并行执行（在阶段 2 内））
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)（基础层完成后，所有用户故事可并行启动（如果团队能力允许））
- All tests for a user story marked [P] can run in parallel（同一用户故事中所有标记为 [P] 的测试可并行执行）
- Different user stories can be worked on in parallel by different team members（不同用户故事可由不同团队成员并行推进）

---

## Implementation Strategy（实现策略）

### MVP First (User Story 1 Only)（先做 MVP（仅用户故事 1））

1. Complete Phase 1: Setup（完成阶段 1：初始化）
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)（完成阶段 2：基础层（关键——阻塞所有故事））
3. Complete Phase 3: User Story 1（完成阶段 3：用户故事 1）
4. **STOP and VALIDATE**: Test User Story 1 independently（**停止并验证**：独立测试用户故事 1）
5. Deploy/demo if ready（如已就绪，则部署/演示）

### Incremental Delivery（增量交付）

1. Complete Setup + Foundational → Foundation ready（完成初始化 + 基础层 → 基础能力就绪）
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)（加入用户故事 1 → 独立测试 → 部署/演示（MVP！））
3. Add User Story 2 → Test independently → Deploy/Demo（加入用户故事 2 → 独立测试 → 部署/演示）
4. Add User Story 3 → Test independently → Deploy/Demo（加入用户故事 3 → 独立测试 → 部署/演示）
5. Each story adds value without breaking previous stories（每个故事在不破坏前序故事的前提下增加价值）

### Parallel Team Strategy（并行团队策略）

With multiple developers:（当有多名开发者时：）

1. Team completes Setup + Foundational together（团队共同完成初始化 + 基础层）
2. Once Foundational is done:（基础层完成后：）
   - Developer A: User Story 1（开发者 A：用户故事 1）
   - Developer B: User Story 2（开发者 B：用户故事 2）
   - Developer C: User Story 3（开发者 C：用户故事 3）
3. Stories complete and integrate independently（各故事独立完成并集成）

---

## Notes（说明）

- [P] tasks = different files, no dependencies（[P] 任务 = 不同文件、无依赖）
- [Story] label maps task to specific user story for traceability（[Story] 标签用于将任务映射到特定用户故事，以便追踪）
- Each user story should be independently completable and testable（每个用户故事都应可独立完成并可独立测试）
- Verify tests fail before implementing（实现前先确认测试失败）
- Commit after each task or logical group（每完成一个任务或一个逻辑组后提交）
- Stop at any checkpoint to validate story independently（在任一检查点暂停，以独立验证该故事）
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence（避免：含糊任务、同文件冲突、破坏独立性的跨故事依赖）
