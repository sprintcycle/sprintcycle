---

description: "Task list template for feature implementation"（功能实现任务列表模板）
---

# Tasks: [FEATURE NAME]（任务：[FEATURE NAME]）

**Input**: Design documents from `/specs/[###-feature-name]/`（输入：来自 `/specs/[###-feature-name]/` 的设计文档）

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

- [ ] T001 Create project structure per implementation plan（按实现计划创建项目结构）
- [ ] T002 Initialize [language] project with [framework] dependencies（使用 [framework] 依赖初始化 [language] 项目）
- [ ] T003 [P] Configure linting and formatting tools（[P] 配置 lint 和格式化工具）

---

## Phase 2: Foundational (Blocking Prerequisites)（阶段 2：基础层（阻塞性前置条件））

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented（**目的**：在实现任何用户故事之前必须完成的核心基础设施）

**⚠️ CRITICAL**: No user story work can begin until this phase is complete（**⚠️ 关键**：在本阶段完成前，不能开始任何用户故事工作）

Examples of foundational tasks (adjust based on your project):（基础任务示例（请根据项目调整）：）

- [ ] T004 Setup database schema and migrations framework（搭建数据库 schema 和迁移框架）
- [ ] T005 [P] Implement authentication/authorization framework（[P] 实现认证/授权框架）
- [ ] T006 [P] Setup API routing and middleware structure（[P] 搭建 API 路由与中间件结构）
- [ ] T007 Create base models/entities that all stories depend on（创建所有故事都依赖的基础模型/实体）
- [ ] T008 Configure error handling and logging infrastructure（配置错误处理与日志基础设施）
- [ ] T009 Setup environment configuration management（搭建环境配置管理）

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel（**检查点**：基础能力已就绪——现在可以并行开始用户故事实现）

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP（阶段 3：用户故事 1 - [标题]（优先级：P1）🎯 MVP）

**Goal**: [Brief description of what this story delivers]（**目标**：[简述该故事交付的内容]）

**Independent Test**: [How to verify this story works on its own]（**独立测试**：[如何验证该故事可独立工作]）

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️（用户故事 1 的测试（可选——仅在要求测试时添加）⚠️）

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**（> **注意：请先编写这些测试，确保在实现前它们会失败**）

- [ ] T010 [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py（[P] [US1] 在 tests/contract/test_[name].py 中编写 [endpoint] 的契约测试）
- [ ] T011 [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py（[P] [US1] 在 tests/integration/test_[name].py 中编写 [user journey] 的集成测试）

### Implementation for User Story 1（用户故事 1 的实现）

- [ ] T012 [P] [US1] Create [Entity1] model in src/models/[entity1].py（[P] [US1] 在 src/models/[entity1].py 中创建 [Entity1] 模型）
- [ ] T013 [P] [US1] Create [Entity2] model in src/models/[entity2].py（[P] [US1] 在 src/models/[entity2].py 中创建 [Entity2] 模型）
- [ ] T014 [US1] Implement [Service] in src/services/[service].py (depends on T012, T013)（[US1] 在 src/services/[service].py 中实现 [Service]（依赖 T012、T013））
- [ ] T015 [US1] Implement [endpoint/feature] in src/[location]/[file].py（[US1] 在 src/[location]/[file].py 中实现 [endpoint/feature]）
- [ ] T016 [US1] Add validation and error handling（[US1] 添加校验与错误处理）
- [ ] T017 [US1] Add logging for user story 1 operations（[US1] 为用户故事 1 的操作添加日志）

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently（**检查点**：到这里，用户故事 1 应已完全可用并可独立测试）

---

## Phase 4: User Story 2 - [Title] (Priority: P2)（阶段 4：用户故事 2 - [标题]（优先级：P2））

**Goal**: [Brief description of what this story delivers]（**目标**：[简述该故事交付的内容]）

**Independent Test**: [How to verify this story works on its own]（**独立测试**：[如何验证该故事可独立工作]）

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️（用户故事 2 的测试（可选——仅在要求测试时添加）⚠️）

- [ ] T018 [P] [US2] Contract test for [endpoint] in tests/contract/test_[name].py（[P] [US2] 在 tests/contract/test_[name].py 中编写 [endpoint] 的契约测试）
- [ ] T019 [P] [US2] Integration test for [user journey] in tests/integration/test_[name].py（[P] [US2] 在 tests/integration/test_[name].py 中编写 [user journey] 的集成测试）

### Implementation for User Story 2（用户故事 2 的实现）

- [ ] T020 [P] [US2] Create [Entity] model in src/models/[entity].py（[P] [US2] 在 src/models/[entity].py 中创建 [Entity] 模型）
- [ ] T021 [US2] Implement [Service] in src/services/[service].py（[US2] 在 src/services/[service].py 中实现 [Service]）
- [ ] T022 [US2] Implement [endpoint/feature] in src/[location]/[file].py（[US2] 在 src/[location]/[file].py 中实现 [endpoint/feature]）
- [ ] T023 [US2] Integrate with User Story 1 components (if needed)（[US2] 如有需要，与用户故事 1 的组件集成）

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently（**检查点**：到这里，用户故事 1 和 2 都应可独立工作）

---

## Phase 5: User Story 3 - [Title] (Priority: P3)（阶段 5：用户故事 3 - [标题]（优先级：P3））

**Goal**: [Brief description of what this story delivers]（**目标**：[简述该故事交付的内容]）

**Independent Test**: [How to verify this story works on its own]（**独立测试**：[如何验证该故事可独立工作]）

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️（用户故事 3 的测试（可选——仅在要求测试时添加）⚠️）

- [ ] T024 [P] [US3] Contract test for [endpoint] in tests/contract/test_[name].py（[P] [US3] 在 tests/contract/test_[name].py 中编写 [endpoint] 的契约测试）
- [ ] T025 [P] [US3] Integration test for [user journey] in tests/integration/test_[name].py（[P] [US3] 在 tests/integration/test_[name].py 中编写 [user journey] 的集成测试）

### Implementation for User Story 3（用户故事 3 的实现）

- [ ] T026 [P] [US3] Create [Entity] model in src/models/[entity].py（[P] [US3] 在 src/models/[entity].py 中创建 [Entity] 模型）
- [ ] T027 [US3] Implement [Service] in src/services/[service].py（[US3] 在 src/services/[service].py 中实现 [Service]）
- [ ] T028 [US3] Implement [endpoint/feature] in src/[location]/[file].py（[US3] 在 src/[location]/[file].py 中实现 [endpoint/feature]）

**Checkpoint**: All user stories should now be independently functional（**检查点**：所有用户故事现在都应可独立运行）

---

[Add more user story phases as needed, following the same pattern]（如有需要，可按相同模式继续添加更多用户故事阶段）

---

## Phase N: Polish & Cross-Cutting Concerns（阶段 N：润色与跨切关注点）

**Purpose**: Improvements that affect multiple user stories（**目的**：影响多个用户故事的改进）

- [ ] TXXX [P] Documentation updates in docs/（[P] 更新 docs/ 中的文档）
- [ ] TXXX Code cleanup and refactoring（代码清理与重构）
- [ ] TXXX Performance optimization across all stories（跨所有故事的性能优化）
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/（[P] 如有需要，在 tests/unit/ 中补充单元测试）
- [ ] TXXX Security hardening（安全加固）
- [ ] TXXX Run quickstart.md validation（运行 quickstart.md 验证）

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
