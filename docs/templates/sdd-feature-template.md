# SDD feature template (SDD 功能落档模板)

Use for **L2/L3** new work under `docs/sdd-designs/YYYY-MM-DD/`.  
用于 **L2/L3** 新需求，落档至 `docs/sdd-designs/YYYY-MM-DD/`。

**Workflow (工作流)**: `/sprint sdd` → PRD → plan → (optional) tasks → principle review → implement  
**Governance (治理)**: `docs/SPRINTCYCLE_CONSTITUTION.md` + `docs/SPRINT_SDD_GATES.md`

---

## File naming (文件命名)

```text
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<short-name>-PRD.md
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<short-name>-plan.md
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<short-name>-tasks.md   # L3 optional
```

---

## PRD template (PRD 模板)

```markdown
# <Title> (PRD)

**Date**: YYYY-MM-DD

## Decision principles (决策原则)
- **Rational**: …
- **Experience**: …
- **Long-term**: …
- **Thorough**: …

## Goal / Non-goals (目标 / 非目标)

## User stories (用户故事)
### US-xxx-01 …

## Rules (编号规则 if-then)

## Acceptance T-xxx

## Rollback (回滚)
```

---

## Plan template (技术方案模板)

```markdown
# <Title> (technical plan)

**PRD**: link

## Current state (现状)

## Target architecture (目标架构)

## Change list C1… (变更点)

## File / module map (文件映射)

## Phases / implementation order (分期)

## Risks and revert (风险与回滚)

## Decision principles (决策原则)
```

---

## Tasks template (任务模板 — L3)

```markdown
# <Title> (tasks)

**Plan**: link

## Phase 1
- [ ] T001 [P] Description — `path/to/file`

## Checkpoint
Principle review table before coding (SPRINT_SDD_GATES §6).
```

---

## Checkpoint before implement (实施前检查点)

1. PRD + plan HITL approved
2. Four-principle review table — all ✅ or fixed
3. L/F grade recorded in PRD or plan header
