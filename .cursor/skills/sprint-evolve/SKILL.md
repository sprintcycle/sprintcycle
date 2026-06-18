---
name: sprint-evolve
description: SprintCycle semi-automated evolution — detect, rank, HITL, sprint-optimize, validate
author: SprintCycle Team
version: 1.1.0
---

# SprintCycle Semi-automated Evolution / 半自动进化 Skill

## Overview / 概述

Semi-automated closed loop (半自动闭环):

1. **Detect (检测)** — architecture validation + opportunity scoring (`evolve.py`)
2. **Prioritize (排序)** — Top 3 scored directions
3. **HITL (人工确认)** — scope + technical plan before any code edit
4. **Execute (实施)** — Cursor Agent + `.cursor/commands/sprint-optimize.md`
5. **Validate (验证)** — `make ci-local-quick` or `/ci-fix-loop`
6. **Report (报告)** — markdown summary

`evolve.py` **does not** apply product code changes. ( `evolve.py` **不**直接修改产品代码。)

## Triggers / 触发

| Type | Value |
|------|-------|
| Command | `/sprint-evolve` |
| Keywords | 进化 · 自动优化 · 自我改进 · 架构进化 · SprintCycle 进化 |

## Non-negotiable rules / 硬性规则

1. **Skill + shim routing** — command `.cursor/commands/sprint-evolve.md` is entry only; this file is source of truth.
2. **HITL before edits** — same gates as `sprintcycle-optimization.mdc` (scope, then technical plan).
3. **No fake execution** — never claim optimizations were applied unless Agent followed `sprint-optimize`.
4. **uv only** — `uv run python ...` for all Python invocations.
5. **Stories opt-in** — MetaGPT analysis only with `--enable-user-stories`.

## Agent pipeline / Agent 流水线

### Step 1 — Detect

```bash
uv run python .cursor/skills/sprint-evolve/evolve.py --report-only
```

Read `evolution_report.md` at repo root.

### Step 2 — HITL scope

Use `AskUserQuestion`: approve Top 3, narrow scope, or cancel.

### Step 3 — HITL technical plan

Draft plan per optimization type (field consolidation, DDD governance, compatibility cleanup, frontend-backend alignment). User must approve before implementation.

### Step 4 — Implement

Read and follow `.cursor/commands/sprint-optimize.md` → `docs/SPRINT_OPTIMIZE_WORKFLOW.md` and `.cursor/rules/sprintcycle-optimization.mdc`.

### Step 5 — Validate

```bash
make ci-local-quick
```

If failures persist, route to `.cursor/commands/ci-fix-loop.md`.

### Step 6 — Report

Summarize: detection results, approved scope, files changed, validation status, doc updates.

## Scoring criteria / 评分标准

| Factor | Weight |
|--------|--------|
| Architecture impact | 30% |
| Business value | 25% |
| Complexity (lower better) | 20% |
| Risk (lower better) | 15% |
| Test coverage | 10% |

## CLI flags / 命令行参数

| Flag | Purpose |
|------|---------|
| `--report-only` | Detect + baseline validate; no HITL CLI prompts |
| `--dry-run` | Simulate full flow without writes |
| `--force` | Skip stdin HITL in CLI (Agent should still confirm) |
| `--enable-user-stories` | Opt in to MetaGPT (skipped by default) |
| `--silent` | Reduce log noise |

## Implementation layout / 实现结构

```
.cursor/skills/sprint-evolve/
├── SKILL.md                 # This file
├── evolve.py                # Detect, score, validate, report
├── document_updater.py      # Optional doc sync helpers
├── config.example.json      # LLM / story generator template
└── story_*.py               # Optional MetaGPT integration
```

## Optional: user stories / 可选用户故事

MetaGPT story generation is **optional**. Enable only when user requests it and `metagpt` is installed. Default: `--skip-user-stories`.

## Related / 关联文档

- `docs/SPRINT_EVOLVE_SYSTEM.md` — full system guide
- `.cursor/commands/sprint-optimize.md` — implementation workflow
- `.cursor/rules/sprintcycle-optimization.mdc` — optimization invariants

---

*Last updated: 2026-06-18*
