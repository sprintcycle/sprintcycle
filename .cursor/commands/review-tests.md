# Test risk review / 测试风险审查

Use the `test-risk-reviewer` subagent to identify missing tests, edge cases, and regression risks.

使用 `test-risk-reviewer` 子代理识别缺失测试、边界情况与回归风险。

Canonical references:
- `docs/AI_GOVERNANCE.md` for governance constraints that affect test scope
- `docs/CURSOR_TEAM_PLAYBOOK.md` for QA/Review responsibilities

## When to use / 适用场景
- Behavior changes / 行为变更
- Refactors touching critical paths / 关键路径重构
- API or contract changes / API 或 contract 变更
- Deletions that may remove coverage / 删除可能造成覆盖缺失
- Any change where regression risk matters / 任何有回归风险的变更

## Expected output / 期望输出
- Summary
- Missing tests
- High-risk scenarios
- Suggestions
- Verdict
