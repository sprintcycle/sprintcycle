---
description: "Task list for Multi-Dimension Fitness feature"（多维度 Fitness 功能任务列表）
---

# Tasks: Multi-Dimension Fitness（任务：多维度 Fitness）

**Input**: Design documents from `/specs/001-fitness-multi-dimension/`（输入：来自 `/specs/001-fitness-multi-dimension/` 的设计文档）

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/（前置条件：plan.md（必需）、spec.md（用户故事必需）、research.md、data-model.md、contracts/）

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.（**测试**：下面示例包含测试任务。测试为可选项——仅在功能规格明确要求时才包含。）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.（**组织方式**：任务按用户故事分组，以便每个故事都能独立实现和独立测试。）

## Format: `[ID] [P?] [Story] Description`（格式：`[ID] [P?] [Story] 描述`）

- **[P]**: Can run in parallel (different files, no dependencies)（**[P]**：可并行执行（不同文件、无依赖））
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)（**[Story]**：该任务所属的用户故事（例如 US1、US2、US3））
- Include exact file paths in descriptions（描述中需包含精确文件路径）

## Path Conventions（路径约定）

- **Single project**: `src/`, `tests/` at repository root（**单项目**：仓库根目录下的 `src/`、`tests/`）
- **Web app**: `backend/src/`, `frontend/src/`（**Web 应用**：`backend/src/`、`frontend/src/`）
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`（**移动端**：`api/src/`、`ios/src/` 或 `android/src/`）
- Paths shown below assume single project - adjust based on plan.md structure（下方路径示例默认按单项目结构编写——请根据 plan.md 的结构进行调整）

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->
<!--
  ============================================================================
  重要：以下任务仅用于示例说明。

  /speckit-tasks 命令必须基于以下内容替换为真实任务：
  - 来自 spec.md 的用户故事（含优先级 P1、P2、P3...）
  - 来自 plan.md 的功能需求
  - 来自 data-model.md 的实体
  - 来自 contracts/ 的端点

  任务必须按用户故事组织，以便每个故事都可以：
  - 独立实现
  - 独立测试
  - 作为一个 MVP 增量交付

  不要将这些示例任务保留在生成的 tasks.md 文件中。
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)（阶段 1：初始化（共享基础设施））

**Purpose**: Project initialization and basic structure（**目的**：项目初始化与基础结构搭建）

- [ ] T001 Create `sprintcycle/domain/fitness/` package structure and update `sprintcycle/domain/fitness/__init__.py`（创建 `sprintcycle/domain/fitness/` 包结构并更新 `sprintcycle/domain/fitness/__init__.py`）
- [ ] T002 Define `DimensionScore`, `FitnessResult`, and related typing contracts in `sprintcycle/domain/fitness/multi_dimension.py`, including `FitnessResult.to_dict()` serialization（在 `sprintcycle/domain/fitness/multi_dimension.py` 中定义 `DimensionScore`、`FitnessResult` 及相关类型契约，并包含 `FitnessResult.to_dict()` 序列化）
- [ ] T003 [P] Add async test scaffolding under `tests/domain/fitness/` for multi-dimension evaluation（[P] 在 `tests/domain/fitness/` 下添加多维评估的异步测试脚手架）

---

## Phase 2: Foundational (Blocking Prerequisites)（阶段 2：基础层（阻塞性前置条件））

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented（**目的**：在实现任何用户故事之前必须完成的核心基础设施）

**⚠️ CRITICAL**: No user story work can begin until this phase is complete（**⚠️ 关键**：在本阶段完成前，不能开始任何用户故事工作）

- [ ] T004 Create the `MultiDimensionFitness` coordinator class in `sprintcycle/domain/fitness/multi_dimension.py`（在 `sprintcycle/domain/fitness/multi_dimension.py` 中创建 `MultiDimensionFitness` 协调类）
- [ ] T005 [P] Add configurable default weights and pass threshold constants in the fitness domain module（[P] 在 fitness 领域模块中添加可配置默认权重和通过阈值常量）
- [ ] T006 [P] Establish adapter injection points for `ruff`, `bandit`, `import-linter`, `mypy`, `coverage`, `maintainability`, and `performance` checks（[P] 为 `ruff`、`bandit`、`import-linter`、`mypy`、`coverage`、`maintainability` 和 `performance` 检查建立适配器注入点）
- [ ] T007 Define a result aggregation shape that preserves per-dimension scores, weights, details, and suggestions（定义一个结果聚合结构，保留每个维度的分数、权重、明细和建议）
- [ ] T008 [P] Add adapter stub fixtures for async orchestration tests（[P] 为异步编排测试添加适配器 stub fixture）

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel（**检查点**：基础能力已就绪——现在可以并行开始用户故事实现）

---

## Phase 3: User Story 1 - Unified fitness evaluation (Priority: P1)（阶段 3：用户故事 1 - 统一 Fitness 评估（优先级：P1））

**Goal**: Expose one callable entry point that returns weighted total score, per-dimension breakdown, and pass/fail status.（**目标**：暴露一个可调用入口，返回加权总分、维度明细和通过/失败状态。）

**Independent Test**: Run evaluation against a sample project and verify the payload contains all seven dimensions plus the weighted total and pass flag.（**独立测试**：对示例项目运行评估，验证结果包含全部七个维度、加权总分和通过标记。）

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️（用户故事 1 的测试（可选——仅在要求测试时添加）⚠️）

- [ ] T009 [P] [US1] Add unit tests for total score computation and pass/fail threshold in `tests/domain/fitness/test_multi_dimension.py`（[P] [US1] 在 `tests/domain/fitness/test_multi_dimension.py` 中添加总分计算和通过/失败阈值的单元测试）
- [ ] T010 [P] [US1] Add unit tests for per-dimension score packaging in `tests/domain/fitness/test_multi_dimension.py`（[P] [US1] 在 `tests/domain/fitness/test_multi_dimension.py` 中添加维度分数封装的单元测试）

### Implementation for User Story 1（用户故事 1 的实现）

- [ ] T011 [US1] Implement weighted score aggregation logic in `sprintcycle/domain/fitness/multi_dimension.py`（[US1] 在 `sprintcycle/domain/fitness/multi_dimension.py` 中实现加权分数聚合逻辑）
- [ ] T012 [US1] Add evaluation payload assembly with `total`, `dimensions`, and `passed` fields in `sprintcycle/domain/fitness/multi_dimension.py`（[US1] 在 `sprintcycle/domain/fitness/multi_dimension.py` 中添加包含 `total`、`dimensions` 和 `passed` 字段的评估结果组装）
- [ ] T013 [US1] Ensure default weights and threshold are applied when configuration is omitted（[US1] 确保在未提供配置时应用默认权重和阈值）

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently（**检查点**：到这里，用户故事 1 应已完全可用并可独立测试）

---

## Phase 4: User Story 2 - Orchestrate multi-tool checks (Priority: P2)（阶段 4：用户故事 2 - 编排多工具检查（优先级：P2））

**Goal**: Coordinate the underlying quality and governance adapters so their results are gathered through one async flow.（**目标**：协调底层质量与治理适配器，使结果通过一个异步流程收集。）

**Independent Test**: Stub each adapter and verify evaluation invokes every configured dimension check and aggregates partial results when possible.（**独立测试**：为每个适配器做 stub，验证评估会调用每个配置的维度检查，并在可能时聚合部分结果。）

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️（用户故事 2 的测试（可选——仅在要求测试时添加）⚠️）

- [ ] T014 [P] [US2] Add async orchestration tests for adapter invocation order and parallel execution in `tests/domain/fitness/test_multi_dimension.py`（[P] [US2] 在 `tests/domain/fitness/test_multi_dimension.py` 中添加适配器调用顺序和并发执行的异步编排测试）
- [ ] T015 [P] [US2] Add partial-failure tests for unavailable adapters and timeout handling（[P] [US2] 添加适配器不可用和超时处理的部分失败测试）

### Implementation for User Story 2（用户故事 2 的实现）

- [ ] T016 [US2] Implement async orchestration over all configured dimensions inside `MultiDimensionFitness.evaluate()`（[US2] 在 `MultiDimensionFitness.evaluate()` 中实现对全部配置维度的异步编排）
- [ ] T017 [US2] Add adapter result normalization so each dimension check returns a consistent numeric score and metadata payload（[US2] 添加适配器结果归一化，使每个维度检查返回一致的数值分数和元数据载荷）
- [ ] T018 [US2] Preserve per-dimension failure details without blocking remaining dimension evaluations when feasible（[US2] 在可行时保留每个维度的失败细节，而不阻塞其余维度的评估）

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently（**检查点**：到这里，用户故事 1 和 2 都应可独立工作）

---

## Phase 5: User Story 3 - Provide governance suggestions (Priority: P3)（阶段 5：用户故事 3 - 提供治理建议（优先级：P3））

**Goal**: Attach remediation-oriented governance suggestions to the evaluation result when one or more dimensions underperform.（**目标**：当一个或多个维度表现不足时，将面向修复的治理建议附加到评估结果中。）

**Independent Test**: Verify suggestions are emitted for under-threshold dimensions and remain empty when all dimensions pass cleanly.（**独立测试**：验证低于阈值的维度会输出建议，而当所有维度都通过时建议保持为空。）

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️（用户故事 3 的测试（可选——仅在要求测试时添加）⚠️）

- [ ] T019 [P] [US3] Add suggestion-generation tests for failing dimensions in `tests/domain/fitness/test_multi_dimension.py`（[P] [US3] 在 `tests/domain/fitness/test_multi_dimension.py` 中添加失败维度的建议生成测试）
- [ ] T020 [P] [US3] Add empty-suggestion tests for fully passing evaluations（[P] [US3] 添加全部通过时建议为空的测试）

### Implementation for User Story 3（用户故事 3 的实现）

- [ ] T021 [US3] Implement suggestion assembly for failing and warning dimensions in `sprintcycle/domain/fitness/multi_dimension.py`（[US3] 在 `sprintcycle/domain/fitness/multi_dimension.py` 中实现对失败与警告维度的建议组装）
- [ ] T022 [US3] Add remediation hints that identify the highest-priority dimensions to fix first（[US3] 添加可识别优先修复维度的治理提示）
- [ ] T023 [US3] Ensure suggestions are returned as part of the evaluation payload rather than side effects（[US3] 确保建议作为评估结果的一部分返回，而不是副作用）

**Checkpoint**: All user stories should now be independently functional（**检查点**：所有用户故事现在都应可独立运行）

---

## Phase 6: Polish & Cross-Cutting Concerns（阶段 6：润色与跨切关注点）

**Purpose**: Improvements that affect multiple user stories（**目的**：影响多个用户故事的改进）

- [ ] T024 [P] Update module exports in `sprintcycle/domain/fitness/__init__.py` for the new fitness API（[P] 更新 `sprintcycle/domain/fitness/__init__.py` 中的新 fitness API 导出）
- [ ] T025 [P] Add or refine documentation strings for the multi-dimension fitness coordinator and entities（[P] 为多维 Fitness 协调器和实体补充或优化文档字符串）
- [ ] T026 Run and verify async unit tests for `tests/domain/fitness/`（运行并验证 `tests/domain/fitness/` 的异步单元测试）
- [ ] T027 Validate lint/type checks for modified fitness domain files（验证修改过的 fitness 领域文件的 lint/type 检查）
- [ ] T028 Confirm governance and architecture boundaries remain unchanged after integration（确认集成后治理和架构边界保持不变）

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
- Models before services（先模型，后服务）
- Services before endpoints（先服务，后端点）
- Core implementation before integration（先核心实现，后集成）
- Story complete before moving to next priority（完成当前故事后再进入下一个优先级）

### Parallel Opportunities（并行机会）

- All Setup tasks marked [P] can run in parallel（所有标记为 [P] 的初始化任务可并行执行）
- All Foundational tasks marked [P] can run in parallel (within Phase 2)（所有标记为 [P] 的基础任务可并行执行（在阶段 2 内））
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)（基础层完成后，所有用户故事可并行启动（如果团队能力允许））
- All tests for a user story marked [P] can run in parallel（同一用户故事中所有标记为 [P] 的测试可并行执行）
- Models within a story marked [P] can run in parallel（同一故事中标记为 [P] 的模型任务可并行执行）
- Different user stories can be worked on in parallel by different team members（不同用户故事可由不同团队成员并行推进）

---

## Parallel Example: User Story 1（并行示例：用户故事 1）

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Add unit tests for total score computation and pass/fail threshold in `tests/domain/fitness/test_multi_dimension.py`"
Task: "Add unit tests for per-dimension score packaging in `tests/domain/fitness/test_multi_dimension.py`"

# Launch all models for User Story 1 together:
Task: "Implement weighted score aggregation logic in `sprintcycle/domain/fitness/multi_dimension.py`"
Task: "Add evaluation payload assembly with `total`, `dimensions`, and `passed` fields in `sprintcycle/domain/fitness/multi_dimension.py`"
```

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
