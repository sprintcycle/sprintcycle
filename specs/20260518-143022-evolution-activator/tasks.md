# Tasks: EvolutionActivator（自进化激活器）

**Input**: Design documents from `/specs/20260518-143022-evolution-activator/`（输入：来自 `/specs/20260518-143022-evolution-activator/` 的设计文档）

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/（前置条件：plan.md（必需）、spec.md（用户故事必需）、research.md、data-model.md、contracts/）

**Tests**: Included because the feature specification explicitly requires unit testing of activation, health checks, retry behavior, degraded mode, and recovery.（**测试**：已包含，因为功能规格明确要求对激活、健康检查、重试行为、降级态和恢复进行单元测试。）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.（**组织方式**：任务按用户故事分组，以便每个故事都能独立实现和独立测试。）

## Format: `[ID] [P?] [Story] Description`（格式：`[ID] [P?] [Story] 描述`）

- **[P]**: Can run in parallel (different files, no dependencies)（**[P]**：可并行执行（不同文件、无依赖））
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)（**[Story]**：该任务所属的用户故事（例如 US1、US2、US3））
- Include exact file paths in descriptions（描述中需包含精确文件路径）

## Phase 1: Setup (Shared Infrastructure)（阶段 1：初始化（共享基础设施））

**Purpose**: Create the feature scaffolding and align the implementation with the documented application-layer boundary.（**目的**：创建功能脚手架，并使实现与文档化的 application 层边界保持一致。）

- [X] T001 Create `application/evolution/` package structure with `application/evolution/__init__.py` and `application/evolution/activator.py`（创建 `application/evolution/` 包结构：`application/evolution/__init__.py` 和 `application/evolution/activator.py`）
- [X] T002 [P] Create `domain/evolution/` runtime state module scaffolding in `domain/evolution/__init__.py` and `domain/evolution/runtime_state.py`（[P] 在 `domain/evolution/__init__.py` 和 `domain/evolution/runtime_state.py` 中创建运行时状态模块脚手架）
- [X] T003 [P] Create `infrastructure/evolution/adapters/` scaffolding in `infrastructure/evolution/adapters/health_check.py` and `infrastructure/evolution/adapters/retry_policy.py`（[P] 在 `infrastructure/evolution/adapters/health_check.py` 和 `infrastructure/evolution/adapters/retry_policy.py` 中创建适配器脚手架）

---

## Phase 2: Foundational (Blocking Prerequisites)（阶段 2：基础层（阻塞性前置条件））

**Purpose**: Define the minimal shared abstractions that all stories depend on before activation, health, retry, and recovery logic can be implemented.（**目的**：定义最小的共享抽象，供所有故事在实现激活、健康、重试和恢复逻辑之前依赖。）

**⚠️ CRITICAL**: No user story work can begin until this phase is complete（**⚠️ 关键**：在本阶段完成前，不能开始任何用户故事工作）

- [X] T004 Define `EvolutionHealthState` and activation state enums/data structures in `domain/evolution/runtime_state.py`（在 `domain/evolution/runtime_state.py` 中定义 `EvolutionHealthState` 与激活状态枚举/数据结构）
- [X] T005 Define guard/result and retry/result value objects or protocols in `domain/evolution/runtime_state.py`（在 `domain/evolution/runtime_state.py` 中定义守卫/结果和重试/结果值对象或协议）
- [X] T006 Define adapter-facing interfaces for health checks and retry policy resolution in `infrastructure/evolution/adapters/health_check.py` and `infrastructure/evolution/adapters/retry_policy.py`（在 `infrastructure/evolution/adapters/health_check.py` 和 `infrastructure/evolution/adapters/retry_policy.py` 中定义面向适配器的健康检查与重试策略解析接口）
- [X] T007 Establish explicit blocked/retry/degraded reason codes for activation outcomes in `domain/evolution/runtime_state.py`（在 `domain/evolution/runtime_state.py` 中为激活结果建立显式的阻断/重试/降级原因码）

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel（**检查点**：基础能力已就绪——现在可以并行开始用户故事实现）

---

## Phase 3: User Story 1 - Activate self-evolution safely (Priority: P1) 🎯 MVP（阶段 3：用户故事 1 - 安全激活自进化（优先级：P1）🎯 MVP）

**Goal**: Add a thin `EvolutionActivator` entry point that evaluates activation guards, starts the evolution loop once, and returns a clear active/blocked outcome without embedding domain policy.（**目标**：添加一个薄的 `EvolutionActivator` 入口，评估激活守卫，确保循环只启动一次，并返回清晰的激活/阻断结果，同时不嵌入领域策略。）

**Independent Test**: Create an activator with mocked guard and loop-start collaborators, call `activate()`, and verify active and blocked activation outcomes are reported explicitly.（**独立测试**：使用 mock 的守卫和循环启动协作者创建激活器，调用 `activate()`，验证会显式报告激活和阻断结果。）

### Tests for User Story 1（用户故事 1 的测试）

- [X] T008 [P] [US1] Add unit tests for guarded activation success and blocked activation in `tests/application/evolution/test_activator.py`（[P] [US1] 在 `tests/application/evolution/test_activator.py` 中添加守卫激活成功与阻断激活的单元测试）
- [X] T009 [P] [US1] Add unit tests for single-start / no-duplicate-worker protection in `tests/application/evolution/test_activator.py`（[P] [US1] 在 `tests/application/evolution/test_activator.py` 中添加单次启动 / 不重复 worker 保护的单元测试）

### Implementation for User Story 1（用户故事 1 的实现）

- [X] T010 Implement `EvolutionActivator.activate()` and explicit activation result handling in `application/evolution/activator.py`（在 `application/evolution/activator.py` 中实现 `EvolutionActivator.activate()` 和显式激活结果处理）
- [X] T011 Implement activation guard evaluation and blocked-reason propagation in `application/evolution/activator.py` using the foundational runtime state types（在 `application/evolution/activator.py` 中使用基础运行时状态类型实现激活守卫评估与阻断原因传播）
- [X] T012 Implement loop-start coordination with concurrency/session exclusivity checks in `application/evolution/activator.py`（在 `application/evolution/activator.py` 中实现循环启动协调与并发/session 排他检查）

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently（**检查点**：到这里，用户故事 1 应已完全可用并可独立测试）

---

## Phase 4: User Story 2 - Detect unhealthy evolution runtime (Priority: P2)（阶段 4：用户故事 2 - 检测不健康的演化运行时（优先级：P2））

**Goal**: Add health monitoring, bounded retries, and degraded-state transitions so transient failures are retried while persistent failures pause evolution safely.（**目标**：添加健康监控、有界重试和降级态迁移，使瞬时失败可被重试，而持续失败会安全地暂停自进化。）

**Independent Test**: Stub the health-check collaborator and retry policy, simulate transient and persistent failures, and verify retry exhaustion and degraded transitions.（**独立测试**：stub 健康检查协作者和重试策略，模拟瞬时与持续失败，并验证重试耗尽和降级迁移。）

### Tests for User Story 2（用户故事 2 的测试）

- [X] T013 [P] [US2] Add unit tests for transient failure retry behavior in `tests/application/evolution/test_activator.py`（[P] [US2] 在 `tests/application/evolution/test_activator.py` 中添加瞬时失败重试行为单元测试）
- [X] T014 [P] [US2] Add unit tests for persistent failure degrading activation in `tests/application/evolution/test_activator.py`（[P] [US2] 在 `tests/application/evolution/test_activator.py` 中添加持续失败导致降级激活的单元测试）
- [X] T015 [P] [US2] Add unit tests for health-state updates and reason codes in `tests/application/evolution/test_activator.py`（[P] [US2] 在 `tests/application/evolution/test_activator.py` 中添加健康状态更新和原因码的单元测试）

### Implementation for User Story 2（用户故事 2 的实现）

- [X] T016 Implement health-check orchestration and runtime health snapshot updates in `application/evolution/activator.py`（在 `application/evolution/activator.py` 中实现健康检查编排与运行时健康快照更新）
- [X] T017 Implement bounded retry with configurable backoff in `infrastructure/evolution/adapters/retry_policy.py` and wire it into `application/evolution/activator.py`（在 `infrastructure/evolution/adapters/retry_policy.py` 中实现带可配置退避的有界重试，并接入 `application/evolution/activator.py`）
- [X] T018 Implement degraded-state transition logic in `domain/evolution/runtime_state.py` and update activator state transitions accordingly（在 `domain/evolution/runtime_state.py` 中实现降级态迁移逻辑，并相应更新激活器状态迁移）

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently（**检查点**：到这里，用户故事 1 和 2 都应可独立工作）

---

## Phase 5: User Story 3 - Recover from degraded mode (Priority: P3)（阶段 5：用户故事 3 - 从降级态恢复（优先级：P3））

**Goal**: Allow the activator to recover from degraded mode once guards and health checks pass again, without spawning duplicate workers or bypassing guard validation.（**目标**：允许激活器在守卫和健康检查再次通过时从降级态恢复，同时不产生重复 worker，也不绕过守卫校验。）

**Independent Test**: Simulate a degraded activator, flip dependencies back to healthy, retry activation, and verify recovery resumes the loop without duplicate workers.（**独立测试**：模拟降级态激活器，将依赖切回健康，重试激活，并验证恢复会在不产生重复 worker 的情况下恢复循环。）

### Tests for User Story 3（用户故事 3 的测试）

- [X] T019 [P] [US3] Add unit tests for recovery from degraded mode in `tests/application/evolution/test_activator.py`（[P] [US3] 在 `tests/application/evolution/test_activator.py` 中添加从降级态恢复的单元测试）
- [X] T020 [P] [US3] Add unit tests for recovery guard revalidation and exclusivity protection in `tests/application/evolution/test_activator.py`（[P] [US3] 在 `tests/application/evolution/test_activator.py` 中添加恢复时的守卫重新校验和排他保护单元测试）

### Implementation for User Story 3（用户故事 3 的实现）

- [X] T021 Implement recovery transitions from degraded to active/recovering states in `application/evolution/activator.py`（在 `application/evolution/activator.py` 中实现从降级到激活/恢复状态的迁移）
- [X] T022 Revalidate guards and health checks during recovery in `application/evolution/activator.py` before resuming the loop（在 `application/evolution/activator.py` 中于恢复时重新校验守卫和健康检查后再恢复循环）
- [X] T023 Preserve explicit observability for recovery success/failure reasons in `domain/evolution/runtime_state.py` and `application/evolution/activator.py`（在 `domain/evolution/runtime_state.py` 和 `application/evolution/activator.py` 中保留恢复成功/失败原因的显式可观测性）

**Checkpoint**: All user stories should now be independently functional（**检查点**：所有用户故事现在都应可独立运行）

---

## Phase 6: Polish & Cross-Cutting Concerns（阶段 6：润色与跨切关注点）

**Purpose**: Improvements that affect multiple user stories（**目的**：影响多个用户故事的改进）

- [X] T024 [P] Update `specs/20260518-143022-evolution-activator/quickstart.md` with a minimal activation/recovery verification flow（[P] 更新 `specs/20260518-143022-evolution-activator/quickstart.md`，补充最小激活/恢复验证流程）
- [X] T025 [P] Add or update `specs/20260518-143022-evolution-activator/data-model.md` to document activation, health, retry, and degradation entities（[P] 新增或更新 `specs/20260518-143022-evolution-activator/data-model.md`，记录激活、健康、重试和降级实体）
- [X] T026 [P] Add or update `specs/20260518-143022-evolution-activator/contracts/` with any explicit lifecycle or interface contracts needed for observability and testing（[P] 新增或更新 `specs/20260518-143022-evolution-activator/contracts/`，补充可观测性和测试所需的生命周期或接口契约）
- [X] T027 Run targeted lint and unit tests for `application/evolution/activator.py`, `domain/evolution/runtime_state.py`, and `tests/application/evolution/test_activator.py`（运行针对 `application/evolution/activator.py`、`domain/evolution/runtime_state.py` 和 `tests/application/evolution/test_activator.py` 的定向 lint 与单元测试）
- [X] T028 Validate that `application/evolution/activator.py` remains a thin orchestration boundary aligned with `.cursor/rules/sprintcycle-architecture-orchestration.mdc` and `.cursor/rules/langgraph-orchestration.mdc`（验证 `application/evolution/activator.py` 仍然是与 `.cursor/rules/sprintcycle-architecture-orchestration.mdc` 和 `.cursor/rules/langgraph-orchestration.mdc` 对齐的薄编排边界）

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
- Models or runtime state types before services/activators（先模型或运行时状态类型，后 service/activator）
- Services/activator before integration or recovery wiring（先 service/activator，后集成或恢复接线）
- Core implementation before cross-cutting polish（先核心实现，后跨切润色）
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
