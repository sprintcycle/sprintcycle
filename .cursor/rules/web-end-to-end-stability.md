# SprintCycle Web End-to-End Stability Rule / SprintCycle Web 端到端稳定性规则

## English

### Web end-to-end stability guarantee
- For any task initiated from the Web platform, the system must be able to complete the full lifecycle stably.
- This applies equally to self-evolution tasks and user project optimization tasks.
- Based on the current implementation, the core chain should be understood as:
  request normalization / intent entry → plan and execution preparation → sprint orchestration and decomposition → SprintOrchestrator execution → execution observation and repair → result delivery and summary generation → deployment / runtime coordination → suggestion capture and governance → self-evolution and version evolution
- `SprintCycle` is the public coordination layer and must remain thin.
- The execution backbone centers on `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor`.
- LangGraph currently serves as the orchestration skeleton for `plan / run / observe / repair`.
- Suggestions, governance, observability, and evolution are coordinated capabilities around the execution backbone and must be integrated through existing services, facades, hooks, registries, and orchestrators.
- Any implementation change must preserve the continuity of this chain and must not weaken the ability to progress stably from one stage to the next.

### Implementation guidance
- Treat the web-triggered lifecycle as a stability contract, not as a loose aspiration.
- Do not remove or bypass any stage that is needed to keep the chain continuous.
- If a feature improves only one stage, ensure upstream and downstream handoffs still work.
- If a stage already exists in service or facade form, extend it rather than adding a parallel flow.
- Keep the lifecycle end-to-end complete: changes must preserve the chain from request entry through execution, repair, delivery, deployment/runtime, suggestion handling, and self-evolution.

### 补充稳定性规则
- 禁止平行流程：不要创建竞争性的工作流，也不要绕过既有生命周期路径。
- 扩展优先、替换禁止：如果已有阶段或能力存在，应优先扩展它，而不是另起一套流程。
- 状态只允许通过正式通道变更：影响执行、建议、治理或自进化状态的改动必须走正式 service / facade / hook 流程。
- 端到端闭环优先：如果改动只优化局部，必须确认上下游仍然可以稳定衔接。
- 图编排与领域逻辑分离：编排图只负责流程推进，不承载领域判断与状态污染。

## 中文

### Web 端到端稳定性保障
- 对于任何从 Web 平台发起的任务，无论是自进化任务还是用户项目优化任务，系统都应当能够稳定完成完整闭环。
- 以当前代码实现为准，这条闭环应理解为：
  请求归一化 / 意图入口 → 计划与执行准备 → Sprint 编排与拆分 → SprintOrchestrator 执行 → 执行观测与修复 → 结果交付与摘要生成 → 部署 / 运行时联动 → 建议捕获与治理 → 自进化与版本演化
- `SprintCycle` 是公共协调层，只负责归一化、路由、委派和结果汇总，不承载核心工作流逻辑。
- 执行主干当前以 `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor` 为核心。
- 当前 LangGraph 以 `plan / run / observe / repair` 为主要编排骨架，负责计划、执行、观测和修复的流程组织，不替代领域服务、治理流程或自进化逻辑。
- 建议、治理、可观测性和自进化是围绕执行主干协同工作的系统能力，应通过现有 service、facade、hook、registry 和 orchestrator 接入，不得破坏主干架构。
- 任何实现修改都必须保持这条闭环的连贯性，不能削弱 Web 发起任务后的稳定推进能力，也不能绕过现有服务层、门面层、hook 或编排层。

### 实现指引
- 把 Web 触发的生命周期视为稳定性契约，而不是松散目标。
- 不要删除或绕过维持链路连续性所必需的任何阶段。
- 如果某个功能只改善某一阶段，也要确保上下游交接仍然正常工作。
- 如果某一阶段已经以 service 或 facade 形式存在，应当在其基础上扩展，而不是新增平行流程。
