# SprintCycle

[English](README_EN.md)

**意图驱动的自我进化敏捷开发框架** — 用自然语言描述目标，生成可执行的 Release Plan（YAML），再按 Sprint 编排落地；CLI、MCP、可选 Web Dashboard 与 Python API 共用同一套 `SprintCycle` 入口。

当前版本：**0.9.2**（与 `sprintcycle.__version__` 一致）

---

## ✨ 核心特性

### 🎯 意图驱动开发
- **自然语言描述目标** → 自动生成 Release Plan → 按 Sprint 执行
- 支持断点续跑与恢复
- 智能计划扩展与校验

### 🔧 内置治理引擎
- **多源验证插件系统**（基于 pluggy）
  - 架构契约检查（import-linter）
  - 静态代码分析（ruff + mypy）
  - YAML/Compose 文件验证
  - ADR（架构决策记录）检查
  - 突变测试（mutmut）
  - 依赖安全扫描（pip-audit）
  - 可扩展第三方插件

- **分层门禁机制**
  - Planning Gate：计划生成后验证
  - Review Gate：执行完成后质量检查

### 📊 现代化 Dashboard
- Vue 3 + Element Plus 前端
- 实时执行状态监控
- 治理检查结果可视化
- Sprint 执行历史与趋势
- 运行时配置管理
- SSE 实时推送更新

### ⚙️ 灵活配置系统
- **dynaconf** 多源配置加载
- **pydantic** 类型安全验证
- 环境变量覆盖
- 配置文件热重载
- Profile 支持（dev/test/prod）

### 🤖 MCP 服务器集成
- 标准 MCP 协议支持
- SSE 传输模式
- 可被任意 AI Agent 集成使用

### 🔌 可扩展架构
- **缓存抽象层**（本地内存 → Redis）
- **消息队列抽象层**（预留扩展点）
- **Human-in-the-Loop** 人机回环
- 插件化验证系统

---

## 📋 环境要求

- Python **≥ 3.11**

---

## 🚀 安装

### 基础安装

```bash
pip install -e .
```

### 完整功能安装（推荐）

```bash
pip install -e ".[full,dev]"
```

### 可选能力（按需安装 extras）

| Extra | 用途 |
|--------|------|
| `dashboard` / `full` | Web Dashboard（FastAPI + Uvicorn） |
| `cache-redis` | 执行缓存 Redis 后端（`[cache] backend = redis`） |
| `mcp-sse` | MCP 以 SSE 方式对外提供（需 `uvicorn`、`starlette`） |
| `dev` | 测试、类型检查、import-linter 等开发依赖 |
| `mutation` | 突变测试（`mutmut`） |

---

## ⚡ 一分钟上手

### 初始化

在项目根目录初始化数据目录（状态与日志）：

```bash
sprintcycle init
```

### 生成计划（不执行）

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
# 生产模式（需先 build frontend）
sprintcycle dashboard

# 开发模式（同时启动 FastAPI + Vite）
sprintcycle dashboard --dev
```

### 常用选项

- `--project` / `-p`：指定项目路径
- `--format json`：机器可读输出
- `--mode`：执行模式（`auto`、`evolution`、`normal`、`fix`、`test`）
- `--release-plan`：使用已有 YAML 计划
- `--resume` + `--execution-id`：断点续跑
- `--yes`：自动确认知识注入

---

## 🎮 CLI 命令速查

### 核心流程

| 命令 | 说明 |
|------|------|
| `sprintcycle wizard` | 交互式选择 plan / run / diagnose / status |
| `sprintcycle plan <意图>` | 生成执行计划 |
| `sprintcycle run [意图]` | 执行 Sprint |
| `sprintcycle validate` | 运行治理验证检查 |

### 项目管理

| 命令 | 说明 |
|------|------|
| `sprintcycle diagnose` | 项目体检与健康度分析 |
| `sprintcycle status [execution_id]` | 单条执行状态或历史列表 |
| `sprintcycle rollback <execution_id>` | 回滚执行 |
| `sprintcycle stop <execution_id>` | 停止运行中任务 |

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
| `sprintcycle dashboard` | 启动 Web UI（生产：先 `frontend` build；开发：`--dev`） |

### 系统命令

| 命令 | 说明 |
|------|------|
| `sprintcycle init [path]` | 初始化 `.sprintcycle` 目录结构 |
| `sprintcycle import-state` | JSON 状态目录导入 SQLite |

**全局选项**：`-p/--project`（项目路径）、`--format text|json`（输出格式）、`-v/--verbose`（详细日志）

---

## 🌐 Python API

库与 CLI 共用 **`SprintCycle`**（`sprintcycle.api`）：`plan`、`run`、`diagnose`、`status`、`rollback`、`stop` 等与 CLI 语义对齐，便于在脚本、服务或自动化流水线中调用。

对外模型与解析入口见 `sprintcycle` 包导出：

```python
from sprintcycle import (
    SprintCycle,
    ReleasePlan,
    ReleasePlanParser,
    ReleasePlanValidator,
    SprintOrchestrator,
    SprintExecutor,
    GovernanceRunner,
)

# 基本使用
api = SprintCycle()
result = await api.run("重构认证模块", project_path="./my-project")
```

---

## 🏗️ 仓库结构

```
sprintcycle/
├── api.py                    # 统一 API 入口
├── cli.py                    # 命令行接口
├── config/                   # 配置管理
│   ├── settings.py           # dynaconf 初始化
│   ├── runtime_config.py     # pydantic 配置模型
│   ├── manager.py            # 配置管理器
│   └── backends/             # 配置后端抽象
├── orchestration/            # Sprint 编排引擎
├── execution/                # 执行引擎
│   ├── agent/                # AI Agent 执行
│   ├── state/                # 状态管理
│   └── knowledge/            # 知识钩子与注入
├── release_plan/             # Release Plan 模型与解析
├── governance/               # 治理引擎
│   ├── runner.py             # 治理执行器
│   ├── pluggy_host.py        # 插件系统主机
│   ├── report.py             # 治理报告
│   └── plugins/              # 内置验证插件
├── dashboard/                # Web Dashboard
│   ├── server.py             # FastAPI 后端
│   ├── routes/               # API 路由
│   └── frontend/             # Vue 3 + Element Plus 前端
├── events/                   # 事件总线
├── mcp/                      # MCP 服务器
├── hitl/                     # Human-in-the-Loop
├── cache/                    # 缓存抽象层
├── mq/                       # 消息队列抽象
└── validation/               # 多源验证插件系统
```

---

## 🔍 治理与验证

### 治理级别

| 级别 | 检查项 | 适用场景 |
|------|--------|---------|
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

## 📚 文档与资源

- `docs/RELEASE_CHECKLIST.md` — 发布检查清单
- `sprintcycle/governance/GOVERNANCE_HEAVY_CHECKS.md` — 重量级治理检查说明
- `docs/` 目录下更多技术文档

---

## 🧪 开发与测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行核心测试
pytest tests/test_p0_runtime.py -v

# 运行完整测试套件
pytest tests/ -v

# 架构检查
lint-imports

# 类型检查
mypy sprintcycle/
```

---

## 📄 License

MIT License

---

## 🤝 社区与反馈

欢迎提交 Issue 和 Pull Request！

---

**SprintCycle — 让 AI 成为你的敏捷开发伙伴** 🚀
