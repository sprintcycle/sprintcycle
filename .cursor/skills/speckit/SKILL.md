---
name: "speckit"
description: "Semi-automated spec-kit orchestrator (Speckit-mcp-x parity): preflight, constitution → specify → clarify → plan → tasks, mandatory checkpoint, implement only after approval."
disable-model-invocation: true
---

# Speckit Workflow / Speckit 工作流

Canonical semi-automated entry for the spec-kit lifecycle. (此 skill 是 spec-kit 生命周期的规范半自动入口。)
Behavior aligns with [Speckit-mcp-x](https://github.com/ElliotLion-ing/Speckit-mcp-x) (`speckit_auto_setup`, `speckit_full_workflow`, `speckit_execute_command`, `speckit_review_documents`). (行为对标 Speckit-mcp-x 的自动化工具链。)

## When to use / 何时使用

Invoke when the user `@` mentions this skill, says **「用 speckit …」**, **「speckit 全流程」**, or wants spec-driven development from a feature description. (用户 @ 本 skill、说「用 speckit」或要从自然语言需求走 SDD 时使用。)

## Operating modes / 运行模式

Detect mode from user message; default is **full semi-auto**. (从用户消息判断模式；默认为全流程半自动。)

| Mode | Trigger examples | Behavior |
|------|------------------|----------|
| **full** (default) | feature description only; 「全流程」「半自动」 | Run Phase 0→5 continuously; stop only at checkpoint or when clarify needs answers |
| **single** | 「只执行 specify」; 「执行 constitution 步骤」 | Run exactly one sub-skill, then stop |
| **resume** | 「继续实施」; 「从 checkpoint 继续」; after approval at checkpoint | Continue from last incomplete phase or start `implement` |
| **review** | 「查看文档摘要」; 「review documents」 at checkpoint | Run checkpoint review only (no implement) |

## Non-negotiable rules / 硬性规则

1. **Skill-based source of truth** — Route work through sub-skills below; do not duplicate their logic here. (子 skill 是唯一实现来源。)
2. **Semi-automation** — In **full** mode, after each phase succeeds, **automatically start the next phase** without asking 「是否继续」. (全流程模式下阶段完成后自动进入下一阶段。)
3. **Hard checkpoint after `tasks`** — Never call `speckit-implement` until the user explicitly approves at the checkpoint. (tasks 之后必须停下，未经明确批准不得 implement。)
4. **Clarify exception** — Pause mid-flow only when `speckit-clarify` must ask the user questions; resume semi-auto after answers. (仅 clarify 需要用户回答时可中断。)
5. **No `specify workflow run`** — Do not use `.specify/workflows/speckit/workflow.yml` or `specify workflow run`; this skill replaces that path. (不使用 CLI bundled workflow。)
6. **Missing sub-skill** — Stop and report the missing `.cursor/skills/speckit-*` path. (缺少子 skill 时停止并报错。)

## Sub-skill routing / 子 skill 路由

| Phase | Sub-skill path | MCP tool parity |
|-------|----------------|-----------------|
| 0 Preflight | *(this skill)* | `speckit_auto_setup` / `check_speckit_status` |
| 1 Constitution | `.cursor/skills/speckit-constitution/SKILL.md` | `speckit_execute_command` → constitution |
| 2 Specify | `.cursor/skills/speckit-specify/SKILL.md` | specify |
| 3 Clarify | `.cursor/skills/speckit-clarify/SKILL.md` | *(MCP has no separate tool; run when needed)* |
| 4 Plan | `.cursor/skills/speckit-plan/SKILL.md` | plan |
| 5 Tasks | `.cursor/skills/speckit-tasks/SKILL.md` | tasks → **checkpoint** |
| 6 Implement | `.cursor/skills/speckit-implement/SKILL.md` | implement (post-approval only) |
| Optional analyze | `.cursor/skills/speckit-analyze/SKILL.md` | — |
| Optional git branch | `.cursor/skills/speckit-git-feature/SKILL.md` | — |

**How to run a sub-skill:** Read the full `SKILL.md`, follow it exactly, pass through the user's feature description and any paths produced by prior phases. (读取并严格遵循子 skill，透传用户描述与前序产物路径。)

---

## Phase 0 — Preflight / 预检（对标 auto_setup）

Run once at the start of **full** or **resume** (if workspace state is unknown). (全流程或恢复时先跑预检。)

1. **Repository structure**
   - `.specify/` must exist. If missing: stop and tell the user to run `specify init` (or project onboarding) before continuing. (缺少 `.specify/` 则停止并提示初始化。)
   - `.specify/memory/constitution.md` should exist before constitution phase (create in Phase 1 if absent). (宪章文件在 Phase 1 前最好已存在。)
2. **Sub-skills** — Verify all required paths in the routing table exist (except optional rows). (确认子 skill 文件存在。)
3. **Integration** — Read `.specify/integration.json` if present; prefer `cursor-agent` skills under `.cursor/skills/`. (确认 integration 与 skill 安装一致。)
4. **CLI (advisory)** — If `specify` is on PATH, note version via `specify version`; if absent, continue with skills only (do not block). (CLI 可选，不阻塞 skill 流程。)
5. **Feature context** — If resuming, locate the active feature under `specs/<feature>/` from git branch, user path, or latest `spec.md`. (恢复时定位当前 feature 目录。)

**Preflight output (always brief):**

```text
Speckit preflight
- .specify/: OK | MISSING
- Sub-skills: OK | missing: [...]
- Active feature: specs/<name>/ | (new feature)
- Mode: full | single | resume | review
```

If preflight fails on required items, **stop**. Do not enter Phase 1. (预检失败则停止。)

---

## Full semi-automated pipeline / 全流程半自动（对标 full_workflow + execute_command）

Execute phases **in order**. In **full** mode, **do not ask for confirmation between phases** except clarify user questions and the final checkpoint. (按序执行；阶段间不询问是否继续。)

### Phase 1 — Constitution

- **Read and follow** `speckit-constitution`.
- Ensure `.specify/memory/constitution.md` reflects current project governance.
- On success → **immediately** continue to Phase 2.

### Phase 2 — Specify

- **Read and follow** `speckit-specify` with the user's feature description (`$ARGUMENTS` or chat request).
- Optional: if the project uses git feature branches, run `speckit-git-feature` **before or as part of** specify per that skill's rules.
- Produces `specs/<feature>/spec.md` (and related artifacts per sub-skill).
- On success → run clarify gate (Phase 3).

### Phase 3 — Clarify (conditional)

- Scan `spec.md` for `[NEEDS CLARIFICATION]`, TBD markers, or blocking ambiguities.
- If **none** or user said **skip clarify** / **exploratory spike**: log `Clarify: skipped` and **continue to Phase 4** (warn once if skipping with ambiguities).
- If **found**: **Read and follow** `speckit-clarify`. Ask up to 5 targeted questions, then encode answers into `spec.md`.
- After clarify completes (or user answers) → **continue to Phase 4** without extra confirmation.

### Phase 4 — Plan

- **Read and follow** `speckit-plan` for the active `specs/<feature>/`.
- On success → **immediately** continue to Phase 5.

### Phase 5 — Tasks

- **Read and follow** `speckit-tasks` for the active feature.
- On success → **STOP**. Enter **Checkpoint** (do not start implement).

**Progress between phases (one line each):**

```text
✅ Phase N complete: <phase name> → continuing
```

---

## Checkpoint — Mandatory stop / 强制检查点（对标 review_documents + MCP pause）

After `tasks.md` exists, **always** run checkpoint before implement. (tasks 生成后必须进入检查点。)

### 1. Document review (required)

Read and summarize these paths for the active feature (use `speckit_review_documents` behavior):

| Document | Path |
|----------|------|
| Constitution | `.specify/memory/constitution.md` |
| Specification | `specs/<feature>/spec.md` |
| Plan | `specs/<feature>/plan.md` |
| Tasks | `specs/<feature>/tasks.md` |

Provide a **structured summary** (not full file dumps):

- **Goal** — one sentence
- **Scope** — bullets
- **Plan highlights** — architecture / key decisions
- **Tasks** — task count, phases, critical path items
- **Risks / open questions** — if any remain

### 2. Present checkpoint menu (exact intent, adapt language to user)

```text
Tasks have been generated. Please review:
- Constitution (.specify/memory/constitution.md)
- Specifications (specs/<feature>/spec.md)
- Plan (specs/<feature>/plan.md)
- Tasks (specs/<feature>/tasks.md)

Would you like to:
1. ✅ Proceed with implementation
2. 📝 Refine the plan or tasks
3. 🔄 Make other adjustments
```

**Wait for user reply.** Do not call `speckit-implement` in the same turn as the checkpoint menu. (输出检查点后必须等待用户，不得同轮 implement。)

### 3. Handle checkpoint responses

| User intent | Action |
|-------------|--------|
| **Proceed** — e.g. `继续实施`, `开始 implement`, `proceed`, `option 1`, `批准`, `yes implement` | **Read and follow** `speckit-implement` |
| **Refine plan/tasks** — e.g. `修改 plan`, `refine tasks`, `option 2` | Re-run `speckit-plan` and/or `speckit-tasks`, then **return to Checkpoint** |
| **Other** — constitution/spec/clarify changes, `option 3` | Re-run the affected sub-skill(s), then re-run downstream phases as needed, then **return to Checkpoint** |
| **Review only** — `查看摘要`, `review documents` | Summarize only; stay at checkpoint |
| **Optional analyze** — user asks for consistency check | Run `speckit-analyze`, report findings, stay at checkpoint unless user approves implement |

---

## Single-step mode / 单步模式

If user requests one step only:

1. Run preflight if needed.
2. Execute **only** the matching sub-skill.
3. If step is `tasks`, run **Checkpoint** afterward.
4. If step is `implement`, require explicit approval unless user already approved in the same session after a checkpoint.

---

## Resume mode / 恢复模式

1. Run preflight; resolve `specs/<feature>/`.
2. Determine last complete phase from artifacts:
   - no `spec.md` → start Phase 2
   - no `plan.md` → start Phase 4
   - no `tasks.md` → start Phase 5
   - `tasks.md` exists, no implement yet → **Checkpoint**
   - user approved implement → Phase 6 only
3. Continue semi-auto from that phase through checkpoint or implement per user message.

---

## Error handling / 错误处理

- Sub-skill or script failure: stop, report phase name + error, suggest fix; do not skip ahead. (失败则停在该阶段。)
- Missing `specs/<feature>/`: run specify first or ask user for feature name once. (缺少 feature 目录时先 specify 或询问一次。)
- User cancels: acknowledge and list completed artifacts. (用户取消时汇总已完成产物。)

---

## User documentation / 用户文档

- Human-readable guide: `docs/SPECKIT_SKILL_GUIDE.md` (usage, examples, troubleshooting). (人类可读使用指南。)

## Compatibility / 兼容性

- Replaces legacy `.cursor/commands/speckit.md` orchestration logic; that file remains a shim pointing here. (旧命令仅为 shim。)
- Parity target: [Speckit-mcp-x](https://github.com/ElliotLion-ing/Speckit-mcp-x) semi-automation with skill execution instead of MCP tools when MCP is not configured. (无 MCP 时用本 skill 达到同等半自动体验。)
- Optional MCP: if `speckit` MCP server is configured, prefer **this skill** for orchestration consistency unless the user explicitly asks to use MCP tools. (已配置 MCP 时仍以本 skill 编排为准，除非用户明确要求 MCP。)

## Quick reference — user phrases / 用户话术速查

| Phrase | Action |
|--------|--------|
| Feature description only | **full** semi-auto from Phase 0 |
| `继续` (mid-flow, not at checkpoint) | Continue next phase (full mode) |
| `继续实施` / `开始 implement` | `speckit-implement` after checkpoint |
| `查看生成的文档摘要` | Checkpoint review only |
| `重新生成 tasks` | Re-run `speckit-tasks` → Checkpoint |
| `跳过 clarify` | Phase 3 skip → Phase 4 |
