# Speckit Compatibility Shim / Speckit 兼容适配层

This legacy command exists only to preserve old `speckit` entry points. (此旧命令仅用于保留旧的 `speckit` 入口。)

The canonical workflow now lives in `.cursor/skills/speckit/`. (现在的规范工作流位于 `.cursor/skills/speckit/`。)

User guide: `docs/SPECKIT_SKILL_GUIDE.md`. (使用文档见 `docs/SPECKIT_SKILL_GUIDE.md`。)

## Behavior / 行为

- Use the skill-based speckit workflow as the source of truth. (使用基于 skill 的 speckit 工作流作为唯一真实来源。)
- Do not re-implement constitution, specify, clarify, plan, tasks, or implement logic here. (不要在这里重复实现 constitution、specify、clarify、plan、tasks 或 implement 的逻辑。)
- Keep `tasks` as a hard checkpoint and stop for explicit user approval before implementation. (将 `tasks` 作为硬性检查点，并在进入 implementation 前等待用户明确批准。)
- If the skill entry is missing, stop and report the missing skill rather than guessing. (如果缺少对应 skill，停止并报告缺失项，不要自行猜测。)

## Compatibility / 兼容说明

- Existing callers keep working. (现有调用方仍可继续使用。)
- New work is routed through the skill-based workflow. (新的工作流将路由到基于 skill 的流程。)
- The legacy command remains only as a compatibility shim. (旧命令仅作为兼容 shim 保留。)
