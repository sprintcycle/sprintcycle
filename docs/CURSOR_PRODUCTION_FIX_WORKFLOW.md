# Cursor 生产就绪修复工作流

SprintCycle 在 Cursor 中的 **代码级生产就绪** = 本地 `make ci-local` 与 GitHub Actions `.github/workflows/ci.yml` 一致且全绿。

**运行时生产就绪** 另见 `docs/production/PRODUCTION_CHECKLIST.md`（Docker、TLS、持久化等）。

---

## 组件一览

| 组件 | 路径 | 作用 |
|------|------|------|
| 本地 CI 脚本 | `scripts/ci-local.sh` | 镜像 CI 各阶段，写入 `.cursor/.ci-local-last-exit` |
| Import 快检 | `scripts/import-smoke.sh` | `lint-imports` + 架构测试 + collect-only |
| Make 入口 | `Makefile` | `ci-local`, `ci-local-quick`, `ci-smoke`, `arch-gate` |
| 主循环命令 | `.cursor/commands/ci-fix-loop.md` | `/ci-fix-loop` 检测→修复→检测 |
| Import 修复 | `.cursor/commands/fix-python-imports.md` | **路径迁移优先** |
| 架构契约 | `.cursor/commands/fix-arch-imports.md` | `lint-imports` 分层违规 |
| 自动续跑 Hook | `.cursor/hooks.json` + `ci-stop-followup.sh` | Agent 停止后未通过则续跑 |
| 架构规则 | `.cursor/rules/*.mdc` | 每轮修复硬约束 |

---

## 快速开始

### 1. 环境（一次性）

```bash
cd /path/to/sprintcycle
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev,dashboard]"
cd frontend && npm ci && cd ..
chmod +x scripts/ci-local.sh scripts/import-smoke.sh .cursor/hooks/ci-stop-followup.sh
```

### 2. 基线检测

```bash
make ci-smoke          # 快：import / 架构
make ci-local-quick    # 全 CI 除 Playwright
make ci-local          # 含 E2E，与 GitHub 一致
```

日志：`.cursor/ci-local-last.log`  
退出码：`.cursor/.ci-local-last-exit`（`0` = 通过）

### 3. Cursor 自动循环

在 Cursor 聊天中：

1. 终端：`make ci-fix-loop-start`
2. 输入：`/ci-fix-loop`（或描述「按 ci-fix-loop 跑到 CI 全绿」）
3. 完成后：`make ci-fix-loop-stop`

Hook 在 Agent **stop** 时若 CI 未通过且 flag 已开启，会自动注入 `followup_message` 继续（默认最多 12 轮，`CI_FIX_LOOP_MAX` 可改）。

在 **Cursor → Settings → Hooks** 确认项目 hooks 已加载。

---

## Import 修复策略（路径迁移优先）

当错误为 `ModuleNotFoundError` / `ImportError` 时：

1. **默认原因**：文件/目录在重构中移动，旧 import 未更新。
2. **正确做法**：在代码库中找到符号的**当前路径**，只改 import 行。
3. **禁止**：重建旧路径、兼容 shim、`try/except ImportError`、re-export 别名。

辅助命令：

```bash
git log --follow --name-status -- 'sprintcycle/path/to/old_module.py'
git log --diff-filter=R --summary -30 -- sprintcycle/
rg -n 'class Foo|def foo' sprintcycle tests
```

专用命令：`/fix-python-imports`

若为 **分层 forbidden import**（非找不到模块），使用 `/fix-arch-imports`，且不得削弱 `pyproject.toml` 中的 import-linter 契约。

---

## 失败分簇与优先级

| 簇 | 现象 | 处理 |
|----|------|------|
| A Import/路径 | ModuleNotFound, collect-only 失败 | `/fix-python-imports` |
| B 架构契约 | lint-imports forbidden | `/fix-arch-imports` |
| C Ruff | E/F/W/I | 仅风格与 import 排序 |
| D Pytest 逻辑 | import 已绿，断言失败 | 最小业务/测试修复，遵守分层 |
| E 前端 | lint/build | frontend 目录 |
| F E2E | Playwright | 仅 UI/路由 |

**每轮只修一簇** → 重跑对应 `CI_LOCAL_PHASE` → 再 `make ci-local-quick` → 最后 `make ci-local`。

---

## 环境变量

| 变量 | 说明 |
|------|------|
| `CI_LOCAL_SKIP_E2E=1` | 跳过 Playwright（`make ci-local-quick`） |
| `CI_LOCAL_PHASE=arch\|ruff\|pytest\|frontend\|e2e` | 只跑某一阶段 |
| `CI_FIX_LOOP_MAX=12` | Hook 最大自动续跑轮次 |

---

## 停止条件

- `make ci-local` 退出码 `0`
- 同一 blocker 连续 3 轮未变
- 需要产品/架构决策（生命周期语义、promotion 策略等）
- 达到 `CI_FIX_LOOP_MAX`

---

## 与 GitHub CI 的对应关系

| CI job / step | 本地 |
|---------------|------|
| `lint-imports` | `make arch-gate` / `CI_LOCAL_PHASE=arch` |
| `ruff check` | `CI_LOCAL_PHASE=ruff` |
| `pytest` | `make test` / `CI_LOCAL_PHASE=pytest` |
| frontend build+lint | `CI_LOCAL_PHASE=frontend` |
| Playwright | `make ci-local`（非 quick） |

---

## 故障排查

| 问题 | 处理 |
|------|------|
| Hook 不续跑 | 确认 `make ci-fix-loop-start`；重启 Cursor；看 Hooks 输出通道 |
| `.venv` 缺失 | 按上文创建 venv 并 `pip install -e ".[dev,dashboard]"` |
| import 反复失败 | 检查是否在重建旧路径；用 git history 确认新路径 |
| lint-imports 与 import 错误混淆 | 前者用 `/fix-arch-imports`，后者用 `/fix-python-imports` |

---

## 相关文档

- `AGENTS.md` — Agent 协作底线
- `.cursor/rules/sprintcycle-architecture-orchestration.mdc` — 分层边界
- `docs/production/PRODUCTION_CHECKLIST.md` — 部署上线清单
