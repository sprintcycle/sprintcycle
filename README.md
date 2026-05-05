# SprintCycle - 自进化敏捷开发框架

[![Version](https://img.shields.io/badge/version-v0.9.2-blue.svg)](sprintcycle/__init__.py)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-50%20passed-brightgreen.svg)]()

**SprintCycle** 是一个 PRD 驱动的自我进化敏捷开发框架，通过统一进化管道实现代码生成、测试验证与持续优化的闭环。

## 产品与技术方案（V4.0 唯一真理源）

对外叙述与架构评审以仓库内文档为准，与附件《3.1 SprintCycle 产品与技术完整方案 V4.0》冲突时，**以下文件优先**：

1. **[`docs/PRODUCT_TECH_V4.md`](docs/PRODUCT_TECH_V4.md)** — 真理源入口与主路径声明  
2. **[`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`](SPRINTCYCLE_PRODUCT_TECH_PLAN.md)** — 完整修订版（G1–G4、六 Phase、改造路线 §6）

**主执行路径**：`SprintCycle` → `SprintOrchestrator` → `SprintExecutor.execute_sprints`（`EvolutionPipeline` 为进化/实验场景，非并列「第二唯一编排」）。

### 与 Scrum 的对应（命名对齐）

| 代码 / 文件 | Scrum 里怎么理解 |
|-------------|------------------|
| 根包 `ReleasePlan` / plan YAML | **可执行交付计划**（多 Sprint）；`from sprintcycle import ReleasePlan, ReleasePlanParser` |
| `SprintDefinition`、`sprints[]` | 一次 **Sprint**；`goals` ≈ Sprint Goal；`tasks` ≈ **Sprint Backlog** |
| `SprintBacklogItem`、`description`（YAML 仅 `description:`） | **Sprint Backlog Item** 的工作说明 |
| `SprintOrchestrator` | **Sprint 执行编排**（orchestrator），非日历排期 |

完整分级与命名约定见 **[`docs/DESIGN_SCRUM_NAMING_MIGRATION.md`](docs/DESIGN_SCRUM_NAMING_MIGRATION.md)**。

### 质量门禁 G1–G4（与 `quality_level` / `quality_profile` 对照）

| 门禁 | 含义 | 代码与配置锚点 |
|------|------|----------------|
| **G1** | 静态与规范 | Ruff / 静态分析；`L1+` 起 `runs_static_gate` |
| **G2** | 测试与覆盖 | `MeasurementProvider`、pytest；`L2/L3` |
| **G3** | 适应度与回归 | 测量维度、反馈闭环；`L3` 侧重 |
| **G4** | 架构不变量 | `pyproject.toml` 中 `[tool.importlinter]`；可选 Semgrep（`.github/workflows/semgrep.yml`） |

详见 **`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`** §2.3 与 **`docs/PRODUCT_TECH_V4.md`**。

## 核心特性

- **统一 API 层** - plan/run/diagnose/status/rollback/stop 六大操作
- **三端入口** - CLI / MCP（stdio + SSE 双传输）/ Dashboard Web UI
- **7 个 Agent** - analyzer/architect/coder/evolver/tester/regression_tester/traceback_parser
- **Dashboard 四面板** - PRD 编辑器 / 执行历史 / 诊断 / 实时事件（EventBus→SSE）
- **FeedbackLoop 反馈闭环** - 进化管道的持续优化机制
- **断点续跑** - resume 安全恢复执行状态
- **安全取消** - stop 优雅停止 sprint
- **执行结果持久化** - StateStore + Checkpoint 状态存储
- **差异化进化策略** - 根据问题类型自动选择进化路径
- **智能错误路由** - LEVEL_1_STATIC → LEVEL_2_PATTERN → LEVEL_3_LLM 三级路由
- **多编码引擎** - `aider` / **Claude Code** (`claude_code`) / **Cursor Cookbook** (`cursor_cookbook`)，未就绪时回退 LiteLLM（详见 [`docs/CODING_ENGINES_CLAUDE_CURSOR.md`](docs/CODING_ENGINES_CLAUDE_CURSOR.md)）
- **统一配置** - RuntimeConfig 统一管理所有配置项

## 快速开始

### 安装

```bash
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle
pip install -e .
```

### 配置

```bash
# 设置 API Key
export DEEPSEEK_API_KEY="your-api-key"

# 或创建 .env 文件
echo "DEEPSEEK_API_KEY=your-api-key" > .env
```

### 基本使用

```python
from sprintcycle.release_plan.models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode
from sprintcycle.execution.engine import ExecutionEngine

prd = PRD(
    project=PRDProject(name="my-project", path="."),
    mode=ExecutionMode.NORMAL,
    sprints=[
        PRDSprint(
            name="Sprint 1",
            tasks=[PRDTask(description="实现一个可运行的最小功能", agent="coder")],
        )
    ],
)

engine = ExecutionEngine()
result = await engine.execute(prd)
```

进化管道从磁盘加载人工计划时，默认在项目根目录的 **`release_plan/*.yaml`** 查找（`ManualPRDSource` 的 `plan_subdir` 可改为其它相对路径）。

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    PRD-driven Sprint                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌─────────────────┐    ┌───────────┐ │
│  │ ManualPRD    │    │ EvolutionPipeline│    │ Diagnostic│ │
│  │ Source       │───▶│ (统一进化管道)   │───▶│ PRD Source│ │
│  └──────────────┘    └─────────────────┘    └───────────┘ │
│                              │                              │
│                              ▼                              │
│                     ┌─────────────────┐                     │
│                     │  SprintExecutor │                     │
│                     └─────────────────┘                     │
│                              │                              │
│              ┌───────────────┼───────────────┐            │
│              ▼               ▼               ▼            │
│        ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│        │ Analyzer │    │  Coder   │    │  Tester  │       │
│        └──────────┘    └──────────┘    └──────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        Error Router (三级路由)                       │   │
│  │  LEVEL_1_STATIC → LEVEL_2_PATTERN → LEVEL_3_LLM     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 路径 | 说明 |
|------|------|------|
| `EvolutionPipeline` | `sprintcycle/evolution/pipeline.py` | 统一进化管道 |
| `SprintExecutor` | `sprintcycle/execution/sprint_executor.py` | Sprint 执行器 |
| `ExecutionEngine` | `sprintcycle/execution/engine.py` | 统一执行引擎 |
| `ErrorRouter` | `sprintcycle/execution/error_router.py` | 错误路由 |
| `PRDValidator` | `sprintcycle/release_plan/validator.py` | 执行计划验证器 |

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `SPRINTCYCLE_LLM_PROVIDER` | LLM 提供商 | deepseek |
| `SPRINTCYCLE_LLM_MODEL` | 模型名称 | deepseek-reasoner |
| `SPRINTCYCLE_LLM_TEMPERATURE` | 温度参数 | 0.7 |
| `SPRINTCYCLE_LLM_MAX_TOKENS` | 最大 Token | 2048 |
| `SPRINTCYCLE_EVOLUTION_ENABLED` | 启用进化 | true |
| `SPRINTCYCLE_DRY_RUN` | 试运行模式 | false |
| `SPRINTCYCLE_MAX_SPRINTS` | 最大 Sprint 数 | 10 |
| `SPRINTCYCLE_PARALLEL_TASKS` | 并行任务数 | 3 |
| `SPRINTCYCLE_LOG_LEVEL` | 日志级别 | INFO |
| `SPRINTCYCLE_QUALITY_PROFILE` | 质量预设 `off`/`fast`/`default`/`strict`（§6.3） | `default` |
| `SPRINTCYCLE_CODING_ENGINE` | Coder 编码引擎（覆盖 toml） | `aider` |
| `SPRINTCYCLE_CLAUDE_BIN` | Claude Code 可执行文件 | `claude` |
| `SPRINTCYCLE_CURSOR_USE_CLI` | Cursor Cookbook 是否再调 `agent` CLI | 未设置 |

更多环境变量见 [`docs/CODING_ENGINES_CLAUDE_CURSOR.md`](docs/CODING_ENGINES_CLAUDE_CURSOR.md)。

### Claude Code 与 Cursor Cookbook

- **Claude Code**：本机安装官方 CLI 后，在 `sprintcycle.toml` 的 `[engine]` 中设置 `name = "claude_code"`（或 `SPRINTCYCLE_CODING_ENGINE=claude_code`）。SprintCycle 使用非交互 `claude -p` 调用。
- **Cursor Cookbook**：`name = "cursor_cookbook"` 时会在项目下生成 `.sprintcycle/cursor-cookbook/*.md` 食谱文件，便于在 Cursor 中打开并粘贴到 Agent；可选 `SPRINTCYCLE_CURSOR_USE_CLI=1` 触发本机 `agent -p` 一轮。

完整说明与中英对照见 **[`docs/CODING_ENGINES_CLAUDE_CURSOR.md`](docs/CODING_ENGINES_CLAUDE_CURSOR.md)**。

## 项目结构

```
sprintcycle/
├── cli.py                    # 命令行入口
├── coding_engine.py          # 编码引擎
├── llm_provider.py           # LLM 提供商
├── exceptions.py             # 异常定义
│
├── config/
│   └── manager.py            # 配置管理 (RuntimeConfig, LLMConfig)
│
├── evolution/                 # 进化系统
│   ├── pipeline.py           # EvolutionPipeline
│   ├── evolution_plan_source.py  # 进化计划源 (Manual/Diagnostic)
│   ├── measurement.py        # 测量
│   ├── memory_store.py       # 记忆存储
│   └── rollback_manager.py   # 回滚管理
│
├── diagnostic/               # 诊断系统
│   ├── provider.py           # 诊断提供者
│   ├── health_report.py      # 健康报告
│   └── release_plan_generator.py  # 由诊断生成执行计划
│
├── execution/                # 执行系统
│   ├── engine.py             # 执行引擎
│   ├── sprint_executor.py    # Sprint 执行器
│   ├── error_router.py       # 错误路由
│   ├── static_analyzer.py    # 静态分析
│   └── agents/               # Agent 实现
│       ├── analyzer.py
│       ├── coder.py
│       └── tester.py
│
├── intent/                    # 意图识别
│   ├── parser.py
│   └── runner.py
│
├── release_plan/              # 可执行多 Sprint 计划（实现类名 PRD*；根包导出 Scrum 名）
│   ├── models.py            # 数据模型
│   ├── parser.py            # 解析器
│   └── validator.py         # 验证器
│
├── orchestration/             # Sprint 编排
│   └── sprint_orchestrator.py # SprintOrchestrator
│
└── integrations/             # 集成
    └── evolution_integration.py
```

## 开发

### 一键环境脚本（canonical 路径）

仓库内脚本路径为 **`docs-dev/dev-setup.sh`**（勿假设 `main/dev-setup.sh` 等未存在路径）。从 GitHub  raw 安装时请将组织、仓库与分支换成你的 fork 或固定 tag，例如：

`https://raw.githubusercontent.com/<org>/<repo>/<ref>/docs-dev/dev-setup.sh`

CI 会校验该文件存在于默认分支。

### 运行测试

```bash
pytest tests/ -v
```

含 **Hypothesis** 属性测试（`tests/test_g4_properties.py`，V4.0 §6.4）；需 `pip install -e ".[dev]"`。

### 架构门禁（G4）

- **PR 必过**：GitHub Actions 中 **`architecture-gate`** job 运行 `lint-imports`（与 `pyproject.toml` 中契约一致）。
- **突变测试（可选）**：`pip install -e ".[mutation]"`；定时/手动见 **`.github/workflows/mutation.yml`**。
- **Semgrep（可选）**：见 **`.github/workflows/semgrep.yml`**，失败不阻塞主 CI。

### 代码检查

```bash
# mypy 类型检查
mypy sprintcycle/ --ignore-missing-imports

# ruff 代码格式
ruff check sprintcycle/
```

### 状态

- **版本**: 0.9.2
- **测试**: 以 CI / `pytest tests/` 为准（含 G4 属性测试与 import-linter 单测）
- **mypy**: 0 errors

## License

MIT License
