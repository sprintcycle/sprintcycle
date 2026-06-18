# CI fix loop / 生产就绪修复循环

Drive SprintCycle to the same bar as GitHub CI using a **detect → fix → detect** loop. All fixes must obey repository rules (architecture, venv-only, minimal diff). (使用 **detect → fix → detect** 循环，让 SprintCycle 达到与 GitHub CI 相同的标准。所有修复都必须遵守仓库规则：架构约束、仅用 venv、最小 diff。)

## Production definition / 生产就绪定义

**Code production-ready** = local `make ci-local` exits 0 (mirrors `.github/workflows/ci.yml`). (**代码生产就绪** = 本地 `make ci-local` 退出码为 0，与 `.github/workflows/ci.yml` 一致。)

**Runtime production-ready** = additionally complete `docs/production/PRODUCTION_CHECKLIST.md` (Docker, TLS, persistence). ( **运行时生产就绪** = 另外完成 `docs/production/PRODUCTION_CHECKLIST.md`（Docker、TLS、持久化）。)

This command targets **code production-ready**. (本命令只针对 **代码生产就绪**。)

## Session setup (first message only) / 会话初始化（仅首次消息）

1. Run `make ci-fix-loop-start` to enable Hook auto-continue (max 12 iterations; override with `CI_FIX_LOOP_MAX`). (运行 `make ci-fix-loop-start` 启用 Hook 自动继续（最多 12 轮；可用 `CI_FIX_LOOP_MAX` 覆盖）。)
2. Run baseline detection: (运行基线检测：)
   ```bash
   make ci-smoke || true
   make ci-local-quick || true
   ```
3. Read `.cursor/ci-local-last.log` and classify failures into **clusters** (see below). (读取 `.cursor/ci-local-last.log` 并把失败分类为下面的 **clusters**。)

## Failure clusters (fix one cluster per iteration) / 失败分类（每轮只修一个 cluster）

| Cluster | Detector | Fix command / strategy |
|---------|----------|----------------------|
| **A — Import / path** | `ModuleNotFoundError`, `ImportError`, pytest collect-only, `lint-imports` import graph | Follow **path migration first** (see `/fix-python-imports`) |
| **B — Architecture contract** | `lint-imports` forbidden layer | `/fix-arch-imports` — move code or imports across layers, never silence contracts |
| **C — Ruff** | `ruff check` | Style/import order only; no behavior change |
| **D — Pytest logic** | assertion failures with imports already green | Minimal test + production code fix; respect service/facade/hook boundaries |
| **E — Frontend** | `npm run lint` / `build` | Types, lint, OpenAPI sync |
| **F — E2E** | Playwright | UI/routing only; do not duplicate backend orchestration in frontend |

**Priority order:** A → B → C → D → E → F (优先级顺序：A → B → C → D → E → F)

## Path migration first (cluster A — mandatory) / 路径迁移优先（A 类必做）

When fixing imports, **default hypothesis: the module moved during refactor/restructure**. (修复 import 时，**默认假设：模块在重构/重排时被移动了**。)

1. **Do not** recreate the old package path. (**不要** 重新创建旧的包路径。)
2. **Do not** add compatibility shims, `try/except ImportError`, or re-export aliases. (**不要** 添加兼容 shim、`try/except ImportError` 或 re-export 别名。)
3. **Do** locate the symbol in its **current** file and update `import` lines to the final module path. (**要** 找到符号当前所在文件，并把 `import` 改到最终模块路径。)

### Path migration workflow / 路径迁移流程

1. From the error, record `old.module.path` and the missing symbol. (从错误里记录 `old.module.path` 和缺失的符号。)
2. Find the new home: (查找新位置：)
   ```bash
   git log --follow --name-status -- '**/old_file.py'
   git log --diff-filter=R --summary -20
   rg -n 'class SymbolName|def symbol_name' sprintcycle tests
   ```
3. Build a mapping table (report in output): (构建映射表，并在输出中报告：)

   | Broken import | Likely cause | New module path | Evidence |
   |---------------|--------------|-----------------|----------|

4. Apply the **smallest** import-line change in the importing file. (在导入方文件中做 **最小** 的 import 行修改。)
5. Re-run: (重新运行：)
   ```bash
   make ci-smoke
   ```

## Detect → fix → detect loop / 检测 → 修复 → 再检测循环

```
┌─────────────┐
│ make ci-smoke│  (fast, import-focused)
└──────┬──────┘
       ▼
┌─────────────┐     cluster A/B      ┌──────────────────┐
│ pick 1 cluster│ ──────────────────► │ minimal code fix │
└──────┬──────┘                      └────────┬─────────┘
       │                                        │
       │         re-run targeted phase          │
       │◄───────────────────────────────────────┘
       ▼
┌──────────────────┐
│ make ci-local-quick │  (skip E2E for inner loops)
└────────┬─────────┘
         ▼ green?
┌──────────────────┐
│ make ci-local    │  (full CI including Playwright)
└────────┬─────────┘
         ▼
    report + make ci-fix-loop-stop
```

### Per-iteration rules / 每轮规则

- Fix **at most one cluster** per iteration.（每轮最多修一个 cluster。）
- Before each fix, confirm the **owning subsystem / layer** and whether the issue is import, architecture, logic, frontend, or e2e. If the fix would cross layers or change lifecycle responsibility, stop and re-scope before editing.（每次修复前，先确认**所属子系统/层**，以及问题属于 import、architecture、logic、frontend 还是 e2e；如果修复会跨层或改变生命周期责任，先停止并重新定界，再编辑。）
- After each fix, re-run the **narrowest** check: (每次修复后，重新运行**最窄范围**的检查：)
  - A/B: `make ci-smoke` or `CI_LOCAL_PHASE=arch bash scripts/ci-local.sh`
  - C: `CI_LOCAL_PHASE=ruff bash scripts/ci-local.sh`
  - D: `CI_LOCAL_PHASE=pytest bash scripts/ci-local.sh`
  - E: `CI_LOCAL_PHASE=frontend bash scripts/ci-local.sh`
- When A/B/C/D/E are green, run `make ci-local`. (当 A/B/C/D/E 都通过后，运行 `make ci-local`。)
- **Stop conditions:** (**停止条件：**)
  - `make ci-local` exits 0 → success, run `make ci-fix-loop-stop` (`make ci-local` 退出码为 0 → 成功，运行 `make ci-fix-loop-stop`)
  - Same blocker text **3 times in a row** → stop, report blocker + options (同一个阻塞信息连续出现 **3 次** → 停止，报告阻塞和选项)
  - Non-import blocker needs product/architecture decision → stop (非 import 阻塞需要产品/架构决策 → 停止)

### Parallelization (optional) / 并行处理（可选）

If two clusters touch **disjoint file sets**, spawn parallel subagents; **you** merge and run `make ci-local-quick` before declaring success. (如果两个 cluster 影响的文件集 **互不重叠**，可以并行子代理；在宣布成功前，**你** 负责合并并运行 `make ci-local-quick`。)

## Hard constraints (always) / 强制约束（始终适用）

- `.cursor/rules/python-venv-only.mdc` — use `uv run` for Python/pytest (使用 `uv run`)
- `.cursor/rules/sprintcycle-architecture-orchestration.mdc` — no domain logic in API/UI; no bypassing hooks/facades (`.cursor/rules/sprintcycle-architecture-orchestration.mdc` — API/UI 中不要放领域逻辑；不要绕过 hooks/facades)
- No unrelated refactors (不要做无关重构)
- No weakening import-linter contracts to “make CI green” (不要为了“让 CI 变绿”而削弱 import-linter contracts)

## Output (every iteration) / 输出（每轮都要）

Report: (报告：)

1. Cluster addressed (处理的 cluster)
2. Path migration table (if cluster A)（路径迁移表，若是 cluster A）
3. Files changed（修改的文件）
4. Commands run + pass/fail（运行的命令 + 通过/失败）
5. Contents of `.cursor/.ci-local-last-exit`（`.cursor/.ci-local-last-exit` 的内容）
6. Next cluster or final status（下一个 cluster 或最终状态）
