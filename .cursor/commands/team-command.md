# Team command / 团队总控命令

Use the `team-commander` subagent to classify the task, choose the right workflow, and produce a minimal execution plan.

使用 `team-commander` 子代理对需求分类、选择合适工作流，并给出最小执行计划。

Canonical references:
- `docs/AI_GOVERNANCE.md` for governance and routing policy
- `docs/CURSOR_TEAM_PLAYBOOK.md` for team roles and workflow order
- `docs/IT_RESEARCH_TEAM_FLOW.md` for the formal execution flow

## When to use / 适用场景
- New feature planning / 新功能规划
- Multi-step refactor / 多步骤重构
- Cross-layer change / 跨层变更
- Unclear requirements / 需求不明确
- Need a coordinated workflow / 需要协调式工作流

## Expected output / 期望输出
- Task classification
- Recommended routing
- Execution plan
- Risks
- Next step

## Reusable command format / 可复用命令格式

Use this command shape when you want the team workflow to be applied consistently:

```text
/team-command <task summary> | <goal> | <scope or target path>
```

Examples:

```text
/team-command "Fitness多维度整合" | 当前Fitness分散，需统一评分入口 | 在 domain/fitness/ 创建
```

```text
/team-command "Refactor orchestration flow" | unify evaluator entrypoint | affects sprintcycle/domain/fitness/
```

## Response contract / 回复契约

When invoked, the command should return:
- classification
- complexity
- chosen route
- execution plan
- key risks
- next step
