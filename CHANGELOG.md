## [Unreleased]

### Breaking / 命名收敛
- **`ManualPRDSource`**：默认扫描目录由项目根下 **`prd/`** 改为 **`release_plan/`**；构造参数由 **`prd_dir`** 改为 **`plan_subdir`**（默认 ``"release_plan"``）。使用进化管道且依赖磁盘 YAML 的项目请将计划文件迁入 **`release_plan/*.yaml`** 或传入自定义子路径。
- 知识注入落盘文件：**`prd_overlay.yaml` → `release_plan_overlay.yaml`**（项目根；`KnowledgeInjector` 常量 `RELEASE_PLAN_OVERLAY_FILENAME`）。
- 知识注入运行时上下文：**`prd_overlay_yaml` → `release_plan_overlay_yaml`**、**`prd_overlay_written` → `release_plan_overlay_written`**；Coder / Cookbook 路径 **`codebase_context["prd_overlay"]` → `["release_plan_overlay"]`**；**`prd_overlay_hint` → `release_plan_overlay_hint`**（`build_cookbook_body` / `run_cursor_cookbook_flow`）。
- 包与模块路径（Scrum 对等工程名）：**`sprintcycle.prd` → `sprintcycle.release_plan`**；**`orchestration/dispatcher.py` → `sprint_orchestrator.py`**；**`evolution/prd_source.py` → `evolution_plan_source.py`**；**`evolution/prd_adapter.py` → `release_plan_adapter.py`**；**`diagnostic/prd_*.py` → `release_plan_*.py`**；**`execution/task_splitter.py` → `work_item_splitter.py`**（`TaskSplitter`/`Task` → **`WorkItemSplitter`** / **`IntentWorkItem`**）；对应测试文件已改名
- 移除 `sprintcycle.scheduler` 包；统一自 **`SprintOrchestrator`**（`from sprintcycle.orchestration.sprint_orchestrator import …` 或 `from sprintcycle import SprintOrchestrator`）
- `SprintCycle.dispatcher` → **`orchestrator`**（`SprintOrchestrator` 实例）
- `TaskResult.task` → **`work_item`**（`PRDTask`）；`TaskResult.to_dict` 与事件负载使用 **`description`**；`create_event(..., description=…)`（不再使用 `task` 参数名）
- `PRDParser`：Sprint Backlog 项 **仅**接受 YAML 键 **`description`**（不再接受 `task` / `name`）
- 移除 **`DeliveryMode`** 与 **`delivery_mode_to_execution_mode`**（`release_plan.models`、`scrum`、根包导出）
- `execution` 包不再导出 **`TaskStatus`**（请使用 `ExecutionStatus`）

### Features
- P1 Scrum：`scrum` 根包导出；CLI/MCP/Dashboard「执行计划」话术；`SprintResult`/`TaskResult` Scrum docstring（`docs/DESIGN_SCRUM_NAMING_MIGRATION.md`）
- V4.0：`require_knowledge_injection_confirm` / `persist_sprint_knowledge_cards`（`[behavior]` + `SPRINTCYCLE_*`）；`KnowledgeInjector.inject_for_sprint(..., persist_overlay=False)` 预览；`RunResult.pending_knowledge_confirmation`；CLI `run --yes`；MCP `confirm_knowledge`
- V4.0：Coder 任务按 `max_verify_fix_rounds` 验证-修复重试；单 Sprint 锁定 `_sprint_coding_engine`；Sprint 结束可选写入 `knowledge_cards`（`sprint_knowledge_card.persist_sprint_outcome_card`）
- docs: `docs/EXTENSION_POINTS.md`（Authlib / Helm / 审计等企业能力接入位，无默认实现）
- config: `quality_profile`（off/fast/default/strict）与 `RuntimeConfig.effective_quality_level()`（V4.0 §6.3）；`sprintcycle.toml` `[quality] profile`
- evolution: `EvolutionPipeline.execute_async` 在有 `RuntimeConfig` 时委托 `SprintOrchestrator`；`evolve_sprint` 供 `SprintExecutor` 进化模式调用（§6.2）
- agents: `EvolutionPath` 枚举（保留 `EvolutionStrategy` 别名，§6.7）
- ci: 校验 `docs-dev/dev-setup.sh` 存在；独立 **`architecture-gate`** job（import-linter）；可选 `mutation.yml` + `semgrep.yml`；`pyproject` `[mutation]`、`dev` 含 **hypothesis**
- g4: `tests/test_g4_properties.py`（Hypothesis）；import-linter 增加 **release_plan** / **execution** 不得依赖 `dashboard`

### Documentation
- docs: V4.0 canonical entry `docs/PRODUCT_TECH_V4.md`；README 真理源；`SPRINTCYCLE_PRODUCT_TECH_PLAN.md` 顶栏；`evolution/pipeline`、`orchestration/sprint_orchestrator`、`config/quality` 与 G1–G4 说明

## [v0.9.2] - 2025-12-20

### Features
- feat: integration tests for CLI/MCP/API/Dashboard entry points
- feat: Dashboard frontend enhancement - PRD editor, execution history, diagnostics, live events
- feat: EventBus→SSE real-time execution progress streaming
- feat: MCP SSE transport mode for remote agent access
- feat: end-to-end resume support - reconnect api to SprintExecutor
- feat: P2 - Dashboard (FastAPI + SSE + Web UI)
- feat: P1 - stop/resume/status enhancement
- feat: unified SprintCycle API + refactored CLI & MCP entry points
- feat: Phase 5 - persist sprint results to StateStore + task execution logging
- feat: Phase 4 - differentiated evolution strategies + full task chain in evolution mode
- feat: add RegressionTestAgent for Step 5.5 regression testing
- feat: add ArchitectureAgent for Step 5.1 architecture design
- feat: add MCP Server entry point
- feat: close FeedbackLoop + remove Step7 empty shell
- feat: Phase 15 - evolution report and skill self-iteration
- feat: P0.7 - Config桥接 - 5个小Config新增from_runtime_config工厂方法
- feat: P1+P2 - 补测试、异常体系、pyproject.toml、消灭type:ignore

### Refactors
- refactor: consolidate TextContent type:ignore into helper, restore 21/21 validation
- refactor: Phase 1-4 architecture optimization
- refactor: Phase 1-4 architecture optimization
- refactor: Phase 12 - architecture optimization
- refactor: Phase 11 - code quality
- refactor: P0.6 - Config精简 - LLMProviderConfig合并进LLMConfig, EvolutionConfig→RollbackConfig
- refactor: P0.5 - 移除GEPA/Hermes/Pareto全部残留

### Bug Fixes
- fix: Phase 1 - Fix import errors and test failures

### Tests
- test: Phase 13 - end-to-end integration verification
- test: Phase 10 - improve coverage
- test: Phase 4 - Add tests for agents, bug_models, patterns, and prd_generator modules
- test: Phase 4 - Add integrations and diagnostic tests

### Documentation
- docs: Phase 15 - evolution report and skill self-iteration

### Chores
- chore: Phase 14 - rollback fallback (N/A)

# Changelog

All notable project changes will be documented in this file.

## [v0.6.0] - 2025-04-29

### Architecture Upgrade
- **Plan A**: Evolution becomes Sprint enhancement capability
- `EvolutionEngine.evolve_sprint()`: Evolve Sprint targets
- `SprintExecutor` supports Normal and Evolution modes

### New Features
- `evolve_sprint()`: Multi-generation evolution with target extraction
- `execute_sprints(mode="normal"|"evolution")`: Dual-mode execution
- `set_evolution_engine()`: Inject EvolutionEngine
- `_convert_evolution_result()`: Result format conversion

### Refactoring
- Agent tasks simplified to placeholder implementations
- Code organization improvements

---

## [v0.5.0] - 2025-04-28

### Initial Release
- PRD module: PRDDraft, PRD, PRDSprint, PRDTask
- Intent module: Intent parsing and task routing
- Execution module: Sprint executor with parallel/serial support
- Config module: Multi-provider configuration
- Coding module: Code generation engine
- Evolution module: Self-evolution engine (GEPA)
