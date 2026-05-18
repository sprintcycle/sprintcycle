# Research: LangGraph Orchestration Refactor（LangGraph 编排重构）

## Current code audit（当前代码审计）

- `sprintcycle/infrastructure/integrations/langgraph/graph.py` currently defines a descriptive `LangGraphGraphSpec` with `LangGraphNodeSpec` / `LangGraphEdgeSpec`, but it does not compile a runnable graph.
- `sprintcycle/infrastructure/integrations/langgraph/graph_runtime.py` currently builds a `StateGraph(dict)` inline and returns a stringified description rather than a compiled runtime artifact.
- `sprintcycle/infrastructure/integrations/langgraph/runtime.py` wraps the descriptive graph/spec objects and exposes `build_graph()` as a metadata surface.
- `sprintcycle/infrastructure/integrations/langgraph/intent_graph.py` and `sprintcycle/infrastructure/integrations/langgraph/sprint_graph.py` currently implement orchestration as Python method chaining with retry loops, not LangGraph node/edge execution.
- `sprintcycle/infrastructure/integrations/langgraph/plan_runtime.py` remains part of the compatibility surface and should continue to provide release-plan shaping support until the graph nodes own the top-level flow.
- `sprintcycle/infrastructure/integrations/langgraph/adapter.py` is part of the runtime integration surface and must remain thin, delegating into compiled graph accessors rather than duplicating execution logic.

## Key findings（关键发现）

1. The repo already has a LangGraph-facing package, but the current runtime is only partially graph-based and still behaves like a wrapper around method calls.
2. The top-level intent flow and per-sprint flow both need a real compiled graph boundary so that routing and recovery can be driven by the graph itself.
3. The current codebase already contains the execution backbone (`SprintExecutor` and surrounding orchestration), so the refactor should reuse that backbone rather than introducing a parallel pipeline.
4. Recovery should be modeled through an explicit checkpoint abstraction with a default local implementation, while leaving room for native LangGraph checkpointer injection at compile/runtime boundaries.
