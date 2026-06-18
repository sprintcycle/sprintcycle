# Speckit retirement and unified SDD (technical plan / 技术方案)

**Date (日期)**: 2026-06-18  
**PRD**: `2026-06-18-speckit退役与SDD统一-PRD.md`  
**Status (状态)**: Implemented — final layout: 2 commands (`/sprint`, `/ci-fix-loop`), 6 rules + workspace; no shims.

---

## 1. Target architecture (目标架构)

```text
                    ┌─────────────────────────────┐
                    │ docs/SPRINTCYCLE_CONSTITUTION│
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │      /sprint (modes)        │
                    │  sdd · optimize · evolve · commit │
                    └──────────────┬──────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         v                         v                         v
docs/sdd-designs/YYYY-MM-DD/  SPRINT_OPTIMIZE_*     sprint-evolve/SKILL.md
         │                         │                         │
         └──────────────┬──────────┴─────────────────────────┘
                        v
              docs/archive/specs/ (read-only)
```

**Also**: `/ci-fix-loop` (CI repair). **Removed**: all command shims, `.specify/`, speckit skills.

---

## 2. Change list (变更点)

| ID | Action | Path |
|----|--------|------|
| C1 | Create | `docs/SPRINTCYCLE_CONSTITUTION.md` (from `.specify/memory/constitution.md`, v1.1.0 workflow section) |
| C2 | Move | `specs/` → `docs/archive/specs/` |
| C3 | Delete tree | `.specify/` |
| C4 | Delete tree | `.cursor/skills/speckit*` (15 skills) |
| C5 | Delete | `.cursor/commands/speckit.md`, `docs/SPECKIT_SKILL_GUIDE.md` |
| C6 | Replace | `.cursor/rules/specify-rules.mdc` → SDD + constitution pointer |
| C7 | Rewrite | `docs/SPRINT_SDD_GATES.md`, `sprintcycle-sdd-gates.mdc`, `sdd-designs/README.md` |
| C8 | Update | `AGENTS.md`, `SPRINT_OPTIMIZE_WORKFLOW.md` §0, optimize/evolve rules & skills |
| C9 | Create | `docs/templates/sdd-feature-template.md` |
| C10 | Update | `sprintcycle-architecture-orchestration.mdc` shim reference |
| C11 | Create | `docs/archive/specs/README.md` |

---

## 3. Constitution migration (宪法迁移)

- Source: `.specify/memory/constitution.md`
- Target: `docs/SPRINTCYCLE_CONSTITUTION.md`
- **Version**: 1.0.0 → **1.1.0** (MINOR: workflow path change)
- **Development Workflow** step 2 becomes: PRD/plan in `docs/sdd-designs/` per `docs/SPRINT_SDD_GATES.md`; L2+ requires HITL before code
- Remove HTML sync-impact comment block; add amendment note for 2026-06-18 speckit retirement

---

## 4. SDD feature template (功能型落档)

New file `docs/templates/sdd-feature-template.md` replaces speckit `spec/plan/tasks` trio:

| Artifact | File pattern | Minimum sections |
|----------|--------------|------------------|
| PRD | `*-PRD.md` | Goal, stories, rules, non-goals, T-xxx, principles |
| Plan | `*-plan.md` |现状, file map, phases, risks, revert |
| Tasks | `*-tasks.md` (optional L3) | Ordered T001… with file paths |

Checkpoint: principle review table (§6 SPRINT_SDD_GATES) before implement.

---

## 5. Reference cleanup (引用清理)

Files to update (grep-driven):

- `AGENTS.md`
- `.cursor/rules/sprintcycle-sdd-gates.mdc`
- `.cursor/commands/sprint-sdd-gates.md`, `sprint-optimize.md`
- `.cursor/rules/sprintcycle-optimization.mdc`
- `.cursor/rules/sprintcycle-architecture-orchestration.mdc`
- `.cursor/rules/sprintcycle-evolution.mdc`
- `.cursor/skills/sprint-evolve/SKILL.md`
- `docs/SPRINT_OPTIMIZE_WORKFLOW.md`, `docs/SPRINT_OPTIMIZE_GUIDE.md` (if speckit mention)

---

## 6. Implementation order (实施顺序)

1. Write PRD + plan (this Epic)
2. Create `docs/SPRINTCYCLE_CONSTITUTION.md`
3. `git mv specs docs/archive/specs`
4. Delete `.specify/`, speckit skills, speckit command, SPECKIT guide
5. Replace specify-rules.mdc
6. Update all references + templates
7. Verify T-SDD-01…07

---

## 7. Risks (风险)

| Risk | Mitigation |
|------|------------|
| Broken doc links to `specs/` | Archive README + redirect note in constitution |
| Agent habit `@speckit` | Remove skills; AGENTS.md explicit deprecation |
| Lost constitution | Copy before delete `.specify/` |

---

## 8. Decision principles (决策原则 — technical)

| Principle | Satisfied by |
|-----------|--------------|
| **Rational** | Single artifact root `docs/sdd-designs/`; constitution in `docs/` |
| **Experience** | One workflow table in AGENTS.md |
| **Long-term** | No `.specify/` maintenance; archive preserves history |
| **Thorough** | Delete entry points; verify grep; template for future features |

---

## SDD principle review (2026-06-18)

| Principle | Result | Finding | Action |
|-----------|--------|---------|--------|
| Rational | ✅ | Single path defined | — |
| Experience | ✅ | Removes triple workflow | — |
| Long-term | ✅ | Archive not delete history | — |
| Thorough | ✅ | C1–C11 + T-SDD-01…07 | Proceed to implement |
