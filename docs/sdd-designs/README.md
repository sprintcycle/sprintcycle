# SDD design artifacts (SDD 设计落档)

Dated PRD, technical plans, and optional task lists for SprintCycle SDD work.

SprintCycle 的 PRD、技术方案与可选任务清单落档目录。

## Layout (目录结构)

```text
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<short-name>-PRD.md
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<short-name>-plan.md
docs/sdd-designs/YYYY-MM-DD/YYYY-MM-DD-<short-name>-tasks.md   # L3 optional
```

## Workflow (工作流)

| Command | Role |
|---------|------|
| **`/sprint sdd`** | Scope, L/F grade, principle review |
| **`/sprint optimize`** | Medium+ refactors (includes §0 SDD gates) |
| **`/sprint evolve`** | Detection → gates → optimize |

## Rules (规则)

- Template: `docs/templates/sdd-feature-template.md`
- Methodology: `docs/SPRINT_SDD_GATES.md`
- Constitution: `docs/SPRINTCYCLE_CONSTITUTION.md`
- Workflow rule: `sprintcycle-workflow.mdc` · Baseline: `sprintcycle-baseline.mdc`
- After落档: three-layer review (SPRINT_SDD_GATES §6) before implement
- Historical speckit specs: `docs/archive/specs/` (read-only)

## Related (关联)

- Command: `/sprint` · Index: `.cursor/README.md`
