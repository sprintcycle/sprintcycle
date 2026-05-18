# Data Model: LangGraph Orchestration Refactor（LangGraph 编排重构）

## IntentState

Top-level orchestration state passed through the intent graph.

### Fields
- `intent: str` — Raw user or system intent.
- `context: Dict[str, Any]` — Orchestration context, runtime config, and collaborators.
- `release_plan: Optional[Dict[str, Any]]` — Structured release plan produced or supplied during orchestration.
- `release_plan_source: str` — Source tag for the release plan, e.g. `generated` or `provided_dict`.
- `sprints: List[Dict[str, Any]]` — Sprint decomposition derived from the release plan.
- `sprint_results: List[Dict[str, Any]]` — Results returned by per-sprint graph execution.
- `evaluation: Dict[str, Any]` — Retry/finalize/abort decision data.
- `attempt: int` — Current orchestration attempt counter.
- `timeline: List[Dict[str, Any]]` — Ordered execution evidence across graph nodes.
- `error: Optional[str]` — Explicit error indicator when orchestration cannot proceed.

## SprintState

Per-sprint orchestration state passed through the sprint graph.

### Fields
- `sprint: Dict[str, Any]` — Sprint payload.
- `context: Dict[str, Any]` — Sprint-specific runtime context and collaborators.
- `sprint_context: Dict[str, Any]` — Derived sprint execution context.
- `sprint_result: Optional[Dict[str, Any]]` — Concrete result returned from `SprintExecutor` or fallback handling.
- `observation: Optional[Dict[str, Any]]` — Observability and metrics snapshot from execution.
- `repair_decision: Optional[Dict[str, Any]]` — Retry/finalize decision data.
- `attempt: int` — Current sprint attempt counter.
- `timeline: List[Dict[str, Any]]` — Ordered execution evidence across sprint nodes.
- `error: Optional[str]` — Explicit error indicator when sprint execution cannot proceed.
- `final_sprint_result: Optional[Dict[str, Any]]` — Finalized sprint output.

## CheckpointStore

Abstract storage contract for graph recovery.

### Responsibilities
- Persist graph state keyed by `thread_id` or recovery key.
- Restore the most recent graph state for a given execution thread.
- Support a development-friendly local implementation without forcing a persistent backend.

### Default local implementation
- `LocalJsonCheckpointStore` writes state to a JSON file path under a configurable checkpoint directory.
- The local implementation is intended for development and test flows only.

## Compiled graph runtime outputs

Compiled graph accessors should return executable graph artifacts plus runtime metadata.

### Fields
- `graph_name: str`
- `nodes: List[str]`
- `edges: List[Dict[str, Any]]`
- `entrypoint: str`
- `finish_point: str`
- `checkpointer: Optional[Any]`
- `config: Dict[str, Any]`

## Application entrypoint contract

`sprintcycle/application/release/orchestrator.py` remains the canonical thin entrypoint for invoking compiled graphs.

### Responsibilities
- Normalize incoming release orchestration inputs.
- Create or populate `IntentState`.
- Pass recovery keys and graph config through to compiled graph invocation.
- Aggregate graph outputs without duplicating routing decisions.
