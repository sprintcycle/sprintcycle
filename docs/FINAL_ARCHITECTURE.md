# SprintCycle 最终终态架构说明

本文档作为 SprintCycle 仓库内的技术方案定稿，描述当前已经收敛后的最终目标架构、分层边界、入口策略和阶段性落地原则。

---

## 1. 架构定稿结论

SprintCycle 的最终终态不是“多入口并行透出所有能力”，而是一个**分层清晰、入口收敛、能力隔离、可治理、可扩展**的生命周期编排平台。

最终只保留两类正式入口：

- **Dashboard**：面向人类使用的可视化控制台
- **REST API**：面向外部系统和自动化编排的标准集成入口

同时，能力分层为：

- **Core Domain**：统一业务内核
- **Internal API**：Dashboard 专属控制面
- **Public API**：外部系统最小稳定集成面
- **Infrastructure Governance Placeholders**：鉴权、审计、限流的统一接入位

不再把 CLI 和 MCP 作为产品主路径。

---

## 2. 最终架构总览

```text
Dashboard ───────────────┐
                         │
                         ▼
                  Internal API
                         │
                         ▼
                     Core Domain
                         ▲
                         │
External Systems ────► Public API

Infrastructure 层提供：
- Auth
- Audit
- Rate Limit
```

### 2.1 设计原则

1. **Dashboard 使用全集能力**
   - Dashboard 面向人类操作与可视化控制
   - 可以调用内部治理、运行态、执行详情、观测、建议、修复等完整能力

2. **外部系统只使用 Public API**
   - 只暴露稳定、最小、可控的接口
   - 不直接暴露内部状态和治理细节

3. **Core Domain 不依赖入口类型**
   - 业务内核不感知 Dashboard / REST / future auth 入口差异
   - 入口只做适配，不承载业务裁决

4. **统一治理能力预留接入点**
   - 鉴权、审计、限流先作为正式命名模块保留
   - 当前实现可以是默认放行或占位实现，但接口边界要固定

5. **不推进模板系统和扩展生态**
   - 本终态架构不包含模板层、插件市场、MCP、CLI 主入口等扩展方向
   - 只保留当前闭环所需能力

---

## 3. 四层架构定义

### 3.1 Core Domain

Core Domain 是 SprintCycle 的真实业务内核，负责：

- 计划
- 执行
- 状态
- 停止
- 诊断
- 回滚
- 恢复
- 观测
- 修复
- 治理
- 版本晋升

核心要求：

- 不依赖 HTTP
- 不依赖 Dashboard
- 不依赖 CLI / MCP
- 不关心鉴权实现
- 不关心前端展示

### 3.2 Internal API

Internal API 是 Dashboard 的专属控制面，负责：

- 聚合内部状态
- 返回 Dashboard 友好的 payload
- 暴露 execution detail、trace、replay、governance、runtime、suggestion、platform overview 等全量能力
- 支持更复杂的查询与调试语义

### 3.3 Public API

Public API 是外部系统的标准集成入口，负责：

- 提供稳定最小契约
- 满足 CI/CD、外部系统、Agent 等调用场景
- 限制暴露面，减少内部结构泄漏

建议对外仅保留：

- `plan`
- `run`
- `status`
- `stop`
- `rollback`
- `diagnose`

### 3.4 Infrastructure Governance Placeholders

这一层先保留正式模块名，作为未来治理能力接入点：

- `auth`
- `audit`
- `rate_limit`

当前实现可以是默认上下文、默认放行或空记录，但接口和命名应稳定下来。

---

## 4. 入口终态

### 4.1 Dashboard

Dashboard 是 SprintCycle 的核心人机交互入口。

职责：

- 执行控制
- 进度可视化
- 运行态查看
- 观测与回放
- 修复和治理辅助
- 建议审查

Dashboard 通过 Internal API 获取完整能力。

### 4.2 REST API

REST API 是 SprintCycle 的标准自动化集成入口。

职责：

- 外部系统触发
- 自动化执行
- 状态查询
- 基础诊断
- 中断与回滚

REST API 只暴露 Public API 子集。

### 4.3 被移除的入口

以下入口不再作为产品主路径存在：

- CLI
- MCP

它们可能在历史上用于调试或兼容，但终态不再保留为正式产品能力。

---

## 5. 最终的能力边界

### 5.1 Dashboard 使用的能力

Dashboard 可以访问：

- `console_overview`
- `platform_overview`
- `management_overview`
- `fitness_view`
- `deploy_view`
- `deploy_lifecycle`
- `governance_view`
- `governance_lifecycle`
- `fix_view`
- `architecture_check`
- `execution_detail`
- `execution_events`
- `replay_execution`
- `runtime_latest`
- `runtime_update`
- `observability_trace`
- `observability_replay`
- `lifecycle_contract`
- `diagnose_repair_observe`
- `suggestion_overview`
- `review_suggestion`
- `approve_suggestion`
- `reject_suggestion`

### 5.2 Public API 使用的能力

外部系统建议仅使用：

- `plan`
- `run`
- `status`
- `stop`
- `rollback`
- `diagnose`

如果未来需要扩充，必须先明确稳定契约，再决定是否进入 Public API。

---

## 6. 当前代码层面的落地状态

### 6.1 `sprintcycle/api.py`

`SprintCycle` 仍是核心 Facade，承担：

- 生命周期协调
- 结果聚合
- 核心服务编排
- 业务方法暴露

它不应继续承担入口语义。

### 6.2 `sprintcycle/application/internal_api_service.py`

负责 Dashboard 的内部控制面编排。

### 6.3 `sprintcycle/application/public_api_service.py`

负责外部系统的最小 API 契约。

### 6.4 `sprintcycle/presentation/server.py`

负责 Dashboard 与 REST API 的路由挂载与请求适配。

### 6.5 `sprintcycle/infrastructure/auth.py`
### 6.6 `sprintcycle/infrastructure/audit.py`
### 6.7 `sprintcycle/infrastructure/rate_limit.py`

这三个模块是未来统一治理能力的接入点。

---

## 7. 生命周期终态原则

SprintCycle 仍然围绕单一生命周期契约运作：

```text
new → normalized → planned → prepared → decomposed → executing → observing → diagnosed → repairing → verifying → delivering → runtime_linked → governing → promotion_ready → promoted
```

其中：

- `diagnosed → repairing → verifying → observing` 形成显式修复闭环
- `delivering → runtime_linked → governing → promotion_ready → promoted` 形成交付晋升闭环

终态仍然强调：

- 一个 contract
- 一条证据链
- 一个 final snapshot
- 一个可审计版本归档

---

## 8. Public / Internal 的行业实践划分

这套划分参考的是成熟控制面 / 集成面分离思路：

### Internal API

- 面向控制台
- 允许更细粒度内部数据
- 允许聚合展示
- 允许更丰富的运维语义

### Public API

- 面向外部系统
- 只暴露稳定能力
- 只保留最小集合
- 支持未来鉴权、审计、限流接入

这是 SprintCycle 当前最合适的边界方式。

---

## 9. 明确不做的事情

终态架构不推进以下内容：

- 模板系统
- MCP 主入口
- CLI 主入口
- 插件市场
- 额外扩展生态
- 独立 OpenAI API 入口
- 复杂的多租户治理落地

如果未来需要这些能力，应作为独立演进项，不进入当前定稿。

---

## 10. 最终结论

SprintCycle 的最终终态架构可以概括为：

> **以 Core Domain 为唯一业务内核，以 Internal API 服务 Dashboard，以 Public API 服务外部系统，以 Auth / Audit / Rate Limit 作为统一治理接入位，最终收敛到 Dashboard + REST API 两类正式入口。**

这份边界定义保证：

- 逻辑不丢
- 入口收敛
- 能力可治理
- 内外隔离清晰
- 未来鉴权和审计可以自然接入

---

## 11. 文档状态

- 文档性质：技术方案定稿
- 适用范围：仓库内架构说明与后续实现依据
- 目标状态：当前终态
- 版本策略：随代码演进可做增量修订，但不再改变上述核心边界
