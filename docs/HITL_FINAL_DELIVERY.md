# SprintCycle HITL 交付说明

## 1. 项目目标

将 SprintCycle 的 Human-in-the-Loop 能力从顶层旁路模块迁移并收口到治理域 `sprintcycle/governance/hitl/`，形成统一、可审计、可扩展的人工决策编排层。

## 2. 交付结果

### 架构层面
- HITL 主实现已迁移到治理域
- 顶层旧 `sprintcycle/hitl/` 已删除
- 内部引用已统一切换到治理域
- 全量 lint 通过

### 功能层面
- 支持 HITL gate / decision / session / risk level / policy / coordinator / service
- 支持 SQLite 持久化与 memory 存储
- 支持 timeout 自动决策
- 支持治理、任务、质量层触发 HITL

### 三端接入
- CLI 支持 HITL 查询与决策
- MCP 支持 HITL 工具调用
- Dashboard 支持 HITL REST API 与总览统计

## 3. 关键接入点

### 治理门
- `GovernanceRunner`

### 任务治理
- `GovernanceTaskLifecycleHooks`

### 质量层
- `QualityLifecycleHooks`

### 统一 API
- `SprintCycle`

## 4. 统一决策语义

- `approve`
- `reject`
- `request_changes`
- `skip_sprint`
- `abort_execution`

## 5. 兼容与迁移策略

- 顶层旧 `sprintcycle/hitl/` 已删除
- 现有实现仅保留在 `sprintcycle/governance/hitl/`
- 后续新增能力全部沿治理域扩展

## 6. 验收状态

- 结构收口完成
- 主流程接入完成
- 三端联动完成
- 配置接入完成
- lint 检查通过

## 7. 后续建议

- 增强 `modify` / `retry` 的产品语义
- 增加多审批人机制
- 增加审批审计视图
- 如需复杂长事务，可考虑引入工作流引擎

## 结论

这次 SprintCycle HITL 已完成从“独立模块”到“治理域中台能力”的演进，已经具备长期维护与扩展的基础，且旧顶层实现已清理完毕。
