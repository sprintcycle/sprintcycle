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
