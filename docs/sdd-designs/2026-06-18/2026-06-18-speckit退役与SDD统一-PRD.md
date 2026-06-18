# Speckit retirement and unified SDD (PRD / Speckit 退役与 SDD 统一 — PRD)

**Date (日期)**: 2026-06-18  
**Status (状态)**: Implemented (已实施) — **2026-06-18 consolidation**: single entry `/sprint` only; no command shims.

---

## 1. Background (背景)

SprintCycle is a **lifecycle orchestration platform**. Most substantive work is architecture governance, contract alignment, refactors, and semi-automated evolution — not greenfield feature specs via GitHub spec-kit.

SprintCycle 是 **生命周期编排平台**，主要工作是架构治理、契约对齐、重构与半自动进化，而非 spec-kit 式的功能规格工厂。

Current pain:

- **Triple workflow**: speckit + `/sprint-optimize` + SDD gates — agents route inconsistently
- **Dual artifact paths**: `specs/` vs `docs/sdd-designs/`
- **Weak always-on rule**: `specify-rules.mdc` only says "read the current plan"
- **Platform misfit**: speckit checkpoint (after tasks) lacks impact surface, L/F grading, and four-principle review already defined in SDD gates

---

## 2. Goal (目标)

Retire speckit as the primary SDD orchestrator; establish **one canonical SDD path** for all new work.

退役 speckit 作为主编排；**所有新工作**走统一 SDD 路径。

## 3. Non-goals (非目标)

- Rewriting historical archived spec content
- Changing product runtime code (`sprintcycle/`, `frontend/`) in this Epic
- Importing parents-bio 3000-line rules wholesale

---

## 4. Decision principles (决策原则)

| Principle | How this PRD satisfies |
|-----------|------------------------|
| **Rational** | Single entry `/sprint` (modes: sdd · optimize · evolve · commit); artifacts `docs/sdd-designs/`; constitution `docs/SPRINTCYCLE_CONSTITUTION.md` |
| **Experience** | Agents and humans no longer choose between speckit vs SDD gates |
| **Long-term** | No dual tracks; archived `specs/` read-only; whole-package revert if needed |
| **Thorough** | Remove `.specify/`, all speckit skills, shims; migrate constitution; update all references |

---

## 5. User stories (用户故事)

### US-SDD-01 — Agent routing

**As** a Cursor agent, **when** starting medium+ work, **I** use `/sprint sdd` or `/sprint optimize` **so that** I do not invoke deprecated `@speckit`.

### US-SDD-02 — Design artifacts

**As** a developer, **when** I need a PRD/plan, **I** write under `docs/sdd-designs/YYYY-MM-DD/` **so that** there is one dated archive.

### US-SDD-03 — Governance

**As** a reviewer, **when** checking architecture compliance, **I** read `docs/SPRINTCYCLE_CONSTITUTION.md` **so that** governance is not tied to `.specify/`.

---

## 6. Scope (范围)

| In scope | Out of scope |
|----------|--------------|
| Migrate constitution to `docs/` | Re-run old speckit features |
| Archive `specs/` → `docs/archive/specs/` | Edit archived spec bodies |
| Delete `.specify/`, speckit skills, `speckit.md` | parents-bio rule import |
| Replace `specify-rules.mdc` with SDD pointer | New Dashboard UI |
| Update AGENTS, SDD gates, optimize, evolve docs | |

---

## 7. Acceptance (验收 T-xxx)

| ID | Criterion |
|----|-----------|
| T-SDD-01 | No `.specify/` directory in repo |
| T-SDD-02 | No `.cursor/skills/speckit*` directories |
| T-SDD-03 | `docs/SPRINTCYCLE_CONSTITUTION.md` exists; Development Workflow references SDD gates |
| T-SDD-04 | `docs/archive/specs/` contains former `specs/` tree |
| T-SDD-05 | `grep -r speckit .cursor docs AGENTS.md` returns zero actionable entry points (archive/historical mentions OK with DEPRECATED label) |
| T-SDD-06 | `docs/templates/sdd-feature-template.md` documents PRD/plan/tasks shape for L2/L3 features |
| T-SDD-07 | AGENTS.md lists single SDD workflow table (no speckit row) |

---

## 8. Rollback (回滚)

Whole-package revert: restore commit before Epic; re-run `specify init` only if speckit must return (not planned).

整包 revert：恢复本 Epic 前 commit；仅在必须恢复 speckit 时重新 `specify init`（非计划路径）。
