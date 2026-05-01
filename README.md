# SprintCycle - 自进化敏捷开发框架

[![Version](https://img.shields.io/badge/version-v0.9.2-blue.svg)](sprintcycle/__init__.py)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-50%20passed-brightgreen.svg)]()

**SprintCycle** 是一个 PRD 驱动的自我进化敏捷开发框架，通过统一进化管道实现代码生成、测试验证与持续优化的闭环。

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
- **多编码引擎** - 支持 cursor、llm、claude 等编码引擎
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
from sprintcycle.prd.models import PRD, ExecutionMode
from sprintcycle.execution.engine import ExecutionEngine

# 创建 PRD
prd = PRD(
    project_name="my-project",
    mode=ExecutionMode.NORMAL,
    # ... 其他配置
)

# 执行
engine = ExecutionEngine()
result = await engine.execute(prd)
```

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
| `PRDValidator` | `sprintcycle/prd/validator.py` | PRD 验证器 |

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
| `CODING_ENGINE` | 编码引擎 | cursor |

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
│   ├── prd_source.py         # PRD 源 (Manual/Diagnostic)
│   ├── measurement.py        # 测量
│   ├── memory_store.py       # 记忆存储
│   └── rollback_manager.py   # 回滚管理
│
├── diagnostic/               # 诊断系统
│   ├── provider.py           # 诊断提供者
│   ├── health_report.py      # 健康报告
│   └── prd_generator.py      # PRD 生成
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
├── prd/                       # PRD 处理
│   ├── models.py            # PRD 模型
│   ├── parser.py            # 解析器
│   └── validator.py         # 验证器
│
└── integrations/             # 集成
    └── evolution_integration.py
```

## 开发

### 运行测试

```bash
pytest tests/ -v
```

### 代码检查

```bash
# mypy 类型检查
mypy sprintcycle/ --ignore-missing-imports

# ruff 代码格式
ruff check sprintcycle/
```

### 状态

- **版本**: 0.9.2
- **代码行数**: ~15000
- **测试**: 50 passed (集成测试)
- **mypy**: 0 errors

## License

MIT License
