# Cursor configuration index (Cursor 配置索引)

Single map for commands, rules, agents, and skills. (命令、规则、Agent、Skill 唯一索引。)

## Commands (命令) — 2 only

| Command | Purpose |
|---------|---------|
| **`/sprint`** | **Main entry** — modes: `sdd` · `optimize` · `evolve` · `commit` |
| **`/ci-fix-loop`** | CI / production-ready repair loop |

## Rules (规则)

| Rule | alwaysApply | Role |
|------|-------------|------|
| `sprintcycle-baseline.mdc` | yes | Routing → `/sprint`, constitution pointers |
| `sprintcycle-architecture-orchestration.mdc` | yes | DDD / layer boundaries (slim) |
| `sprintcycle-workflow.mdc` | no (glob) | SDD + optimize + evolve (unified) |
| `python-venv-only.mdc` | yes | `uv run` policy |
| `codegraph.mdc` | yes | Structural search |
| `documentation-bilingual-format.mdc` | yes | Docs EN+(中文) |

## Agents (Agent)

| Agent | Invoked via |
|-------|-------------|
| `it-commit-message-agent.md` | `/sprint commit` |

## Skills (Skill)

| Skill | Invoked via |
|-------|-------------|
| `sprint-evolve/` | `/sprint evolve` only |

## Docs (文档真源)

| Topic | Path |
|-------|------|
| Constitution | `docs/SPRINTCYCLE_CONSTITUTION.md` |
| SDD gates | `docs/SPRINT_SDD_GATES.md` |
| Optimize workflow | `docs/SPRINT_OPTIMIZE_WORKFLOW.md` |
| Evolve system | `docs/SPRINT_EVOLVE_SYSTEM.md` |
| CI fix loop | `docs/CURSOR_PRODUCTION_FIX_WORKFLOW.md` |
| Architecture (full) | `docs/CURSOR_ARCHITECTURE_ORCHESTRATION.md` |
| Design artifacts | `docs/sdd-designs/` |

## Multi-root workspace (多根工作区)

Open `.cursor/rules/sprintcycle.code-workspace` for sprintcycle + parents-bio.
