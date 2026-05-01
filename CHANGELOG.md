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
