# Spec-Kit command / Spec-Kit 命令

Use the `spec-kit` command when a task has already been classified as medium/high complexity and needs a standalone Spec-Kit artifact before architecture and implementation.

当任务已经被判定为中 / 高复杂度，并且需要先产出独立的 Spec-Kit 工件，再进入 Architect 和 Implementation 时，使用 `spec-kit` 命令。

Canonical references:
- `docs/AI_GOVERNANCE.md` for governance and routing policy
- `docs/CURSOR_TEAM_PLAYBOOK.md` for team roles and workflow order
- `docs/SPEC_KIT.md` for the Spec-Kit template
- `docs/specs/` for task-specific spec artifacts

## When to use / 适用场景
- Medium/high complexity tasks / 中高复杂度任务
- Cross-layer changes / 跨层变更
- Contract-impacting work / 影响 contract 的任务
- Architecture-sensitive work / 架构敏感任务
- Tasks that need a durable spec artifact / 需要持久化 spec 工件的任务

## Expected output / 期望输出
- Task classification
- Spec-Kit route confirmation
- Draft task spec scope
- Risks and constraints
- Next step

## Reusable command format / 可复用命令格式

Use this command shape when you want the workflow to produce a formal Spec-Kit artifact:

```text
/spec-kit <task summary> | <goal> | <scope or target path>
```

Examples:

```text
/spec-kit "Fitness多维度整合" | 统一 Fitness 评分入口并保留可解释性 | docs/specs/2026-05-16-fitness-multidimensional-integration.md
```

```text
/spec-kit "Domain contract migration" | prepare a formal spec before implementation | docs/specs/<date>-<topic>.md
```

## Output contract / 回复契约

When invoked, the command should return:
- complexity classification
- explicit Spec-Kit decision
- proposed spec outline
- risks and constraints
- next action (architect, revise spec, or route back)
