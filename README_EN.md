# SprintCycle

[中文](README.md)

**SprintCycle** is a self-evolving contract-driven agile development platform that transforms "natural language requirements" into "traceable software delivery", using `LifecycleRoot` to connect the complete closed loop from intent to versioned evolution.

Current Version: **0.9.2** (matches `sprintcycle.__version__`)

---

## Product Definition

### One-sentence Definition

SprintCycle is a self-evolving contract-driven agile development platform — turning "natural language requirements" into "traceable software delivery", with LifecycleContract connecting the complete closed loop from intent to versioned evolution.

### Product Essence

**SprintCycle is NOT:**

- Not a code generator (doesn't write code directly)
- Not a CI/CD tool (doesn't do build/deployment pipelines)
- Not a project management tool (doesn't do kanban or ticketing)

**SprintCycle IS:**

- **Intent-to-delivery closed-loop orchestrator**: Input natural language intent, output versioned deliverables with evidence
- **Contract-driven**: `LifecycleRoot` is the single source of truth across the entire pipeline — from requirements to code to testing to deployment, everything revolves around the same root
- **Self-evolving**: Execute → Observe → Diagnose → Repair → Deliver → Govern → Promote, forming a traceable, replayable, promotable evolution loop

### Core Problems & Solutions

| Problem | SprintCycle Solution |
|---------|---------------------|
| Intent fragmentation: Requirements only exist in chat history, AI doesn't know context, starts from zero each time | `LifecycleRoot` is created from the requirement stage, all subsequent phases revolve around the same root |
| Execution fragmentation: AI writes code but has no evidence chain — don't know what changed, why, or if it's correct | Unified state machine + evidence chain, each stage produces verifiable evidence |
| Evolution fragmentation: No versioned knowledge accumulation, changes are lost after each iteration, cannot build up | Versioned evolution — each promotion writes to version registry |

### Core Concepts

#### LifecycleRoot (Lifecycle Aggregate Root)

The single source of truth across the entire pipeline. Created from intent, flows through all stages, and ultimately becomes versioned evolution.

```text
Intent → Contract → Plan → Execute → Observe → Repair → Deliver → Govern → Promote → Evolution
```

#### LifecycleStage

Adopts **Phase-Substage Architecture**, covering the complete closed loop from "new requirement" to "promoted":

**INITIALIZING Phase**:
```text
NEW → NORMALIZED → PLANNED → DECOMPOSED
```

**EXECUTING Phase**:
```text
RUNNING → OBSERVING → DIAGNOSED → REPAIRING → VERIFYING
```

**DELIVERING Phase**:
```text
DELIVERING → RUNTIME_LINKED
```

**GOVERNING Phase**:
```text
GOVERNING → PROMOTION_READY
```

**TERMINAL Phase**:
```text
PROMOTED, FAILED, ABORTED, CANCELLED
```

**Key recovery path**: Failure at any stage → DIAGNOSED → REPAIRING → VERIFYING → OBSERVING → Continue

#### PromotionPolicy

Not all contracts can be promoted. Must meet all criteria:

- Score ≥ 70 (configurable)
- Runtime healthy
- Governance approval passed
- Evidence chain complete (has final_snapshot)
- Repair loop confirmed

### Product Capability Matrix

| Capability | Description | Technical Implementation |
|------------|-------------|-------------------------|
| Intent-driven | Natural language → Structured ReleasePlan | IntentParser + ReleasePlanGenerator |
| Sprint Orchestration | Scrum-based multi-sprint sequential execution | SprintOrchestrator + SprintExecutor |
| Multi-Agent Collaboration | 5 Agent types: Coder/Tester/Architect/Analyzer/RegressionTester | AgentStrategy pattern |
| Checkpoint Resume | Resume from any interrupted stage | StateStore + checkpoint |
| Auto Repair | Execution failure automatically enters diagnose→repair→verify loop | RepairOrchestrationService |
| Governance Checks | Architecture contracts/static analysis/security scanning/mutation testing | pluggy plugin system, 7 built-in plugins |
| HITL Human Approval | Request human confirmation at key decision points | HitlFacade + Coordinator |
| Versioned Evolution | Write to version registry after promotion, supports rollback | EvolutionRequest + VersionStore |
| Observability & Audit | Real-time event stream, trace, replay, health metrics | ObservabilityService + Phoenix integration |
| Skills Subsystem | Scene recognition → skill matching → injection → review | SkillStore + SkillOrchestrator |

### User Journey: A Solo Developer's Day

```text
09:00  sprintcycle run "Add JWT refresh token to user auth module"
        → System creates LifecycleContract
        → Intent normalization → Generates ReleasePlan (2 Sprints)
        
09:02  Sprint 1 begins execution
        → Architect Agent analyzes existing code
        → Coder Agent implements JWT refresh logic
        → Tester Agent generates tests
        
09:15  Execution complete → OBSERVING → Score 82
        → DELIVERING → RUNTIME_LINKED
        
09:16  Governance checks run automatically
        → Architecture layering ✅
        → Static analysis ✅
        → Security scan ⚠️ (1 potential issue found)
        
09:17  Enters GOVERNING → Human approval (HITL)
        → Developer confirms security scan results are acceptable
        
09:18  PROMOTION_READY → PromotionPolicy evaluation → Passed
        → Writes to version registry → v0.3.1
```

### Differentiation from Competitors

| Dimension | Cursor/Copilot | CI/CD (GitHub Actions) | Project Management (Jira/Linear) | SprintCycle |
|-----------|---------------|------------------------|----------------------------------|-------------|
| Focus | Code generation | Build/deployment | Task management | Intent-to-delivery closed loop |
| Context | Current chat window | None | None | LifecycleContract full pipeline |
| Traceability | ❌ Lost when chat disappears | ✅ Build logs | ⚠️ Task status | ✅ Evidence chain + version registry |
| Self-repair | ❌ | ❌ | ❌ | ✅ diagnose→repair→verify |
| Governance | ❌ | ⚠️ Lint | ❌ | ✅ 7-layer governance + HITL |
| Version Evolution | ❌ | ✅ Git tag | ❌ | ✅ versioned evolution + promotion gates |

**SprintCycle fills the gap** between AI coding and formal delivery.

### Product Positioning

SprintCycle is the agile delivery engine for the AI era.

It's not about making AI write code faster — it's about making every line of code AI writes have a source, have evidence, have governance, and have versioning — forming an evolvable software delivery closed loop from intent to versioned evolution.

### Target Users

- **Solo developers / One-person companies**: Using AI to accelerate development but needing structured delivery processes rather than pure vibe coding
- **AI-assisted development teams**: Needing governance and approval mechanisms to constrain AI-generated code quality
- **Self-evolving system builders**: Needing measurement + evolution loops to continuously improve systems

### Business Model Direction

- **Open Source Core**: SprintCycle framework itself MIT licensed
- **Value-added Services**: Cloud Dashboard / Team Collaboration / Enterprise Governance (future)
- **Ecosystem**: Skills Marketplace / Agent Plugin ecosystem

### Version Roadmap

| Version | Milestone | Status |
|---------|-----------|--------|
| 0.9.x | Hexagonal Architecture completed, DDD Aggregate Root design, Phase-Substage Architecture | ✅ Current |
| 1.0.0 | OpenHands integration + production ready | ⏳ |
| 1.1.0 | Multi-project workspace support | 🔮 |
| 2.0.0 | Self-evolving closed loop validation (measurement → evolution automatic cycle) | 🔮 |

---

## Technical Architecture

### One-sentence Summary

Hexagonal Architecture (Ports & Adapters) + DDD (Domain-Driven Design), 4-layer separation (interfaces → application → domain → infrastructure), 4 core subdomains (lifecycle / execution / evolution / governance), 14 port abstractions, 469+ Python files.

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    interfaces/http/                        │ ← Input Port Adapters
│   (HTTP API: dashboard/[execution, governance, lifecycle, │
│    hitl, suggestions] / public/ / middleware/)            │
├─────────────────────────────────────────────────────────────┤
│                     application/                           │ ← Application Services
│   (services/: execution, governance, lifecycle, evolution, │
│    dashboard, observability, release)                     │
│   (composition/: http_factory, evolution_factory,         │
│                  orchestration_factory)                   │
├─────────────────────────────────────────────────────────────┤
│                       domain/                              │ ← Core Business Logic
│   (Core: lifecycle, execution, evolution, governance;     │
│    Supporting: intent, fitness;                           │
│    Generic: errors, prompts, models, platform, interfaces)│
│   (ports/: 14 port definitions)                          │
├─────────────────────────────────────────────────────────────┤
│                  infrastructure/                           │ ← Output Port Adapters
│  (adapters/core/, adapters/generic/)                      │
└─────────────────────────────────────────────────────────────┘
```

### Core Positioning

SprintCycle is not a single-purpose task runner. It is an end-to-end **intent-driven closed-loop production platform** that keeps one authoritative `LifecycleContract` across the entire flow and uses a unified state machine, recovery path, promotion gate, and version registry to make Dashboard / REST API / Python SDK-initiated work stable and auditable.

### End-to-end Lifecycle

```text
Intent → Normalize → Plan → Prepare → Decompose → Execute → Observe → Diagnose → Repair → Deliver → Link Runtime → Govern → Promote Versioned Evolution
```

### Key Platform Principles

- **Intent-driven**: Start from natural language intent and generate executable plans
- **Unified contract**: `LifecycleContract` is the single source of truth for lifecycle facts
- **Unified state machine**: `LifecycleStateMachine` defines canonical lifecycle stages and transitions (Phase-Substage Architecture)
- **Unified recovery**: any failed stage can route into `repair → verify → observe`
- **Unified final snapshot**: `final_snapshot` captures the complete, promotable end state of an iteration
- **Unified promotion gate**: promotion only accepts evidence-complete contracts with a valid final snapshot
- **Unified versioning**: promoted iterations are stored in the version registry as `versioned evolution`
- **Closed-loop production**: Complete closed loop from intent to usable software
- **Port-Adapters pattern**: Define interfaces in `domain/ports/`, implement in `infrastructure/adapters/`

---

## DDD Domain-Driven Design Architecture

### Subdomain Partitioning

SprintCycle follows DDD Hexagonal Architecture with subdomain partitioning:

#### Core Domains - Core Competency

| Subdomain | Responsibility | Aggregate Roots | Value Objects |
|-----------|---------------|-----------------|---------------|
| **lifecycle** | Lifecycle contracts and state machine (Phase-Substage Architecture) | `LifecycleRoot` | `StageEvidence`, `CorrelationContext`, `LifecycleEvidence`, `FailureInfo`, `RuntimeRef`, `GovernanceRef`, `EvolutionRef` |
| **execution** | Execution engine and task orchestration | `SprintAggregate`, `ReleasePlanAggregate` | `TaskResult`, `SprintResult` |
| **evolution** | Version evolution and promotion | `EvolutionRequest`, `SandboxSession` | `VersionArtifact`, `EvolutionEvidence` |
| **governance** | Governance and suggestion handling (includes verification engine) | `GovernanceSession`, `RuleSetAggregate` | `GovernanceRule`, `RuleEvaluation`, `Finding`, `VerificationFinding`, `VerificationRule`, `VerificationReport` |

#### Supporting Domains - Business Support

| Subdomain | Responsibility | Main Modules |
|-----------|---------------|--------------|
| **intent** | Intent parsing and normalization | `supporting/intent/` |
| **fitness** | Health evaluation | `supporting/fitness/` |

#### Generic Domains - Infrastructure Abstractions

| Subdomain | Responsibility | Main Modules |
|-----------|---------------|--------------|
| **errors** | Error handling and knowledge routing | `generic/errors/` |
| **prompts** | Prompt management | `generic/prompts/` |
| **models** | Generic data models | `generic/models/` |
| **platform** | Platform views | `generic/platform/` |
| **interfaces** | Generic interface definitions | `generic/interfaces/` |

#### Ports - External Dependency Abstractions

All external dependency interfaces are defined in `domain/ports/` (17 ports):

| Port File | Protocol | Responsibility |
|-----------|----------|---------------|
| `state_store.py` | `StateStoreProtocol` | State persistence |
| `llm.py` | `EngineAdapterProtocol` | LLM engine calls |
| `cache.py` | `CacheBackendProtocol` | Cache services |
| `governance.py` | `LinterAdapterProtocol` | Unified code checking/architecture analysis (merged ArchGuard, Grimp, ImportLinter, Ruff, TypeCheck) |
| `observability.py` | `ObservabilityFacadeProtocol` | Observability integration |
| `registry.py` | `RuntimeRegistryProtocol` | Runtime registration |
| `knowledge.py` | `KnowledgeRepositoryProtocol` | Knowledge management |
| `evolution.py` | `EvolutionRegistryProtocol`, `VersionManifestProtocol` | Version evolution |
| `hitl.py` | `HitlStoreProtocol` | Human-in-the-loop |
| `audit.py` | `AuditPort` | Audit logging |
| `config.py` | `RuntimeConfigProtocol` | Runtime configuration |
| `deploy.py` | `PlatformLaunchServiceProtocol` | Deployment services |
| `rate_limit.py` | `RateLimitPort` | Rate limiting |
| `diagnostics.py` | `DiagnosticPort` | Diagnostics services |
| `integrations.py` | `LangGraphRuntimeAdapterProtocol` | Third-party integrations (refactored: merged AutoGPT, Phoenix, etc.) |
| `suggestion.py` | `SuggestionStoreProtocol` | Suggestion system |
| `orchestration.py` | `RuntimeConfigPort`, `TraceRuntimePort` | Execution orchestration |

### Aggregate Root Design Principles

1. **Immutable Design**: All state modifications return new instances for thread safety
2. **Phase-Substage Architecture**: `LifecycleRoot` adopts phase-substage layered architecture for better organization
3. **Value Objects**: No identity, equality based on attribute values
4. **Event-Driven**: Subdomains communicate via `DomainEvent` for decoupling
5. **ID References**: Cross-aggregate references use IDs instead of direct object references to prevent circular dependencies

### Domain Services

| Service | Responsibility | Location |
|---------|---------------|----------|
| `LifecycleStateMachineService` | State machine transition rules (Phase-Substage Architecture) | `domain/core/lifecycle/services.py` |
| `EventBus` | Event publish/subscribe mechanism | `domain/core/events/handlers.py` |

### Port-Adapters Pattern

```python
# Port definition (domain/ports/)
class StateStoreProtocol(Protocol):
    def save(self, state: ExecutionState) -> None: ...
    def load(self, execution_id: str) -> Optional[ExecutionState]: ...

# Adapter implementation (infrastructure/adapters/)
class SqliteStateStore(StateStoreProtocol):
    def save(self, state: ExecutionState) -> None:
        # SQLite implementation
        ...
```

### Composition Root Pattern

```python
# application/composition/http_factory.py
class InfrastructureFactory:
    """Infrastructure factory registrar - responsible for registering all Domain layer Infrastructure factory functions"""
    
    def _register_infrastructure_factories(self) -> None:
        # Register state store factory
        register_state_store_factory(create_state_store)
        # Register cache factory
        register_cache_backend_factory(create_cache_backend)
        # Register config factory
        register_runtime_config_factory(create_runtime_config)
        # ... more factory registrations
```

---

## Key Capabilities

### 1. Intent-driven delivery loop
- Describe goals in natural language
- Generate Release Plans (YAML / structured plans)
- Support sprint orchestration, checkpoint resume, and recovery
- Support normalized lifecycle stage transitions (Phase-Substage Architecture)
- **DDD Aggregate Root**: `LifecycleRoot` serves as the lifecycle domain aggregate root with immutable design and Phase-Substage Architecture

### 2. Standard lifecycle contract
- `LifecycleStateMachine` owns the canonical stage transition rules (Phase-Substage Architecture)
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
- **Verification Engine**: Integrated into governance subdomain with multiple verification providers

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
|-------|---------|
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
    LifecycleStateMachine,
    LifecyclePhase,
    LifecycleSubstage,
    ExecutionStatus,
    create_lifecycle,
    StageEvidence,
    CorrelationContext,
)

# Create lifecycle aggregate root (Phase-Substage Architecture)
lifecycle = create_lifecycle(
    execution_id="exec-123",
    task_id="task-456",
    project_path="/workspace",
    intent="optimize code"
)

# Unified state machine (context parameter switches execution/lifecycle)
machine = LifecycleStateMachine(context="lifecycle")
print(machine.STAGES)

# Execution context state machine
exec_machine = LifecycleStateMachine(context="execution")
print(exec_machine.EXECUTION_STATES)
```

---

## Repository Structure

```
sprintcycle/
├── __init__.py                 # Module entry
├── api.py                      # Unified API entrypoint
├── application/                # Application services layer (DDD Application Layer)
│   ├── services/               # Core business services (organized by domain)
│   │   ├── execution/          # Execution-related services (phase_workflow, evaluator_agent)
│   │   ├── governance/         # Governance-related services (governance_facade, repair_orchestration, suggestion_facade)
│   │   ├── lifecycle/          # Lifecycle-related services (lifecycle_service, delivery_service, hook_service, lifecycle_evolution, promotion_policy_service, recovery_lifecycle_service)
│   │   ├── evolution/          # Version evolution services (evolution_promotion, evolution_version)
│   │   ├── dashboard/          # Dashboard view services (dashboard_view, management_overview, platform_summary)
│   │   ├── observability/      # Observability services
│   │   └── release/            # Release orchestration services (orchestrator)
│   ├── orchestration/          # Orchestration layer (sprint_orchestrator)
│   ├── dto/                    # Data transfer objects (results)
│   ├── events/                 # Application events
│   └── composition/            # Composition root (dependency injection)
│       ├── http_factory.py     # HTTP service dependency injection
│       ├── evolution_factory.py # Evolution Facade factory
│       └── orchestration_factory.py # Orchestrator dependency assembly
├── domain/                     # Domain models (DDD Domain Layer)
│   ├── core/                   # Core subdomains
│   │   ├── lifecycle/          # Lifecycle contracts and state machine (Unified State Machine - Phase-Substage Architecture)
│   │   │   ├── lifecycle_root.py    # LifecycleRoot aggregate root (immutable design)
│   │   │   ├── state_machine.py     # LifecycleStateMachine (unified, context-switching)
│   │   │   ├── services.py          # Domain services (StateTransition)
│   │   │   ├── values.py            # Value objects (StageEvidence, CorrelationContext, GovernanceRef, EvolutionRef, RuntimeRef, LifecycleEvidence, FailureInfo)
│   │   │   ├── models.py            # Business constants (evidence schema, stage sequences)
│   │   │   └── requests.py          # Request data classes (BuildLifecycleRequest, TransitionRequest)
│   │   ├── execution/          # Execution engine and task orchestration
│   │   │   ├── aggregates/          # SprintAggregate, ReleasePlanAggregate (immutable design)
│   │   │   ├── agents/              # 5 Agent types (coder/tester/architect/analyzer/regression_tester)
│   │   │   ├── hooks/               # Execution hooks (governance_context, hook_context, quality_hooks, skill_hooks, sprint_hooks, task_hooks)
│   │   │   ├── orchestrator/        # SprintOrchestrator (strategy pattern)
│   │   │   ├── planners/            # Plan generators (builders, execution_planners, expand, generator, parser, validator, work_item_splitter)
│   │   │   ├── core/                # Core execution (policies, context, error_handler, events, feedback, hooks, lifecycle_transitions, protocols, run_workspace, sprint_types, state_machine, static_analyzer)
│   │   │   └── skills/              # Skills subsystem (marketplace, models, orchestrator, store)
│   │   ├── evolution/          # Version evolution and promotion
│   │   │   ├── aggregates/          # EvolutionRequest, SandboxSession (immutable design)
│   │   │   ├── activator.py         # Evolution activator
│   │   │   ├── controller.py        # Evolution controller
│   │   │   ├── facade.py            # Evolution facade
│   │   │   ├── rollback_manager.py  # Rollback manager
│   │   │   └── intent_evolution_loop.py # Intent evolution loop
│   │   ├── governance/         # Governance and suggestion handling
│   │   │   ├── aggregates/          # GovernanceSession, RuleSetAggregate (immutable design)
│   │   │   ├── arch_guard/          # Architecture guard (architecture_checker, architecture_guard, architecture_layers, cli, compose_hint, config, engine, loader, model, registry, reporter, yaml_checks)
│   │   │   ├── hitl/                # Human-in-the-loop (coordinator, decision_normalize, facade, hooks, policy, service, session)
│   │   │   ├── suggestion/          # Suggestion system (analyzer, approval, bridge, classifier, facade, reviewer, service)
│   │   │   ├── verification/        # Verification engine (engine, model, providers)
│   │   │   ├── quality_spec/        # Quality specification (adapters, hooks, providers, rules, spec)
│   │   │   ├── core/                # Governance core (facade, history, plugin_host, report, runner, yaml_merge)
│   │   │   └── hooks/               # Governance hooks (sprint_hooks, task_hooks)
│   │   └── events/             # Domain events (common, handlers)
│   ├── supporting/             # Supporting subdomains
│   │   ├── intent/             # Intent parsing
│   │   └── fitness/            # Health evaluation
│   ├── generic/                # Generic subdomains
│   │   ├── errors/             # Error handling and knowledge routing
│   │   ├── prompts/            # Prompt management
│   │   ├── models/             # Generic data models
│   │   ├── platform/           # Platform views
│   │   └── interfaces/         # Generic interface definitions
│   └── ports/                  # Port definitions (17 ports)
│       ├── __init__.py         # Port module entry
│       ├── state_store.py      # StateStoreProtocol, ExecutionState
│       ├── llm.py              # EngineAdapterProtocol, EngineResult, EngineAdapterConfig
│       ├── cache.py            # CacheBackendProtocol
│       ├── governance.py       # LinterAdapterProtocol (merged ArchGuard, Grimp, ImportLinter, Ruff, TypeCheck)
│       ├── observability.py    # ObservabilityFacadeProtocol
│       ├── registry.py         # RuntimeRegistryProtocol
│       ├── knowledge.py        # KnowledgeRepositoryProtocol, SprintOutcomeCardAdapter
│       ├── evolution.py        # EvolutionRegistryProtocol, VersionManifestProtocol
│       ├── hitl.py             # HitlStoreProtocol
│       ├── audit.py            # AuditPort, AuditRecord
│       ├── config.py           # RuntimeConfigProtocol
│       ├── deploy.py           # PlatformLaunchServiceProtocol
│       ├── rate_limit.py       # RateLimitPort, RateLimitState
│       ├── diagnostics.py      # DiagnosticPort
│       ├── integrations.py     # LangGraphRuntimeAdapterProtocol (refactored: merged AutoGPT, Phoenix, etc.)
│       ├── suggestion.py       # SuggestionStoreProtocol
│       └── orchestration.py    # RuntimeConfigPort, TraceRuntimePort
├── infrastructure/             # Adapter layer (DDD Infrastructure Layer)
│   ├── shared/                 # Shared infrastructure
│   │   └── persistence/        # Persistence (sqlite_store, sync_sqlite_store, session, models)
│   └── adapters/               # Adapter implementations
│       ├── core/               # Core subdomain adapters
│       │   ├── execution/      # Execution engine adapters (state_store, checkpoint, cache, sqlite_event_backend)
│       │   ├── evolution/      # Version evolution adapters (version_store, rollback_store, health_check, evolution_registry_access)
│       │   ├── governance/     # Governance adapters (arch_guard, hitl_store, suggestion_store)
│       │   └── orchestration/  # Orchestration adapters (adapters)
│       └── generic/            # Generic adapters
│           ├── config/         # Configuration implementations (runtime_config, runtime_registry, manager, quality, llm_config, rate_limit)
│           ├── cache/          # Cache implementations (RedisCache, DiskCache, NullCache)
│           ├── integrations/   # Third-party integrations (LangGraph, Phoenix, LLM provider)
│           ├── observability/  # Observability implementations (facade, diagnostics, event_models)
│           ├── deploy/         # Deployment implementations (platform_launch_service, deployment_spec_service, auto_deployer, compose_manager)
│           ├── knowledge/      # Knowledge management (knowledge_repository, knowledge_injector, knowledge_hook)
│           ├── sandbox/        # Sandbox management (manager, worktree_backend)
│           ├── mq/             # Message queue (sqlite_mq)
│           └── llm/            # LLM adapters (cursor_cookbook, claude_code, aider, engine_adapters, registry)
└── interfaces/                 # HTTP interface layer (Input Port Adapters)
    └── http/                   # HTTP adaptation layer
        ├── app.py              # FastAPI application factory
        ├── request_context.py  # Request context management
        ├── middleware/         # Middleware (rate_limit, audit)
        ├── handlers/           # Request handlers (execution, governance, lifecycle, hitl, config, suggestions)
        ├── dashboard/          # Dashboard routes (organized by domain)
        │   ├── execution/      # Execution routes
        │   ├── governance/     # Governance routes
        │   ├── lifecycle/      # Lifecycle routes
        │   ├── hitl/           # HITL routes
        │   └── suggestions/    # Suggestion routes
        └── public/             # Public API endpoints (health, execution)
```

### Layer Responsibilities

| Layer | Responsibility | Key Constraints |
|-------|---------------|----------------|
| **interfaces** | HTTP interfaces, request routing, context passing, middleware | Forward only, no business logic |
| **application** | Use case orchestration, service coordination, transaction boundaries, composition root | Depends on domain, no infrastructure dependencies |
| **domain** | Domain models, business rules, aggregate roots, value objects, domain services, port definitions | No external dependencies, pure business expression |
| **infrastructure** | Adapter implementations, configuration, persistence, external integrations, observability | Implements domain ports, not exposed to business layers |

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

- `docs/ARCHITECTURE_INVARIANTS.md` — Architecture invariants documentation (includes DDD aggregate root design, Phase-Substage Architecture)
- `docs/production/` — Production deployment guides
- `AGENTS.md` — AI coding agent collaboration specification

---

## Development and Testing

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run lint
uv run ruff check sprintcycle/

# Type checking
uv run mypy sprintcycle/
```

---

## License

MIT License

---

## Community and Feedback

Issues and Pull Requests are welcome.

---

**SprintCycle — Let AI be your agile development partner**
