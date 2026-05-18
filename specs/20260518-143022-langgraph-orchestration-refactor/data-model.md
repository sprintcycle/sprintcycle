# Data Model: LangGraph Orchestration Cleanup（数据模型：LangGraph 编排清理）

## Intent execution data（意图执行数据）

### `IntentState`
Represents the top-level orchestration state carried through the compiled intent graph. It should contain only orchestration-relevant data and explicit status fields.（表示通过已编译 intent 图传递的顶层编排状态。它只应包含与编排相关的数据以及显式状态字段。）

Recommended fields:（建议字段：）
- `intent`: raw user intent or release goal string（原始用户意图或 release 目标字符串）
- `context`: project/runtime context dictionary（项目/运行时上下文字典）
- `release_plan`: structured release plan object or dict（结构化 release plan 对象或字典）
- `sprint_inputs`: derived sprint dispatch payloads（派生的 sprint 派发载荷）
- `sprint_results`: compiled results from per-sprint execution（每个 sprint 执行后的汇总结果）
- `evaluation`: routing/evaluation outcome used to decide retry vs finalize（用于决定重试或完成的路由/评估结果）
- `status`: current orchestration status（当前编排状态）
- `error`: explicit error payload if a node fails（节点失败时的显式错误载荷）
- `attempt`: retry counter for top-level routing（顶层路由的重试计数）
- `timeline`: optional list of phase markers or timestamps（可选的阶段标记或时间戳列表）
- `metadata`: explicit integration metadata such as execution_id/thread_id/checkpoint hints（显式集成元数据，如 execution_id/thread_id/checkpoint 提示）

### `SprintState`
Represents the per-sprint execution state carried through the compiled sprint graph. It should be sufficient to prepare, execute, observe, repair, and finalize a sprint.（表示通过已编译 sprint 图传递的每个 sprint 执行状态。它应足以完成 sprint 的准备、执行、观测、修复和收尾。）

Recommended fields:（建议字段：）
- `sprint`: sprint definition or sprint name（sprint 定义或 sprint 名称）
- `sprint_input`: input payload for the sprint execution cycle（sprint 执行周期的输入载荷）
- `context`: execution context for the sprint（sprint 的执行上下文）
- `execution_result`: primary result returned by `SprintExecutor` or a mocked equivalent（由 `SprintExecutor` 或 mock 等价物返回的主结果）
- `observation`: post-execution observation and evaluation data（执行后的观测与评估数据）
- `repair_decision`: retry/fix decision for the current sprint cycle（当前 sprint 周期的重试/修复决策）
- `final_result`: normalized sprint result for orchestrator consumption（供 orchestrator 消费的规范化 sprint 结果）
- `status`: current sprint status（当前 sprint 状态）
- `error`: explicit error payload if execution fails（执行失败时的显式错误载荷）
- `attempt`: per-sprint retry counter（每个 sprint 的重试计数）
- `timeline`: optional list of node/phase markers（可选的节点/阶段标记列表）
- `metadata`: explicit execution metadata, including checkpoint hints and tracing fields（显式执行元数据，包括 checkpoint 提示和 tracing 字段）

## Runtime outputs（运行时输出）

### `CompiledGraphRuntime`
A compiled graph wrapper returned by `compiler.py` that packages the compiled graph object with metadata the application boundary can inspect.（由 `compiler.py` 返回的已编译图包装器，它将已编译图对象与 application 边界可检查的元数据打包在一起。）

Recommended fields:（建议字段：）
- `graph_name`: stable graph identifier（稳定的图标识）
- `graph`: compiled LangGraph object（已编译 LangGraph 对象）
- `entrypoint`: entry node name（入口节点名）
- `finish_point`: terminal node name（终止节点名）
- `nodes`: ordered node names for introspection/testing（用于内省/测试的有序节点名）
- `edges`: edge metadata for introspection/testing（用于内省/测试的边元数据）
- `checkpointer`: injected checkpoint implementation or `None`（注入的 checkpoint 实现或 `None`）
- `config`: runtime config metadata（运行时配置元数据）

## Checkpoint abstraction（checkpoint 抽象）

### `CheckpointStore`
Abstract contract for saving and restoring graph execution state.（用于保存和恢复图执行状态的抽象契约。）

Required operations:（必需操作：）
- save a checkpoint by execution/thread key（按 execution/thread key 保存 checkpoint）
- load a checkpoint by execution/thread key（按 execution/thread key 加载 checkpoint）
- list or inspect available checkpoints for debugging/testing when supported（在支持时列出或检查可用 checkpoint 以便调试/测试）

### `LocalJsonCheckpointStore`
Default local implementation used by development and tests.（开发和测试使用的默认本地实现。）

Behavioral requirements:（行为要求：）
- stores checkpoint data on disk in a human-readable format（以人类可读格式将 checkpoint 数据存储到磁盘）
- accepts an explicit restore key path derived from graph invocation config（接受由图调用配置派生的显式恢复 key 路径）
- can be swapped for a durable backend without changing compiled graph node logic（无需更改已编译图节点逻辑即可替换为持久化后端）

## Execution evidence（执行证据）

### `ExecutionSummary`
Normalized summary returned by the application boundary after graph execution.（图执行后由 application 边界返回的规范化摘要。）

Recommended fields:（建议字段：）
- `execution_id`: release execution identifier（release 执行标识）
- `release_plan_name`: release plan name（release plan 名称）
- `sprint_count`: number of executed sprints（已执行 sprint 数量）
- `success`: boolean success flag（成功布尔标志）
- `finalization`: finalization payload or dict（finalization 载荷或字典）
- `sprints`: list of sprint names or summaries（sprint 名称或摘要列表）
- `status`: final orchestration status（最终编排状态）
- `error`: normalized error payload when execution fails（执行失败时的规范化错误载荷）
