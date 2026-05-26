# SprintCycle

[中文](README.md)

**SprintCycle** is a contract-driven lifecycle orchestration platform for Dashboard / REST API / Python SDK. It uses a single `LifecycleContract` to connect intent normalization, planning, preparation, decomposition, execution, observation, diagnosis, repair, delivery, runtime linkage, governance, and versioned evolution, producing a traceable, replayable, and promotable `final snapshot` and `versioned evolution`.

Current Version: **0.9.2** (matches `sprintcycle.__version__`)

---

## Core Positioning

SprintCycle is not a single-purpose task runner. It is an end-to-end **contract-driven lifecycle platform** that keeps one authoritative `LifecycleContract` across the entire flow and uses a unified state machine, recovery path, promotion gate, and version registry to make Dashboard / REST API / Python SDK-initiated work stable and auditable.

Its current code structure is closer to a thin-entry + application-orchestration + execution + governance/observability/infrastructure composition. `SprintCycle` remains the unified entry, but it primarily coordinates, routes, and aggregates.

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
- **DDD Aggregate Root**: `LifecycleRoot` serves as the lifecycle domain aggregate root with immutable design

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
- **DDD Aggregate Roots**: `GovernanceSession`, `RuleSetAggregate` manage governance sessions and rule sets

### 5. Observability, audit, and runtime
- Execution events, trace, replay, summary, and health read models
- Observability traces write audit payloads into the lifecycle contract
- Runtime registry and deployment linkage
- `lifecycle_contract(...)` and `evolution_overview(...)` can query final snapshots, active versions, and promotion guards directly

### 6. Versioned evolution
- Successful promotion writes to the SQLite version registry
- Active version pointers are linked to final snapshots
- `EvolutionOverviewResult` shows recent versions, active versions, and final snapshot versions together
- **DDD Aggregate Roots**: `EvolutionRequest`, `SandboxSession` manage version evolution and sandbox sessions

### 7. Dashboard and integrations
- Vue 3 + Element Plus web dashboard
- FastAPI backend
- Dashboard, REST API, and Python SDK share the same core contract entry
- Quality decisions are made explicit through an independent Evaluator Agent and a Sprint Contract

### 8. Skills subsystem
- Scene recognition, skill matching, skill injection, review checklist enrichment, and retro cleanup
- Hooked into the main flow through `SprintOrchestrator` sprint hooks
- **DDD Aggregate Roots**: `SprintAggregate`, `ReleasePlanAggregate` manage execution aggregates

---

## DDD Domain-Driven Design Architecture

### Subdomain Partitioning

SprintCycle follows DDD Onion Architecture with subdomain partitioning:

#### Core Domains - Core Competency

| Subdomain | Responsibility | Aggregate Roots | Value Objects |
|---------|---------------|----------------|---------------|
| **lifecycle** | Lifecycle contracts and state machine | `LifecycleRoot` | `StageEvidence`, `CorrelationContext`, `LifecycleEvidence`, `FailureInfo`, `RuntimeRef`, `GovernanceRef`, `EvolutionRef` |
| **execution** | Execution engine and task orchestration | `SprintAggregate`, `ReleasePlanAggregate` | `TaskResult`, `SprintResult` |
| **evolution** | Version evolution and promotion | `EvolutionRequest`, `SandboxSession` | `VersionArtifact`, `EvolutionEvidence` |
| **governance** | Governance and suggestion handling | `GovernanceSession`, `RuleSetAggregate` | `GovernanceRule`, `RuleEvaluation`, `Finding` |

#### Supporting Domains - Business Support

| Subdomain | Responsibility | Main Modules |
|---------|---------------|--------------|
| **intent** | Intent parsing and normalization | `supporting/intent/` |
| **verification** | Verification engine | `supporting/verification/` |
| **fitness** | Health evaluation | `supporting/fitness/` |

#### Generic Domains - Infrastructure Abstractions

| Subdomain | Responsibility | Main Modules |
|---------|---------------|--------------|
| **errors** | Error handling and knowledge routing | `generic/errors/` |
| **prompts** | Prompt management | `generic/prompts/` |
| **models** | Generic data models | `generic/models/` |
| **platform** | Platform views | `generic/platform/` |
| **ports** | Infrastructure port abstractions | `generic/ports/` |

### Aggregate Root Design Principles

1. **Immutable Design**: All state modifications return new instances for thread safety
2. **Value Objects**: No identity, equality based on attribute values
3. **Event-Driven**: Subdomains communicate via `DomainEvent` for decoupling
4. **ID References**: Cross-aggregate references use IDs instead of direct object references to prevent circular dependencies

### Domain Services

| Service | Responsibility | Location |
|---------|---------------|----------|
| `LifecycleStateMachineService` | State machine transition rules | `domain/core/lifecycle/services.py` |
| `EventBus` | Event publish/subscribe mechanism | `domain/core/events/handlers.py` |

### Event-Driven Architecture

The system uses events for inter-subdomain decoupling:

| Event Type | Source Subdomain | Target Subdomain |
|-----------|-----------------|-----------------|
| `SprintCompleted` | execution | governance |
| `GovernanceCompleted` | governance | evolution |
| `EvolutionPromoted` | evolution | lifecycle |

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

**DDD Core Components**:

```python
from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
    LifecycleStateMachineService,
    StageEvidence,
    CorrelationContext,
)

# Create lifecycle aggregate root
lifecycle = create_lifecycle(
    execution_id="exec-123",
    task_id="task-456",
    project_path="/workspace",
    intent="optimize code"
)

# State transitions (immutable, returns new instance)
lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
lifecycle = lifecycle.transition_to(LifecycleStage.PLANNED)
```

---

## Repository Structure

```
sprintcycle/
├── api.py                    # Unified API entrypoint
├── application/              # Use cases and service orchestration (DDD Application Layer)
│   ├── services/            # Core business services (organized by domain)
│   │   ├── execution/       # Execution-related services
│   │   ├── governance/      # Governance-related services
│   │   ├── lifecycle/       # Lifecycle-related services
│   │   ├── evolution/       # Version evolution services
│   │   ├── dashboard/       # Dashboard view services
│   │   ├── observability/   # Observability services
│   │   └── release/         # Release orchestration services
│   ├── orchestration/       # Orchestration layer
│   ├── factories/           # Factory layer (pure wiring logic only)
│   │   ├── http.py          # Composition root
│   │   └── orchestration.py # Orchestrator dependency assembly
│   └── dto/                 # Data transfer objects
├── domain/                   # Domain models (DDD Domain Layer - subdomain organized)
│   ├── core/                # Core subdomains (core competency)
│   │   ├── lifecycle/       # Lifecycle contracts and state machine
│   │   │   ├── lifecycle_root.py    # LifecycleRoot aggregate root
│   │   │   ├── services.py          # LifecycleStateMachineService
│   │   │   ├── values.py            # Value objects
│   │   │   └── models.py            # Business constants
│   │   ├── execution/       # Execution engine and task orchestration
│   │   │   └── aggregates/          # SprintAggregate, ReleasePlanAggregate
│   │   ├── evolution/       # Version evolution and promotion
│   │   │   └── aggregates/          # EvolutionRequest, SandboxSession
│   │   ├── governance/      # Governance and suggestion handling
│   │   │   └── aggregates/          # GovernanceSession, RuleSetAggregate
│   │   └── events/          # Domain events (DomainEvent, EventBus)
│   ├── supporting/          # Supporting subdomains (business support)
│   │   ├── intent/          # Intent parsing and normalization
│   │   ├── verification/    # Verification engine
│   │   └── fitness/         # Health evaluation
│   └── generic/             # Generic subdomains (infrastructure abstractions)
│       ├── errors/          # Error handling
│       ├── prompts/         # Prompt management
│       ├── models/          # Generic data models
│       ├── platform/        # Platform views
│       ├── interfaces/      # Generic interface definitions
│       └── ports/           # Infrastructure port abstractions
├── infrastructure/          # Adapter layer (DDD Infrastructure Layer)
│   ├── shared/              # Shared infrastructure
│   └── adapters/            # Subdomain adapter implementations
│       ├── core/           # Core subdomain adapters
│       │   ├── execution/  # Execution engine adapters
│       │   ├── evolution/  # Version evolution adapters
│       │   ├── governance/ # Governance adapters
│       │   └── orchestration/ # Orchestration adapters
│       └── generic/        # Generic subdomain adapters
│           ├── config/      # Configuration implementations
│           ├── cache/       # Cache implementations
│           ├── deploy/      # Deployment implementations
│           └── integrations/ # Third-party integrations
└── interfaces/              # HTTP interface layer (DDD Interface Adapter Layer)
    └── http/                # HTTP adaptation layer
        ├── app.py           # FastAPI application factory
        ├── request_context.py # Request context
        ├── dashboard/       # Dashboard-specific HTTP routes
        │   ├── execution/   # Execution domain routes
        │   ├── governance/  # Governance domain routes
        │   ├── lifecycle/   # Lifecycle domain routes
        │   ├── hitl/        # HITL domain routes
        │   └── suggestions/ # Suggestions domain routes
        └── public/          # Public API endpoints
            ├── execution.py # Plan, run, status, rollback, stop endpoints
            └── health.py    # Health check endpoint
```

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
- `docs/ARCHITECTURE_INVARIANTS.md` — Architecture invariants documentation (includes DDD aggregate root design)

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