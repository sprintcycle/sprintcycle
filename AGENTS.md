# SprintCycle AGENTS.md

This file gives guidance to AI coding agents working in the SprintCycle repository.

本文件为在 SprintCycle 仓库中工作的 AI 编码代理提供协作规范。

## Project overview / 项目概述

SprintCycle is a contract-driven lifecycle orchestration platform for Web Dashboard / REST API / SDK. The system is organized around a unified `LifecycleContract`, a canonical state machine, governance checks, recovery flows, and versioned evolution.

SprintCycle 是一个面向 Web Dashboard / REST API / SDK 的契约驱动生命周期编排平台。系统围绕统一的 `LifecycleContract`、规范的状态机、治理检查、恢复流程与版本化演化来组织整个执行闭环。

## Document hierarchy / 文档层级

- `AGENTS.md` — repository-level baseline / 仓库级底线
- `docs/AI_GOVERNANCE.md` — project-level governance charter / 治理总纲
- `docs/CURSOR_TEAM_PLAYBOOK.md` — execution manual / 执行手册
- `.cursor/rules/` — routing and priority rules / 路由和优先级
- `.cursor/commands/` — command entry points / 命令入口

## What to optimize for / 需要优先优化的目标

- Prefer small, safe, incremental changes.
- 除非用户明确要求重构，否则保持统一的 contract / state-machine 设计不变。
- Keep Dashboard, REST API, SDK, and core services aligned semantically.
- 修改要可追溯、可验证，尽量以证据为导向。
- Only introduce new abstractions when they clearly reduce duplication or improve consistency.
- 只有在确实能减少重复或提升一致性时，才引入新的抽象。

## Repository conventions / 仓库约定

- Python backend is the source of truth for lifecycle logic.
- Python 后端是生命周期逻辑的事实来源。
- Frontend lives under `frontend/` and is a Vue 3 application.
- 前端位于 `frontend/`，是 Vue 3 应用。
- Public HTTP surfaces and internal HTTP surfaces should remain clearly separated.
- 公共 HTTP 接口与内部 HTTP 接口应保持明确分离。
- Shared behavior should be implemented once in core services and reused by API / dashboard layers.
- 共享行为应尽量在核心服务中实现一次，再复用到 API / dashboard 层。
- Documentation should reflect the current architecture and terminology.
- 文档应反映当前架构与术语，不要与代码语义脱节。

## Editing guidance / 编辑指导

- Before changing behavior, inspect the relevant code paths and understand the contract flow.
- 在修改行为之前，先阅读相关代码路径，理解 contract 的流转。
- Keep edits focused on the files involved in the user request.
- 尽量把修改范围控制在用户请求涉及的文件中。
- Prefer existing patterns over inventing new ones.
- 优先沿用现有模式，不要轻易发明新模式。
- When introducing a new concept, update the relevant docs and call sites together if needed.
- 当引入新概念时，必要时要同步更新相关文档和调用点。
- Do not modify generated artifacts or build outputs unless explicitly requested.
- 未经明确要求，不要修改生成产物或构建输出。

## Python guidance / Python 指南

- Use Python 3.11+ compatible code.
- 使用兼容 Python 3.11+ 的代码。
- Prefer explicit types for public APIs, dataclasses, and structured data.
- 对公开 API、dataclass 和结构化数据优先使用显式类型。
- Preserve lifecycle stage names, contract fields, and correlation identifiers unless a deliberate migration is requested.
- 除非用户明确要求迁移，否则保持生命周期阶段名、contract 字段和关联标识符不变。
- Treat `LifecycleContract`, `LifecycleStateMachine`, promotion policy, and recovery orchestration as core platform primitives.
- 将 `LifecycleContract`、`LifecycleStateMachine`、promotion policy 和 recovery orchestration 视为核心平台原语。
- Keep side effects in service layers rather than spreading them across handlers.
- 尽量把副作用放在 service 层，不要分散到各个 handler 中。

## Frontend guidance / 前端指南

- Keep Vue components and stores aligned with backend contract semantics.
- 保持 Vue 组件与 store 的语义和后端 contract 一致。
- Prefer existing layout and store patterns in `frontend/src/`.
- 优先使用 `frontend/src/` 里已有的布局和 store 模式。
- When modifying request/response shapes, avoid breaking dashboard API assumptions.
- 当修改 request / response 形状时，避免破坏 dashboard 的 API 约定。

## Testing and validation / 测试与验证

- Run the most relevant tests for the area you changed.
- 运行与你修改范围最相关的测试。
- If a change affects shared contracts, validate downstream callers as well.
- 如果改动影响共享 contract，要同时验证下游调用方。
- For backend changes, prefer targeted pytest runs before broader suites.
- 后端改动优先跑定向的 pytest，再考虑更广泛的测试集。
- For frontend changes, check TypeScript / Vue lint or the project’s frontend validation workflow if available.
- 前端改动优先检查 TypeScript / Vue lint，或者项目已有的前端校验流程。

## Documentation guidance / 文档指导

- Update `README.md`, `README_EN.md`, or other docs only when the change affects user-visible behavior, architecture, setup, or workflows.
- 只有在改动影响用户可见行为、架构、安装或工作流时，才更新 `README.md`、`README_EN.md` 或其他文档。
- Keep terminology consistent with the existing contract-driven lifecycle language.
- 保持术语与现有的 contract-driven lifecycle 语言一致。
- `docs/AI_GOVERNANCE.md` is the project-level governance source of truth for AI collaboration.
- `docs/CURSOR_TEAM_PLAYBOOK.md` is the execution-layer companion that explains roles, routing, and workflow order.
- `AGENTS.md` provides the repository-level baseline and should remain aligned with the governance document, but it does not duplicate its full policy.

## When in doubt / 不确定时

- If a change could affect lifecycle semantics, promotion rules, or contract structure, ask for clarification first.
- 如果变更可能影响生命周期语义、promotion 规则或 contract 结构，先确认再改。
- If multiple implementations are possible, choose the one that best matches the existing architecture and minimizes risk.
- 如果有多种实现方式，选择最符合现有架构、风险最低的方案。
