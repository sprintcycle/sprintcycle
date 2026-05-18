# Research: LangGraph Orchestration Cleanup（调研：LangGraph 编排清理）

## 1. Current state audit（当前状态审计）

The repository already contains a real compiled LangGraph implementation in `sprintcycle/infrastructure/integrations/langgraph/compiler.py`. That module builds and caches actual `StateGraph.compile()` outputs for intent and sprint flows, and it exposes `compile_intent_graph()`, `compile_sprint_graph()`, `get_intent_graph()`, and `get_sprint_graph()` as the production-facing entry points.（仓库中已经存在真实的已编译 LangGraph 实现，位于 `sprintcycle/infrastructure/integrations/langgraph/compiler.py`。该模块为意图和 sprint 流程构建并缓存实际的 `StateGraph.compile()` 产物，并将 `compile_intent_graph()`、`compile_sprint_graph()`、`get_intent_graph()` 和 `get_sprint_graph()` 作为面向生产的入口。）

However, `sprintcycle/application/orchestration/sprint_orchestrator.py` still instantiates `IntentGraphRuntime` from `sprintcycle/infrastructure/integrations/langgraph/intent_graph.py`. That legacy runtime is a pseudo-implementation that rebuilds `LangGraphExecutionRuntime` on demand and falls back to `graph.ainvoke(...)` only if the runtime exposes it. The orchestrator therefore still depends on the old surface even though the compiler-backed runtime already exists.（然而，`sprintcycle/application/orchestration/sprint_orchestrator.py` 仍然实例化来自 `sprintcycle/infrastructure/integrations/langgraph/intent_graph.py` 的 `IntentGraphRuntime`。这个旧运行时是伪实现，它按需重建 `LangGraphExecutionRuntime`，并且只有在运行时暴露 `graph.ainvoke(...)` 时才会调用它。因此，尽管基于 compiler 的运行时已经存在，orchestrator 仍然依赖旧表面。）

`graph_runtime.py` and `intent_graph.py` both act as wrappers over the older runtime model, while `plan_runtime.py` remains a placeholder-style helper that constructs a synthetic release plan object. These modules no longer need to be the primary runtime source of truth once the orchestrator is wired to the compiler-backed graph objects.（`graph_runtime.py` 和 `intent_graph.py` 都只是旧运行时模型的包装器，而 `plan_runtime.py` 仍然是一个占位式辅助器，用来构造合成的 release plan 对象。一旦 orchestrator 接线到基于 compiler 的图对象，这些模块就不再需要作为主运行时事实来源。）

## 2. Replacement strategy（替换策略）

The cleanest migration is a single-path cutover: update the orchestrator to call the compiled graph accessors, then retire the old runtime modules from production usage. This avoids maintaining two parallel graph APIs and prevents future ambiguity about which runtime is authoritative.（最干净的迁移方式是单路径切换：先更新 orchestrator 调用已编译图访问器，然后让旧运行时模块退出生产使用。这样可以避免维护两套并行图 API，并防止未来对哪个运行时才是权威来源产生歧义。）

Because the compiled graph helpers already exist, the main implementation work is not graph invention but reference cleanup and output-shape alignment. The orchestrator should consume compiled graph results, map them into `SprintResult` objects, and preserve existing finalization/event/persistence behavior without reintroducing imperative routing.（由于已编译图辅助函数已经存在，主要实现工作不是发明新的图，而是做引用清理和输出形状对齐。orchestrator 应消费已编译图结果，将其映射为 `SprintResult` 对象，并在不重新引入命令式路由的情况下保留现有的 finalization/事件/持久化行为。）

## 3. Checkpoint/recovery decision（checkpoint/恢复决策）

The current compiled runtime already accepts a `checkpointer` argument, which means the cleanup can preserve the existing abstraction boundary without inventing a new orchestration protocol. The plan is to keep a thin `CheckpointStore` abstraction in the LangGraph integration layer and use the compiled graph invocation boundary to inject the store or restore key as needed.（当前已编译运行时已经接受 `checkpointer` 参数，这意味着这次清理可以保留现有抽象边界，而无需发明新的编排协议。计划是在 LangGraph 集成层保留一个薄的 `CheckpointStore` 抽象，并在已编译图调用边界按需注入存储或恢复 key。）

For this cleanup, the key requirement is not a new recovery system but to keep the runtime API explicit enough that a future durable backend can replace the local implementation without graph rewrites. A local file/JSON store is sufficient for development and tests.（对这次清理来说，关键要求不是一个新的恢复系统，而是让运行时 API 足够显式，以便未来能用持久化后端替换本地实现而无需重写图。对于开发和测试，本地文件/JSON 存储已经足够。）

## 4. Application boundary decision（application 边界决策）

`SprintOrchestrator` remains the canonical thin application entrypoint. The orchestrator should continue to own event emission, release finalization persistence, and result summarization, but it should delegate graph routing to the compiled LangGraph runtime rather than to a legacy runtime wrapper.（`SprintOrchestrator` 仍然是 canonical 的薄 application 入口。orchestrator 应继续负责事件上报、release finalization 持久化和结果摘要，但它应将图路由委托给已编译的 LangGraph 运行时，而不是委托给旧运行时包装器。）

The orchestrator may still transform the compiled graph output into existing domain result classes, but it should not directly invoke `SprintExecutor` once the graph path is in place. The goal is to keep the execution backbone in the sprint graph and not in application code.（orchestrator 仍然可以把已编译图输出转换成现有领域结果类，但一旦图路径到位，它不应直接调用 `SprintExecutor`。目标是把执行主干保留在 sprint 图中，而不是放在 application 代码里。）

## 5. Testing implications（测试影响）

The cleanup should be covered by tests that prove three things: the orchestrator no longer constructs `IntentGraphRuntime`; the package exports no longer advertise the retired runtime path as the production surface; and the compiled graph path still produces sprint results plus finalization metadata. A secondary regression check should search for stale references to the old modules in the production path.（这次清理应通过测试覆盖三件事：orchestrator 不再构造 `IntentGraphRuntime`；包导出不再将已退役运行时路径作为生产表面；以及已编译图路径仍然会产出 sprint 结果和 finalization 元数据。次级回归检查应搜索生产路径中对旧模块的过时引用。）

## Decision summary（决策摘要）

- Use the existing compiler-backed LangGraph implementation as the sole runtime source of truth.（使用现有基于 compiler 的 LangGraph 实现作为唯一运行时事实来源。）
- Remove legacy runtime entry points from production usage instead of keeping compatibility shims.（从生产使用中移除旧运行时入口，而不是保留兼容垫片。）
- Keep orchestration thin and preserve current behavior around events, finalization, and persistence.（保持编排薄，并保留围绕事件、finalization 和持久化的当前行为。）
- Keep checkpointing abstract and local-by-default so the recovery model stays replaceable later.（保持 checkpoint 抽象，并默认本地实现，使恢复模型以后仍可替换。）
