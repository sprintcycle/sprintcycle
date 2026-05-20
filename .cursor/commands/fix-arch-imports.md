# Fix architecture import contracts / 修复架构 import 契约

Use when `lint-imports` fails with **forbidden import** or **layer violation** (not `ModuleNotFoundError`). (当 `lint-imports` 因 **禁止导入** 或 **层级违规** 失败时使用；不是 `ModuleNotFoundError`。)

For missing modules after directory moves, use `/fix-python-imports` instead (path migration first). (如果是目录移动后缺少模块，请改用 `/fix-python-imports`（先做路径迁移）。)

## Goal / 目标

- Make `.venv/bin/lint-imports` pass without weakening `pyproject.toml` contracts. (让 `.venv/bin/lint-imports` 通过，同时不削弱 `pyproject.toml` 的 contracts。)
- Preserve 8-layer boundaries in `.cursor/rules/sprintcycle-architecture-orchestration.mdc`. (保持 `.cursor/rules/sprintcycle-architecture-orchestration.mdc` 里的 8 层边界。)
- If the fix would change responsibility layers or lifecycle ownership, stop and re-scope before editing. (如果修复会改变责任层或生命周期归属，先停止并重新定界，再编辑。)

## Rules / 规则

- **Never** delete or comment out import-linter contracts to get green CI. (**不要** 删除或注释掉 import-linter contracts 来让 CI 变绿。)
- **Never** add `# noqa` or linter ignores for architectural violations. (**不要** 为架构违规添加 `# noqa` 或忽略规则。)
- Prefer moving the **dependent** code or changing the import direction to respect layers. (优先移动**依赖方**代码，或调整 import 方向以符合层级。)
- Smallest change only; no drive-by refactors. (只做最小修改；不要顺手做无关重构。)

## Workflow / 流程

1. Run `.venv/bin/lint-imports` and capture the contract name + modules involved. (运行 `.venv/bin/lint-imports`，记录 contract 名称和涉及模块。)
2. Open the matching `[[tool.importlinter.contracts]]` block in `pyproject.toml` for intent. (打开 `pyproject.toml` 中对应的 `[[tool.importlinter.contracts]]` 块，理解设计意图。)
3. Identify which layer owns the behavior (service, facade, orchestration, etc.). (识别该行为属于哪一层：service、facade、orchestration 等。)
4. Fix by one of: (按以下方式修复之一：)
   - Import from the correct upstream layer
   - Move shared types to a neutral module both layers may depend on
   - Delegate through an existing facade/service instead of a direct import
5. Re-run: (重新运行：)
   ```bash
   make ci-smoke
   CI_LOCAL_PHASE=arch bash scripts/ci-local.sh
   ```

## Output / 输出

- Contract violated（违反的 contract）
- Root cause (wrong layer coupling)（根因：错误的层级耦合）
- Files changed（修改的文件）
- `lint-imports` result（`lint-imports` 结果）
