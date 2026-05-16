# Cursor 使用说明 / Cursor Guide

本目录用于存放 SprintCycle 项目的 Cursor 专用配置，包括：

- `agents/`：子代理（subagent）配置
- `commands/`：命令入口配置
- `rules/`：项目规则与约束

这些配置都是**项目级**的，适用于当前仓库 `sprintcycle`。

## 文档入口 / Document entry points

- `AGENTS.md` — 仓库级底线 / repository-level baseline
- `docs/AI_GOVERNANCE.md` — 治理总纲 / governance charter
- `docs/CURSOR_TEAM_PLAYBOOK.md` — 执行手册 / execution manual
- `.cursor/commands/README.md` — 命令索引 / command index

如果你想快速了解这套协作团队，请先看：

- `docs/AI_GOVERNANCE.md`：项目级治理总纲
- `docs/CURSOR_TEAM_PLAYBOOK.md`：执行层手册

## 入口说明

- 想了解“规则、命令、文档、Spec-Kit、OpenSpec 如何分层治理” → 看 `docs/AI_GOVERNANCE.md`
- 想了解“SprintCycle 的最小完整 AI 研发团队模型如何协作” → 看 `docs/CURSOR_TEAM_PLAYBOOK.md`
- 想了解“Cursor 里有哪些固定命令、怎么调用” → 看 `commands/README.md`
- 想了解“哪些约束会始终生效” → 看 `rules/`

## 目录结构

```text
.cursor/
  README.md
  agents/
  commands/
  rules/
```
