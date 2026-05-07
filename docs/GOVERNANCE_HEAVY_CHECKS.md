# 重型多源验证：Playwright、视觉与 CI（v4.0）

本文档与 **多源验证方案 v4.0** 对齐，说明 **浏览器 E2E**、**视觉回归** 及 **开关模型**，作为「重型验证矩阵」的单一事实来源。

## 1. 原则

- **仍走 Tier 1**：以子进程 `argv` 执行 Playwright / 脚本，结果经 `GovernanceReport` 汇总；**不把浏览器嵌入** `GovernanceRunner` Python 进程。
- **默认轻**：`review_browser_e2e` / `review_visual` 默认为 **false**，带对应 `tags` 的条目在合并后会被过滤，除非在 `sprintcycle.toml` 显式打开。
- **可组合**：方式 A（pack 拔插）、B（`enabled: false`）、C（TOML 总开关）、D（仅 CI job）可叠加。

## 2. 开关模型（A / B / C / D）

| 方式 | 做法 | 适用 |
|------|------|------|
| **A** | `governance_pack_paths` 是否包含 `examples/governance/playwright-visual.example.yaml` | 整包开关 |
| **B** | 单条 `enabled: false` | 同仓库保留模板、按需打开 |
| **C** | `[governance] review_browser_e2e = true` / `review_visual = true` | 带 `tags: [browser]` / `[visual]` 的条目才执行 |
| **D** | CI 单独 job 跑 `playwright test`，本地 `governance check` 不含浏览器 | 本地零负担 |

## 3. Playwright

- **安装**：`npm ci` 后 `npx playwright install`（CI 缓存 `~/.cache/ms-playwright`）。
- **无头**：CI 默认 `HEADLESS=1` 或 `playwright.config` 中 `fullyParallel` 等按项目约定。
- **超时**：治理 YAML `timeout_sec` 与 Playwright 用例超时对齐，避免挂死。
- **失败定位**：开启 `trace: 'on-first-retry'` 或上传 `playwright-report/` 为 CI 制品。

## 4. 视觉回归

- **基线**：截图或 Percy/Chromatic 基线提交策略写进团队 wiki；更新基线走独立 PR。
- **稳定性**：同一 CI 镜像、固定视口、关闭动画；flaky 用重试与 quarantine 列表。
- **与 Playwright 合并**：若使用 `toHaveScreenshot()`，可与 **§3 同一条** `argv` 完成，无需单独 `visual` 条目。

## 5. `sprintcycle governance check` / `validate` 与观测

- CLI：**`sprintcycle governance check`** 与顶层 **`sprintcycle validate`** 等价（v1 文档别名）。
- 每次 **planning / review** 成功后 **写盘**：`governance_planning_last.json`、`governance_last.json`；并追加 **`governance_history/<UTC>_<gate>.json`**（受 **`[governance] history_max_files`** 裁剪，默认 50）。
- 可选 **`[governance] cli_emit_events = true`**：向执行事件后端派发 `GOVERNANCE_GATE`（`sprint_name` 为 `__cli__`）。
- Dashboard：
  - **`GET /api/governance/latest`**：最近一次 Planning/Review JSON（若均不存在则 404）。
  - **`GET /api/governance/history?limit=`**：历史快照元数据（错误/警告计数等）。
  - **`POST /api/governance/check`**：请求体 `{"gate":"review"|"planning"|"both"}`，执行门禁并落盘，返回报告与 **`should_fail_ci`**。

## 6. 依赖扫描与突变（示例 pack）

- **`examples/governance/pip-audit.example.yaml`**：`pip-audit`（默认 `enabled: false`；需 `requirements.txt` 与已安装 `pip-audit`）。
- **`examples/governance/mutmut.example.yaml`**：`mutmut run`（默认关；需 **`pip install -e ".[mutation]"`**，建议在 CI 全量跑）。

## 7. 插件总线（v1 对齐、stdlib 优先）

- **Entry points**（默认开启，可用 **`[governance] argv_entry_points = false`** 关闭）：
  - 组名 **`sprintcycle_governance.review_argv`** / **`sprintcycle_governance.planning_argv`**。
  - 可调用签名：`() -> list[dict]` 或 **`(runtime_config, project_root: Path) -> list[dict]`**，返回的 dict 与治理 YAML `argv` 条目同形；合并后再做 **`tags` / `enabled`** 过滤。
- **可选 pluggy**（**`pip install sprintcycle[governance-ext]`** 且 **`[governance] pluggy_argv = true`**）：
  - 组 **`sprintcycle_governance.pluggy_plugin`**：可调用 **`register(pm)`**，在传入的 `PluginManager` 上注册 **`extra_governance_argv`** hookimpl（见 `sprintcycle/governance/pluggy_host.py`）。

## 8. Dashboard「治理」页

- 前端路由 **`/governance`**：展示 **最新报告**、**历史表**、**一键运行门禁**（调 `POST /api/governance/check`）及指向 **`docs/GOVERNANCE_ENGINEERING.md`** 的排障链接（非自动修复代码）。

## 9. 参考

- `examples/governance/playwright-visual.example.yaml`
- `examples/governance/pip-audit.example.yaml`、`mutmut.example.yaml`
- `docs/GOVERNANCE_ENGINEERING.md` §13.1.1
- `docs/GOVERNANCE_GOLDEN.md`（pytest 标记与模型对比）
