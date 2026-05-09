# SprintCycle 代码治理与质量门禁工程实践（设计稿）

> 版本：与 SprintCycle 仓库代码（约 v0.9.x）对齐的二次设计  
> 语言：中文  
> 范围：治理模型、扩展点、开源复用、Docker 一键启动、与现有质量档位（L0–L3 / G1–G4）的关系；**不引入 Kubernetes**。

---

## 1. 目标与原则

### 1.1 目标

- 将产品迭代与 SprintCycle 自进化从「无约束生成」推进为「**受治理的进化**」：准则、组件边界、交互契约可检验、可回归、可部署。
- 与 **Scrum** 节奏对齐：在**最合适的阶段**做**最合适的**检查与阻断。
- **自动化部署**以 **Docker / Docker Compose** 为界，暂不接入 K8s。
- 在**现有架构**上增量演进：**不**并行造第二套「质量档位」语义；治理与 `quality_level` / `quality_profile` **正交或可组合**。

### 1.2 原则

- **默认低开销**：治理与任务级钩子仍**默认关闭**；质量档位与存储则按「普通产品迭代」预设为 **L2（pytest+覆盖率）** 与 **SQLite 状态库**（无 `sprintcycle.toml` 时亦如此），便于自动化测试与单机自闭环。速写原型可用 `[quality] profile = "fast"` 或 `level = "L0"` 显式降级。
- **「开箱即审」保守组合（可选）**：见 **`sprintcycle.toml.example`** 中 `[governance]` 整段——`enabled = true`、`block_on = "none"`（**从不**因 Planning/Review 的 error 让 `governance check` 退出失败，也不阻断 Sprint）、`downgrade_errors_to_warnings = true`（聚合包内 **error → warning**，仍落盘/日志/SSE）。需要 CI 硬失败时再改 `block_on` 并关闭 downgrade。
- **钩子优先、内核稳定**：通过 `SprintLifecycleHooks` / 未来可选任务钩子扩展，少改编排器与执行器核心路径。
- **复用优于自研**：静态分析、架构边界、容器规范等优先调用成熟 CLI，SprintCycle 负责编排与报告聚合。

---

## 2. 与现行代码的对照

### 2.1 质量档位（已有）

`config/quality.py` 与 `RuntimeConfig` 已定义 L0–L3 与 G1–G4 的对应关系（静态、测试、覆盖率、架构不变量等）。治理方案**应复用** `effective_quality_level()` 与 `runs_static_gate` / `runs_pytest` 等，避免再引入一套「L0–L3」重复命名。

### 2.2 Sprint 生命周期钩子（已有）

- `execution/hooks/sprint_hooks.py`：`SprintLifecycleHooks`（`on_before_sprint` / `on_after_sprint`）、`ChainedSprintHooks`。
- 编排侧 `_OrchestratorSprintHooks` 与知识注入等可**链式叠加**。

### 2.3 计划与 Backlog（已有）

- `release_plan/validator.py`：`ReleasePlanValidator` —— 适合作为 **Backlog / Planning 结构门禁** 的延伸点（字段、agent 白名单、路径等）。

### 2.4 任务执行与 Daily（已有）

- `SprintExecutor`：任务并行执行、Coder 的 `max_verify_fix_rounds` 验证闭环。
- **任务级钩子**：可选 `TaskLifecycleHooks`（`GovernanceTaskLifecycleHooks` + 治理 YAML ``task_after``）在任务成功路径挂载；**Daily 类治理**仍以 `quality_level` + Coder/Tester 为主，``task_after`` 为团队可开关的增量门禁。

### 2.5 静态与架构（已有）

- `execution/static_analyzer.py`：Ruff / Mypy 等结果封装。
- `pyproject.toml`：`import-linter` 合约（G4 方向）。

---

## 3. Scrum 阶段 × 治理映射

| 阶段 | 治理重点 | 建议落点 |
|------|----------|----------|
| Product Backlog / 意图 → Plan | Spec 先行、条目可测、可切片 | `plan` 路径或 Validator 扩展；默认 **仅警告** |
| Sprint Planning | 与本 Sprint 质量档位一致、依赖与 Agent 合理 | `on_before_sprint`：报告 + 可选阻断（strict / 显式开关） |
| Daily（每任务） | 静态、增量测试、产出物契约 | 现有 `quality_level` + Coder/Tester；可选后续 TaskHooks |
| Sprint Review | 全量/门禁测试、覆盖率、架构、进化测量 | `on_after_sprint` + 测量/知识卡片已有基础 |
| Increment / 部署 | Compose 可起、健康检查、无 root/无密钥入镜像 | Review 包轻量规则 + `sprintcycle product` CLI |

---

## 4. 扩展点设计（少而精）

### P0（首版推荐）

1. **配置**（`sprintcycle.toml` / `RuntimeConfig`）  
   - `governance.enabled`（默认 `false`）  
   - **规则包**：`governance.config_path`（主包）与 **`governance.packs`**（附加包列表，顺序合并）；实现上合并 `planning` / `review` / `task_after` 与 `gates.*` 中的列表型段落，后者覆盖前者同 id 时以**后出现**为准。  
   - `governance.block_on`：`none` | `review_only` | `planning_and_review`（示例，实现时可收敛枚举）  
   - **SDD / Planning 扩展**（可选）：`spec_marker`（在 `spec_glob` 匹配文件中扫描该前缀）、`acceptance_glob`（如 `**/acceptance.yaml` 存在性与轻量形状）、`planning_validate_release_plan`（默认 true：Planning 门在拿到内存中的 `ReleasePlan` 时跑 `ReleasePlanValidator` + backlog 条目的 `spec_ref` 文件存在性）。  
   - **Review / Compose**：`compose_supply_chain`（默认 false：对 `:latest` / `latest` 镜像与 `build` 缺 Dockerfile 等给出 warning 级提示）。  
   - **测量与 CI 切片**：`[execution] incremental_test_command`、`[governance] ci_matrix_tags`（逗号分隔标签字符串）写入 Sprint 后 `run_metadata`，并参与 `measurement_context_hash` 绑定（便于矩阵 job 对齐回溯）。

2. **钩子**  
   - `GovernanceSprintHooks`：实现 `SprintLifecycleHooks`，内部调用 `GovernanceRunner`。  
   - 在编排组装 `ChainedSprintHooks` 时**按需**追加；与 `KnowledgeInjectionHook` 等顺序文档化（建议：知识注入 → 治理 Planning → … → 治理 Review）。

3. **规则形态（两种即可）**  
   - **声明式**：YAML（字段存在、glob、命令退出码阈值）。  
   - **命令式**：`python -m team_governance_plugin` 子进程，便于团队隔离维护。

### P1（按需）

4. **`TaskLifecycleHooks`（可选）**  
   - 在任务完成路径 `await`；默认 `NoOp`，避免全员支付 async 成本。

### 刻意不做（首期）

- OPA/Rego、大型自研规则 DSL、L3 AI 自动修复与核心强绑定。

---

## 5. SDD（规范驱动）与分阶段验证

- **约定目录**：如 `docs/specs/<feature-id>.md`，可选机器可读片段（YAML front matter 或并列 `acceptance.yaml`）。
- **Planning（已实现 v1）**：`spec_glob` 无匹配仍为 warning；若配置 **`governance_spec_marker`**，则在 glob 匹配文件内扫描该标记子串；若配置 **`governance_acceptance_glob`**，则检查匹配路径下 YAML 顶层为 mapping 且含 `criteria` 列表（或等价轻量形状）。编排器将当前 **`ReleasePlan`** 注入 Planning 门上下文；当 **`governance_planning_validate_release_plan`** 为 true 时，调用 **`ReleasePlanValidator`**，并对 backlog 项可选字段 **`spec_ref`**（相对项目根的文件路径）做存在性检查（缺失为 violation）。任务 YAML 中可写 **`spec_ref:`** 以落盘到模型（见 `release_plan` 解析器）。
- **Daily**：静态分析 + 变更相关 pytest 子集（`[execution] incremental_test_command` 供测量元数据记录；实际增量跑测仍由 `quality_level` / Coder-Tester 闭环主导）。
- **Review**：L2/L3 下已有 pytest/覆盖率/import-linter 语义；治理层聚合报告并决定是否阻断。

与 `quality_profile`（`off` / `fast` / `default` / `strict`）组合：**fast** 少跑全量；**strict** 收紧 Planning + Review。

---

## 6. ADR 与自动化合规

- **目录约定**：`docs/adr/NNNN-title.md`（或团队统一路径）。
- **自动化**：Review 包内轻量规则 —— ADR 索引与文件一致、编号单调、必填字段（Status/Date）等；**不**替代人工架构评审。
- **与 G4 对齐**：ADR 中引用 `import-linter` 所表达的模块边界，避免「文档写一套、仓库另一套」。

---

## 7. Guardrails

| 类型 | 做法 | 接入 |
|------|------|------|
| 输入 | Release Plan / Intent 的 Schema；敏感信息脱敏 | Validator / intent parser |
| 生成中 | Prompt 注入规范与架构摘要 | 已有 Coder 架构段；可扩展 spec 摘要 |
| 输出 | 关键 JSON schema、diff/文件清单上限 | 反馈环与报告 |
| 安全 | Semgrep、pip-audit 等 **optional** | Review 或 CI；默认关闭 |

---

## 8. 回归与模型升级

1. **确定性基线（推荐必做）**  
   - `tests/golden/` 或固定标记的 pytest 子集；同一 commit 对不同模型各跑一轮，对比：失败集合、覆盖率、耗时；产出 `artifacts/model_ab_report.json`（路径可配置）。

2. **LLM-as-judge（可选）**  
   - 仅用于无唯一真值的产出；**默认不作为硬门禁**，控制成本与漂移。

与 `evolution/measurement` 衔接：记录模型名、prompt hash，便于自进化回溯。

---

## 9. 可复用开源与工程实践

| 领域 | 工具 |
|------|------|
| 静态 / 风格 | Ruff、Mypy |
| 模块边界 | import-linter（已用） |
| 安全 SAST | Semgrep（可选） |
| 依赖漏洞 | pip-audit / uv audit |
| HTTP 契约 | schemathesis 等（有 API 产品时） |
| 容器 | Docker、Docker Compose |
| CI | GitHub Actions 调用 `sprintcycle` + compose |

---

## 10. 质量守护模块形态（建议）

- **包路径建议**：`sprintcycle/governance/`（或可选 extra `sprintcycle[governance]`，视依赖体积而定）。
- **职责**：`GovernanceFacade` 作为治理域统一入口，路由到 `observability` / `runner` / `arch_guard` / `hitl` 等子能力；`GovernanceRunner` 保持门禁编排与报告聚合职责。
- **约束**：不违反现有 `import-linter` 合约（如 api/orchestration/execution 不依赖 dashboard）。

---

## 11. Docker 一键部署与启动 Product

**用户产品仓库约定**（文档化即可，模板可后续提供）：

- 根目录：`Dockerfile`（多阶段）、`docker-compose.yml`（`app` + 可选依赖；`healthcheck`）。

**SprintCycle CLI（规划）**：

- `sprintcycle product docker-build` —— `docker compose build`  
- `sprintcycle product up` —— `docker compose up -d`  
- `sprintcycle product down` / `logs`  
- 默认工作目录：`ReleasePlan.project.path`；支持 `--compose-file`、`--project-directory`。

**治理**：Review 包可对 Compose/Dockerfile 做轻量检查（compose 存在、非 root、明显密钥模式等），复杂 Dockerfile AST 非首期目标。

---

## 12. 扩展点与使用者成本权衡

| 策略 | 说明 |
|------|------|
| 默认 `governance.enabled=false` | 零配置与当前行为一致 |
| 文档只强调三个旋钮 | `quality_profile`、`governance.enabled`、规则目录 |
| 阻断默认集中在 Review | 降低「规划阶段被卡死」的挫败感；strict 再放开 |
| TaskHooks 为 P1 | 强监管团队再开 |

---

## 13. 演进路线（摘要）

- **阶段 A（已实现）**：`GovernanceFacade` 作为总入口，内部路由到 `observability` / `runner`；`GovernanceRunner` + `GovernanceReport`；`GovernanceSprintHooks`（Planning + Review）；CLI `sprintcycle governance check` 与等价别名 **`sprintcycle validate`**（**写盘** `governance_planning_last.json` / `governance_last.json`，并轮转 **`governance_history/`**；可选 **`cli_emit_events`** 派发 `GOVERNANCE_GATE`）；`sprintcycle.toml` `[governance]` 与 `RuntimeConfig` 字段（含 **`history_max_files`**、**`argv_entry_points`**、**`pluggy_argv`**）；Review 包聚合静态分析、可选 import-linter、可选 ADR/Compose 轻量检查；**v4.0**：argv 条目 **`enabled`**、**`tags`**（`browser` / `visual`）与总开关 **`review_browser_e2e`** / **`review_visual`**；Dashboard **`GET /api/governance/latest`**、**`GET /api/governance/history`**、**`POST /api/governance/check`**（与 CLI 同路径；ASGI 下经线程调度避免嵌套事件循环）及 **「治理 / 多源验证」** 页。  
- **阶段 B（已实现）**：`sprintcycle product`（`docker-build` / `up` / `down` / `logs`）。  
- **阶段 C（已完成相对 v7「二、可落地仍有空间」一揽子）**：`sprintcycle governance model-compare`（含 ``--quick`` → 默认 ``-m golden``）、golden 约定文档 ``docs/GOVERNANCE_GOLDEN.md``、``pytest`` marker ``golden``；``TaskLifecycleHooks`` + **G-3～G-5**（``task_after``、事件、可选阻断）；**F-3 v4**：`run_metadata` 含 Sprint/任务绑定 ``task_outcome_digest``、``measurement_context_hash``，以及 **稳定 prompt 模板全文摘要**（``sprintcycle.prompt_sources`` 含 Coder / Analyzer / Architect / Tester / RegressionTester 等登记模板 → ``prompt_source_digests`` / ``prompt_sources_aggregate_sha256``）；**F-3 v5**：``test_command_incremental``、``ci_matrix_tags`` / ``ci_matrix_tags_joined`` 写入 ``run_metadata`` 并参与哈希绑定；Dashboard **governance_gate** 事件展示 Planning/Review 摘要与 ``compose:*`` 规则命中；**E-3 v1**：Compose YAML 逐服务 ``restart``/``healthcheck`` 提示；**E-3 v2**：可选 **compose 供应链轻量提示**（``:latest``、缺 Dockerfile）；**多包合并**（``config_path`` + ``packs``）；**SDD Planning**（``spec_marker``、``acceptance_glob``、内存 ``ReleasePlan`` + Validator + ``spec_ref``）。  
- **仍待办（远期）**：OPA/Rego、更重的供应链扫描、L3 AI 自动修复与核心强绑定等（见 §4「刻意不做」与 v7 愿景）。

### 13.1 配置示例（`sprintcycle.toml`）

```toml
[governance]
enabled = true
config_path = ".sprintcycle/governance.yaml"
block_on = "review_only"   # none | review_only | planning_and_review
# 保守观察：true 时 Planning/Review 聚合结果中 severity=error 降为 warning（默认 true，见 RuntimeConfig）
# downgrade_errors_to_warnings = true
spec_glob = "docs/specs/*.md"
# packs = [".sprintcycle/governance-team.yaml"]   # 顺序合并进主 config_path（若有）
# spec_marker = "SPEC>"                           # 在 spec_glob 匹配文件中要求出现该前缀
# acceptance_glob = "**/acceptance.yaml"         # 存在性 + 轻量 YAML 形状检查
# planning_validate_release_plan = true         # Planning 门内跑 ReleasePlanValidator + spec_ref 文件检查
# compose_supply_chain = false                  # Review：:latest 与 build.context Dockerfile 提示
# ci_matrix_tags = "py311,linux"                # 写入 run_metadata，供 CI 矩阵与测量对齐
run_static = true
run_import_linter = true
check_adr = false
# D-2 v1：非空时 README 索引的 ADR basename 须与下列 glob（相对项目根）匹配的 *.md 集合完全一致
# adr_glob = "docs/adr/*.md"
check_compose = false
report_dir = ".sprintcycle"
task_hooks = false          # 任务级治理钩子（需 enabled=true）
# G v3：task_after 子进程失败时是否将已成功任务标为 failed（可被 YAML 单条 block_on_failure 覆盖）
# task_after_block_on_failure = false
# ── v4.0 可选：浏览器 / 视觉类 argv（需条目 ``tags: [browser]`` / ``[visual]``）总开关，默认 false
# review_browser_e2e = false
# review_visual = false
# ``governance check`` 成功后向执行事件后端派发 GOVERNANCE_GATE（默认 false）
# cli_emit_events = false
```

### 13.1.1 argv 条目扩展（v4.0 多源）

与 `planning` / `review` / `task_after` 共用子进程字段，另支持：

| 字段 | 说明 |
|------|------|
| **`enabled`** | 为 **`false`** 时跳过该条（缺省视为开启）。 |
| **`tags`** | 字符串列表，大小写不敏感。含 **`browser`** 时，仅当 **`[governance] review_browser_e2e = true`** 执行；含 **`visual`** 时，仅当 **`review_visual = true`** 执行。无 `tags` 的条目不受上述总开关影响。 |

Playwright / 视觉接法、CI 与本地策略见 **`docs/GOVERNANCE_HEAVY_CHECKS.md`**。示例 pack：`examples/governance/playwright-visual.example.yaml`。

与 Sprint 后测量绑定（可选，写在 **`[execution]`**）：

```toml
[execution]
# incremental_test_command = "pytest -q --lf"   # 写入 run_metadata.test_command_incremental
```

### 13.2 治理 YAML：`task_after`（任务级 / Daily v1）

与 `planning` / `review` 相同字段：`id`、`argv`、`cwd`、`expect_code`、`timeout_sec`、`severity`；亦支持 §13.1.1 的 **`enabled`**、**`tags`**（`task_after` 同样经总开关过滤）。另支持 **`run_when`**、**`block_on_failure`**（单条覆盖 TOML 默认）。**`run_when`**：`success`（默认）、`failure`、`always`。需 `sprintcycle.toml` 中 **`governance.enabled`** 与 **`task_hooks`** 均为 true，且 **`config_path`** 指向含下列片段的 YAML：

```yaml
version: 1
task_after:
  - id: daily-echo
    argv: ["python", "-c", "print('ok')"]
    expect_code: 0
    run_when: success
```

子进程会附带环境变量：`SPRINTCYCLE_TASK_AGENT`、`SPRINTCYCLE_TASK_TARGET`、`SPRINTCYCLE_TASK_DESCRIPTION`、`SPRINTCYCLE_SPRINT_NAME`、`SPRINTCYCLE_TASK_STATUS`。检查失败时按 `severity` 写日志。若 **`task_after_block_on_failure`** 或该条 **`block_on_failure: true`**，且任务本体已成功，则 **G v3**：``SprintExecutor`` 将该任务标为 **failed**（``error`` 含 ``task_after`` 摘要）。编排器注入与 ``SprintExecutor`` 相同的 ``EventBus`` 时，每条检查结束后发送 **`governance_task_check`**（`status`=`passed`/`failed`，`check_id`、`governance_rule_id`、`message`）。Planning/Review 门结束后另发 **`governance_gate`**（门名、违规计数、``compose_rule_ids`` / ``compose_hits`` 等），供 Dashboard 与外部订阅消费。

### 13.3 安全说明（H-2）

治理 YAML 中的 `argv`（含 `planning` / `review` / `task_after`）由子进程执行：**勿**将不可信内容拼入命令；`cwd` 必须落在项目根下（实现已校验）。日志与报告对 stdout/stderr 做截断，避免巨输出撑爆磁盘。生产环境请结合 CI 与最小权限运行 `docker compose`。

---

## 14. 可执行 Issue 列表

以下条目可直接迁移为 GitHub / GitLab Issue；**建议标签**：`governance`、`quality`、`docs`、`cli`。  
**状态说明**：下表「状态」列标注仓库当前实现进度（2026-05）。

### Epic A — 治理内核与报告

| ID | 标题 | 验收标准（摘要） | 状态 |
|----|------|------------------|------|
| A-1 | 新增 `sprintcycle.governance` 包骨架与 `GovernanceReport` 数据模型 | 含 `violations[]`、`gate`、`to_dict()`、`should_block_ci`；单元测试 | **已完成** |
| A-2 | 实现 `GovernanceRunner` 最小闭环 | YAML `argv` + 超时；截断 stderr | **已完成** |
| A-3 | Review 包：聚合静态分析 | 复用 `StaticAnalyzer` | **已完成** |
| A-4 | Review 包：import-linter 可选 | `lint-imports` 检测；缺失为 warning | **已完成** |
| A-5 | 配置项 | `RuntimeConfig` + `flatten_sprintcycle_toml`；`governance_block_on` 校验 | **已完成** |

### Epic B — 钩子集成

| ID | 标题 | 验收标准（摘要） | 状态 |
|----|------|------------------|------|
| B-1 | `GovernanceSprintHooks` | Planning + Review；异常吞掉并打日志 | **已完成** |
| B-2 | 编排注册链式钩子 | `SprintOrchestrator._build_sprint_hooks` | **已完成** |
| B-3 | Planning 包 v0 | `checks_planned` + `spec_glob` + YAML planning | **已完成** |
| B-4 | Planning：内存 `ReleasePlan` + Validator + `spec_ref` | `SprintOrchestrator` 注入上下文；`governance_planning_validate_release_plan`；`sdd_checks` | **已完成** |
| B-5 | 多规则包合并 | `config_path` + `packs[]` → `yaml_merge.load_merged_governance_data` | **已完成** |

### Epic C — CLI 与本地可执行

| ID | 标题 | 验收标准（摘要） | 状态 |
|----|------|------------------|------|
| C-1 | `sprintcycle governance check` | 根级 `-p` 与 `--format json`；子命令 `--gate` review/planning/both | **已完成** |
| C-2 | QUICKSTART 互链 | 指向本文 | **已完成** |

### Epic D — Spec / ADR 轻量门禁

| ID | 标题 | 验收标准（摘要） | 状态 |
|----|------|------------------|------|
| D-1 | Planning：`spec_glob` | 无匹配 → warning | **已完成**（v0） |
| D-2 | ADR 索引一致性 | v0：README vs `docs/adr/*.md`；v1：``adr_glob`` 时 README basename 与 glob 集合双向一致（error） | **已完成** |
| D-3 | SDD：`spec_marker` / `acceptance_glob` | Planning 门内 `sprintcycle.governance.sdd_checks` | **已完成** |
| D-4 | Backlog `spec_ref` | 任务 YAML → `SprintBacklogItem.spec_ref`；Planning 存在性检查 | **已完成** |

### Epic E — Docker / Product

| ID | 标题 | 验收标准（摘要） | 状态 |
|----|------|------------------|------|
| E-1 | `product docker-build` | `docker compose build` | **已完成** |
| E-2 | `up` / `down` / `logs` | 非零退出码 | **已完成** |
| E-3 | Compose 轻量规则 | 全文 healthcheck + YAML 解析后逐服务 ``restart`` / ``healthcheck`` 提示；可选 **供应链提示**（``:latest``、build Dockerfile） | **已完成**（v1 + v2 可选） |

### Epic F — 回归与模型升级

| ID | 标题 | 验收标准（摘要） | 状态 |
|----|------|------------------|------|
| F-1 | golden / marker 文档 | `docs/GOVERNANCE_GOLDEN.md` + `pyproject` markers | **已完成** |
| F-2 | `governance model-compare` | 双跑 pytest + junit；``--quick`` 默认 golden | **已完成** |
| F-3 | measurement 衔接 | `run_metadata`：配置指纹 + LLM 环境 + ``sprint_*`` / ``task_outcome_digest`` / ``measurement_context_hash`` + 稳定 prompt 模板摘要；**增量测命令与 CI 矩阵标签**；知识卡片同步 | **已完成**（v5） |

### Epic G — 可选任务钩子（P1）

| ID | 标题 | 验收标准（摘要） | 状态 |
|----|------|------------------|------|
| G-1 | `TaskLifecycleHooks` 协议 | `execution/hooks/task_hooks.py` | **已完成** |
| G-2 | `SprintExecutor` 挂载 | `governance_task_hooks_enabled` + `GovernanceTaskLifecycleHooks` | **已完成** |
| G-3 | `task_after` 声明式子进程 | 治理 YAML + `run_argv_item` + `SPRINTCYCLE_TASK_*` 环境 | **已完成**（v1：日志；不阻断任务） |
| G-4 | `task_after` → EventBus | `EventType.GOVERNANCE_TASK_CHECK`；Dashboard SSE 订阅 | **已完成**（v2） |
| G-5 | `task_after` 阻断任务 | `task_after_block_on_failure` / `block_on_failure`；context → ``TaskResult`` failed | **已完成**（v3） |

### Epic H — 文档与发布

| ID | 标题 | 验收标准（摘要） | 状态 |
|----|------|------------------|------|
| H-1 | CHANGELOG 条目 | Unreleased 已记 | **已完成** |
| H-2 | 安全说明 | §13.3 | **已完成** |

---

## 15. 附录：与 v7 附件文档的关系

- v7 中的 **4 Gate / RuleEngine / L0–L3 行为矩阵** 作为**长期愿景**保留；本仓库**首期**以 `quality.py` 的 L 档位 + 本设计的 **Gate 检查包** 实现，避免两套 Level 语义并存。
- v7 部署图中的 **Kubernetes** 按产品决策**不采纳**；以 Docker Compose 为主。

---

*本文档随实现迭代更新；Issue 编号仅为规划用，迁移至跟踪系统时可重新编号。*
