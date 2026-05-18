# Feature Specification: LangGraph Orchestration Cleanup（LangGraph 编排清理）

**Feature Branch**: `20260518-143022-langgraph-orchestration-refactor`（功能分支：`20260518-143022-langgraph-orchestration-refactor`）

**Created**: 2026-05-18（创建时间：2026-05-18）

**Status**: Draft（状态：草稿）

**Input**: User request: "清理旧LangGraph实现，让Orchestrator使用新版compiler.LangGraph两套实现并存（旧版未清理）"（输入：用户需求：“清理旧LangGraph实现，让 Orchestrator 使用新版 compiler.LangGraph 两套实现并存（旧版未清理）”）

## Clarifications（澄清）

### Session 2026-05-18
- Q: 这次改造应落在哪一层？ → A: 仅聚焦 LangGraph 集成层与 application 编排入口，清理旧实现并切换到新版 compiler 运行时。
- Q: 旧实现如何处理？ → A: 直接清理旧实现并同步删除/重构相关引用，完成单一路径切换。
- Q: 需要保留兼容层吗？ → A: 不需要；目标是让 Orchestrator 只依赖新版编译产物。
- Q: 功能名是什么？ → A: `langgraph-orchestration-cleanup`。

## User Scenarios & Testing *(mandatory)*（用户场景与测试 *（必填）*）

### User Story 1 - Orchestrator uses compiled LangGraph runtimes（Orchestrator 使用已编译的 LangGraph 运行时） (Priority: P1)（用户故事 1 - Orchestrator 使用已编译的 LangGraph 运行时（优先级：P1））

As a maintainer, I want `SprintOrchestrator` to invoke the compiler-backed LangGraph runtime so that top-level orchestration is driven by compiled graphs instead of the old `IntentGraphRuntime` pseudo-implementation.（作为维护者，我希望 `SprintOrchestrator` 调用基于 compiler 的 LangGraph 运行时，这样顶层编排就由已编译图驱动，而不是由旧的 `IntentGraphRuntime` 伪实现驱动。）

**Why this priority**: The current orchestrator still instantiates the old runtime path, so the new compiler path exists but is not yet the source of truth.（为什么是这个优先级：当前 orchestrator 仍然实例化旧运行时路径，因此新版 compiler 路径虽然存在，但还不是唯一事实来源。）

**Independent Test**: Instantiate `SprintOrchestrator`, execute a release plan, and verify the code path uses the compiler-backed LangGraph runtime and no longer constructs `IntentGraphRuntime`.（独立测试：实例化 `SprintOrchestrator`，执行 release plan，并验证代码路径使用了基于 compiler 的 LangGraph 运行时，且不再构造 `IntentGraphRuntime`。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** a release plan, **When** `SprintOrchestrator.execute_release_plan()` runs, **Then** it invokes the compiled intent graph path and produces sprint execution results from graph output.（**Given** 一个 release plan，**When** `SprintOrchestrator.execute_release_plan()` 运行，**Then** 它会调用已编译的 intent graph 路径，并从图输出中生成 sprint 执行结果。）
2. **Given** the orchestrator initialization path, **When** dependencies are constructed, **Then** no code path instantiates the old `IntentGraphRuntime` as the primary runtime.（**Given** orchestrator 初始化路径，**When** 依赖被构造，**Then** 不应再有任何代码路径将旧的 `IntentGraphRuntime` 作为主运行时实例化。）

---

### User Story 2 - Remove old LangGraph runtime entry points（移除旧的 LangGraph 运行时入口） (Priority: P2)（用户故事 2 - 移除旧的 LangGraph 运行时入口（优先级：P2））

As a maintainer, I want the old LangGraph runtime modules removed or refactored away so that there is only one supported graph implementation path.（作为维护者，我希望旧的 LangGraph 运行时模块被删除或重构掉，这样系统里就只剩下一条受支持的图实现路径。）

**Why this priority**: Keeping two parallel graph implementations causes confusion, stale imports, and regressions when the wrong runtime surface is used.（为什么是这个优先级：保留两套并行图实现会造成混乱、过时导入，并在误用错误运行时表面时引入回归。）

**Independent Test**: Search the codebase for old runtime symbols and verify there are no production references to `intent_graph.py`, `sprint_graph.py`, or `graph_runtime.py` in the execution path.（独立测试：搜索代码库中的旧运行时符号，并验证在执行路径中没有对 `intent_graph.py`、`sprint_graph.py` 或 `graph_runtime.py` 的生产引用。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** the repository after cleanup, **When** the LangGraph integration package is imported, **Then** it exposes only the新版 compiler-oriented API surface needed by the orchestrator.（**Given** 清理后的仓库，**When** 导入 LangGraph 集成包，**Then** 它只暴露 orchestrator 所需的新版 compiler 导向 API 面。）
2. **Given** the removed/updated modules, **When** the application layer resolves graph runtime dependencies, **Then** it resolves through the new compiler-backed path rather than any old pseudo-runtime wrapper.（**Given** 已删除/更新的模块，**When** application 层解析图运行时依赖，**Then** 它将通过新的 compiler-backed 路径解析，而不是任何旧的伪运行时包装器。）

---

### User Story 3 - Preserve existing execution behavior while switching graph source（切换图来源时保持现有执行行为） (Priority: P3)（用户故事 3 - 切换图来源时保持现有执行行为（优先级：P3））

As an operator, I want the graph-source migration to preserve release finalization, event emission, and `SprintExecutor` behavior so that the cleanup does not change the observable execution contract.（作为运维人员，我希望图来源迁移能够保留 release finalization、事件上报和 `SprintExecutor` 行为，这样清理就不会改变可观察执行契约。）

**Why this priority**: The cleanup should remove the old LangGraph path without changing the surrounding orchestration semantics.（为什么是这个优先级：清理应移除旧的 LangGraph 路径，但不能改变周边编排语义。）

**Independent Test**: Run the orchestrator through a representative release plan and verify event emission, completion summary, finalization persistence, and `SprintExecutor`-backed sprint results still work after the switch.（独立测试：通过一个具代表性的 release plan 运行 orchestrator，并验证切换后事件上报、完成摘要、finalization 持久化以及基于 `SprintExecutor` 的 sprint 结果仍然正常工作。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** a successful execution path, **When** the orchestrator uses the compiled graph runtime, **Then** it still records completion state and persists release finalization metadata.（**Given** 一个成功执行路径，**When** orchestrator 使用已编译的图运行时，**Then** 它仍会记录完成状态并持久化 release finalization 元数据。）
2. **Given** a sprint execution failure, **When** the graph returns failure state, **Then** the orchestrator surfaces the failure without reintroducing direct imperative branching around the old runtime.（**Given** 一个 sprint 执行失败，**When** 图返回失败状态，**Then** orchestrator 会暴露失败，而不会围绕旧运行时重新引入直接命令式分支。）

### Edge Cases（边界情况）

- What happens if the compiler-backed graph returns no sprint results?（如果基于 compiler 的图没有返回 sprint 结果，会发生什么？）
- What happens if a stale import still references `IntentGraphRuntime` during cleanup?（如果清理过程中仍有过时导入引用 `IntentGraphRuntime` 会发生什么？）
- What happens if the new compiled runtime output shape differs from what the orchestrator currently expects?（如果新的已编译运行时输出形状与 orchestrator 当前预期不同，会发生什么？）
- What happens if the old LangGraph modules are removed before all references are updated?（如果在所有引用更新前就移除了旧的 LangGraph 模块，会发生什么？）

## Requirements *(mandatory)*（需求 *（必填）*）

### Functional Requirements（功能需求）

- **FR-001**: System MUST route `SprintOrchestrator` through the新版 compiler-backed LangGraph runtime and stop instantiating `IntentGraphRuntime` as the primary execution path.（系统必须让 `SprintOrchestrator` 走新版 compiler-backed LangGraph 运行时，并停止将 `IntentGraphRuntime` 作为主执行路径实例化。）
- **FR-002**: System MUST remove or fully retire the old pseudo-implementation entry points in `intent_graph.py`, `sprint_graph.py`, and `graph_runtime.py` so they are not part of the production execution path.（系统必须移除或完全退役 `intent_graph.py`、`sprint_graph.py` 和 `graph_runtime.py` 中的旧伪实现入口，使其不再参与生产执行路径。）
- **FR-003**: System MUST update LangGraph package exports so callers import only the supported compiler-backed APIs.（系统必须更新 LangGraph 包导出，使调用方只导入受支持的 compiler-backed API。）
- **FR-004**: System MUST preserve `SprintExecutor` as the concrete sprint execution engine while ensuring the orchestrator reaches it only through the compiled graph path.（系统必须保留 `SprintExecutor` 作为具体的 sprint 执行引擎，同时确保 orchestrator 只能通过已编译的图路径触达它。）
- **FR-005**: System MUST keep release finalization, event emission, and state persistence behavior intact during the migration.（系统必须在迁移期间保持 release finalization、事件上报和状态持久化行为不变。）
- **FR-006**: System MUST eliminate any parallel runtime path that bypasses the compiler-backed graph once the cleanup is complete.（系统必须在清理完成后消除任何绕过 compiler-backed 图的并行运行时路径。）
- **FR-007**: System MUST provide tests that prove the old runtime symbols are no longer used by the orchestrator and that the compiled graph path still produces expected results.（系统必须提供测试，证明 orchestrator 不再使用旧运行时符号，并且已编译图路径仍能产出预期结果。）

### Key Entities *(include if feature involves data)*（关键实体 *（如果功能涉及数据则填写）*）

- **CompiledIntentGraph**: The executable graph object returned by the new compiler-backed intent graph path.（`CompiledIntentGraph`：由新的 compiler-backed intent 图路径返回的可执行图对象。）
- **CompiledSprintGraph**: The executable graph object used for per-sprint execution.（`CompiledSprintGraph`：用于每个 sprint 执行的可执行图对象。）
- **SprintOrchestrator**: Application-layer orchestrator that coordinates release plan execution and now consumes compiled graphs.（`SprintOrchestrator`：协调 release plan 执行并现在消费已编译图的 application 层 orchestrator。）
- **ExecutionSummary**: The final execution result summary containing sprint outcomes, finalization metadata, and status information.（`ExecutionSummary`：包含 sprint 结果、finalization 元数据和状态信息的最终执行摘要。）

## Success Criteria *(mandatory)*（成功标准 *（必填）*）

### Measurable Outcomes（可衡量结果）

- **SC-001**: `SprintOrchestrator` no longer instantiates or depends on the old `IntentGraphRuntime` in the primary execution path.（`SprintOrchestrator` 在主执行路径中不再实例化或依赖旧的 `IntentGraphRuntime`。）
- **SC-002**: The LangGraph integration package exports only the supported compiler-backed runtime surface needed by production code.（LangGraph 集成包只导出生产代码所需的受支持 compiler-backed 运行时表面。）
- **SC-003**: `intent_graph.py`, `sprint_graph.py`, and `graph_runtime.py` are removed from production usage, with no remaining production references after cleanup.（`intent_graph.py`、`sprint_graph.py` 和 `graph_runtime.py` 从生产使用中移除，并在清理后没有剩余生产引用。）
- **SC-004**: Release execution still produces sprint results, finalization metadata, and lifecycle events after the switch to compiler-backed graphs.（切换到 compiler-backed 图后，release 执行仍然产出 sprint 结果、finalization 元数据和生命周期事件。）
- **SC-005**: Tests can detect regression if any code path reintroduces the old runtime entry points.（如果任何代码路径重新引入旧运行时入口，测试可以检测到回归。）

## Assumptions（假设）

- The new `compiler.py` implementation already provides a real `StateGraph.compile()` path and is the target runtime source of truth.（新的 `compiler.py` 实现已经提供了真正的 `StateGraph.compile()` 路径，并且是目标运行时事实来源。）
- Existing application-layer orchestration behavior around finalization, events, and state persistence should remain stable.（围绕 finalization、事件和状态持久化的现有 application 层编排行为应保持稳定。）
- It is acceptable to remove legacy LangGraph runtime modules once their usages are fully migrated to the compiler-backed path.（一旦用法完全迁移到 compiler-backed 路径，允许移除旧的 LangGraph 运行时模块。）
