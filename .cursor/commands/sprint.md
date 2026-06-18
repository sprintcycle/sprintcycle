---
description: SprintCycle unified workflow — sdd, optimize, evolve, commit
---

# /sprint — Unified workflow (统一工作流)

**Rule**: `.cursor/rules/sprintcycle-workflow.mdc` · **Index**: `.cursor/README.md`

Detect mode from user message; default **sdd** when ambiguous substantive work.

## Modes (模式)

### `sdd` — SDD gates (default for design / scope)

**Doc**: `docs/SPRINT_SDD_GATES.md` · **Constitution**: `docs/SPRINTCYCLE_CONSTITUTION.md`

```
L/F grade → impact surface + C1… → initial vs suggested scope (HITL if expanded)
  → [L2+] docs/sdd-designs/YYYY-MM-DD/ PRD + plan
  → three-layer principle review → implement or hand off to optimize
  → closure line
```

**Triggers**: 影响面 · 范围判定 · 蝴蝶效应 · 原则审查 · 落档审查 · `/sprint` · `/sprint sdd`

---

### `optimize` — Medium+ refactors

**Doc**: `docs/SPRINT_OPTIMIZE_WORKFLOW.md` · **Rules**: `docs/CURSOR_OPTIMIZATION_RULES.md`

Run **sdd** gates first (§0), then Phase 1–6 with HITL on PRD + technical plan.

**Triggers**: 重构 · DDD治理 · 删字段 · 删兼容 · 前后端对齐 · `/sprint optimize`

---

### `evolve` — Semi-automated evolution

**Skill (source of truth)**: `.cursor/skills/sprint-evolve/SKILL.md` · **Guide**: `docs/SPRINT_EVOLVE_SYSTEM.md`

```
uv run python .cursor/skills/sprint-evolve/evolve.py --report-only
  → HITL scope (Top 3) → HITL plan → optimize mode → make ci-local-quick
```

**Triggers**: 进化 · 自动优化 · 自我改进 · 架构进化 · `/sprint evolve`

Do **not** duplicate evolve logic here — follow the skill.

---

### `commit` — Commit message

**Agent**: `.cursor/agents/it-commit-message-agent.md`

Inspect `git status` / `git diff`; output summary + commit message. Does not commit unless user asks.

**Triggers**: commit message · 提交信息 · `/sprint commit`

---

## CI repair (separate command / 独立命令)

**Not a `/sprint` mode.** Use `/ci-fix-loop` for detect → fix → detect until `make ci-local` green.

Cluster A (import/path) and B (architecture contract) strategies are defined in `.cursor/commands/ci-fix-loop.md`.
