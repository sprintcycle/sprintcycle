# LangGraph Runtime Contract（LangGraph 运行时契约）

## Purpose（目的）

Define the supported compile-and-run boundary for SprintCycle’s LangGraph integration after legacy runtime entry points are removed.（定义在移除旧运行时入口后 SprintCycle LangGraph 集成所支持的编译与运行边界。）

## Contract（契约）

### Compiled graph access（已编译图访问）
- `compile_intent_graph(checkpointer=None)` returns a compiled graph runtime wrapper with a compiled `graph` object and graph metadata.（`compile_intent_graph(checkpointer=None)` 返回一个已编译图运行时包装器，包含已编译的 `graph` 对象和图元数据。）
- `compile_sprint_graph(checkpointer=None)` returns a compiled graph runtime wrapper with a compiled `graph` object and graph metadata.（`compile_sprint_graph(checkpointer=None)` 返回一个已编译图运行时包装器，包含已编译的 `graph` 对象和图元数据。）
- The application layer consumes these compiled artifacts instead of `IntentGraphRuntime` or other legacy wrappers.（application 层消费这些已编译产物，而不是 `IntentGraphRuntime` 或其他旧包装器。）

### State handling（状态处理）
- The compiled intent graph consumes `IntentState` and the compiled sprint graph consumes `SprintState`.（已编译 intent 图消费 `IntentState`，已编译 sprint 图消费 `SprintState`。）
- Node implementations must only mutate graph state fields that belong to orchestration concerns.（节点实现只能修改属于编排关注点的图状态字段。）

### Checkpoint handling（checkpoint 处理）
- A `CheckpointStore` implementation may be injected at compile/invoke time.（可在编译/调用时注入 `CheckpointStore` 实现。）
- The default local implementation is allowed for development and tests, but the contract must not require it in production.（默认本地实现可用于开发和测试，但契约在生产中不应强制要求它。）
- Restore keys must be explicit and stable so recovery can resume the same execution thread.（恢复 key 必须显式且稳定，以便恢复同一执行线程。）

### Execution boundaries（执行边界）
- `SprintExecutor` must remain reachable only from the sprint graph execute node.（`SprintExecutor` 必须只能从 sprint 图的 execute 节点触达。）
- Application code must not directly call `SprintExecutor` once compiled graph execution is available.（一旦已编译图执行可用，application 代码不得直接调用 `SprintExecutor`。）
- Finalization and event emission remain application-layer concerns and are not moved into the graph contract.（finalization 和事件上报仍属于 application 层职责，不迁移到图契约中。）
