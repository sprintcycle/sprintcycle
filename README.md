# SprintCycle

[English](README_EN.md)

**意图驱动的自我进化敏捷开发框架** — 用自然语言描述目标，生成可执行的 Release Plan（YAML），再按 Sprint 编排落地；CLI、MCP、可选 Web Dashboard 与 Python API 共用同一套 `SprintCycle` 入口。

当前版本：**0.9.2**（与 `sprintcycle.__version__` 一致）

## 环境要求

- Python **≥ 3.11**

## 安装

```bash
pip install -e .
```

可选能力（按需安装 extras，见 `pyproject.toml`）：

| Extra | 用途 |
|--------|------|
| `dashboard` / `full` | Web Dashboard（FastAPI + Uvicorn） |
| `mcp-sse` | MCP 以 SSE 方式对外提供（需 `uvicorn`、`starlette`） |
| `dev` | 测试、类型检查、import-linter 等开发依赖 |
| `mutation` | 突变测试（`mutmut`） |

示例：

```bash
pip install -e ".[full,dev]"
```

## 一分钟上手

在项目根目录初始化数据目录（状态与日志）：

```bash
sprintcycle init
```

**只看计划、不执行：**

```bash
sprintcycle plan "为登录流程增加单元测试" -m auto
```

**直接执行（无子命令时，整段参数视为 `run` 的意图）：**

```bash
sprintcycle run "修复 README 中的死链"
# 等价于：
sprintcycle "修复 README 中的死链"
```

常用选项：`--project` / `-p` 指定项目路径，`--format json` 机器可读输出，`--mode` 可选 `auto`、`evolution`、`normal`、`fix`、`test`，`--release-plan` 指向已有 YAML，`--resume` + `--execution-id` 断点续跑。若配置要求确认知识注入，需加 `--yes`。

## 核心能力

- **plan**：意图 → Release Plan（校验、扩展后可执行结构），不跑任务。
- **run**：编排 Sprint → `SprintExecutor` 执行任务；支持检查点与恢复。
- **diagnose**：项目健康度与问题摘要。
- **status** / **rollback** / **stop**：执行历史、回滚、停止运行中任务。
- **知识卡片**：`sprintcycle knowledge search` 检索；执行路径上可配合知识注入与确认策略。
- **MCP**：`sprintcycle serve`（默认 stdio；`--transport sse` 用于远程 Agent）。
- **Dashboard**：`sprintcycle dashboard`（需安装 dashboard 相关依赖）。

## CLI 速查

| 命令 | 说明 |
|------|------|
| `sprintcycle wizard` | 交互式选择 plan / run / diagnose / status |
| `sprintcycle plan <意图>` | 生成执行计划 |
| `sprintcycle run [意图]` | 执行 Sprint |
| `sprintcycle diagnose` | 项目体检 |
| `sprintcycle status [execution_id]` | 单条状态或列表 |
| `sprintcycle rollback <execution_id>` | 回滚 |
| `sprintcycle stop <execution_id>` | 停止 |
| `sprintcycle import-state` | JSON 状态目录导入 SQLite |
| `sprintcycle knowledge search` | 检索知识卡片 |
| `sprintcycle serve` | 启动 MCP Server |
| `sprintcycle dashboard` | 启动 Web UI |
| `sprintcycle init [path]` | 初始化 `.sprintcycle` 目录结构 |

全局选项：`-p/--project`、`--format text|json`、`-v/--verbose`。

## Python API

库与 CLI 共用 **`SprintCycle`**（`sprintcycle.api`）：`plan`、`run`、`diagnose`、`status`、`rollback`、`stop` 等与 CLI 语义对齐，便于在脚本、服务或自动化流水线中调用。

对外模型与解析入口见 `sprintcycle` 包导出：`ReleasePlan`、`ReleasePlanParser`、`ReleasePlanValidator`、`SprintOrchestrator`、`SprintExecutor` 等（详见 `sprintcycle/__init__.py`）。

## 仓库结构（高层）

- `sprintcycle/api.py` — 统一 API
- `sprintcycle/cli.py` — 命令行
- `sprintcycle/orchestration/` — Sprint 编排
- `sprintcycle/execution/` — 执行引擎、状态、Agent、知识钩子
- `sprintcycle/release_plan/` — 计划模型、解析、校验、生成与扩展
- `sprintcycle/intent/` — 意图解析与 Runner
- `sprintcycle/mcp/` — MCP 服务
- `sprintcycle/dashboard/` — 可选 Web 面板
- `tests/` — pytest 用例

## 开发与测试

```bash
pip install -e ".[dev]"
pytest
```

## 贡献

提交 issue / PR 前建议本地跑通 `pytest` 与项目约定的静态检查；具体许可证以仓库根目录说明文件为准（若有）。
