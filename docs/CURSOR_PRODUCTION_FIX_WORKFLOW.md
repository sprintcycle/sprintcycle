# Cursor 生产就绪修复工作流

SprintCycle 在 Cursor 中的 **代码级生产就绪** = 本地 `make ci-local` 与 GitHub Actions `.github/workflows/ci.yml` 一致且全绿。

**运行时生产就绪** 另见 `docs/production/PRODUCTION_CHECKLIST.md`（Docker、TLS、持久化等）。

这份文档的目标是把“怎么把失败修到 CI 全绿”讲清楚，确保每一轮修复都满足三个原则：

1. **先识别责任层，再动手修**：先判断问题属于 import、architecture、logic、frontend 还是 e2e。
2. **每轮只修一个簇**：避免多处同时改动导致无法判断修复是否真正有效。
3. **永远回到 detect**：任何修复都必须通过对应检测重新验证，而不是凭感觉结束。

---

## 这套工作流解决什么问题

Cursor 里的生产就绪修复工作流，解决的是“本地改动后如何稳定回到和 GitHub CI 一致的绿色状态”。它不是一个随意的试错脚本，而是一套受约束的闭环：

- 先跑本地检测，拿到真实失败信号
- 根据失败类型分簇
- 每轮只修一个最小范围问题
- 修完立即重新检测
- 直到本地 `make ci-local` 和 GitHub CI 的检查项一致且通过

这个设计的核心不是“快修完”，而是“**修得可验证、可归因、可停止**”。

---

## 组件一览

| 组件 | 路径 | 作用 |
|------|------|------|
| 本地 CI 脚本 | `scripts/ci-local.sh` | 镜像 CI 各阶段，写入 `.cursor/.ci-local-last-exit` |
| Import 快检 | `scripts/import-smoke.sh` | `lint-imports` + 架构测试 + collect-only |
| Make 入口 | `Makefile` | `ci-local`, `ci-local-quick`, `ci-smoke`, `arch-gate` |
| 主循环命令 | `.cursor/commands/ci-fix-loop.md` | `/ci-fix-loop` 检测 → 修复 → 检测 |
| 自动续跑 Hook | `.cursor/hooks.json` + `ci-stop-followup.sh` | Agent 停止后未通过则续跑 |
| 架构规则 | `.cursor/rules/*.mdc` | 每轮修复硬约束 |

### 组件之间的关系

- `scripts/ci-local.sh` 是最底层的执行器，负责把阶段结果写入日志和退出码文件。
- `make ci-smoke`、`make ci-local-quick`、`make ci-local` 是面向人的入口，帮你按不同粒度触发检测。
- `.cursor/commands/ci-fix-loop.md` 是总流程，负责把“检测 → 修复 → 再检测”串起来；cluster A/B 修复策略内联于该命令（路径迁移优先、分层契约）。
- `.cursor/rules/*.mdc` 是所有修复动作的边界约束，命令和脚本都必须遵守它们。

---

## 推荐使用场景

这套流程适合下面这些情况：

- 本地改完代码后，CI 开始失败
- `lint-imports` 报分层违规
- `pytest --collect-only` 因导入失败而挂掉
- `ruff` 报风格或 import 排序问题
- 前端 lint/build 失败
- Playwright E2E 失败，需要逐步定位是 UI 还是接口契约问题

不适合的情况：

- 你还没拿到真实失败信息，想先凭感觉改
- 你想一次修很多问题，但无法判断每个问题属于哪一层
- 你准备绕过既有 contract、hook 或 facade 去“快速修好”

---

## 快速开始

### 1. 环境（一次性）

```bash
cd /path/to/sprintcycle
python3.12 -m venv .venv
.venv/bin/pip install -e "[dev,dashboard]"
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

### 3. Cursor 自动循环（首次使用时）

在 Cursor 聊天中：

1. 终端：`make ci-fix-loop-start`
2. 输入：`/ci-fix-loop`（或描述「按 ci-fix-loop 跑到 CI 全绿」）
3. 完成后：`make ci-fix-loop-stop`

Hook 在 Agent **stop** 时若 CI 未通过且 flag 已开启，会自动注入 `followup_message` 继续（默认最多 12 轮，`CI_FIX_LOOP_MAX` 可改）。

在 **Cursor → Settings → Hooks** 确认项目 hooks 已加载。

---

## 生产就绪修复的核心原则

### 1. 先判断 owning subsystem / layer

每次修复前先回答三个问题：

- 这次失败属于哪一类：import、architecture、logic、frontend 还是 e2e？
- 这个问题的责任层在哪里：service、facade、hook、orchestration、tests、frontend？
- 修复会不会跨层，或者改变生命周期责任？

如果答案表明这次修改会跨层，或者需要改变责任归属，就不要直接修；先停止并重新定界，再决定是否继续。

### 2. 每轮只修一个 cluster

一个 cluster 就是一类同质失败。常见 cluster 包括：

- A：import / path
- B：architecture contract
- C：ruff
- D：pytest logic
- E：frontend
- F：E2E

每轮只修一个 cluster 的原因是：

- 能保持改动范围最小
- 能让失败原因和修复动作一一对应
- 能避免“顺手修太多”，最后不知道到底哪个改动起作用

### 3. 修复后必须立刻 detect

修完不是结束。每轮都要根据 cluster 重新运行最窄范围的检查，然后再决定下一步。

这意味着：

- A/B 修复后，先跑 `make ci-smoke` 或 `CI_LOCAL_PHASE=arch bash scripts/ci-local.sh`
- C 修复后，跑 `CI_LOCAL_PHASE=ruff bash scripts/ci-local.sh`
- D 修复后，跑 `CI_LOCAL_PHASE=pytest bash scripts/ci-local.sh`
- E 修复后，跑 `CI_LOCAL_PHASE=frontend bash scripts/ci-local.sh`
- 所有前置阶段绿了，再跑 `make ci-local`

---

## 失败分簇与优先级

| 簇 | 现象 | 处理 |
|----|------|------|
| A Import/路径 | `ModuleNotFoundError`、`ImportError`、`pytest --collect-only` 失败 | `/ci-fix-loop` cluster A — 路径迁移优先 |
| B 架构契约 | `lint-imports` forbidden layer | `/ci-fix-loop` cluster B — 按架构规则移动代码/import |
| C Ruff | `ruff check` | 仅风格与 import 排序 |
| D Pytest 逻辑 | imports 已绿，但断言失败 | 最小业务/测试修复，遵守分层 |
| E 前端 | `npm run lint` / `build` | frontend 目录内修复 |
| F E2E | Playwright | 仅 UI / 路由 / 交互问题 |

**优先级顺序**：A → B → C → D → E → F

这个优先级的意思不是“别的失败不重要”，而是**先解决最容易阻塞下游判断的东西**。例如 import 不通时，pytest 的断言结果往往没有意义，所以要先处理 A/B。

---

## Import 修复策略（路径迁移优先）

当错误为 `ModuleNotFoundError` / `ImportError` 时：

1. **默认原因**：文件或目录在重构中移动了，旧 import 没更新。
2. **正确做法**：在代码库中找到符号的**当前路径**，只改 import 行。
3. **禁止**：重建旧路径、兼容 shim、`try/except ImportError`、re-export 别名。

辅助命令：

```bash
git log --follow --name-status -- 'sprintcycle/path/to/old_module.py'
git log --diff-filter=R --summary -30 -- sprintcycle/
rg -n 'class Foo|def foo' sprintcycle tests
```

专用策略：见 `.cursor/commands/ci-fix-loop.md` § Path migration first。

### 为什么强调“路径迁移优先”

因为这个仓库经历过 8 层结构重排，很多 import 失败并不是“功能不存在”，而是“位置变了”。如果这时新建旧路径、加 shim 或写 fallback，就会：

- 破坏当前分层边界
- 让旧结构重新变成事实上的主路径
- 让代码同时存在“真实路径”和“兼容路径”，增加维护负担

所以这里的原则很明确：**只修导入方，不重建旧路径**。

### 什么时候要停止

如果搜索和 git history 证明该符号不是“移动”而是“删除”，就不要猜测性修复。此时应当停止并报告为非 import 阻塞，由产品或架构决策是否恢复该能力。

---

## 架构契约修复策略

当失败来自分层违规时，按 `/ci-fix-loop` cluster B 与 `sprintcycle-architecture-orchestration.mdc` 处理。

这类问题的核心不是“让 lint 过”，而是“让 import 方向重新符合架构责任”。常见处理方式包括：

- 改成从正确的上游层导入
- 把共享类型移动到中性模块
- 通过已有 facade / service 委派，而不是直接跨层 import

### 这类修复的边界

- **不要** 删除或注释 import-linter contracts
- **不要** 用 `# noqa` 或其他忽略手段掩盖违规
- **不要** 用兼容层把违规永久化
- **不要** 为了短期绿灯引入新的平行路径

### 什么时候要停止

如果修复需要改变责任层或生命周期归属，就不能直接改 import 糊过去。应当先停止，重新确认这个行为到底属于哪一层，再决定是移动代码、拆共享类型，还是通过已有 service/facade 转发。

---

## Pytest 逻辑修复策略

当 `import` 已经绿了，但 pytest 仍失败，通常说明问题已经进入业务逻辑或测试逻辑层。

这时的原则是：

- 先确认是生产代码还是测试断言有问题
- 修复尽量落在 owning service / facade / hook / domain，而不是入口层
- 只做能够证明问题根因的最小改动

### 常见误区

- 为了通过测试，把逻辑临时塞回 `api.py`
- 在 HTTP 层补业务判断
- 在 UI 层复制后端编排逻辑
- 为了快速绿灯，破坏服务边界

### 正确方向

如果测试失败说明业务行为改变了，就让修复回到对应的领域层或 service 层；如果测试本身写错了，也应当把测试改成真实反映契约，而不是迁就错误实现。

---

## 前端与 E2E 修复策略

前端和 E2E 的失败不要反向污染后端编排。

### Frontend

适用范围：

- `npm run lint`
- `npm run build`
- 类型错误
- OpenAPI 同步问题

处理原则：

- 在 `frontend/` 内解决
- 不要为了前端通过，去改后端流程边界
- 如果接口契约不匹配，优先修契约或生成过程，而不是在 UI 中补临时逻辑

### E2E

适用范围：

- Playwright 失败
- 页面交互/路由/等待条件问题

处理原则：

- 只修 UI、路由、等待和可见交互
- 不要把后端编排逻辑复制到前端
- 不要把运行时状态机嵌进页面

---

## 自动续跑 Hook 是怎么工作的

Hook 的作用是：**当 Agent 停止但 CI 还没绿时，自动把任务接回去**。

它的价值在于减少“修了一半就断掉”的情况。尤其是在这类长循环里，人工容易在：

- 修复一次后忘记重新跑检测
- 某个 cluster 绿了但整体还没绿
- 失败反复出现但没有持续跟踪

Hook 会在满足条件时继续执行，但它不是绕过人工判断的手段。真正的规则仍然是：

- 每轮只修一个 cluster
- 每次修完都重新检测
- 如果问题需要架构或产品决策，就停止

---

## 停止条件

以下情况应该停止，而不是继续盲修：

- `make ci-local` 退出码为 `0`
- 同一 blocker 连续 3 轮未变化
- 失败需要产品或架构决策，例如生命周期语义、promotion 策略、责任层调整
- 达到 `CI_FIX_LOOP_MAX`

停止的意思不是“放弃”，而是“当前自动循环不再适合继续，应该换成显式决策或单独分析”。

---

## 与 GitHub CI 的对应关系

| CI job / step | 本地 |
|---------------|------|
| `lint-imports` | `make arch-gate` / `CI_LOCAL_PHASE=arch` |
| `ruff check` | `CI_LOCAL_PHASE=ruff` |
| `pytest` | `make test` / `CI_LOCAL_PHASE=pytest` |
| frontend build + lint | `CI_LOCAL_PHASE=frontend` |
| Playwright | `make ci-local`（非 quick） |

这个对应关系保证本地修复和 GitHub CI 的判断口径一致。也就是说，**本地绿不只是“看起来能跑”，而是“和 CI 检查项一致地通过”**。

---

## 推荐的操作节奏

1. 跑 `make ci-smoke`
2. 看 `.cursor/ci-local-last.log` 和 `.cursor/.ci-local-last-exit`
3. 识别失败 cluster
4. 只修一个 cluster
5. 按对应最窄检查重新验证
6. 如果 A/B/C/D/E 都绿了，再跑 `make ci-local`
7. 通过后执行 `make ci-fix-loop-stop`

如果中途遇到跨层问题、生命周期问题或产品决策问题，就停止并升级，而不是继续在自动循环里硬磨。

---

## 故障排查

| 问题 | 处理 |
|------|------|
| Hook 不续跑 | 确认 `make ci-fix-loop-start`；重启 Cursor；看 Hooks 输出通道 |
| `.venv` 缺失 | 按上文创建 venv 并 `pip install -e "[dev,dashboard]"` |
| import 反复失败 | 检查是否在重建旧路径；用 git history 确认新路径 |
| lint-imports 与 import 错误混淆 | 前者 cluster B（分层契约），后者 cluster A（路径迁移）；均见 `/ci-fix-loop` |
| 修复后还是回到同一 blocker | 检查是不是已经超出自动修复范围，需要架构或产品决策 |

---

## 这份工作流的底线

这套工作流的底线可以概括为一句话：

**只做最小、可验证、符合分层边界的修复；修完马上回到检测；一旦越界就停止。**

它不是“无限修复脚本”，而是“带边界的生产就绪恢复流程”。

---

## 相关文档

- `AGENTS.md` — Agent 协作底线
- `.cursor/rules/sprintcycle-architecture-orchestration.mdc` — 分层边界
- `docs/production/PRODUCTION_CHECKLIST.md` — 部署上线清单
