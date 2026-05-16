# Architecture review / 架构审查

Use the `arch-guardian` subagent to review the current change for layered-architecture boundaries, ownership, and cross-layer coupling.

使用 `arch-guardian` 子代理审查当前变更是否违反分层架构、职责归属和跨层耦合约束。

Canonical references:
- `docs/AI_GOVERNANCE.md` for governance hierarchy and ownership boundaries
- `docs/CURSOR_TEAM_PLAYBOOK.md` for architecture review role boundaries

## When to use / 适用场景
- Service migrations / 服务迁移
- Import/export changes / import-export 变更
- Public API changes / 公共 API 变更
- Layer boundary changes / 分层边界变更
- Duplicate business logic concerns / 重复业务逻辑风险

## Expected output / 期望输出
- Summary
- Blocking issues
- Warnings
- Suggestions
- Verdict
