# SprintCycle

[中文](README.md)

**Intent-driven, self-evolving agile delivery framework** — describe goals in natural language, materialize a runnable **Release Plan** (YAML), then execute it through Sprint orchestration. The CLI, MCP server, optional Web Dashboard, and Python API all share the same **`SprintCycle`** entry point.

Current version: **0.9.2** (aligned with `sprintcycle.__version__`)

## Requirements

- Python **≥ 3.11**

## Installation

```bash
pip install -e .
```

Optional extras (see `pyproject.toml`):

| Extra | Purpose |
|--------|---------|
| `dashboard` / `full` | Web Dashboard (FastAPI + Uvicorn) |
| `mcp-sse` | MCP over SSE (`uvicorn`, `starlette`) |
| `dev` | Tests, typing, import-linter, etc. |
| `mutation` | Mutation testing (`mutmut`) |

Example:

```bash
pip install -e ".[full,dev]"
```

## Quick start

Initialize per-project directories (state and logs):

```bash
sprintcycle init
```

**Plan only (no execution):**

```bash
sprintcycle plan "Add unit tests for the login flow" -m auto
```

**Run (default group command forwards bare args to `run`):**

```bash
sprintcycle run "Fix dead links in README"
# same as:
sprintcycle "Fix dead links in README"
```

Common flags: `--project` / `-p` for repo root, `--format json` for machine-readable output, `--mode` one of `auto`, `evolution`, `normal`, `fix`, `test`, `--release-plan` for an existing YAML, `--resume` with `--execution-id` to continue. If knowledge injection requires confirmation, pass `--yes`.

## Capabilities

- **plan**: intent → validated / expanded Release Plan; no tasks executed.
- **run**: orchestrated Sprints via `SprintExecutor`; checkpoints and resume supported.
- **diagnose**: project health summary and issues.
- **status** / **rollback** / **stop**: history, rollback, and cancel in-flight work.
- **Knowledge cards**: `sprintcycle knowledge search`; execution path supports injection and confirmation policies.
- **MCP**: `sprintcycle serve` (default **stdio**; `--transport sse` for remote agents).
- **Dashboard**: `sprintcycle dashboard` (install dashboard extras first).

## CLI cheat sheet

| Command | Description |
|--------|-------------|
| `sprintcycle wizard` | Interactive plan / run / diagnose / status |
| `sprintcycle plan <intent>` | Generate execution plan |
| `sprintcycle run [intent]` | Execute sprints |
| `sprintcycle diagnose` | Health check |
| `sprintcycle status [execution_id]` | Single run or list |
| `sprintcycle rollback <execution_id>` | Roll back |
| `sprintcycle stop <execution_id>` | Stop a run |
| `sprintcycle import-state` | Import JSON state dir into SQLite |
| `sprintcycle knowledge search` | Search knowledge cards |
| `sprintcycle serve` | Start MCP server |
| `sprintcycle dashboard` | Start Web UI |
| `sprintcycle init [path]` | Create `.sprintcycle` layout |

Global options: `-p/--project`, `--format text|json`, `-v/--verbose`.

## Python API

Use **`SprintCycle`** from `sprintcycle.api` — `plan`, `run`, `diagnose`, `status`, `rollback`, `stop`, etc., mirroring the CLI for scripts, services, or CI.

Public models and helpers are re-exported from the top-level `sprintcycle` package (`ReleasePlan`, `ReleasePlanParser`, `ReleasePlanValidator`, `SprintOrchestrator`, `SprintExecutor`, …; see `sprintcycle/__init__.py`).

## Repository layout (high level)

- `sprintcycle/api.py` — unified API
- `sprintcycle/cli.py` — CLI
- `sprintcycle/orchestration/` — Sprint orchestration
- `sprintcycle/execution/` — engine, state, agents, knowledge hooks
- `sprintcycle/release_plan/` — models, parse, validate, generate, expand
- `sprintcycle/intent/` — intent parsing and runner
- `sprintcycle/mcp/` — MCP server
- `sprintcycle/dashboard/` — optional Web UI
- `tests/` — pytest suite

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Contributing

Run `pytest` (and project lint rules) before opening PRs. If a license file is added at the repo root, it governs distribution terms.
