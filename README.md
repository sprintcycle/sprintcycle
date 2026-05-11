# SprintCycle

[English](README_EN.md)

**SprintCycle** 是一个面向 Web / CLI / MCP / SDK 的统一编排框架：用自然语言表达意图，生成可执行的 Release Plan，并通过统一生命周期契约驱动计划、执行、观测、修复、交付、运行时联动、治理与自我演化。

当前版本：**0.9.2**（与 `sprintcycle.__version__` 一致）

---

## 核心定位

SprintCycle 不是单一的任务执行器，而是一个端到端的生命周期编排平台，覆盖以下闭环：

1. 意图接入与标准化
2. 计划生成与校验
3. 任务拆解与执行准备
4. Sprint 执行与事件记录
5. 观测、诊断与修复闭环
6. 交付与运行时联动
7. 治理审核与建议处理
8. 版本晋升与自我演化

系统的当前实现以 `SprintCycle` 统一入口为中心，底层由一组工作流服务、领域 Facade、运行时注册表、观测层、skills 子系统和演化层协作完成。

---

## 主要能力

### 意图驱动的开发闭环
- 通过自然语言描述目标
- 生成 Release Plan（YAML / 结构化计划）
- 支持 Sprint 编排、断点续跑与恢复
- 支持标准化生命周期状态迁移

### 统一生命周期契约
- `LifecycleStateMachine` 负责阶段迁移规则
- `LifecycleContract` 负责跨服务状态事实载体
- 统一 correlation model 串联 `execution_id`、`task_id`、`suggestion_id`、`runtime_id`、`version_id`、`trace_id`

### 修复与交付闭环
- 显式支持 `diagnosed → repairing → verifying → observing` 闭环
- 显式支持 `delivering → runtime_linked → governing → promotion_ready → promoted` 晋升链路
- 提供修复、验证、运行时联动与建议晋升的结构化载体

### 治理与建议处理
- 多源验证插件系统（基于 pluggy）
- 架构契约检查、静态分析、YAML 校验、ADR 检查、突变测试、依赖安全扫描
- 建议审查、批准、拒绝、归档与 HITL 晋升

### 观测与运行时
- 执行事件、trace、replay、摘要与健康状态读模型
- 运行时注册表与部署联动
- 面向 Dashboard / API 的观测视图

### Dashboard 与集成
- Vue 3 + Element Plus Web Dashboard
- FastAPI 后端
- MCP Server（stdio / SSE）
- Python API 与 CLI 共用同一套核心入口

### 配置与扩展
- `dynaconf` + `pydantic` 配置体系
- 本地缓存与 Redis 后端抽象
- 预留消息队列扩展点
- 可插拔的治理、建议与观测 Facade

---

## 环境要求

- Python **≥ 3.11**

---

## 安装

### 基础安装

```bash
pip install -e .
```

### 完整安装（推荐）

```bash
pip install -e "[full,dev]"
```

### 常用可选能力

| Extra | 用途 |
|------|------|
| `dashboard` / `full` | Web Dashboard（FastAPI + Uvicorn） |
| `cache-redis` | 执行缓存 Redis 后端 |
| `mcp-sse` | 以 SSE 方式对外提供 MCP |
| `dev` | 测试、类型检查、import-linter 等开发依赖 |
| `mutation` | 突变测试（`mutmut`） |

---

## 快速开始

### 初始化项目数据目录

```bash
sprintcycle init
```

### 生成计划但不执行

```bash
sprintcycle plan "为登录流程增加单元测试" -m auto
```

### 直接执行

```bash
sprintcycle run "修复 README 中的死链"
# 等价于：
sprintcycle "修复 README 中的死链"
```

### 启用治理检查

```bash
sprintcycle run "重构配置模块" --governance-level standard
```

### 启动 Dashboard

```bash
# 生产模式（通常需要先构建前端）
sprintcycle dashboard

# 开发模式（同时启动 FastAPI + Vite）
sprintcycle dashboard --dev
```

---

## 命令速查

### 核心流程

| 命令 | 说明 |
|------|------|
| `sprintcycle wizard` | 交互式选择 plan / run / diagnose / status |
| `sprintcycle plan <意图>` | 生成执行计划 |
| `sprintcycle run [意图]` | 执行 Sprint |
| `sprintcycle validate` | 运行治理验证 |

### 项目管理

| 命令 | 说明 |
|------|------|
| `sprintcycle diagnose` | 项目健康度分析 |
| `sprintcycle status [execution_id]` | 单条执行状态或历史列表 |
| `sprintcycle rollback <execution_id>` | 回滚执行 |
| `sprintcycle stop <execution_id>` | 停止运行中的任务 |

### 知识管理

| 命令 | 说明 |
|------|------|
| `sprintcycle knowledge search` | 检索知识卡片 |
| `sprintcycle knowledge list` | 列出所有知识卡片 |

### 配置管理

| 命令 | 说明 |
|------|------|
| `sprintcycle config show` | 显示当前配置 |
| `sprintcycle config set <key> <value>` | 设置配置项 |
| `sprintcycle config get <key>` | 获取配置项 |

### 服务与集成

| 命令 | 说明 |
|------|------|
| `sprintcycle serve` | 启动 MCP Server（默认 stdio；`--transport sse` 用于远程 Agent） |
| `sprintcycle dashboard` | 启动 Web UI |

### 系统命令

| 命令 | 说明 |
|------|------|
| `sprintcycle init [path]` | 初始化 `.sprintcycle` 目录结构 |
| `sprintcycle import-state` | 将 JSON 状态目录导入 SQLite |

**全局选项**：`-p/--project`（项目路径）、`--format text|json`（输出格式）、`-v/--verbose`（详细日志）

---

## Python API

Python API 与 CLI 共享同一个 `SprintCycle` 入口，`plan`、`run`、`diagnose`、`status`、`rollback`、`stop` 等能力语义一致，方便在脚本、服务和自动化流水线中调用。

```python
from sprintcycle import SprintCycle

api = SprintCycle(project_path="./my-project")
result = await api.run("重构认证模块")
```

常见导出对象包括：

- `SprintCycle`
- `ReleasePlan`
- `ReleasePlanParser`
- `ReleasePlanValidator`
- `SprintOrchestrator`
- `SprintExecutor`

---

## 代码结构

```
sprintcycle/
├── api.py                    # 统一 API 入口
├── cli/                      # CLI 包
├── config/                   # 配置管理
├── orchestration/            # Sprint 编排引擎
├── execution/                # 执行引擎
├── release_plan/             # Release Plan 模型与解析
├── governance/               # 治理引擎、插件与建议处理
├── dashboard/                # Web Dashboard
├── events/                   # 事件总线
├── mcp/                      # MCP Server
├── runtime_observability/    # 运行时观测与回放
├── cache/                    # 缓存抽象层
├── mq/                       # 消息队列抽象层
├── validation/               # 多源验证插件系统
└── services/                 # 生命周期、治理、观测、建议、交付等应用服务
```

---

## 最新代码中的关键服务

### 生命周期中枢

- `sprintcycle/services/lifecycle_state_machine.py`
  - 定义统一阶段：`new → normalized → planned → prepared → decomposed → executing → observing → diagnosed → repairing → verifying → delivering → runtime_linked → governing → promotion_ready → promoted`
  - 提供状态迁移、事件构建与关联信息

- `sprintcycle/services/lifecycle_contracts.py`
  - 定义 `LifecycleContract`
  - 统一承载 execution、task、project、trace、diagnostics、runtime、suggestion、governance、evolution 等字段

- `sprintcycle/services/phase_workflow.py`
  - 提供 plan / prepare / decompose / observe / diagnose / repair / deliver 等阶段性结构化 artifact

### 运行生命周期

- `sprintcycle/services/execution_lifecycle_service.py`
  - 负责执行启动、状态归一、运行时注册、观测事件发射和执行详情读取

- `sprintcycle/orchestration/sprint_orchestrator.py`
  - 负责 Release Plan 扩展、Sprint 编排、任务执行与运行时事件协调

### Skills 子系统

- `sprintcycle/execution/skills.py`
  - 负责场景识别、skill 匹配、注入前准备、review checklist 增强和复盘清理

- `sprintcycle/execution/hooks/skill_hooks.py`
  - 负责把 skill 编排挂接到 sprint 生命周期的 before/after/before_review/after_retro 节点

- `sprintcycle/execution/skill_store.py`
  - 负责 skill artifact、injection state、execution record 和 task trace 的持久化

skills 子系统通过 `SprintOrchestrator._build_sprint_hooks()` 接入主流程，在计划后、执行前、评审前、复盘后参与上下文增强与证据沉淀。它不是旁路执行器，而是主生命周期上的一个执行时能力层。

### 观测、治理与建议

- `sprintcycle/services/observability_service.py`
  - 负责 trace、replay、执行详情与观测读模型

- `sprintcycle/services/governance_orchestration_service.py`
  - 负责治理检查与治理读流程

- `sprintcycle/services/suggestion_application_service.py`
  - 负责建议的审查、批准、拒绝、归档与 HITL 晋升

### 修复、晋升与演化

- `sprintcycle/services/repair_orchestration_service.py`
  - 负责修复编排与修复闭环所需的数据组织

- `sprintcycle/services/promotion_policy.py`
  - 负责建议/版本晋升门禁策略

- `sprintcycle/services/lifecycle_evolution_service.py`
  - 负责生命周期演化、运行时联动与晋升准备

---

## 治理与验证

### 治理级别

| 级别 | 检查项 | 适用场景 |
|------|--------|----------|
| `minimal` | 仅基础语法检查 | 快速迭代 |
| `standard` | 静态分析 + 架构检查 | 日常开发 |
| `strict` | 全部检查 + 突变测试 | 发布前验证 |

### 内置验证插件

| 插件 | 功能 | 依赖 |
|------|------|------|
| Architecture | 导入分层契约检查 | import-linter |
| StaticAnalysis | ruff + mypy 静态检查 | ruff, mypy |
| YAMLValidation | YAML 文件语法校验 | pyyaml |
| ComposeHint | Docker Compose 文件检查 | PyYAML |
| ADRCheck | 架构决策记录一致性 | - |
| MutmutPlugin | 突变测试（可选） | mutmut |
| PipAuditPlugin | 依赖安全扫描（可选） | pip-audit |

---

## 文档

- `docs/SYSTEM_OVERVIEW.md` — 系统总览与目标成熟架构
- `docs/RELEASE_CHECKLIST.md` — 发布检查清单
- `docs/GOVERNANCE_HEAVY_CHECKS.md` — 重量级治理检查说明

---

## 开发与测试

### 框架开发

```bash
./tools/start_develop/dev-setup.sh
source tools/start_develop/activate.sh
pytest tests/test_p0_runtime.py -v
pytest tests/ -v
./tools/start_develop/run-lint.sh
```

### 用 SprintCycle 开发产品

```bash
pip install sprintcycle
# 或：
pip install "sprintcycle[dashboard,mcp-sse]"

sprintcycle init
sprintcycle run "为登录模块添加单元测试"
sprintcycle dashboard
sprintcycle serve
```

---

## License

MIT License

---

## 社区与反馈

欢迎提交 Issue 和 Pull Request。

---

**SprintCycle — 让 AI 成为你的敏捷开发伙伴**
