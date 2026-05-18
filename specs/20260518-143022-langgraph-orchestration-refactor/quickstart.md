# Quickstart: LangGraph Orchestration Cleanup（快速开始：LangGraph 编排清理）

## 1. Verify the compiled graph accessors（验证已编译图访问器）

Confirm that `sprintcycle/infrastructure/integrations/langgraph/compiler.py` exposes compiled graph accessors and no longer requires the old runtime wrapper to be the primary path.（确认 `sprintcycle/infrastructure/integrations/langgraph/compiler.py` 暴露已编译图访问器，并且不再需要旧运行时包装器作为主路径。）

Expected outcome: you can import and call `compile_intent_graph()` and `compile_sprint_graph()` to get compiled graph artifacts with metadata.（预期结果：你可以导入并调用 `compile_intent_graph()` 和 `compile_sprint_graph()` 以获得带元数据的已编译图产物。）

## 2. Exercise the orchestrator path（执行 orchestrator 路径）

Run `SprintOrchestrator.execute_release_plan()` against a representative `ReleasePlan` fixture. The orchestrator should consume the compiled intent graph, convert graph output into `SprintResult` objects, and continue to publish events and persist finalization state.（针对一个具有代表性的 `ReleasePlan` fixture 运行 `SprintOrchestrator.execute_release_plan()`。orchestrator 应消费已编译的 intent 图，将图输出转换为 `SprintResult` 对象，并继续发布事件和持久化 finalization 状态。）

Expected outcome: the old `IntentGraphRuntime` is not instantiated, and the execution path still yields sprint results and completion metadata.（预期结果：旧的 `IntentGraphRuntime` 不会被实例化，且执行路径仍然产出 sprint 结果和完成元数据。）

## 3. Verify cleanup of legacy entry points（验证旧入口清理）

Search the production code path for imports or construction sites of `IntentGraphRuntime`, `graph_runtime.py`, and `sprint_graph.py`. These symbols should not appear in the execution path once the cleanup is complete.（搜索生产代码路径中 `IntentGraphRuntime`、`graph_runtime.py` 和 `sprint_graph.py` 的导入或构造位置。清理完成后，这些符号不应出现在执行路径中。）

Expected outcome: only compiler-backed LangGraph accessors remain as supported production entry points.（预期结果：只有基于 compiler 的 LangGraph 访问器仍然作为受支持的生产入口。）

## 4. Exercise checkpoint-backed recovery behavior（验证基于 checkpoint 的恢复行为）

Instantiate the compiled graph with a local `CheckpointStore` implementation, execute a flow, then restore from the same key path and verify the graph resumes from the last recorded state instead of starting a parallel path.（使用本地 `CheckpointStore` 实例化已编译图，执行一个流程，然后从同一 key path 恢复，并验证图会从最后记录的状态恢复，而不是启动并行路径。）

Expected outcome: recovery is explicit, repeatable, and isolated inside the LangGraph boundary.（预期结果：恢复过程是显式、可重复且隔离在 LangGraph 边界内的。）
