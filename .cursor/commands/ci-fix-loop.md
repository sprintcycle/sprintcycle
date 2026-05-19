# CI fix loop / 生产就绪修复循环

Drive SprintCycle to the same bar as GitHub CI using a **detect → fix → detect** loop. All fixes must obey repository rules (architecture, venv-only, minimal diff).

## Production definition

**Code production-ready** = local `make ci-local` exits 0 (mirrors `.github/workflows/ci.yml`).

**Runtime production-ready** = additionally complete `docs/production/PRODUCTION_CHECKLIST.md` (Docker, TLS, persistence).

This command targets **code production-ready**.

## Session setup (first message only)

1. Run `make ci-fix-loop-start` to enable Hook auto-continue (max 12 iterations; override with `CI_FIX_LOOP_MAX`).
2. Run baseline detection:
   ```bash
   make ci-smoke || true
   make ci-local-quick || true
   ```
3. Read `.cursor/ci-local-last.log` and classify failures into **clusters** (see below).

## Failure clusters (fix one cluster per iteration)

| Cluster | Detector | Fix command / strategy |
|---------|----------|----------------------|
| **A — Import / path** | `ModuleNotFoundError`, `ImportError`, pytest collect-only, `lint-imports` import graph | Follow **path migration first** (see `/fix-python-imports`) |
| **B — Architecture contract** | `lint-imports` forbidden layer | `/fix-arch-imports` — move code or imports across layers, never silence contracts |
| **C — Ruff** | `ruff check` | Style/import order only; no behavior change |
| **D — Pytest logic** | assertion failures with imports already green | Minimal test + production code fix; respect service/facade/hook boundaries |
| **E — Frontend** | `npm run lint` / `build` | Types, lint, OpenAPI sync |
| **F — E2E** | Playwright | UI/routing only; do not duplicate backend orchestration in frontend |

**Priority order:** A → B → C → D → E → F

## Path migration first (cluster A — mandatory)

When fixing imports, **default hypothesis: the module moved during refactor/restructure**.

1. **Do not** recreate the old package path.
2. **Do not** add compatibility shims, `try/except ImportError`, or re-export aliases.
3. **Do** locate the symbol in its **current** file and update `import` lines to the final module path.

### Path migration workflow

1. From the error, record `old.module.path` and the missing symbol.
2. Find the new home:
   ```bash
   git log --follow --name-status -- '**/old_file.py'
   git log --diff-filter=R --summary -20
   rg -n 'class SymbolName|def symbol_name' sprintcycle tests
   ```
3. Build a mapping table (report in output):

   | Broken import | Likely cause | New module path | Evidence |
   |---------------|--------------|-----------------|----------|

4. Apply the **smallest** import-line change in the importing file.
5. Re-run:
   ```bash
   make ci-smoke
   ```

## Detect → fix → detect loop

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

### Per-iteration rules

- Fix **at most one cluster** per iteration.
- After each fix, re-run the **narrowest** check:
  - A/B: `make ci-smoke` or `CI_LOCAL_PHASE=arch bash scripts/ci-local.sh`
  - C: `CI_LOCAL_PHASE=ruff bash scripts/ci-local.sh`
  - D: `CI_LOCAL_PHASE=pytest bash scripts/ci-local.sh`
  - E: `CI_LOCAL_PHASE=frontend bash scripts/ci-local.sh`
- When A/B/C/D/E are green, run `make ci-local`.
- **Stop conditions:**
  - `make ci-local` exits 0 → success, run `make ci-fix-loop-stop`
  - Same blocker text **3 times in a row** → stop, report blocker + options
  - Non-import blocker needs product/architecture decision → stop

### Parallelization (optional)

If two clusters touch **disjoint file sets**, spawn parallel subagents; **you** merge and run `make ci-local-quick` before declaring success.

## Hard constraints (always)

- `.cursor/rules/python-venv-only.mdc` — use `.venv/bin/python`, `.venv/bin/pytest` only
- `.cursor/rules/sprintcycle-architecture-orchestration.mdc` — no domain logic in API/UI; no bypassing hooks/facades
- No unrelated refactors
- No weakening import-linter contracts to “make CI green”

## Output (every iteration)

Report:

1. Cluster addressed
2. Path migration table (if cluster A)
3. Files changed
4. Commands run + pass/fail
5. Contents of `.cursor/.ci-local-last-exit`
6. Next cluster or final status
