---
description: SprintCycle optimization workflow shim (medium+ refactors, HITL-gated)
---

# Sprint-optimize compatibility shim / Sprint-optimize 兼容入口

Canonical workflow: `docs/SPRINT_OPTIMIZE_WORKFLOW.md` (detailed phases).  
User guide: `docs/SPRINT_OPTIMIZE_GUIDE.md`.  
Optimization rules: `.cursor/rules/sprintcycle-optimization.mdc` (glob-scoped).  
规范工作流见 `docs/SPRINT_OPTIMIZE_WORKFLOW.md`。

## Behavior / 行为

- **Medium+ optimizations only** — field consolidation, DDD governance, compatibility cleanup, frontend-backend alignment, core refactors. (中等及以上优化。)
- **HITL mandatory** — requirements → PRD → technical design → implement. (必须 HITL。)
- **No compatibility layers** — final state in one pass, all call sites updated. (一次性终态，无过渡层。)
- **Do not duplicate** phase logic here; read the workflow doc when executing. (不在此重复阶段细节。)

## Pipeline / 流水线

```
Phase 1 Requirements (AskUserQuestion)
    → Phase 2 Design + HITL PRD/plan approval
    → Phase 3 Implement (domain → app → HTTP → frontend)
    → Phase 4 Test (uv run pytest, frontend lint/build)
    → Phase 5 Docs sync
    → Phase 6 PR + CI
```

## Triggers / 触发

`/sprint-optimize` · 「删减字段」· 「DDD 治理」· 「删除兼容逻辑」· 「优化架构」· 「前后端对齐」· 「重构」

## Related / 关联

- Invoked by `/sprint-evolve` after detection + scope approval
- Architecture: `.cursor/rules/sprintcycle-architecture-orchestration.mdc`
- CI repair: `.cursor/commands/ci-fix-loop.md`
