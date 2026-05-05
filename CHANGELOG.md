## [Unreleased]

### Features
- V4.0：`require_knowledge_injection_confirm` / `persist_sprint_knowledge_cards`（`[behavior]` + `SPRINTCYCLE_*`）；`KnowledgeInjector.inject_for_sprint(..., persist_overlay=False)` 预览；`RunResult.pending_knowledge_confirmation`；CLI `run --yes`；MCP `confirm_knowledge`
- V4.0：Coder 任务按 `max_verify_fix_rounds` 验证-修复重试；单 Sprint 锁定 `_sprint_coding_engine`；Sprint 结束可选写入 `knowledge_cards`（`sprint_knowledge_card.persist_sprint_outcome_card`）
- docs: `docs/EXTENSION_POINTS.md`（Authlib / Helm / 审计等企业能力接入位，无默认实现）
- config: `quality_profile`（off/fast/default/strict）与 `RuntimeConfig.effective_quality_level()`（V4.0 §6.3）；`sprintcycle.toml` `[quality] profile`
- evolution: `EvolutionPipeline.execute_async` 在有 `RuntimeConfig` 时委托 `TaskDispatcher`；`evolve_sprint` 供 `SprintExecutor` 进化模式调用（§6.2）
- agents: `EvolutionPath` 枚举（保留 `EvolutionStrategy` 别名，§6.7）
- ci: 校验 `docs-dev/dev-setup.sh` 存在；独立 **`architecture-gate`** job（import-linter）；可选 `mutation.yml` + `semgrep.yml`；`pyproject` `[mutation]`、`dev` 含 **hypothesis**
- g4: `tests/test_g4_properties.py`（Hypothesis）；import-linter 增加 **prd** / **execution** 不得依赖 `dashboard`

### Documentation
- docs: V4.0 canonical entry `docs/PRODUCT_TECH_V4.md`；README 真理源；`SPRINTCYCLE_PRODUCT_TECH_PLAN.md` 顶栏；`evolution/pipeline`、`scheduler/dispatcher`、`config/quality` 与 G1–G4 说明

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
