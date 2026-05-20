# Commit message command (提交信息命令)

Use the `it-commit-message-agent` to summarize the current change and draft a commit message. (使用 `it-commit-message-agent` 总结当前变更并生成 commit message。)

## Goal (目标)
Produce two outputs. (产出两个内容。)
1. a concise summary of the current changes. (当前变更的简洁摘要。)
2. a commit message that explains the purpose of the change, not just the files modified. (说明这次修改目的的 commit message，而不只是改了哪些文件。)

## Inputs to inspect (需要检查的输入)
- `git status`. (查看 `git status`。)
- `git diff --staged`. (查看 `git diff --staged`。)
- `git diff`. (查看 `git diff`。)
- Recent commit messages for style consistency. (查看最近的提交信息，用于保持风格一致。)

## Steps (步骤)
1. Identify the main change type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, or similar. (识别主要变更类型：`feat`、`fix`、`refactor`、`docs`、`test`、`chore` 等。)
2. Summarize the current changes in 2–4 bullets. (用 2–4 个要点总结当前变更。)
3. Summarize the user-facing or architectural purpose in one sentence. (用一句话总结面向用户或架构层面的目的。)
4. Keep the commit message aligned with the repository's existing commit style. (让 commit message 与仓库现有风格保持一致。)
5. If there are multiple unrelated changes, mention the dominant one and keep the message broad but accurate. (如果有多个不相关的变更，突出主要变更，保持信息足够宽泛但准确。)

## Output format (输出格式)
Return exactly two sections in this order. (严格按以下顺序输出两个部分。)

### Current change summary (当前变更摘要)
- Bullet 1. (要点 1。)
- Bullet 2. (要点 2。)
- Bullet 3. (要点 3。)

### Commit message (提交信息)
One-line subject. (一行标题。)

Optional 1–2 line body explaining why the change was made. (可选 1–2 行正文，说明为什么要做这次修改。)

## Constraints (约束)
- Do not invent details that are not supported by the diff. (不要编造 diff 中没有支持的细节。)
- Do not include implementation trivia unless it is needed for clarity. (除非有助于说明，否则不要写实现细节。)
- Keep the subject short and action-oriented. (标题要简短、动作导向。)
- Prefer lowercase unless the repository convention suggests otherwise. (除非仓库惯例另有要求，否则优先使用小写。)
