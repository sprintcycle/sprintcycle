# SprintCycle

[中文](README.md)

**SprintCycle** is a contract-driven lifecycle orchestration platform for Web Dashboard / REST API / SDK. A natural-language intent enters through a unified entrypoint, gets normalized, planned, prepared, decomposed, executed, observed, diagnosed, repaired, delivered, linked to runtime, reviewed by governance, and finally promoted into versioned evolution through a structured lifecycle contract.

Current Version: **0.9.2** (matches `sprintcycle.__version__`)

---

## Core Positioning

SprintCycle is not a single-purpose task runner. It is an end-to-end **contract-driven lifecycle platform** that keeps one authoritative lifecycle contract across the entire flow and uses a unified state machine, recovery path, promotion gate, and version registry to make Web-initiated work stable and auditable.

### End-to-end lifecycle

```text
Web Request → Normalize → Plan → Prepare → Decompose → Execute → Observe → Diagnose → Repair → Deliver → Link Runtime → Govern Suggestions → Promote Versioned Evolution
```

### Key platform principles

- **Unified entrypoint**: Dashboard / REST API / SDK enter through the same `SprintCycle` API
- **Unified contract**: `LifecycleContract` is the single source of truth for lifecycle facts
- **Unified state machine**: `LifecycleStateMachine` defines canonical lifecycle stages and transitions
- **Unified recovery**: any failed stage can route into `repair → verify → observe`
- **Unified final snapshot**: `final_snapshot` captures the complete, promotable end state of an iteration
- **Unified promotion gate**: promotion only accepts evidence-complete contracts with a valid final snapshot
- **Unified versioning**: promoted iterations are stored in the version registry as `versioned evolution`

---

## Key Capabilities

### 1. Intent-driven delivery loop
- Describe goals in natural language
- Generate Release Plans (YAML / structured plans)
- Support sprint orchestration, checkpoint resume, and recovery
- Support normalized lifecycle stage transitions

### 2. Standard lifecycle contract
- `LifecycleStateMachine` owns the canonical stage transition rules
- `LifecycleContract` carries cross-service state facts
- A unified correlation model links `execution_id`, `task_id`, `suggestion_id`, `runtime_id`, `version_id`, and `trace_id`
- `final_snapshot` aggregates execution, observation, governance, repair, delivery, runtime, and promotion evidence

### 3. Repair and delivery loop
- Explicitly supports `diagnosed → repairing → verifying → observing`
- Explicitly supports `delivering → runtime_linked → governing → promotion_ready → promoted`
- `RepairOrchestrationService` provides a unified recovery route
- `PromotionPolicy` acts as a promotion gate and blocks incomplete contracts

### 4. Governance and suggestion handling
- Multi-source validation plugin system powered by pluggy
- Architecture contract checks, static analysis, YAML validation, ADR checks, mutation testing, and dependency security scanning
- Suggestion review, approval, rejection, archival, and HITL promotion
- suggestion / governance / promotion all operate on the same contract

### 5. Observability, audit, and runtime
- Execution events, trace, replay, summary, and health read models
- Observability traces write audit payloads into the lifecycle contract
- Runtime registry and deployment linkage
- `lifecycle_contract(...)` and `evolution_overview(...)` can query final snapshots, active versions, and promotion guards directly

### 6. Versioned evolution
- Successful promotion writes to the SQLite version registry
- Active version pointers are linked to final snapshots
- `EvolutionOverviewResult` shows recent versions, active versions, and final snapshot versions together
- Version artifacts keep a final-snapshot contract reference for auditability and rollback

### 7. Dashboard and integrations
- Vue 3 + Element Plus web dashboard
- FastAPI backend
- Python API and Web Dashboard share the same core entrypoint

### 8. Skills subsystem
- Scene recognition, skill matching, skill injection, review checklist enrichment, and retro cleanup
- Hooked into the main flow through `SprintOrchestrator`
- Skill artifacts and execution traces are persistable and auditable

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
| `sprintcycle dashboard` | Start the web UI |
| HTTP API | Exposed through `sprintcycle.interfaces.http` as public / internal routes |

### System Commands

| Command | Description |
|---------|-------------|
| `sprintcycle init [path]` | Initialize the `.sprintcycle` directory structure |
| `sprintcycle import-state` | Import a JSON state directory into SQLite |

**Global options**: `-p/--project` (project path), `--format text|json` (output format), `-v/--verbose` (verbose logging)

---

## Python API

The Python API and Dashboard / REST API share the same `SprintCycle` entrypoint. `plan`, `run`, `diagnose`, `status`, `rollback`, and `stop` all align semantically with the REST surface, making it easy to use in scripts, services, and automation pipelines.

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
├── config/                   # Configuration management
├── orchestration/            # Sprint orchestration engine
├── execution/                # Execution engine
├── release_plan/             # Release Plan models and parsing
├── governance/               # Governance engine, plugins, and suggestion handling
├── dashboard/                # Web Dashboard
├── events/                   # Event bus
├── runtime_observability/    # Runtime observability and replay
├── cache/                    # Cache abstraction layer
├── mq/                       # Message queue abstraction layer
├── validation/               # Multi-source validation plugin system
└── services/                 # Lifecycle, governance, observability, suggestion, repair, delivery, evolution services
```

---

## Key Services in the Latest Code

### Lifecycle Core

- `sprintcycle/services/lifecycle_state_machine.py`
  - Defines the canonical stages: `new → normalized → planned → prepared → decomposed → executing → observing → diagnosed → repairing → verifying → delivering → runtime_linked → governing → promotion_ready → promoted`
  - Provides stage transitions, event building, and correlation helpers

- `sprintcycle/services/lifecycle_contracts.py`
  - Defines `LifecycleContract`
  - Carries execution, task, project, trace, diagnostics, runtime, suggestion, governance, evolution, recovery, validation_refs, and final snapshot evidence
  - Provides evidence validation and final snapshot construction helpers

- `sprintcycle/services/phase_workflow.py`
  - Provides structured artifacts for plan / prepare / decompose / observe / diagnose / repair / deliver phases

### Runtime Lifecycle

- `sprintcycle/services/execution_lifecycle_service.py`
  - Handles execution bootstrap, normalization, runtime registration, observation event emission, and execution detail reads

- `sprintcycle/orchestration/sprint_orchestrator.py`
  - Handles Release Plan expansion, sprint orchestration, task execution, and runtime event coordination

### Recovery, Governance, and Evolution

- `sprintcycle/services/repair_orchestration_service.py`
  - Provides a unified recovery route, supporting the `diagnose → repair → verify → observe` loop

- `sprintcycle/services/promotion_policy.py`
  - Provides the promotion gate, only allowing evidence-complete contracts with a correct stage and final snapshot to move forward

- `sprintcycle/services/lifecycle_evolution_service.py`
  - Builds lifecycle contracts, evaluates promotion, performs promotion, and registers version artifacts

- `sprintcycle/versioning/sqlite_registry.py`
  - Manages version registration, active version pointers, and manifest indexing

### Observability, Governance, and Suggestions

- `sprintcycle/services/observability_service.py`
  - Handles trace, replay, execution detail assembly, and observability read models
  - Writes audit payloads into the lifecycle contract

- `sprintcycle/services/governance_orchestration_service.py`
  - Handles governance checks and governance read workflows

- `sprintcycle/services/suggestion_application_service.py`
  - Handles suggestion review, approval, rejection, archival, and HITL promotion

### Dashboard / Overview / Views

- `sprintcycle/services/platform_summary_service.py`
  - Handles dashboard/platform-facing summary payloads

- `sprintcycle/results.py`
  - Unified result models
  - Includes `FinalSnapshotResult`, `FinalSnapshotVersionSummary`, and `EvolutionOverviewResult`

### Skills Subsystem

- `sprintcycle/execution/skills.py`
  - Handles scene recognition, skill matching, pre-injection preparation, review checklist enrichment, and retro cleanup

- `sprintcycle/execution/hooks/skill_hooks.py`
  - Hooks skill orchestration into sprint lifecycle nodes such as before/after/before_review/after_retro

- `sprintcycle/execution/skill_store.py`
  - Persists skill artifacts, injection state, execution records, and task traces

The skills subsystem is connected through `SprintOrchestrator._build_sprint_hooks()` and participates in the main flow after planning, before execution, before review, and after retro. It is not a side executor; it is an execution-time capability layer on the main lifecycle.

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
pip install "sprintcycle[dashboard]"

sprintcycle init
sprintcycle run "Add unit tests for the login module"
sprintcycle dashboard
```

---

## License

MIT License

---

## Community and Feedback

Issues and Pull Requests are welcome.

---

**SprintCycle — Let AI be your agile development partner**
