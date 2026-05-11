# SprintCycle

[中文](README.md)

**SprintCycle** is a web / CLI / MCP / SDK orchestration framework: describe intent in natural language, generate an executable Release Plan, and drive planning, execution, observation, repair, delivery, runtime linkage, governance, and self-evolution through a unified lifecycle contract.

Current Version: **0.9.2** (matches `sprintcycle.__version__`)

---

## Core Positioning

SprintCycle is not just a task runner. It is an end-to-end lifecycle orchestration platform that covers the following closed loop:

1. Intent intake and normalization
2. Plan generation and validation
3. Task decomposition and execution preparation
4. Sprint execution and event recording
5. Observation, diagnosis, and repair loop
6. Delivery and runtime linkage
7. Governance review and suggestion handling
8. Version promotion and self-evolution

The current implementation centers on the `SprintCycle` unified entrypoint. Under the hood, workflow services, domain facades, runtime registries, observability, the skills subsystem, and evolution services collaborate to complete the lifecycle.

---

## Key Capabilities

### Intent-Driven Delivery Loop
- Describe goals in natural language
- Generate Release Plans (YAML / structured plans)
- Support sprint orchestration, checkpoint resume, and recovery
- Support normalized lifecycle stage transitions

### Unified Lifecycle Contract
- `LifecycleStateMachine` owns canonical stage transition rules
- `LifecycleContract` carries cross-service state facts
- A unified correlation model links `execution_id`, `task_id`, `suggestion_id`, `runtime_id`, `version_id`, and `trace_id`

### Repair and Delivery Loop
- Explicitly supports `diagnosed → repairing → verifying → observing`
- Explicitly supports `delivering → runtime_linked → governing → promotion_ready → promoted`
- Provides structured artifacts for repair, verification, runtime handoff, and suggestion promotion

### Governance and Suggestion Handling
- Multi-source validation plugin system powered by pluggy
- Architecture contract checks, static analysis, YAML validation, ADR checks, mutation testing, and dependency security scanning
- Suggestion review, approval, rejection, archival, and HITL promotion

### Observability and Runtime
- Execution events, trace, replay, summary, and health read models
- Runtime registry and deployment linkage
- Observation views for Dashboard and API consumers

### Dashboard and Integrations
- Vue 3 + Element Plus web dashboard
- FastAPI backend
- MCP Server over stdio or SSE
- Python API and CLI share the same core entrypoint

### Configuration and Extensibility
- `dynaconf` + `pydantic` configuration stack
- Local cache and Redis backend abstraction
- Reserved extension point for message queues
- Pluggable governance, suggestion, and observability facades

---

## Requirements

- Python **≥ 3.11**

---

## Installation

### Basic Installation

```bash
pip install -e .
```

### Full Installation (Recommended)

```bash
pip install -e "[full,dev]"
```

### Common Extras

| Extra | Purpose |
|------|---------|
| `dashboard` / `full` | Web Dashboard (FastAPI + Uvicorn) |
| `cache-redis` | Redis backend for execution cache |
| `mcp-sse` | Expose MCP over SSE |
| `dev` | Test, type-check, import-linter, and other development dependencies |
| `mutation` | Mutation testing with `mutmut` |

---

## Quick Start

### Initialize Project Data

```bash
sprintcycle init
```

### Generate a Plan Without Executing

```bash
sprintcycle plan "Add unit tests for the login flow" -m auto
```

### Execute Directly

```bash
sprintcycle run "Fix broken links in the README"
# Equivalent to:
sprintcycle "Fix broken links in the README"
```

### Enable Governance Checks

```bash
sprintcycle run "Refactor the configuration module" --governance-level standard
```

### Start the Dashboard

```bash
# Production mode (typically requires a frontend build first)
sprintcycle dashboard

# Development mode (start FastAPI + Vite together)
sprintcycle dashboard --dev
```

---

## Command Reference

### Core Workflow

| Command | Description |
|---------|-------------|
| `sprintcycle wizard` | Interactive selection of plan / run / diagnose / status |
| `sprintcycle plan <intent>` | Generate an execution plan |
| `sprintcycle run [intent]` | Execute a sprint |
| `sprintcycle validate` | Run governance validation |

### Project Management

| Command | Description |
|---------|-------------|
| `sprintcycle diagnose` | Project health analysis |
| `sprintcycle status [execution_id]` | Single execution status or history list |
| `sprintcycle rollback <execution_id>` | Roll back an execution |
| `sprintcycle stop <execution_id>` | Stop a running task |

### Knowledge Management

| Command | Description |
|---------|-------------|
| `sprintcycle knowledge search` | Search knowledge cards |
| `sprintcycle knowledge list` | List all knowledge cards |

### Configuration Management

| Command | Description |
|---------|-------------|
| `sprintcycle config show` | Show the current configuration |
| `sprintcycle config set <key> <value>` | Set a configuration value |
| `sprintcycle config get <key>` | Get a configuration value |

### Services and Integrations

| Command | Description |
|---------|-------------|
| `sprintcycle serve` | Start the MCP Server (stdio by default; use `--transport sse` for remote agents) |
| `sprintcycle dashboard` | Start the web UI |

### System Commands

| Command | Description |
|---------|-------------|
| `sprintcycle init [path]` | Initialize the `.sprintcycle` directory structure |
| `sprintcycle import-state` | Import a JSON state directory into SQLite |

**Global options**: `-p/--project` (project path), `--format text|json` (output format), `-v/--verbose` (verbose logging)

---

## Python API

The Python API and CLI share the same `SprintCycle` entrypoint. `plan`, `run`, `diagnose`, `status`, `rollback`, and `stop` all align semantically with the CLI, making it easy to use in scripts, services, and automation pipelines.

```python
from sprintcycle import SprintCycle

api = SprintCycle(project_path="./my-project")
result = await api.run("Refactor the authentication module")
```

Common exports include:

- `SprintCycle`
- `ReleasePlan`
- `ReleasePlanParser`
- `ReleasePlanValidator`
- `SprintOrchestrator`
- `SprintExecutor`

---

## Repository Structure

```
sprintcycle/
├── api.py                    # Unified API entrypoint
├── cli/                      # CLI package
├── config/                   # Configuration management
├── orchestration/            # Sprint orchestration engine
├── execution/                # Execution engine
├── release_plan/             # Release Plan models and parsing
├── governance/               # Governance engine, plugins, and suggestion handling
├── dashboard/                # Web Dashboard
├── events/                   # Event bus
├── mcp/                      # MCP server
├── runtime_observability/    # Runtime observability and replay
├── cache/                    # Cache abstraction layer
├── mq/                       # Message queue abstraction layer
├── validation/               # Multi-source validation plugin system
└── services/                 # Lifecycle, governance, observability, suggestion, delivery, and evolution services
```

---

## Key Services in the Latest Code

### Lifecycle Core

- `sprintcycle/services/lifecycle_state_machine.py`
  - Defines the canonical stages: `new → normalized → planned → prepared → decomposed → executing → observing → diagnosed → repairing → verifying → delivering → runtime_linked → governing → promotion_ready → promoted`
  - Provides stage transitions, event building, and correlation helpers

- `sprintcycle/services/lifecycle_contracts.py`
  - Defines `LifecycleContract`
  - Carries execution, task, project, trace, diagnostics, runtime, suggestion, governance, and evolution fields

- `sprintcycle/services/phase_workflow.py`
  - Provides structured artifacts for plan / prepare / decompose / observe / diagnose / repair / deliver phases

### Runtime Lifecycle

- `sprintcycle/services/execution_lifecycle_service.py`
  - Handles execution bootstrap, normalization, runtime registration, observation event emission, and execution detail reads

- `sprintcycle/orchestration/sprint_orchestrator.py`
  - Handles Release Plan expansion, sprint orchestration, task execution, and runtime event coordination

### Skills Subsystem

- `sprintcycle/execution/skills.py`
  - Handles scene recognition, skill matching, pre-injection preparation, review checklist enrichment, and retro cleanup

- `sprintcycle/execution/hooks/skill_hooks.py`
  - Hooks skill orchestration into sprint lifecycle nodes such as before/after/before_review/after_retro

- `sprintcycle/execution/skill_store.py`
  - Persists skill artifacts, injection state, execution records, and task traces

The skills subsystem is connected through `SprintOrchestrator._build_sprint_hooks()` and participates in the main flow after planning, before execution, before review, and after retro. It is not a side executor; it is an execution-time capability layer on the main lifecycle.

### Observability, Governance, and Suggestions

- `sprintcycle/services/observability_service.py`
  - Handles trace, replay, execution detail assembly, and observability read models

- `sprintcycle/services/governance_orchestration_service.py`
  - Handles governance checks and governance read workflows

- `sprintcycle/services/suggestion_application_service.py`
  - Handles suggestion review, approval, rejection, archival, and HITL promotion

### Repair, Promotion, and Evolution

- `sprintcycle/services/repair_orchestration_service.py`
  - Handles repair orchestration and the data shape for repair closed loops

- `sprintcycle/services/promotion_policy.py`
  - Handles promotion gating for suggestions and version promotion

- `sprintcycle/services/lifecycle_evolution_service.py`
  - Handles lifecycle evolution, runtime linkage, and promotion readiness

---

## Governance and Validation

### Governance Levels

| Level | Checks Performed | Use Case |
|-------|------------------|----------|
| `minimal` | Basic syntax checks only | Rapid iteration |
| `standard` | Static analysis + architecture checks | Daily development |
| `strict` | All checks + mutation testing | Pre-release validation |

### Built-in Validation Plugins

| Plugin | Functionality | Dependency |
|--------|---------------|------------|
| Architecture | Import layer contract checking | import-linter |
| StaticAnalysis | ruff + mypy static checking | ruff, mypy |
| YAMLValidation | YAML file syntax validation | pyyaml |
| ComposeHint | Docker Compose file checks | PyYAML |
| ADRCheck | Architecture decision record consistency | - |
| MutmutPlugin | Mutation testing (optional) | mutmut |
| PipAuditPlugin | Dependency security scanning (optional) | pip-audit |

---

## Documentation

- `docs/SYSTEM_OVERVIEW.md` — System overview and target mature architecture
- `docs/RELEASE_CHECKLIST.md` — Release checklist
- `docs/GOVERNANCE_HEAVY_CHECKS.md` — Heavy governance checks documentation

---

## Development and Testing

### Framework Development

```bash
./tools/start_develop/dev-setup.sh
source tools/start_develop/activate.sh
pytest tests/test_p0_runtime.py -v
pytest tests/ -v
./tools/start_develop/run-lint.sh
```

### Using SprintCycle to Build Products

```bash
pip install sprintcycle
# or:
pip install "sprintcycle[dashboard,mcp-sse]"

sprintcycle init
sprintcycle run "Add unit tests for the login module"
sprintcycle dashboard
sprintcycle serve
```

---

## License

MIT License

---

## Community and Feedback

Issues and Pull Requests are welcome.

---

**SprintCycle — Let AI be your agile development partner**
