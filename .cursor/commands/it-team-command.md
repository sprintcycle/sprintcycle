# Team command / 团队总控命令

Use the `it-team-agent` to classify the task, choose the right workflow, and produce a minimal execution plan.

使用 `it-team-agent` 对需求分类、选择合适工作流，并给出最小执行计划。

Canonical references:
- `docs/AI_GOVERNANCE.md` for governance and routing policy
- `docs/CURSOR_TEAM_PLAYBOOK.md` for team roles and workflow order

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

## Response contract / 回复契约

When invoked, the command should return:
- classification
- complexity
- chosen route
- execution plan
- key risks
- next step
