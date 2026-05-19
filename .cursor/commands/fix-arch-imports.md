# Fix architecture import contracts / 修复架构 import 契约

Use when `lint-imports` fails with **forbidden import** or **layer violation** (not `ModuleNotFoundError`).

For missing modules after directory moves, use `/fix-python-imports` instead (path migration first).

## Goal

- Make `.venv/bin/lint-imports` pass without weakening `pyproject.toml` contracts.
- Preserve 8-layer boundaries in `.cursor/rules/sprintcycle-architecture-orchestration.mdc`.

## Rules

- **Never** delete or comment out import-linter contracts to get green CI.
- **Never** add `# noqa` or linter ignores for architectural violations.
- Prefer moving the **dependent** code or changing the import direction to respect layers.
- Smallest change only; no drive-by refactors.

## Workflow

1. Run `.venv/bin/lint-imports` and capture the contract name + modules involved.
2. Open the matching `[[tool.importlinter.contracts]]` block in `pyproject.toml` for intent.
3. Identify which layer owns the behavior (service, facade, orchestration, etc.).
4. Fix by one of:
   - Import from the correct upstream layer
   - Move shared types to a neutral module both layers may depend on
   - Delegate through an existing facade/service instead of a direct import
5. Re-run:
   ```bash
   make ci-smoke
   CI_LOCAL_PHASE=arch bash scripts/ci-local.sh
   ```

## Output

- Contract violated
- Root cause (wrong layer coupling)
- Files changed
- `lint-imports` result
