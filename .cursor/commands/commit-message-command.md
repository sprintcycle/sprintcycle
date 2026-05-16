# Commit message command / 提交信息命令

Use the `commit-message-agent` to summarize the current change and draft a commit message.

使用 `commit-message-agent` 总结当前变更并生成 commit message。

## Goal
Produce two outputs:
1. a concise summary of the current changes
2. a commit message that explains the purpose of the change, not just the files modified

## Inputs to inspect
- `git status`
- `git diff --staged`
- `git diff`
- Recent commit messages for style consistency

## Steps
1. Identify the main change type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, or similar.
2. Summarize the current changes in 2–4 bullets.
3. Summarize the user-facing or architectural purpose in one sentence.
4. Keep the commit message aligned with the repository's existing commit style.
5. If there are multiple unrelated changes, mention the dominant one and keep the message broad but accurate.

## Output format
Return exactly two sections in this order:

### 当前变更摘要
- Bullet 1
- Bullet 2
- Bullet 3

### Commit message
One-line subject

Optional 1–2 line body explaining why the change was made.

## Constraints
- Do not invent details that are not supported by the diff.
- Do not include implementation trivia unless it is needed for clarity.
- Keep the subject short and action-oriented.
- Prefer lowercase unless the repository convention suggests otherwise.
