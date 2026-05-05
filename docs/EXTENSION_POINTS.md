# SprintCycle 扩展点（P2 预留）

企业能力路线图中的 **Authlib（SSO）**、**Helm/K8s 发布**、**审计日志** 等不在当前仓库默认实现；以下为可接入位置，便于后续以独立包或插件形式扩展。

## 认证与授权（Authlib / OIDC）

- **Dashboard / HTTP**：在 FastAPI 应用层挂载 `Authlib` 中间件或依赖注入的 `Security` 方案；本仓库不绑定具体 IdP。
- **API / CLI**：`SprintCycle` 构造时可传入包装后的 `RuntimeConfig` 或后续增加的 `auth_context`（预留字段勿与现有 `api_key` 混用）；执行编排仍以 `TaskDispatcher` 为中心。

## 部署与运行时（Helm）

- **产物契约**：执行与计划结果已通过 `RunResult` / `PlanResult` 的 `to_dict()` 序列化；Helm Chart 可将 `state_dir`、`sqlite_path` 挂载为 `PersistentVolumeClaim`。
- **进程模型**：`SprintCycle.run` 为同步入口；容器内建议单进程 + 外部队列若需水平扩展（当前未实现队列）。

## 审计与合规

- **事件流**：`EventBus`（`sprintcycle.execution.events`）在 Dispatcher / 执行路径上发出 `EXECUTION_*`、`SPRINT_*`、`TASK_*` 等事件；可注册订阅者写入 SIEM、WORM 存储或企业审计管道。
- **数据面**：`knowledge_cards` 表为可选沉淀；企业级审计表可放在同一 SQLite 旁路或外部 DB，通过「订阅 EventBus + 异步 sink」接入，无需修改核心调度逻辑。

## 知识与企业策略

- **知识注入门控**：`require_knowledge_injection_confirm` + `confirm_knowledge` / CLI `--yes`；策略引擎可在确认前替换为组织内审批 URL 或工单系统（在 `SprintCycle.run` 外层包装即可）。

以上扩展均应保持 **Dispatcher → SprintExecutor** 主路径不变，避免在 `agents` 内硬编码企业 SDK。
