# SprintCycle

[中文](README.md)

**SprintCycle** is a contract-driven lifecycle orchestration platform for Dashboard / REST API / Python SDK（一个面向 Dashboard / REST API / Python SDK 的契约驱动生命周期编排平台）. It uses a single `LifecycleContract` to connect intent normalization, planning, preparation, decomposition, execution, observation, diagnosis, repair, delivery, runtime linkage, governance, and versioned evolution, producing a traceable, replayable, and promotable `final snapshot` and `versioned evolution`（它通过单一 `LifecycleContract` 串联意图归一化、计划、准备、拆解、执行、观测、诊断、修复、交付、运行时联动、治理和版本化演化，最终产出可追溯、可回放、可晋升的 `final snapshot` 与 `versioned evolution`）.

Current Version: **0.9.2** (matches `sprintcycle.__version__`)

---

## Core Positioning

SprintCycle is not a single-purpose task runner. It is an end-to-end **contract-driven lifecycle platform** that keeps one authoritative `LifecycleContract` across the entire flow and uses a unified state machine, recovery path, promotion gate, and version registry to make Dashboard / REST API / Python SDK-initiated work stable and auditable.

Its current code structure is closer to a thin-entry + application-orchestration + execution + governance/observability/infrastructure composition than to a single large facade or a multi-entry parallel surface. `SprintCycle` remains the unified entry, but it primarily coordinates, routes, and aggregates.

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
- Primary entry surfaces are Dashboard, REST API, and Python SDK; CLI / MCP are no longer primary paths
- Planning and execution are now primarily coordinated through `application/release_plan/`, `application/orchestration/`, `execution/`, and `application/services/`

### 2. Standard lifecycle contract
- `LifecycleStateMachine` owns the canonical stage transition rules
- `LifecycleContract` carries cross-service state facts
- A unified correlation model links `execution_id`, `task_id`, `suggestion_id`, `runtime_id`, `version_id`, and `trace_id`
- `final_snapshot` aggregates execution, observation, governance, repair, delivery, runtime, and promotion evidence
- Contract assembly and aggregation are primarily handled by services such as `application/services/lifecycle_contracts.py` and `application/services/lifecycle_contract_assembly_service.py`

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
- Observability and runtime reads are primarily provided by `application/services/observability_service.py`, `observability/`, and `infrastructure/integrations/phoenix/`

### 6. Versioned evolution
- Successful promotion writes to the SQLite version registry
- Active version pointers are linked to final snapshots
- `EvolutionOverviewResult` shows recent versions, active versions, and final snapshot versions together
- Version artifacts keep a final-snapshot contract reference for auditability and rollback
- Versioning and evolution are primarily provided by `application/services/lifecycle_evolution_service.py`, `application/services/evolution_version_service.py`, and `governance/versioning/`

### 7. Dashboard and integrations
- Vue 3 + Element Plus web dashboard
- FastAPI backend
- Dashboard, REST API, and Python SDK share the same core contract entry
- Quality decisions are made explicit through an independent Evaluator Agent and a Sprint Contract
- HTTP entry adaptation is handled by `interfaces/http/` for public / internal routes
- The Dashboard is implemented on top of `interfaces/http/` plus the frontend app

### 8. Skills subsystem
- Scene recognition, skill matching, skill injection, review checklist enrichment, and retro cleanup
- Hooked into the main flow through `SprintOrchestrator`
- Skill artifacts and execution traces are persistable and auditable
- This logic is mainly spread across `execution/skills.py`, `execution/hooks/skill_hooks.py`, `execution/skill_store.py`, and `execution/orchestrator/sprint_orchestrator.py`


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
├── application/              # Use cases and service orchestration (DDD Application Layer)
│   ├── services/            # Core business services (organized by domain)
│   │   ├── execution/       # Execution-related services (phase_workflow, evaluator_agent)
│   │   ├── governance/      # Governance-related services (governance_orchestration, promotion_policy)
│   │   ├── lifecycle/       # Lifecycle-related services (state_machine, contracts, evolution)
│   │   ├── evolution/       # Version evolution services (promotion_service, version_service)
│   │   ├── dashboard/       # Dashboard view services (platform_summary, view_service)
│   │   ├── observability/   # Observability services (observability_service)
│   │   └── release/         # Release orchestration services (orchestrator)
│   ├── orchestration/       # Orchestration layer (sprint_orchestrator)
│   ├── factories/           # Factory layer (http.py, evolution.py)
│   └── dto/                 # Data transfer objects (results.py)
├── domain/                   # Domain models (DDD Domain Layer - organized by subdomain)
│   ├── core/                # Core subdomains (core competency)
│   │   ├── lifecycle/       # Lifecycle contracts and state machine
│   │   ├── execution/       # Execution engine and task orchestration (agents, core, hooks, orchestrator, planners)
│   │   ├── evolution/       # Version evolution and promotion
│   │   └── governance/      # Governance and suggestion handling (arch_guard, hitl, quality_spec, suggestion)
│   ├── supporting/          # Supporting subdomains (business support)
│   │   ├── intent/          # Intent parsing and normalization
│   │   ├── verification/    # Verification engine (providers)
│   │   └── fitness/         # Health evaluation
│   └── generic/             # Generic subdomains (infrastructure abstractions)
│       ├── errors/           # Error handling and knowledge routing
│       ├── prompts/          # Prompt management and templates
│       ├── models/           # Generic data models (release_plan, sprint_models)
│       ├── platform/         # Platform views and overview
│       ├── interfaces/       # Generic interface protocol definitions
│       └── ports/            # Infrastructure port abstractions
├── infrastructure/          # Adapter layer (DDD Infrastructure Layer - organized by subdomain)
│   └── adapters/            # Subdomain adapter implementations
│       ├── core/           # Core subdomain adapters
│       │   ├── execution/  # Execution engine adapters (state_store, event_backend)
│       │   ├── evolution/  # Version evolution adapters (version_store, rollback_store)
│       │   └── governance/ # Governance adapters (hitl_store, suggestion_store, arch_guard)
│       └── generic/        # Generic subdomain adapters
│           ├── config/      # Configuration implementations (runtime_config, sprintcycle_config)
│           ├── cache/       # Cache implementations (redis_backend, disk_backend)
│           ├── deploy/      # Deployment implementations (compose_manager, runtime_registry)
│           └── integrations/ # Third-party integrations (langgraph, phoenix, autogpt)
└── interfaces/               # HTTP interface layer (DDD Interface Adapter Layer)
    └── http/                # HTTP adaptation layer
        ├── app.py           # FastAPI application factory
        ├── request_context.py # Request context
        ├── dashboard/       # Dashboard-specific HTTP routes (domain-based)
        │   ├── execution/   # Execution domain routes (trace, detail, replay)
        │   ├── governance/  # Governance domain routes (check, history, latest)
        │   ├── lifecycle/   # Lifecycle domain routes (contract, delivery)
        │   ├── hitl/        # HITL domain routes (pending, history, decision)
        │   └── suggestions/ # Suggestions domain routes (approve, reject, promoted)
        └── public/          # Public API endpoints (External integrations)
            ├── execution.py # Plan, run, status, rollback, stop endpoints
            └── health.py    # Health check endpoint
```

---

## DDD Subdomain Architecture

The domain layer (`domain/`) follows DDD onion architecture with subdomain partitioning, keeping the 3-tier architecture (`application/`, `infrastructure/`, `interfaces/`) unchanged.

### Partitioning Principles

Based on SprintCycle's value streams (intent-driven development loop, lifecycle contracts, repair delivery loop, governance and suggestion handling, observability audit and runtime, versioned evolution), subdomains are partitioned in the order of **Core Domains → Supporting Domains → Generic Domains**.

### Subdomain Structure

#### 1. Core Domains - Core Competency

| Subdomain | Responsibility | Main Modules |
|---------|---------------|--------------|
| **lifecycle** | Lifecycle contracts and state machine, unified stage transitions | `core/lifecycle/` |
| **execution** | Execution engine and task orchestration, Sprint runtime core | `core/execution/` (includes agents, core) |
| **evolution** | Version evolution and promotion, versioned evolution capability | `core/evolution/` |
| **governance** | Governance and suggestion handling, HITL review and gates | `core/governance/` (includes quality_spec) |

#### 2. Supporting Domains - Business Support

| Subdomain | Responsibility | Main Modules |
|---------|---------------|--------------|
| **intent** | Intent parsing and normalization, NL to structured plan | `supporting/intent/` |
| **verification** | Verification engine, validation plugins and quality checks | `supporting/verification/` (includes providers) |
| **fitness** | Health evaluation, multi-dimensional quality scoring | `supporting/fitness/` |

#### 3. Generic Domains - Infrastructure

| Subdomain | Responsibility | Main Modules |
|---------|---------------|--------------|
| **errors** | Error handling and knowledge routing | `generic/errors/` |
| **prompts** | Prompt management and templates | `generic/prompts/` |
| **models** | Generic data models (ReleasePlan, SprintDefinition, etc.) | `generic/models/` |
| **platform** | Platform views and overview | `generic/platform/` |
| **interfaces** | Generic interface protocol definitions | `generic/interfaces/` |
| **ports** | Infrastructure port abstractions | `generic/ports/` |

### Dependency Constraints

```
core/          ───────┐
    │                 │ depends on
    ▼                 ▼
supporting/    ───────┐
    │                 │ depends on
    ▼                 ▼
generic/       ───────┘
```

- **Core domains** can only depend on **Supporting domains** and **Generic domains**
- **Supporting domains** can only depend on **Generic domains**
- **Generic domains** do not depend on any other subdomains

### Skills Subsystem Positioning

The Skills subsystem belongs to the **Core domain (core/execution)** as an execution engine enhancement:
- Scene recognition, skill matching, skill injection
- Hooked into the main flow through `SprintOrchestrator` hooks
- Located at [domain/core/execution/agents/](sprintcycle/domain/core/execution/agents/)

---

## Key Services in the Latest Code

### Lifecycle Core

- `sprintcycle/application/services/lifecycle_state_machine.py`
  - Defines the canonical stages: `new → normalized → planned → prepared → decomposed → executing → observing → diagnosed → repairing → verifying → delivering → runtime_linked → governing → promotion_ready → promoted`
  - Provides stage transitions, event building, and correlation helpers

- `sprintcycle/application/services/lifecycle_contracts.py`
  - Defines `LifecycleContract`
  - Carries execution, task, project, trace, diagnostics, runtime, suggestion, governance, evolution, recovery, validation_refs, and final snapshot evidence
  - Provides evidence validation and final snapshot construction helpers

- `sprintcycle/application/services/phase_workflow.py`
  - Provides structured artifacts for plan / prepare / decompose / observe / diagnose / repair / deliver phases

### Runtime Lifecycle

- `sprintcycle/application/services/execution_lifecycle_service.py`
  - Handles execution bootstrap, normalization, runtime registration, observation event emission, and execution detail reads

- `sprintcycle/orchestration/sprint_orchestrator.py`
  - Handles Release Plan expansion, sprint orchestration, task execution, and runtime event coordination

### Recovery, Governance, and Evolution

- `sprintcycle/application/services/repair_orchestration_service.py`
  - Provides a unified recovery route, supporting the `diagnose → repair → verify → observe` loop

- `sprintcycle/application/services/promotion_policy.py`
  - Provides the promotion gate, only allowing evidence-complete contracts with a correct stage and final snapshot to move forward

- `sprintcycle/application/services/lifecycle_evolution_service.py`
  - Builds lifecycle contracts, evaluates promotion, performs promotion, and registers version artifacts

- `sprintcycle/versioning/sqlite_registry.py`
  - Manages version registration, active version pointers, and manifest indexing

### Observability, Governance, and Suggestions

- `sprintcycle/application/services/observability_service.py`
  - Handles trace, replay, execution detail assembly, and observability read models
  - Writes audit payloads into the lifecycle contract

- `sprintcycle/application/services/governance_orchestration_service.py`
  - Handles governance checks and governance read workflows

- `sprintcycle/application/services/suggestion_application_service.py`
  - Handles suggestion review, approval, rejection, archival, and HITL promotion

### Dashboard / Overview / Views

- `sprintcycle/application/services/platform_summary_service.py`
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
