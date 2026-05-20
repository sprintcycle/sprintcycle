# Fix Python imports / 修复 Python 导入

Repair broken Python imports by aligning them to code that **already exists** in its final location. Default assumption: failures come from **file/directory path changes** during refactor, not missing implementations. (修复 Python imports 时，优先对齐到**已经存在**且位于最终位置的代码。默认假设：失败来自重构/重排时的**文件或目录路径变化**，而不是实现缺失。)

## Goal / 目标

- Recursively resolve `ModuleNotFoundError`, `ImportError`, and pytest collect-only import failures. (递归解决 `ModuleNotFoundError`、`ImportError` 和 pytest collect-only 的导入失败。)
- **Path migration first:** update importing files to new module paths; do not recreate old paths. (**先做路径迁移：** 只更新导入方到新的模块路径；不要重建旧路径。)
- Treat path migration as the default hypothesis **only when search + git history show the code was moved, not deleted**. (只有在搜索 + git 历史表明代码是被移动而不是删除时，才把路径迁移作为默认假设。)
- Run fast smoke, then full tests when smoke is green. (先跑快速 smoke，smoke 通过后再跑完整测试。)
- Stop on non-import blockers with a clear report. (遇到非 import 阻塞时停止，并给出清晰报告。)

## Default hypothesis: path migration / 默认假设：路径迁移

Most import breaks in this repo are caused by **moves/renames** (8-layer restructure, folder policy). Before creating new modules: (这个仓库里的 import 断裂大多来自**移动/重命名**（8 层重构、目录策略）。在创建新模块前：)

1. Treat `old.package.module` as a **relocated** module, not a deleted one. (把 `old.package.module` 当作**已迁移**的模块，而不是已删除。)
2. Find where the symbol lives **now** (`rg`, `git log --follow`, `git log --diff-filter=R`). (找到符号**现在**所在的位置（`rg`、`git log --follow`、`git log --diff-filter=R`）。)
3. Change only the `import` / `from ... import` lines in the **importer**. (只修改**导入方**的 `import` / `from ... import` 行。)
4. Do **not** add compatibility shims, fallback imports, or re-export aliases under the old path. (**不要** 为旧路径添加兼容 shim、fallback imports 或 re-export 别名。)

## Path migration workflow (mandatory for cluster A) / 路径迁移流程（A 类必做）

1. From the traceback, extract: (从 traceback 中提取：)
   - broken module string (e.g. `sprintcycle.foo.bar`)
   - missing name (class/function) if present
   - importing file path
2. Locate the new module: (定位新模块：)
   ```bash
   git log --follow --name-status -- 'sprintcycle/**/bar.py'
   git log --diff-filter=R --summary -30 -- sprintcycle/
   rg -n 'class MissingName|def missing_name' sprintcycle tests
   ```
3. Record a mapping (include in your report): (记录映射表，并包含到报告中：)

   | Broken import | Hypothesis | New import path | Evidence (git/rg) |
   |---------------|------------|-----------------|-------------------|

4. Apply the smallest edit in the importing file(s). (在导入方文件中做最小修改。)
5. If multiple files import the same stale path, fix the **same cluster** in one iteration. (如果多个文件引用同一个过期路径，在同一轮里修同一个 cluster。)
6. Re-run smoke: (重新运行 smoke：)
   ```bash
   bash scripts/import-smoke.sh
   # or: make ci-smoke
   ```

### When the symbol truly does not exist / 当符号确实不存在时

Only after search + git history show the code was removed (not moved): (只有在搜索 + git 历史确认代码是被删除而不是移动后：)

- Stop and report as a **non-import blocker**. (停止，并报告为 **non-import blocker**。)
- Do not invent placeholder modules. (不要发明占位模块。)

## Rules / 规则

- Only import-related changes unless a test proves a tightly coupled fix is required. (除非测试证明需要紧密耦合的修复，否则只做 import 相关修改。)
- No unrelated refactors. (不要做无关重构。)
- Smallest edit that restores importability. (用最小修改恢复可导入性。)
- No compatibility shims, `try/except ImportError`, or re-export aliases. (不要使用兼容 shim、`try/except ImportError` 或 re-export 别名。)
- Use `.venv/bin/python` and `.venv/bin/pytest` only (see `python-venv-only.mdc`). (只使用 `.venv/bin/python` 和 `.venv/bin/pytest`（见 `python-venv-only.mdc`）。)

## Execution flow / 执行流程

1. Run `make ci-smoke` (or `bash scripts/import-smoke.sh`) for baseline. (先运行 `make ci-smoke`（或 `bash scripts/import-smoke.sh`）作为基线。)
2. Build path-mapping for each broken import (table above). (为每个 broken import 建立路径映射表。)
3. Fix one import cluster; re-run smoke. (修一个 import cluster；重新跑 smoke。)
4. When smoke passes, run `.venv/bin/pytest tests/ -q --tb=short`. (smoke 通过后，运行 `.venv/bin/pytest tests/ -q --tb=short`。)
5. If pytest fails on imports, repeat from step 2. (如果 pytest 仍因导入失败，就回到第 2 步。)
6. When imports are clean but assertions fail, stop — hand off to `/ci-fix-loop` cluster D. (当 imports 已清理但断言失败时，停止——交给 `/ci-fix-loop` 的 D 类。)

## Test selection / 测试选择

- **Smoke:** `make ci-smoke` (`lint-imports` + `test_architecture_imports` + `pytest --collect-only`) ( **Smoke:** `make ci-smoke`（`lint-imports` + `test_architecture_imports` + `pytest --collect-only`）)
- **Full:** `.venv/bin/pytest tests/ -q --tb=short` ( **Full:** `.venv/bin/pytest tests/ -q --tb=short`)

## Output / 输出

Report: (报告：)

- Path migration table（路径迁移表）
- Files changed（修改的文件）
- Smoke + full pytest results（smoke + full pytest 结果）
- Remaining blockers (if any)（剩余阻塞（如果有））
