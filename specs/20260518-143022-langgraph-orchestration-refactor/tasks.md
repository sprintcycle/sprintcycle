# Tasks: LangGraph Orchestration Cleanup（LangGraph 编排清理）

**Input**: Design documents from `/specs/20260518-143022-langgraph-orchestration-refactor/`（输入：来自 `/specs/20260518-143022-langgraph-orchestration-refactor/` 的设计文档）

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/（前置条件：plan.md（必需）、spec.md（用户故事必需）、research.md、data-model.md、contracts/）

**Tests**: Included because the feature specification explicitly requires tests proving the orchestrator no longer depends on old runtime symbols, the compiled graph path still works, and the legacy LangGraph modules are no longer part of the production path.（**测试**：已包含，因为功能规格明确要求测试证明 orchestrator 不再依赖旧运行时符号、已编译图路径仍然可用，以及旧 LangGraph 模块不再属于生产路径。）

**Organization**: Tasks are grouped by user story to enable independent implementation and verification of each cleanup step.（**组织方式**：任务按用户故事分组，以便每个清理步骤都能独立实现和独立验证。）

## Format: `[ID] [P?] [Story] Description`（格式：`[ID] [P?] [Story] 描述`）

- **[P]**: Can run in parallel (different files, no dependencies)（**[P]**：可并行执行（不同文件、无依赖））
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)（**[Story]**：该任务所属的用户故事（例如 US1、US2、US3））
- Include exact file paths in descriptions（描述中需包含精确文件路径）

## Phase 1: Setup (Shared Infrastructure)（阶段 1：初始化（共享基础设施））

**Purpose**: Align the cleanup scope with the current LangGraph compiler-backed runtime and identify all references that must be removed or rewritten.（**目的**：将清理范围与当前基于 compiler 的 LangGraph 运行时对齐，并识别所有必须删除或重写的引用。）

- [X] T001 Review `sprintcycle/infrastructure/integrations/langgraph/{compiler.py,graph_runtime.py,runtime.py,intent_graph.py,sprint_graph.py,plan_runtime.py,adapter.py}` and record the cleanup boundary in `specs/20260518-143022-langgraph-orchestration-refactor/research.md`（审查 `sprintcycle/infrastructure/integrations/langgraph/{compiler.py,graph_runtime.py,runtime.py,intent_graph.py,sprint_graph.py,plan_runtime.py,adapter.py}`，并在 `specs/20260518-143022-langgraph-orchestration-refactor/research.md` 中记录清理边界）
- [X] T002 Update `specs/20260518-143022-langgraph-orchestration-refactor/data-model.md` to document compiled runtime outputs, checkpoint abstraction, and execution summary shapes（更新 `specs/20260518-143022-langgraph-orchestration-refactor/data-model.md`，记录已编译运行时输出、checkpoint 抽象和执行摘要形状）
- [X] T003 Update `specs/20260518-143022-langgraph-orchestration-refactor/quickstart.md` with the compiler-backed compile/invoke/recover flow and legacy-entrypoint verification steps（更新 `specs/20260518-143022-langgraph-orchestration-refactor/quickstart.md`，补充基于 compiler 的编译/调用/恢复流程及旧入口验证步骤）
- [X] T004 [P] Update `specs/20260518-143022-langgraph-orchestration-refactor/contracts/langgraph-runtime-contract.md` to describe the supported compiled-graph boundary and removed legacy runtime path（[P] 更新 `specs/20260518-143022-langgraph-orchestration-refactor/contracts/langgraph-runtime-contract.md`，描述受支持的已编译图边界和已移除的旧运行时路径）

---

## Phase 2: Foundational (Blocking Prerequisites)（阶段 2：基础层（阻塞性前置条件））

**Purpose**: Ensure the compiler-backed graph runtime is the only supported LangGraph production path before removing the old wrappers.（**目的**：在删除旧包装器之前，确保基于 compiler 的图运行时是唯一受支持的 LangGraph 生产路径。）

**⚠️ CRITICAL**: No user story work can begin until this phase is complete（**⚠️ 关键**：在本阶段完成前，不能开始任何用户故事工作）

- [X] T005 [P] Tighten `sprintcycle/infrastructure/integrations/langgraph/compiler.py` to expose the compiled intent/sprint graph artifacts as the authoritative runtime accessors（[P] 收紧 `sprintcycle/infrastructure/integrations/langgraph/compiler.py`，使其作为意图/sprint 图产物的权威运行时访问器）
- [X] T006 [P] Align `sprintcycle/infrastructure/integrations/langgraph/states.py` with cleanup-focused orchestration fields and recovery metadata（[P] 使 `sprintcycle/infrastructure/integrations/langgraph/states.py` 与清理聚焦的编排字段和恢复元数据保持一致）
- [X] T007 [P] Finalize `sprintcycle/infrastructure/integrations/langgraph/checkpoint.py` as the single checkpoint abstraction used by compiled graph invocations（[P] 完成 `sprintcycle/infrastructure/integrations/langgraph/checkpoint.py`，使其成为已编译图调用使用的唯一 checkpoint 抽象）
- [X] T008 Update `sprintcycle/infrastructure/integrations/langgraph/__init__.py` to export only supported compiler-backed APIs and stop advertising legacy runtime surfaces（更新 `sprintcycle/infrastructure/integrations/langgraph/__init__.py`，只导出受支持的 compiler-backed API，并停止对旧运行时表面的导出）

**Checkpoint**: Foundation ready - the compiler-backed path is the supported runtime surface, and the legacy wrapper surfaces can now be removed or rewritten safely.（**检查点**：基础能力已就绪——基于 compiler 的路径是受支持的运行时表面，旧包装层现在可以安全移除或重写。）

---

## Phase 3: User Story 1 - Orchestrator uses compiled LangGraph runtimes（Orchestrator 使用已编译的 LangGraph 运行时） (Priority: P1) 🎯 MVP（阶段 3：用户故事 1 - Orchestrator 使用已编译的 LangGraph 运行时（优先级：P1）🎯 MVP）

**Goal**: Switch `SprintOrchestrator` to the compiler-backed runtime path so the primary execution flow no longer instantiates `IntentGraphRuntime`.（**目标**：将 `SprintOrchestrator` 切换到基于 compiler 的运行时路径，使主执行流不再实例化 `IntentGraphRuntime`。）

**Independent Test**: Instantiate `SprintOrchestrator`, execute a release plan, and verify the code path uses the compiled graph accessors and does not construct legacy runtime wrappers.（**独立测试**：实例化 `SprintOrchestrator`，执行 release plan，并验证代码路径使用已编译图访问器且不构造旧运行时包装器。）

### Tests for User Story 1（用户故事 1 的测试）

- [X] T009 [P] [US1] Add unit tests in `tests/application/release/test_orchestrator.py` to verify `SprintOrchestrator` no longer constructs `IntentGraphRuntime`（[P] [US1] 在 `tests/application/release/test_orchestrator.py` 中添加单元测试，验证 `SprintOrchestrator` 不再构造 `IntentGraphRuntime`）
- [X] T010 [P] [US1] Add unit tests in `tests/application/release/test_orchestrator.py` to verify orchestrator consumption of compiled graph results and preservation of finalization/event behavior（[P] [US1] 在 `tests/application/release/test_orchestrator.py` 中添加单元测试，验证 orchestrator 消费已编译图结果并保持 finalization/事件行为）

### Implementation for User Story 1（用户故事 1 的实现）

- [X] T011 [US1] Refactor `sprintcycle/application/orchestration/sprint_orchestrator.py` to call the compiler-backed LangGraph accessors instead of instantiating `IntentGraphRuntime`（[US1] 重构 `sprintcycle/application/orchestration/sprint_orchestrator.py`，改为调用基于 compiler 的 LangGraph 访问器，而不是实例化 `IntentGraphRuntime`）
- [X] T012 [US1] Update `sprintcycle/application/orchestration/sprint_orchestrator.py` result handling so compiled graph output is normalized into `SprintResult` without duplicating routing logic（[US1] 更新 `sprintcycle/application/orchestration/sprint_orchestrator.py` 的结果处理，使已编译图输出被规范化为 `SprintResult`，而不重复路由逻辑）
- [X] T013 [US1] Remove or rewrite imports in `sprintcycle/application/orchestration/sprint_orchestrator.py` and `sprintcycle/infrastructure/integrations/langgraph/__init__.py` so the old runtime path is no longer the production default（[US1] 删除或重写 `sprintcycle/application/orchestration/sprint_orchestrator.py` 和 `sprintcycle/infrastructure/integrations/langgraph/__init__.py` 中的导入，使旧运行时路径不再是生产默认路径）

**Checkpoint**: At this point, the orchestrator should be fully switched to the compiler-backed runtime path.（**检查点**：到这里，orchestrator 应已完全切换到基于 compiler 的运行时路径。）

---

## Phase 4: User Story 2 - Remove old LangGraph runtime entry points（移除旧的 LangGraph 运行时入口） (Priority: P2)（阶段 4：用户故事 2 - 移除旧的 LangGraph 运行时入口（优先级：P2））

**Goal**: Retire `intent_graph.py`, `sprint_graph.py`, and `graph_runtime.py` from the production path so there is only one supported LangGraph implementation.（**目标**：让 `intent_graph.py`、`sprint_graph.py` 和 `graph_runtime.py` 退出生产路径，使系统里只剩一条受支持的 LangGraph 实现。）

**Independent Test**: Search the codebase for old runtime symbols and verify there are no production references to the retired modules in the execution path.（**独立测试**：搜索代码库中的旧运行时符号，并验证执行路径中没有对已退役模块的生产引用。）

### Tests for User Story 2（用户故事 2 的测试）

- [X] T014 [P] [US2] Add regression tests in `tests/application/release/test_orchestrator.py` to fail if `IntentGraphRuntime` is reintroduced into the orchestrator path（[P] [US2] 在 `tests/application/release/test_orchestrator.py` 中添加回归测试，如果 `IntentGraphRuntime` 重新进入 orchestrator 路径则失败）
- [X] T015 [P] [US2] Add repository-wide symbol/reference checks in `tests/infrastructure/integrations/langgraph/test_compiler.py` or a new cleanup-focused test module to detect lingering imports of `intent_graph.py`, `sprint_graph.py`, and `graph_runtime.py`（[P] [US2] 在 `tests/infrastructure/integrations/langgraph/test_compiler.py` 或新的清理聚焦测试模块中添加仓库级符号/引用检查，以检测对 `intent_graph.py`、`sprint_graph.py` 和 `graph_runtime.py` 的残留导入）

### Implementation for User Story 2（用户故事 2 的实现）

- [X] T016 [US2] Remove `sprintcycle/infrastructure/integrations/langgraph/intent_graph.py` from the production import surface or reduce it to a non-production compatibility stub that is not re-exported（[US2] 从生产导入表面移除 `sprintcycle/infrastructure/integrations/langgraph/intent_graph.py`，或将其缩减为不再导出的非生产兼容桩）
- [X] T017 [US2] Remove `sprintcycle/infrastructure/integrations/langgraph/sprint_graph.py` from the production import surface or reduce it to a non-production compatibility stub that is not re-exported（[US2] 从生产导入表面移除 `sprintcycle/infrastructure/integrations/langgraph/sprint_graph.py`，或将其缩减为不再导出的非生产兼容桩）
- [X] T018 [US2] Remove `sprintcycle/infrastructure/integrations/langgraph/graph_runtime.py` from the production import surface or reduce it to a non-production compatibility stub that is not re-exported（[US2] 从生产导入表面移除 `sprintcycle/infrastructure/integrations/langgraph/graph_runtime.py`，或将其缩减为不再导出的非生产兼容桩）
- [X] T019 [US2] Update `sprintcycle/infrastructure/integrations/langgraph/runtime.py`, `plan_runtime.py`, and `adapter.py` so they no longer depend on the legacy runtime wrappers（[US2] 更新 `sprintcycle/infrastructure/integrations/langgraph/runtime.py`、`plan_runtime.py` 和 `adapter.py`，使其不再依赖旧运行时包装器）

**Checkpoint**: At this point, only compiler-backed LangGraph entry points should remain in production use.（**检查点**：到这里，生产使用中应只剩基于 compiler 的 LangGraph 入口。）

---

## Phase 5: User Story 3 - Preserve existing execution behavior while switching graph source（切换图来源时保持现有执行行为） (Priority: P3)（阶段 5：用户故事 3 - 切换图来源时保持现有执行行为（优先级：P3））

**Goal**: Preserve release finalization, event emission, `SprintExecutor` behavior, and state persistence while switching to the compiler-backed graph path.（**目标**：在切换到基于 compiler 的图路径时，保留 release finalization、事件上报、`SprintExecutor` 行为和状态持久化。）

**Independent Test**: Run the orchestrator through a representative release plan and verify event emission, completion summary, finalization persistence, and `SprintExecutor`-backed sprint results still work after the switch.（**独立测试**：通过一个具代表性的 release plan 运行 orchestrator，并验证切换后事件上报、完成摘要、finalization 持久化以及基于 `SprintExecutor` 的 sprint 结果仍然正常工作。）

### Tests for User Story 3（用户故事 3 的测试）

- [X] T020 [P] [US3] Add or update recovery-focused tests in `tests/infrastructure/integrations/langgraph/test_checkpoint.py` to validate save/restore and thread key behavior（[P] [US3] 在 `tests/infrastructure/integrations/langgraph/test_checkpoint.py` 中添加或更新恢复聚焦测试，验证保存/恢复和线程 key 行为）
- [X] T021 [P] [US3] Add or update execution-continuity tests in `tests/infrastructure/integrations/langgraph/test_nodes.py` to verify checkpoint-backed resume does not duplicate active execution paths（[P] [US3] 在 `tests/infrastructure/integrations/langgraph/test_nodes.py` 中添加或更新执行连续性测试，验证基于 checkpoint 的恢复不会重复活跃执行路径）

### Implementation for User Story 3（用户故事 3 的实现）

- [X] T022 [US3] Ensure `sprintcycle/infrastructure/integrations/langgraph/checkpoint.py` exposes the restore-key path used by compiled graph invocations and supports local development recovery（[US3] 确保 `sprintcycle/infrastructure/integrations/langgraph/checkpoint.py` 暴露已编译图调用使用的恢复 key 路径，并支持本地开发恢复）
- [X] T023 [US3] Wire the compiled graph invocation path in `sprintcycle/application/orchestration/sprint_orchestrator.py` to pass checkpoint/config data without reintroducing direct `SprintExecutor` calls（[US3] 在 `sprintcycle/application/orchestration/sprint_orchestrator.py` 中接通已编译图调用路径，传递 checkpoint/config 数据而不重新引入对 `SprintExecutor` 的直接调用）
- [X] T024 [US3] Add guard rails in `sprintcycle/infrastructure/integrations/langgraph/compiler.py` and/or `checkpoint.py` to prevent duplicate workers or concurrent activation sessions during recovery（[US3] 在 `sprintcycle/infrastructure/integrations/langgraph/compiler.py` 和/或 `checkpoint.py` 中添加防护，避免恢复期间出现重复 worker 或并发激活会话）

**Checkpoint**: All user stories should now be independently functional.（**检查点**：所有用户故事现在都应可独立运行。）

---

## Phase 6: Polish & Cross-Cutting Concerns（阶段 6：润色与跨切关注点）

**Purpose**: Final validation that the old runtime path is gone, the compiled graph path is authoritative, and the cleanup has not changed the observable orchestration contract.（**目的**：最终验证旧运行时路径已消失、已编译图路径具有权威性，并且清理没有改变可观察的编排契约。）

- [X] T025 [P] Run targeted lint and unit tests for `sprintcycle/application/orchestration/sprint_orchestrator.py` and `sprintcycle/infrastructure/integrations/langgraph/`（[P] 运行针对 `sprintcycle/application/orchestration/sprint_orchestrator.py` 和 `sprintcycle/infrastructure/integrations/langgraph/` 的定向 lint 与单元测试）
- [X] T026 [P] Verify via repository search that `IntentGraphRuntime` is no longer part of the production execution path and that `sprintcycle/infrastructure/integrations/langgraph/{intent_graph.py,sprint_graph.py,graph_runtime.py}` are not imported by production code（[P] 通过仓库搜索验证 `IntentGraphRuntime` 不再属于生产执行路径，并且 `sprintcycle/infrastructure/integrations/langgraph/{intent_graph.py,sprint_graph.py,graph_runtime.py}` 未被生产代码导入）
- [X] T027 [P] Update `specs/20260518-143022-langgraph-orchestration-refactor/research.md` or `quickstart.md` if final validation reveals any remaining runtime assumptions or cleanup notes（[P] 如果最终验证暴露出任何剩余运行时假设或清理说明，更新 `specs/20260518-143022-langgraph-orchestration-refactor/research.md` 或 `quickstart.md`）

---

## Dependencies & Execution Order（依赖关系与执行顺序）

### Phase Dependencies（阶段依赖）

- **Setup (Phase 1)**: No dependencies - can start immediately（**初始化（阶段 1）**：无依赖——可立即开始）
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories（**基础层（阶段 2）**：依赖初始化完成——阻塞所有用户故事）
- **User Stories (Phase 3+)**: All depend on Foundational phase completion（**用户故事（阶段 3+）**：都依赖基础层完成）
  - User stories can then proceed in priority order (P1 → P2 → P3) or in parallel if the implementation is carefully separated（用户故事随后可按优先级顺序推进（P1 → P2 → P3），或在实现严格隔离时并行推进）
- **Polish (Final Phase)**: Depends on all desired user stories being complete（**润色（最终阶段）**：依赖所有目标用户故事完成）

### User Story Dependencies（用户故事依赖）

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - no dependency on the legacy module removal tasks beyond import updates（**用户故事 1（P1）**：可在基础层（阶段 2）后开始——除导入更新外，不依赖旧模块移除任务）
- **User Story 2 (P2)**: Can start after User Story 1 is complete or alongside it if imports are carefully isolated（**用户故事 2（P2）**：可在用户故事 1 完成后开始，或在导入隔离足够清晰时并行进行）
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and should be validated after the orchestrator is switched to the compiled path（**用户故事 3（P3）**：可在基础层（阶段 2）后开始，并应在 orchestrator 切换到已编译路径后验证）

### Within Each User Story（每个用户故事内部）

- Tests (if included) MUST be written and FAIL before implementation（测试（如包含）必须先编写并在实现前失败）
- Shared cleanup or import changes before cross-file reference removal（跨文件引用移除前先处理共享清理或导入变更）
- Application boundary updates before deleting legacy runtime entry points（删除旧运行时入口前先更新 application 边界）
- Core cleanup before final repository-wide verification（最终仓库级验证前先完成核心清理）

### Parallel Opportunities（并行机会）

- All Setup tasks marked [P] can run in parallel（所有标记为 [P] 的初始化任务可并行执行）
- All Foundational tasks marked [P] can run in parallel (within Phase 2)（所有标记为 [P] 的基础任务可并行执行（在阶段 2 内））
- Tests for a given user story marked [P] can run in parallel（同一用户故事中标记为 [P] 的测试可并行执行）
- Legacy-module cleanup tasks across `intent_graph.py`, `sprint_graph.py`, and `graph_runtime.py` can proceed independently once references are isolated（在引用被隔离后，`intent_graph.py`、`sprint_graph.py` 和 `graph_runtime.py` 的旧模块清理任务可独立进行）

---

## Implementation Strategy（实现策略）

### MVP First (User Story 1 Only)（先做 MVP（仅用户故事 1））

1. Complete Phase 1: Setup（完成阶段 1：初始化）
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)（完成阶段 2：基础层（关键——阻塞所有故事））
3. Complete Phase 3: User Story 1（完成阶段 3：用户故事 1）
4. **STOP and VALIDATE**: Test User Story 1 independently（**停止并验证**：独立测试用户故事 1）
5. Deploy/demo if ready（如已就绪，则部署/演示）

### Incremental Delivery（增量交付）

1. Complete Setup + Foundational → compiler-backed path is authoritative（完成初始化 + 基础层 → 基于 compiler 的路径成为权威）
2. Add User Story 1 → Test independently → Deploy/Demo（加入用户故事 1 → 独立测试 → 部署/演示）
3. Add User Story 2 → Test independently → Deploy/Demo（加入用户故事 2 → 独立测试 → 部署/演示）
4. Add User Story 3 → Test independently → Deploy/Demo（加入用户故事 3 → 独立测试 → 部署/演示）
5. Each story removes more legacy surface area while preserving behavior（每个故事都在保留行为的同时移除更多旧表面）

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
