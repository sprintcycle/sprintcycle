# Quickstart: LangGraph Orchestration Refactor（LangGraph 编排重构）

## Goal（目标）

Verify that the refactor produces compiled graphs, routes through graph state, and can recover from checkpointed runs.

## Minimal flow（最小流程）

1. Compile the intent graph and sprint graph through `sprintcycle/infrastructure/integrations/langgraph/compiler.py`.
2. Invoke the canonical thin application entrypoint at `sprintcycle/application/release/orchestrator.py`.
3. Provide an intent plus a `thread_id` / recovery key in the orchestration context.
4. Confirm the compiled graph returns structured execution state, not just descriptive metadata.
5. Interrupt a run, restore the saved checkpoint, and confirm execution resumes from the saved state.

## Expected results（预期结果）

- The top-level runtime uses compiled graph accessors rather than method chaining.
- The sprint runtime is invoked through the graph execution path only.
- The checkpoint store restores a saved state keyed by `thread_id`.
- The application entrypoint aggregates results without owning routing logic.
