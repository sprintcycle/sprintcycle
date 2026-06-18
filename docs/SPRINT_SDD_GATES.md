# SprintCycle SDD Gates (full reference / 完整参考)

> **Canonical SDD path** for SprintCycle (speckit retired 2026-06-18).  
> **SprintCycle 唯一 SDD 路径**（speckit 已于 2026-06-18 退役）。

---

## 1. Purpose (目标)

Unified **Specification-Driven Development (SDD)** for all substantive SprintCycle work: features, refactors, evolution, and investigations.

统一 **规范驱动开发（SDD）**，覆盖功能、重构、进化与排查类实质性变更。

| Entry | Use for |
|-------|---------|
| **`/sprint sdd`** | Standalone scope/grade/review |
| **`/sprint optimize`** | Medium+ refactors, alignment, DDD cleanup |
| **`/sprint evolve`** | Semi-automated detection → optimize |

**Governance**: `docs/SPRINTCYCLE_CONSTITUTION.md`  
**Artifacts**: `docs/sdd-designs/YYYY-MM-DD/`  
**Template**: `docs/templates/sdd-feature-template.md`  
**Archive**: `docs/archive/specs/` (historical speckit output, read-only)

---

## 2. Decision principles (决策原则 §1.0)

**North Star**: Reduce cognitive cost for operators and developers.  
**北极星**：降低操作者与研发者的认知成本。

| Principle | Decision lens | Typical veto |
|-----------|---------------|--------------|
| **Rational** (合理) | if-then rules; same terms in PRD, plan, code, `LifecycleContract` | Doc ↔ code drift |
| **Experience** (体验) | Short main path; visible failure/empty states | Silent failure |
| **Long-term** (长期) | Constitution-aligned; single final path | Dual tracks, dead flags |
| **Thorough** (彻底) | Root-cause; negative fixtures; delete old paths | Symptom patch |

Constitution = architecture governance; this table = SDD decision factors for daily work.

---

## 3. Grading (需求与修复分级 §1.2)

### 3.1 New work (L*)

| Grade | Minimum deliverable | Encode without doc? |
|-------|---------------------|---------------------|
| **L1** | Inline polish table | Yes |
| **L2** | Slim PRD/plan in `docs/sdd-designs/` | **No** |
| **L3** | Dated PRD + plan (+ optional tasks) | **No** |

### 3.2 Fixes (F*)

| Grade | Minimum deliverable | Encode without doc? |
|-------|---------------------|---------------------|
| **F0** | Root-cause chain + verify steps | Yes |
| **F1** | Slim fix plan in `docs/sdd-designs/` | **No** |
| **F2** | Dated fix plan + sequence | **No** |

### 3.3 Butterfly checklist (L2+/F1+)

Dashboard / API / SDK surfaces · contract fields · hooks/facades · tests + negative case

---

## 4. Scope gate (影响面与范围 §1.3)

```text
① Restate request  ② Impact scan  ③ C1… + principle tags
④ Root cause / extension point  ⑤ Initial vs suggested scope  ⑥ HITL if expanded
```

---

## 5. Document layout (落档路径)

```text
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<name>-PRD.md
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<name>-plan.md
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<name>-tasks.md   # L3 optional
```

See `docs/templates/sdd-feature-template.md`.

---

## 6. Three-layer post-doc review (落档后三层自查)

| Layer | Check |
|-------|--------|
| ① Complete | Principles, non-goals, rollback, T-xxx |
| ② Four principles | Cross-doc consistency — **auto-fix** |
| ③ Implementable | File map, tests, revert |

Output principle review table before 「可实施」.

---

## 7. Workflow integration (工作流集成)

### 7.1 `/sprint optimize`

`docs/SPRINT_OPTIMIZE_WORKFLOW.md` §0

### 7.2 `/sprint evolve`

Scope gate on Top-3; L/F grade; principle table before plan HITL

### 7.3 Closure (收尾)

```text
Closure: Rational ✅ · Experience ✅ · Long-term ✅ · Thorough ✅ — <one sentence>
```

---

## 8. Quick reference (速查)

| User says | Action |
|-----------|--------|
| New feature L2+ | `docs/sdd-designs/` PRD + plan → review → implement |
| Refactor / 对齐 | `/sprint optimize` |
| Small fix F0 | Root-cause + fix |
| ~~@speckit~~ | **Deprecated** — use this doc |

---

## 9. Historical note (历史说明)

Speckit / spec-kit (`.specify/`, `specs/`, speckit skills) was removed 2026-06-18.  
Epic: `docs/sdd-designs/2026-06-18/2026-06-18-speckit退役与SDD统一-PRD.md`
