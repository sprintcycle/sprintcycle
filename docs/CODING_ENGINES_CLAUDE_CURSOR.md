# 编码引擎：Claude Code 与 Cursor Cookbook / Coding engines: Claude Code & Cursor Cookbook

本文说明 SprintCycle 中 **`claude_code`** 与 **`cursor_cookbook`** 两种适配方式：配置入口、环境变量、与官方 CLI 文档链接。

---

## 中文

### 总览

| `sprintcycle.toml` → `[engine] name` | 行为 |
|--------------------------------------|------|
| `aider` | 调用本机 `aider`（与既有逻辑一致）；不可用时回退 LiteLLM。 |
| `claude_code` | 调用 **Claude Code** CLI：`claude -p …`（非交互）；不可用时回退 LiteLLM。 |
| `cursor_cookbook` | 写入 **Cursor Cookbook** Markdown（`.sprintcycle/cursor-cookbook/`），可选再调 **Cursor Agent** CLI；失败或未启用 CLI 时回退 LiteLLM。 |

别名：`claude`、`claude-code` → `claude_code`；`cursor`、`cursor-cookbook` → `cursor_cookbook`（在 `CoderAgent` 内归一化）。

### Claude Code

1. 安装并确保 **`claude`** 在 `PATH`（参见 [Claude Code 文档](https://code.claude.com/docs/en/cli-reference)）。
2. 在 `sprintcycle.toml` 中设置 `[engine] name = "claude_code"`，或导出 `SPRINTCYCLE_CODING_ENGINE=claude_code`。
3. 可选环境变量：
   - **`SPRINTCYCLE_CLAUDE_BIN`**：可执行文件名或路径（默认 `claude`）。
   - **`SPRINTCYCLE_CLAUDE_BARE`**：设为 `1` 时追加 `--bare`（更快、少加载项目插件；适合 CI）。
   - **`SPRINTCYCLE_CLAUDE_EXTRA_ARGS`**：额外参数，`shlex` 拆分（例如 `--max-turns 8`）。

非交互模式说明见官方 [Headless / `-p`](https://code.claude.com/docs/en/headless)。

### Cursor Cookbook

1. **Cookbook 文件（默认即生效）**  
   每次 Coder 任务会在项目根下生成（或更新）`.sprintcycle/cursor-cookbook/recipe-<hash>.md`，内含任务描述、架构摘录、`prd_overlay` 摘录（若上下文中有），以及「在 Cursor 里如何粘贴到 Agent」的简短说明。无需安装 Cursor CLI 也可使用。

2. **可选：Cursor Agent CLI**  
   - 安装参见 [Cursor CLI 概览](https://cursor.com/docs/cli/overview)。  
   - 设置 **`SPRINTCYCLE_CURSOR_USE_CLI=1`** 后，若检测到 **`agent`**（可通过 **`SPRINTCYCLE_CURSOR_AGENT_BIN`** 覆盖），会在项目目录执行一轮 `agent -p <任务>`。  
   - **`SPRINTCYCLE_CURSOR_AGENT_PREFIX_ARGS`**：在 `-p` 之前插入的前缀参数（`shlex` 拆分），例如未来 CLI 增加 `--mode plan` 等。

3. 配置：`[engine] name = "cursor_cookbook"` 或 `SPRINTCYCLE_CODING_ENGINE=cursor_cookbook`。

### 与 RuntimeConfig / 上下文

- 全局默认引擎来自 **`RuntimeConfig.coding_engine`**（`sprintcycle.toml` 的 `[engine] name` 经 `flatten_sprintcycle_toml` 映射）。
- 每个任务仍可通过 Agent **`metadata.coding_engine`** 或 `codebase_context["coding_engine"]` 覆盖（与 `aider` 路径一致）。

---

## English

### Overview

| `[engine] name` in `sprintcycle.toml` | Behavior |
|---------------------------------------|----------|
| `aider` | Runs local `aider` CLI; falls back to LiteLLM if unavailable. |
| `claude_code` | Runs **Claude Code** CLI: `claude -p …` (non-interactive); falls back to LiteLLM if unavailable. |
| `cursor_cookbook` | Writes a **Cursor Cookbook** markdown file under `.sprintcycle/cursor-cookbook/`, optionally runs **Cursor Agent** CLI; falls back to LiteLLM on failure or if CLI is disabled. |

Aliases: `claude`, `claude-code` → `claude_code`; `cursor`, `cursor-cookbook` → `cursor_cookbook`.

### Claude Code

1. Install the **`claude`** CLI and ensure it is on `PATH` ([CLI reference](https://code.claude.com/docs/en/cli-reference)).
2. Set `[engine] name = "claude_code"` or `SPRINTCYCLE_CODING_ENGINE=claude_code`.
3. Optional environment variables: `SPRINTCYCLE_CLAUDE_BIN`, `SPRINTCYCLE_CLAUDE_BARE`, `SPRINTCYCLE_CLAUDE_EXTRA_ARGS` (see Chinese section for semantics).

### Cursor Cookbook

1. **Cookbook file (always)** — Markdown recipes under `.sprintcycle/cursor-cookbook/` for copy-paste into Cursor Agent / Chat.  
2. **Optional Agent CLI** — Set `SPRINTCYCLE_CURSOR_USE_CLI=1` and install the `agent` command ([Cursor CLI docs](https://cursor.com/docs/cli/overview)); override binary with `SPRINTCYCLE_CURSOR_AGENT_BIN`, prefix args with `SPRINTCYCLE_CURSOR_AGENT_PREFIX_ARGS`.  
3. Engine name: `cursor_cookbook`.

### RuntimeConfig & context

Default engine comes from **`RuntimeConfig.coding_engine`**. Per-task overrides use `metadata["coding_engine"]` or `codebase_context["coding_engine"]`, same as for `aider`.
