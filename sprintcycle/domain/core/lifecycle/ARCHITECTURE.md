# Lifecycle Domain Architecture

## Overview

This document describes the architecture of the lifecycle subdomain, following DDD (Domain-Driven Design) and Hexagonal Architecture principles.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL LAYER                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │   HTTP API   │    │  Dashboard   │    │    SDK       │            │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘            │
└─────────┼───────────────────┼───────────────────┼─────────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ADAPTER LAYER                                  │
│                    LifecycleContract (DTO)                             │
│  - Flat structure for serialization                                    │
│  - String-based types for external compatibility                       │
│  - Use LifecycleMapper to convert to/from domain                       │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  LifecycleRootService, SprintOrchestrator, GovernanceServices  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                        │
└──────────────────────────────┼─────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                   │
│                                                                       │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐   │
│  │   LifecycleRoot      │◄───│    LifecycleStateMachine          │   │
│  │   (Aggregate Root)   │    │    (Domain Service - Stateless)   │   │
│  │                      │    │                                  │   │
│  │  - Identity fields   │    │  - Stage transitions             │   │
│  │  - Business methods  │    │  - Status derivation             │   │
│  │  - Value objects     │    │  - Validation rules               │   │
│  │  - Stage history     │    │  - Recovery targets               │   │
│  └──────────────────────┘    └────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Value Objects                             │   │
│  │  CorrelationContext | GovernanceRef | EvolutionRef | RuntimeRef│   │
│  │  StageEvidence | LifecycleEvidence | StageHistoryEntry         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Enums                                     │   │
│  │  LifecycleStage | LifecycleStatus                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. LifecycleContract (DTO)
- **Purpose**: Data transfer object for external interfaces
- **Scope**: Fields needed for API/Dashboard/SDK communication
- **Design**: Flat structure, string-based types, no business logic
- **Location**: `sprintcycle/domain/core/lifecycle/models.py`

### 2. LifecycleMapper
- **Purpose**: Convert between DTO and domain objects
- **Scope**: Single source of truth for conversion logic
- **Methods**:
  - `contract_to_root()`: DTO → Aggregate
  - `root_to_contract()`: Aggregate → DTO
- **Location**: `sprintcycle/domain/core/lifecycle/mapper.py`

### 3. LifecycleRoot (Aggregate Root)
- **Purpose**: Core domain aggregate for lifecycle management
- **Scope**: Business logic, state management, consistency
- **Key Responsibilities**:
  - Maintain current stage and status
  - Validate and execute stage transitions
  - Track stage history
  - Manage cross-subdomain references (by ID)
  - Aggregate stage evidence
- **Location**: `sprintcycle/domain/core/lifecycle/lifecycle_root.py`

### 4. LifecycleStateMachine (Domain Service)
- **Purpose**: Single source of truth for lifecycle transitions
- **Scope**: Stateless domain service with pure functions
- **Key Responsibilities**:
  - Define canonical stage vocabulary
  - Validate transitions between stages
  - Derive status from stage
  - Determine recovery targets
  - Provide stage ordering and metadata
- **Location**: `sprintcycle/domain/core/lifecycle/state_machine.py`

### 5. Value Objects
- **Purpose**: Immutable data structures with value semantics
- **Scope**: Encapsulate domain concepts
- **Examples**:
  - `CorrelationContext`: Request/trace correlation information
  - `GovernanceRef`: Reference to governance session
  - `EvolutionRef`: Reference to evolution request
  - `RuntimeRef`: Reference to runtime instance
  - `StageEvidence`: Evidence collected during a stage
  - `LifecycleEvidence`: Aggregated evidence across all stages
- **Location**: `sprintcycle/domain/core/lifecycle/values.py`

### 6. Enums
- **Purpose**: Type-safe stage and status values
- **Scope**: Domain constants
- **Examples**:
  - `LifecycleStage`: All lifecycle stages (new, normalized, executing, etc.)
  - `LifecycleStatus`: Execution status (pending, running, success, failed, etc.)
- **Location**: `sprintcycle/domain/core/lifecycle/lifecycle_root.py`

## Key Design Principles

### Separation of Concerns
- **DTO**: External interface data only
- **Aggregate**: Business logic and invariants
- **Domain Service**: Business rules and calculations

### Single Source of Truth
- State transitions: `LifecycleStateMachine` only
- Conversion logic: `LifecycleMapper` only
- Value definitions: Centralized enums and constants

### Immutable Updates
- `LifecycleRoot` methods return new instances
- Value objects are immutable (`@dataclass(frozen=True)`)
- Thread-safe and testable

### Dependency Direction
- Domain layer has no dependencies on external layers
- Application layer depends on domain layer
- Adapters convert between external format and domain

## Typical Flow Example

### HTTP Request → Domain → Response
```
HTTP POST /lifecycle/transition
        │
        ▼
WebLifecycleOrchestrationService
        │
        ▼
LifecycleRootService.transition()
        │
        ▼
LifecycleRoot.transition_to()
        │
        ├─→ LifecycleStateMachine.validate_transition()
        ├─→ LifecycleStateMachine.derive_status()
        └─→ Return new LifecycleRoot instance
        │
        ▼
LifecycleMapper.root_to_contract()
        │
        ▼
HTTP Response (LifecycleContract)
```

## Learning Path

For new developers, follow this learning sequence:

1. **Start with Enums**: Understand `LifecycleStage` and `LifecycleStatus`
2. **Learn State Machine**: Study `LifecycleStateMachine` transitions
3. **Understand Aggregate**: Read `LifecycleRoot` and its methods
4. **Explore Value Objects**: Review `values.py` for domain concepts
5. **Understand Conversion**: Examine `LifecycleMapper`
6. **DTO Boundary**: Learn `LifecycleContract` structure
7. **Application Services**: See how services use the domain layer

## Versioning and Evolution

- The lifecycle domain uses semantic versioning
- Breaking changes to `LifecycleContract` require API version bump
- Internal domain changes should not affect external interfaces
- Migration paths should be provided for breaking changes

## References

- DDD Reference: Eric Evans, "Domain-Driven Design"
- Hexagonal Architecture: Alistair Cockburn
- Value Objects: Martin Fowler, "Patterns of Enterprise Application Architecture"
