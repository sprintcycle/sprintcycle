# Fix Python imports / 修复 Python 导入

Use this command to recursively scan the repository for broken Python imports, align every import to the code that already exists in its final location, and drive the project to a final passing state.

## Goal
- Recursively scan all Python files in the repository for broken, missing, or incorrect imports.
- Repair import failures by pointing imports at the current real module paths.
- Move directly toward the final working state instead of preserving compatibility layers or temporary shims.
- Run a fast smoke test first, then the full test suite once the smoke test is green.
- Continue fixing failures until the project reaches a passing state, or clearly report the first non-import blocker.

## Rules
- Only fix import-related issues unless a test failure proves a closely related change is required.
- Do not perform unrelated refactors.
- Prefer the smallest possible edit that restores importability.
- Do not add compatibility shims, fallback paths, transitional glue, or re-export aliases.
- Use the repository virtual environment for all Python and pytest commands.
- Always use `.venv/bin/python` and `.venv/bin/pytest`.
- Do not use the system Python interpreter.
- Do not use global `pytest`.

## Execution flow
1. Scan the whole repository recursively for Python import errors.
2. Build a path-mapping view of where each broken import now lives in the current codebase.
3. Identify the broken import chain and the owning file.
4. If the code already exists in a new location, update the importing code to the new final path instead of recreating the old module path.
5. Apply the smallest necessary fix that moves the code toward the final desired structure.
6. Run a fast smoke test first.
7. If the smoke test fails, fix the cause and repeat.
8. When the smoke test passes, run the full test suite.
9. If the full test suite fails due to import issues, fix them and rerun.
10. Stop only when the tests pass or a non-import blocker is identified and reported.

## Test selection
- Prefer an existing project smoke test or the narrowest useful pytest subset.
- If no dedicated smoke test exists, choose the fastest reasonable subset that exercises import paths first.
- After the smoke test passes, run the full suite with `.venv/bin/pytest`.

## Output
Report:
- which broken import paths were aligned to final module locations
- what was changed
- what smoke test was run
- whether the full test suite passed
- any remaining blockers, if present
