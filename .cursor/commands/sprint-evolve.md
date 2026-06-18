---
description: SprintCycle semi-automated evolution shim (检测 → HITL → 实施 → 验证)
---

# Sprint-evolve compatibility shim / Sprint-evolve 兼容入口

Canonical workflow lives in `.cursor/skills/sprint-evolve/SKILL.md`. (规范工作流位于 `.cursor/skills/sprint-evolve/SKILL.md`。)

User guide: `docs/SPRINT_EVOLVE_SYSTEM.md`. (使用文档见 `docs/SPRINT_EVOLVE_SYSTEM.md`。)

## Behavior / 行为

- **Semi-automated evolution (半自动进化)** — detect and rank automatically; **HITL required** before code changes. (自动检测与排序；**代码变更前必须 HITL 确认**。)
- **Skill is source of truth** — do not duplicate detection/scoring logic in this command. (以 skill 为唯一事实来源。)
- **Implementation via sprint-optimize** — `evolve.py` detects and reports; Cursor Agent implements via `.cursor/commands/sprint-optimize.md` → `docs/SPRINT_OPTIMIZE_WORKFLOW.md`. (`evolve.py` 负责检测与报告；由 Agent 按工作流文档实施。)
- **Validation** — after implementation, run `make ci-local-quick` or `/ci-fix-loop`. (实施后运行 `make ci-local-quick` 或 `/ci-fix-loop`。)

## Agent pipeline / Agent 流水线

1. **Detect (检测)**  
   ```bash
   uv run python .cursor/skills/sprint-evolve/evolve.py --report-only
   ```
2. **HITL gate 1 (范围确认)** — `AskUserQuestion`: approve Top 3 scope or adjust. (确认 Top 3 范围。)
3. **HITL gate 2 (方案确认)** — present technical plan; user approves before edits. (技术方案批准后方可改代码。)
4. **Execute (实施)** — follow `.cursor/commands/sprint-optimize.md` and `.cursor/rules/sprintcycle-optimization.mdc`. (按优化工作流实施。)
5. **Validate (验证)** — `make ci-local-quick`; use `/ci-fix-loop` if red. (验证；失败则走 CI 修复循环。)

## Flags / 参数

| Flag | Effect |
|------|--------|
| `--report-only` | Detection + baseline validation only (recommended default) |
| `--dry-run` | Full flow without file writes |
| `--force` | Skip CLI HITL prompts (Agent must still confirm unless user explicitly forces) |
| `--enable-user-stories` | Opt in to MetaGPT story analysis (skipped by default) |

## Triggers / 触发词

`/sprint-evolve` · 「进化」· 「自动优化」· 「自我改进」· 「架构进化」· 「SprintCycle 进化」

## Related / 关联

- `.cursor/skills/sprint-evolve/SKILL.md`
- `.cursor/commands/sprint-optimize.md`
- `.cursor/rules/sprintcycle-evolution.mdc`
- `.cursor/rules/sprintcycle-optimization.mdc`
