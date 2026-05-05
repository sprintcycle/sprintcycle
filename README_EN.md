# SprintCycle - Self-Evolving Agile Development Framework

[![Version](https://img.shields.io/badge/version-v0.9.2-blue.svg)](sprintcycle/__init__.py)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-50%20passed-brightgreen.svg)]()

**SprintCycle** is a PRD-driven self-evolving agile development framework that implements a closed loop of code generation, test verification, and continuous optimization through a unified evolution pipeline.

## Product & technical spec (V4.0 canonical)

For external communication and architecture reviews, the **in-repo** documents below are authoritative if they differ from any exported note (e.g. Youdao “V4.0” `.mhtml`):

1. **[`docs/PRODUCT_TECH_V4.md`](docs/PRODUCT_TECH_V4.md)** — canonical entry + primary execution path  
2. **[`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`](SPRINTCYCLE_PRODUCT_TECH_PLAN.md)** — full revised plan (G1–G4, six phases, §6 roadmap)

**Primary execution path**: `SprintCycle` → `TaskDispatcher` → `SprintExecutor.execute_sprints` (`EvolutionPipeline` is for evolution/diagnostic flows, not a second “only” orchestrator).

### Quality gates G1–G4 (vs `quality_level` / `quality_profile`)

| Gate | Meaning | Anchors |
|------|---------|---------|
| **G1** | Static & conventions | Ruff / static analysis; `runs_static_gate` from L1+ |
| **G2** | Tests & coverage | `MeasurementProvider`, pytest; L2/L3 |
| **G3** | Fitness & regression | Measurement dimensions, feedback; emphasis at L3 |
| **G4** | Architecture invariants | `[tool.importlinter]` in `pyproject.toml`; optional Semgrep (`.github/workflows/semgrep.yml`) |

See **`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`** §2.3 and **`docs/PRODUCT_TECH_V4.md`**.

## Key Features

- **Unified API Layer** - 6 operations: plan/run/diagnose/status/rollback/stop
- **Three Entry Points** - CLI / MCP (stdio + SSE dual transport) / Dashboard Web UI
- **7 Agents** - analyzer/architect/coder/evolver/tester/regression_tester/traceback_parser
- **Dashboard Four Panels** - PRD Editor / Execution History / Diagnostics / Live Events (EventBus→SSE)
- **FeedbackLoop Feedback Loop** - Continuous optimization mechanism for evolution pipeline
- **Resume Support** - Safely resume execution from checkpoint
- **Safe Stop** - Gracefully stop sprint execution
- **Execution State Persistence** - StateStore + Checkpoint state storage
- **Differentiated Evolution Strategies** - Auto-select evolution path based on problem type
- **Intelligent Error Routing** - Three-level routing: LEVEL_1_STATIC → LEVEL_2_PATTERN → LEVEL_3_LLM
- **Multi-Engine Coding** - `aider`, **Claude Code** (`claude_code`), **Cursor Cookbook** (`cursor_cookbook`), with LiteLLM fallback ([`docs/CODING_ENGINES_CLAUDE_CURSOR.md`](docs/CODING_ENGINES_CLAUDE_CURSOR.md))
- **Unified Configuration** - RuntimeConfig manages all configuration items

## Quick Start

### Installation

```bash
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle
pip install -e .
```

### Configuration

```bash
# Set API Key
export DEEPSEEK_API_KEY="your-api-key"

# Or create .env file
echo "DEEPSEEK_API_KEY=your-api-key" > .env
```

### Basic Usage

```python
from sprintcycle.prd.models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode
from sprintcycle.execution.engine import ExecutionEngine

prd = PRD(
    project=PRDProject(name="my-project", path="."),
    mode=ExecutionMode.NORMAL,
    sprints=[
        PRDSprint(
            name="Sprint 1",
            tasks=[PRDTask(task="Ship a minimal runnable slice", agent="coder")],
        )
    ],
)

engine = ExecutionEngine()
result = await engine.execute(prd)
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRD-driven Sprint                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌─────────────────┐    ┌───────────┐ │
│  │ ManualPRD    │    │ EvolutionPipeline│    │ Diagnostic│ │
│  │ Source       │───▶│ (Unified Pipe)   │───▶│ PRD Source│ │
│  └──────────────┘    └─────────────────┘    └───────────┘ │
│                              │                              │
│                              ▼                              │
│                     ┌─────────────────┐                    │
│                     │  SprintExecutor │                    │
│                     └─────────────────┘                    │
│                              │                              │
│              ┌───────────────┼───────────────┐            │
│              ▼               ▼               ▼            │
│        ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│        │ Analyzer │    │  Coder   │    │  Tester  │      │
│        └──────────┘    └──────────┘    └──────────┘      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │        Error Router (Three-Level)                    │  │
│  │  LEVEL_1_STATIC → LEVEL_2_PATTERN → LEVEL_3_LLM    │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core Modules

| Module | Path | Description |
|--------|------|-------------|
| `EvolutionPipeline` | `sprintcycle/evolution/pipeline.py` | Unified evolution pipeline |
| `SprintExecutor` | `sprintcycle/execution/sprint_executor.py` | Sprint executor |
| `ExecutionEngine` | `sprintcycle/execution/engine.py` | Unified execution engine |
| `ErrorRouter` | `sprintcycle/execution/error_router.py` | Error routing |
| `PRDValidator` | `sprintcycle/prd/validator.py` | PRD validator |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `SPRINTCYCLE_LLM_PROVIDER` | LLM provider | deepseek |
| `SPRINTCYCLE_LLM_MODEL` | Model name | deepseek-reasoner |
| `SPRINTCYCLE_LLM_TEMPERATURE` | Temperature | 0.7 |
| `SPRINTCYCLE_LLM_MAX_TOKENS` | Max tokens | 2048 |
| `SPRINTCYCLE_EVOLUTION_ENABLED` | Enable evolution | true |
| `SPRINTCYCLE_DRY_RUN` | Dry run mode | false |
| `SPRINTCYCLE_MAX_SPRINTS` | Max sprints | 10 |
| `SPRINTCYCLE_PARALLEL_TASKS` | Parallel tasks | 3 |
| `SPRINTCYCLE_LOG_LEVEL` | Log level | INFO |
| `SPRINTCYCLE_QUALITY_PROFILE` | Quality preset `off`/`fast`/`default`/`strict` (§6.3) | `default` |
| `SPRINTCYCLE_CODING_ENGINE` | Coder engine (overrides toml) | `aider` |
| `SPRINTCYCLE_CLAUDE_BIN` | Claude Code executable | `claude` |
| `SPRINTCYCLE_CURSOR_USE_CLI` | Also run Cursor `agent` CLI for cookbook | unset |

See [`docs/CODING_ENGINES_CLAUDE_CURSOR.md`](docs/CODING_ENGINES_CLAUDE_CURSOR.md) for the full list.

### Claude Code & Cursor Cookbook

- **Claude Code**: set `[engine] name = "claude_code"` (or `SPRINTCYCLE_CODING_ENGINE=claude_code`) after installing the official `claude` CLI. SprintCycle invokes non-interactive `claude -p`.
- **Cursor Cookbook**: with `name = "cursor_cookbook"`, writes markdown recipes under `.sprintcycle/cursor-cookbook/` for use in Cursor Agent / Chat; set `SPRINTCYCLE_CURSOR_USE_CLI=1` to optionally run `agent -p` once per task.

Full bilingual notes: **[`docs/CODING_ENGINES_CLAUDE_CURSOR.md`](docs/CODING_ENGINES_CLAUDE_CURSOR.md)**.

## Project Structure

```
sprintcycle/
├── cli.py                    # CLI entry point
├── coding_engine.py          # Coding engine
├── llm_provider.py           # LLM provider
├── exceptions.py             # Exception definitions
│
├── config/
│   └── manager.py            # Config management (RuntimeConfig, LLMConfig)
│
├── evolution/                 # Evolution system
│   ├── pipeline.py           # EvolutionPipeline
│   ├── prd_source.py         # PRD source (Manual/Diagnostic)
│   ├── measurement.py        # Measurement
│   ├── memory_store.py       # Memory store
│   └── rollback_manager.py   # Rollback manager
│
├── diagnostic/               # Diagnostic system
│   ├── provider.py           # Diagnostic provider
│   ├── health_report.py       # Health report
│   └── prd_generator.py      # PRD generator
│
├── execution/                 # Execution system
│   ├── engine.py              # Execution engine
│   ├── sprint_executor.py     # Sprint executor
│   ├── error_router.py        # Error router
│   ├── static_analyzer.py     # Static analyzer
│   └── agents/                # Agent implementations
│       ├── analyzer.py
│       ├── coder.py
│       └── tester.py
│
├── intent/                    # Intent recognition
│   ├── parser.py
│   └── runner.py
│
├── prd/                       # PRD processing
│   ├── models.py             # PRD models
│   ├── parser.py            # Parser
│   └── validator.py         # Validator
│
└── integrations/              # Integrations
    └── evolution_integration.py
```

## Development

### Canonical dev-setup path

The script in-repo is **`docs-dev/dev-setup.sh`**. For `curl`/`bash` from raw GitHub, substitute org, repo, and ref (fork or tag), e.g.  
`https://raw.githubusercontent.com/<org>/<repo>/<ref>/docs-dev/dev-setup.sh`  
CI asserts this file exists on the default branch.

### Run Tests

```bash
pytest tests/ -v
```

Includes **Hypothesis** property tests (`tests/test_g4_properties.py`, V4.0 §6.4); install with `pip install -e ".[dev]"`.

### Architecture gate (G4)

- **Required on PRs**: GitHub Actions job **`architecture-gate`** runs `lint-imports` (contracts in `pyproject.toml`).
- **Mutation testing (optional)**: `pip install -e ".[mutation]"`; see **`.github/workflows/mutation.yml`**.
- **Semgrep (optional)**: **`.github/workflows/semgrep.yml`** — failures do not block the main CI workflow.

### Code Quality

```bash
# mypy type checking
mypy sprintcycle/ --ignore-missing-imports

# ruff linting
ruff check sprintcycle/
```

### Status

- **Version**: 0.9.2
- **Tests**: see CI / `pytest tests/` (includes G4 property tests and import-linter test)
- **mypy**: 0 errors

## License

MIT License
