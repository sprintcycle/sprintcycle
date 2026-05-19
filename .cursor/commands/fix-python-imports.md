# Fix Python imports / 修复 Python 导入

Repair broken Python imports by aligning them to code that **already exists** in its final location. Default assumption: failures come from **file/directory path changes** during refactor, not missing implementations.

## Goal

- Recursively resolve `ModuleNotFoundError`, `ImportError`, and pytest collect-only import failures.
- **Path migration first:** update importing files to new module paths; do not recreate old paths.
- Run fast smoke, then full tests when smoke is green.
- Stop on non-import blockers with a clear report.

## Default hypothesis: path migration

Most import breaks in this repo are caused by **moves/renames** (8-layer restructure, folder policy). Before creating new modules:

1. Treat `old.package.module` as a **relocated** module, not a deleted one.
2. Find where the symbol lives **now** (`rg`, `git log --follow`, `git log --diff-filter=R`).
3. Change only the `import` / `from ... import` lines in the **importer**.
4. Do **not** add compatibility shims, fallback imports, or re-export aliases under the old path.

## Path migration workflow (mandatory for cluster A)

1. From the traceback, extract:
   - broken module string (e.g. `sprintcycle.foo.bar`)
   - missing name (class/function) if present
   - importing file path
2. Locate the new module:
   ```bash
   git log --follow --name-status -- 'sprintcycle/**/bar.py'
   git log --diff-filter=R --summary -30 -- sprintcycle/
   rg -n 'class MissingName|def missing_name' sprintcycle tests
   ```
3. Record a mapping (include in your report):

   | Broken import | Hypothesis | New import path | Evidence (git/rg) |
   |---------------|------------|-----------------|-------------------|

4. Apply the smallest edit in the importing file(s).
5. If multiple files import the same stale path, fix the **same cluster** in one iteration.
6. Re-run smoke:
   ```bash
   bash scripts/import-smoke.sh
   # or: make ci-smoke
   ```

### When the symbol truly does not exist

Only after search + git history show the code was removed (not moved):

- Stop and report as a **non-import blocker**.
- Do not invent placeholder modules.

## Rules

- Only import-related changes unless a test proves a tightly coupled fix is required.
- No unrelated refactors.
- Smallest edit that restores importability.
- No compatibility shims, `try/except ImportError`, or re-export aliases.
- Use `.venv/bin/python` and `.venv/bin/pytest` only (see `python-venv-only.mdc`).

## Execution flow

1. Run `make ci-smoke` (or `bash scripts/import-smoke.sh`) for baseline.
2. Build path-mapping for each broken import (table above).
3. Fix one import cluster; re-run smoke.
4. When smoke passes, run `.venv/bin/pytest tests/ -q --tb=short`.
5. If pytest fails on imports, repeat from step 2.
6. When imports are clean but assertions fail, stop — hand off to `/ci-fix-loop` cluster D.

## Test selection

- **Smoke:** `make ci-smoke` (`lint-imports` + `test_architecture_imports` + `pytest --collect-only`)
- **Full:** `.venv/bin/pytest tests/ -q --tb=short`

## Output

Report:

- Path migration table
- Files changed
- Smoke + full pytest results
- Remaining blockers (if any)
