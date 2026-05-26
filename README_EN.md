# SprintCycle

[中文](README.md)

**SprintCycle** is a self-evolving contract-driven agile development platform that transforms "natural language requirements" into "traceable software delivery", using `LifecycleContract` to connect the complete closed loop from intent to versioned evolution.

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
- **Contract-driven**: `LifecycleContract` is the single source of truth across the entire pipeline — from requirements to code to testing to deployment, everything revolves around the same contract
- **Self-evolving**: Execute → Observe → Diagnose → Repair → Deliver → Govern → Promote, forming a traceable, replayable, promotable evolution loop

### Core Problems & Solutions

| Problem | SprintCycle Solution |
|---------|---------------------|
| Intent fragmentation: Requirements only exist in chat history, AI doesn't know context, starts from zero each time | `LifecycleContract` is created from the requirement stage, all subsequent phases revolve around the same contract |
| Execution fragmentation: AI writes code but has no evidence chain — don't know what changed, why, or if it's correct | Unified state machine + evidence chain, each stage produces verifiable evidence |
| Evolution fragmentation: No versioned knowledge accumulation, changes are lost after each iteration, cannot build up | Versioned evolution — each promotion writes to version registry |

### Core Concepts

#### LifecycleContract

The single source of truth across the entire pipeline. Created from intent, flows through all stages, and ultimately becomes versioned evolution.

```text
Intent → Contract → Plan → Execute → Observe → Repair → Deliver → Govern → Promote → Evolution
```

#### LifecycleStage

18 stages covering the complete closed loop from "new requirement" to "promoted":

```text
NEW → NORMALIZED → PLANNED → PREPARED → DECOMPOSED → EXECUTING
   ↕                                                    ↕
OBSERVING ← VERIFYING ← REPAIRING ← DIAGNOSED         │
   ↓                                                     │
DELIVERING → RUNTIME_LINKED → GOVERNING → PROMOTION_READY → PROMOTED
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
| 0.9.x | Architecture governance complete, Onion Architecture compliant | ✅ Current |
| 1.0.0 | OpenHands integration + production ready | ⏳ |
| 1.1.0 | Multi-project workspace support | 🔮 |
| 2.0.0 | Self-evolving closed loop validation (measurement → evolution automatic cycle) | 🔮 |

---

## Technical Architecture

### One-sentence Summary

Onion Architecture + DDD + Port/Adapter, 5-layer separation (interfaces → composition → application → domain → infrastructure), 4 core subdomains (lifecycle / execution / evolution / governance), 14 port abstractions, 469+ Python files.

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    interfaces/http/                        │
├─────────────────────────────────────────────────────────────┤
│                     composition/                           │
├─────────────────────────────────────────────────────────────┤
│                     application/                           │
├─────────────────────────────────────────────────────────────┤
│                       domain/                              │
│   ├── generic/                                            │
│   ├── core/                                               │
│   │   └── governance/verification/                        │
│   └── supporting/ (intent/fitness)                        │
├─────────────────────────────────────────────────────────────┤
│                  infrastructure/                           │
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
- **Unified state machine**: `LifecycleStateMachine` defines canonical lifecycle stages and transitions
- **Unified recovery**: any failed stage can route into `repair → verify → observe`
- **Unified final snapshot**: `final_snapshot` captures the complete, promotable end state of an iteration
- **Unified promotion gate**: promotion only accepts evidence-complete contracts with a valid final snapshot
- **Unified versioning**: promoted iterations are stored in the version registry as `versioned evolution`
- **Closed-loop production**: Complete closed loop from intent to usable software

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

## DDD Domain-Driven Design Architecture

### Subdomain Partitioning

SprintCycle follows DDD Onion Architecture with subdomain partitioning:

#### Core Domains - Core Competency

| Subdomain | Responsibility | Aggregate Roots | Value Objects |
|-----------|---------------|-----------------|---------------|
| **lifecycle** | Lifecycle contracts and state machine | `LifecycleRoot` | `StageEvidence`, `CorrelationContext`, `LifecycleEvidence`, `FailureInfo`, `RuntimeRef`, `GovernanceRef`, `EvolutionRef` |
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
| **ports** | Infrastructure port abstractions | `generic/ports/` |
| **interfaces** | Generic interface definitions | `generic/interfaces/` |

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
|------------|------------------|------------------|
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
│   └── dto/                 # Data transfer objects
├── composition/              # Composition root layer (dependency injection)
│   ├── http_factory.py      # HTTP service dependency injection
│   ├── evolution_factory.py # Evolution Facade factory
│   └── orchestration_factory.py # Orchestrator dependency assembly
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
│   │   ├── governance/      # Governance and suggestion handling (includes verification)
│   │   │   ├── aggregates/          # GovernanceSession, RuleSetAggregate
│   │   │   └── verification/        # Verification engine
│   │   └── events/          # Domain events (DomainEvent, EventBus)
│   ├── supporting/          # Supporting subdomains (business support)
│   │   ├── intent/          # Intent parsing and normalization
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
        ├── middleware/      # Middleware (rate_limit, audit)
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

### Verification Providers

| Provider | Functionality | Location |
|----------|---------------|----------|
| `ArchProvider` | Architecture checks (import-linter, ruff, grimp) | `domain/core/governance/verification/providers/` |
| `CliProvider` | CLI command verification | `domain/core/governance/verification/providers/` |
| `PlaywrightProvider` | Playwright end-to-end testing | `domain/core/governance/verification/providers/` |
| `PytestProvider` | pytest unit testing | `domain/core/governance/verification/providers/` |
| `SecurityProvider` | Security scanning (gitleaks) | `domain/core/governance/verification/providers/` |
| `VisualProvider` | Visual verification | `domain/core/governance/verification/providers/` |

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