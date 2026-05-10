# SprintCycle

[中文](README.md)

**Intent-Driven Self-Evolving Agile Development Framework** — Describe goals in natural language, generate executable Release Plans (YAML), and orchestrate execution by Sprints. CLI, MCP, optional Web Dashboard, and Python API all share the same `SprintCycle` entrypoint.

Current Version: **0.9.2** (matches `sprintcycle.__version__`)

---

## ✨ Core Features

### 🎯 Intent-Driven Development
- **Natural language goals** → Auto-generate Release Plans → Execute by Sprints
- Checkpoint resume and recovery support
- Intelligent plan expansion and validation

### 🔧 Built-in Governance Engine
- **Multi-source validation plugin system** (powered by pluggy)
  - Architecture contract checking (import-linter)
  - Static code analysis (ruff + mypy)
  - YAML/Compose file validation
  - ADR (Architecture Decision Record) checking
  - Mutation testing (mutmut)
  - Dependency security scanning (pip-audit)
  - Extensible third-party plugins

- **Layered gate mechanism**
  - Planning Gate: Validation after plan generation
  - Review Gate: Quality check after execution completes

### 📊 Modern Dashboard
- Vue 3 + Element Plus frontend
- Real-time execution status monitoring
- Governance check result visualization
- Sprint execution history and trends
- Runtime configuration management
- SSE real-time push updates

### ⚙️ Flexible Configuration System
- **dynaconf** multi-source configuration loading
- **pydantic** type-safe validation
- Environment variable overrides
- Configuration file hot-reload
- Profile support (dev/test/prod)

### 🤖 MCP Server Integration
- Standard MCP protocol support
- SSE transport mode
- Integratable with any AI Agent

### 🔌 Extensible Architecture
- **Cache abstraction layer** (local memory → Redis)
- **Message queue abstraction layer** (extension point reserved)
- **Human-in-the-Loop (HITL)** interaction
- Plugin-based validation system

---

## 📋 Requirements

- Python **≥ 3.11**

---

## 🚀 Installation

### Basic Installation

```bash
pip install -e .
```

### Full Installation (Recommended)

```bash
pip install -e ".[full,dev]"
```

### Optional Capabilities (install extras as needed)

| Extra | Purpose |
|--------|---------|
| `dashboard` / `full` | Web Dashboard (FastAPI + Uvicorn) |
| `cache-redis` | Execution cache Redis backend (`[cache] backend = redis`) |
| `mcp-sse` | Expose MCP via SSE (requires `uvicorn`, `starlette`) |
| `dev` | Testing, type checking, import-linter, and other development dependencies |
| `mutation` | Mutation testing (`mutmut`) |

---

## ⚡ Quick Start

### Initialize

Initialize data directory (state and logs) in project root:

```bash
sprintcycle init
```

### Generate Plan (Without Execution)

```bash
sprintcycle plan "Add unit tests for login flow" -m auto
```

### Direct Execution

```bash
sprintcycle run "Fix broken links in README"
# Equivalent to:
sprintcycle "Fix broken links in README"
```

### Enable Governance Checks

```bash
sprintcycle run "Refactor configuration module" --governance-level standard
```

### Start Dashboard

```bash
# Production mode (requires frontend build first)
sprintcycle dashboard

# Development mode (start FastAPI + Vite together)
sprintcycle dashboard --dev
```

### Common Options

- `--project` / `-p`: Specify project path
- `--format json`: Machine-readable output
- `--mode`: Execution mode (`auto`, `evolution`, `normal`, `fix`, `test`)
- `--release-plan`: Use existing YAML plan
- `--resume` + `--execution-id`: Resume from checkpoint
- `--yes`: Auto-confirm knowledge injection

---

## 🎮 CLI Command Reference

### Core Workflow

| Command | Description |
|---------|-------------|
| `sprintcycle wizard` | Interactive selection: plan / run / diagnose / status |
| `sprintcycle plan <intent>` | Generate execution plan |
| `sprintcycle run [intent]` | Execute Sprint |
| `sprintcycle validate` | Run governance validation checks |

### Project Management

| Command | Description |
|---------|-------------|
| `sprintcycle diagnose` | Project health analysis |
| `sprintcycle status [execution_id]` | Single execution status or history list |
| `sprintcycle rollback <execution_id>` | Rollback execution |
| `sprintcycle stop <execution_id>` | Stop running task |

### Knowledge Management

| Command | Description |
|---------|-------------|
| `sprintcycle knowledge search` | Search knowledge cards |
| `sprintcycle knowledge list` | List all knowledge cards |

### Configuration Management

| Command | Description |
|---------|-------------|
| `sprintcycle config show` | Display current configuration |
| `sprintcycle config set <key> <value>` | Set configuration item |
| `sprintcycle config get <key>` | Get configuration item |

### Services & Integration

| Command | Description |
|---------|-------------|
| `sprintcycle serve` | Start MCP Server (stdio by default; `--transport sse` for remote Agents) |
| `sprintcycle dashboard` | Start Web UI (production: build `frontend` first; development: `--dev`) |

### System Commands

| Command | Description |
|---------|-------------|
| `sprintcycle init [path]` | Initialize `.sprintcycle` directory structure |
| `sprintcycle import-state` | Import JSON state directory to SQLite |

**Global options**: `-p/--project` (project path), `--format text|json` (output format), `-v/--verbose` (detailed logs)

---

## 🌐 Python API

Library and CLI share **`SprintCycle`** (`sprintcycle.api`): `plan`, `run`, `diagnose`, `status`, `rollback`, `stop` etc. are semantically aligned with CLI, making it easy to call in scripts, services, or automated pipelines.

Exported models and parsers available in `sprintcycle` package:

```python
from sprintcycle import (
    SprintCycle,
    ReleasePlan,
    ReleasePlanParser,
    ReleasePlanValidator,
    SprintOrchestrator,
    SprintExecutor,
)

# Basic usage
api = SprintCycle()
result = await api.run("Refactor authentication module", project_path="./my-project")
```

---

## 🏗️ Repository Structure

```
sprintcycle/
├── api.py                    # Unified API entrypoint
├── cli/                      # CLI package (`main.py` entry; console script `sprintcycle.cli:cli`)
├── config/                   # Configuration management
│   ├── settings.py           # dynaconf initialization
│   ├── runtime_config.py     # pydantic configuration model
│   ├── manager.py            # Configuration manager
│   └── backends/             # Configuration backend abstraction
├── orchestration/            # Sprint orchestration engine
├── execution/                # Execution engine
│   ├── agent/                # AI Agent execution
│   ├── state/                # State management
│   └── knowledge/            # Knowledge hooks and injection
├── release_plan/             # Release Plan models and parsing
├── governance/               # Governance engine
│   ├── runner.py             # Governance executor
│   ├── pluggy_host.py        # Plugin system host
│   ├── report.py             # Governance reports
│   └── plugins/              # Built-in validation plugins
├── dashboard/                # Web Dashboard
│   ├── server.py             # FastAPI backend
│   ├── routes/               # API routes
│   └── frontend/             # Vue 3 + Element Plus frontend
├── events/                   # Event bus
├── mcp/                      # MCP server
├── governance/
│   ├── hitl/                 # Governance-side Human-in-the-Loop
│   ├── suggestion/           # Suggestion review & approval
│   └── arch_guard/           # Architecture & rule guards
├── runtime_observability/    # Runtime observability / trace / replay
├── runtime_observability/    # Runtime observability / trace / replay
├── cache/                    # Cache abstraction layer
├── mq/                       # Message queue abstraction
└── validation/               # Multi-source validation plugin system
```

---

## 🔍 Governance & Validation

### Governance Levels

| Level | Checks Performed | Use Case |
|-------|------------------|----------|
| `minimal` | Basic syntax checking only | Rapid iteration |
| `standard` | Static analysis + architecture checks | Daily development |
| `strict` | All checks + mutation testing | Pre-release validation |

### Built-in Validation Plugins

| Plugin | Functionality | Dependency |
|--------|---------------|------------|
| Architecture | Import layer contract checking | import-linter |
| StaticAnalysis | ruff + mypy static checking | ruff, mypy |
| YAMLValidation | YAML file syntax validation | pyyaml |
| ComposeHint | Docker Compose file checking | PyYAML |
| ADRCheck | Architecture decision record consistency | - |
| MutmutPlugin | Mutation testing (optional) | mutmut |
| PipAuditPlugin | Dependency security scanning (optional) | pip-audit |

---

## 📚 Documentation & Resources

- `docs/RELEASE_CHECKLIST.md` — Release checklist
- `docs/GOVERNANCE_HEAVY_CHECKS.md` — Heavy governance checks documentation
- More technical documentation in `docs/` directory

---

## 🧪 Development & Testing

### Framework Development (Contributing to SprintCycle)

```bash
# One-click development environment setup
./tools/start_develop/dev-setup.sh

# Activate development environment
source tools/start_develop/activate.sh

# Run core tests
pytest tests/test_p0_runtime.py -v

# Run full test suite
pytest tests/ -v

# Code quality checks
./tools/start_develop/run-lint.sh
```

### Using SprintCycle to Build Products

**pip install:**
```bash
pip install sprintcycle
# or with full features
pip install sprintcycle[dashboard,mcp-sse]
```

**Quick start:**
```bash
# Initialize
sprintcycle init

# Direct execution
sprintcycle run "Add unit tests for login module"

# Configure LLM: set OPENAI_API_KEY in .env
```

**Dashboard monitoring:**
```bash
sprintcycle dashboard
```

**MCP integration:**
```bash
sprintcycle serve
```

For detailed guide, see [DEVELOPMENT_GUIDE.md](tools/start_develop/DEVELOPMENT_GUIDE.md).

---

## 📄 License
## 📄 License

MIT License

---

## 🤝 Community & Feedback

Issues and Pull Requests are welcome!

---

**SprintCycle — Let AI be your agile development partner** 🚀
