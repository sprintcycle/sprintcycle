# SprintCycle 产品与技术完整方案（修订版）

> 本文档基于《3.1 SprintCycle 产品与技术完整方案》深入分析后重写：修正原文档内部矛盾、与代码库不一致之处；调整不合理表述；给出组件选型建议与**现有代码改造方案**。  
> 分析基准代码版本：`sprintcycle` v0.9.2（`pyproject.toml`）、统一入口 `sprintcycle.api.SprintCycle`（plan / run / diagnose / status / rollback / stop）。

**对外唯一真理源（V4.0 工程落地）**：附件（如有道云笔记导出 `.mhtml`）仅作输入材料；与本文或 `main` 实现冲突时，以 **`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`（本文件）** 与 **`docs/PRODUCT_TECH_V4.md`** 为准。新贡献者请先读 **`docs/PRODUCT_TECH_V4.md`** 再读本文件全文。

---

## 〇、相对原 Word 文档的修订摘要

### 〇.1 一致性修正

| 问题 | 原状 | 修订 |
|------|------|------|
| 质量「四级」两套编号 | 表格：L1 架构 → L4 静态；ASCII 图：Level 4 架构 → Level 1 静态，**层级颠倒** | 统一为 **G1–G4 质量门禁**（见 §2.3），自上而下：G1 静态与类型 → G2 测试与覆盖 → G3 适应度与回归 → G4 架构不变量 |
| Sprint 阶段编号 | Phase 4.4 / 4.5 与 Phase 5 / 6 **内容重复**（结果评估、知识沉淀） | 合并为 **六阶段闭环**（§3），每阶段唯一职责 |
| 「7 阶段」与正文 | 架构不变量写「7 阶段流程顺序」，正文 Sprint 图为 **6 个 Phase** | 统一为 **6 Phase**；若未来拆细子步骤，在 Phase 内用 4.x 编号，避免与顶层 Phase 重复 |
| 执行策略命名 | 文档：`SelfEvolutionStrategy` / `ProductEvolutionStrategy` | 与代码对齐：`execution/strategies.py` 中 **`NormalStrategy` / `EvolutionStrategy`**（执行模式）；`agents/evolver.py` 另有 **`EvolutionStrategy` Enum**（进化路径），文档须分栏说明避免混淆 |
| 企业部署与一键脚本 | `curl …/main/dev-setup.sh` 与「已实现」强绑定 | 改为「**以仓库实际路径为准**」；脚本若位于 `docs-dev/` 等，需在 README 与 curl 示例中**同源发布**（见 §5） |
| 与 README 定位 | Word：「全栈开发**平台**」 | 与 README 对齐：**PRD 驱动的自我进化敏捷开发框架**；平台化能力（多租户、网关）为路线图 |

### 〇.2 不合理或易误导表述的调整

- **「100% 数据可控」**：在默认使用云端 LLM 时无法成立。改为：**代码、状态、审计日志可完全自托管；模型推理可选本地模型、VPC 部署或自带 API Key，数据边界在配置与部署模式中明确。**
- **「Spoon + Hypothesis」**：Spoon 为 **Java** 字节码分析与转换框架，与本仓库 **Python** 栈不符，属明显笔误或错配。改为 **pytest + Hypothesis**（属性测试）及/或 **import-linter / tach**（模块边界）等 Python 生态方案。
- **「Nextpy Guardrails」**：修正为业界通用名称 **NeMo Guardrails**、**guardrails-ai** 或 **LLM Guard**（输出/策略/敏感信息防护），并标注为 **P2 企业增强**，非当前核心依赖。
- **「openclaw 插件」**：名称不确定且易与具体商业产品混淆。改为 **「IDE / 助手类 MCP 插件（按实际集成名称填写）」**，或与 **MCP 标准入口**并列描述。
- **支柱二「绑定某一个模型」**：与「多编码引擎」矛盾。改为：**单次 Sprint 内保持同一执行后端以保证行为一致；跨 Sprint 可切换引擎（由 RuntimeConfig / 策略工厂约束）。**

### 〇.3 组件选型：合理性评估与替换建议

| 领域 | 文档或隐含方案 | 当前代码 | 评估与建议 |
|------|----------------|----------|------------|
| LLM 统一接入 | Aider / Claude / Cursor | **LiteLLM**（`llm_provider.py`） | **保持 LiteLLM**：成熟、多厂商、与现有代码一致。Aider/Cursor 宜描述为「**CLI/IDE 侧可选执行后端**」，通过适配器或子进程接入，而非重复造网关。 |
| MCP | MCP Server | **mcp>=1.0** | **保持**，与 CLI/Dashboard 并列作为标准入口。 |
| 本地缓存 | （企业稿）Redis | **diskcache** | 单机与测试 **保持 diskcache**；企业版引入 **Redis** 做跨实例 State/Event，与文档 §5.2 一致。 |
| 静态分析 | Ruff + Mypy | **Ruff** 封装在 `static_analyzer.py` | **保持**；Mypy 可作为可选 dev 门禁（`pyproject` 已含 mypy dev）。 |
| 突变测试 | mutmut | **未集成** | **mutmut** 或 **cosmic-ray** 二选一即可；优先 **mutmut**（Python 常用）作为 CI 可选阶段。 |
| 架构规则 | ArchGuard | **无** | ArchGuard 偏 **JVM/多语言仓库级**；Python 单体可优先 **import-linter**、**tach**、**semgrep** 自定义规则 + 现有 Architect 产出约束；ArchGuard 作为 **单仓多语言或大型企业** 的可选集成。 |
| LLM 输出安全 | 「Nextpy Guardrails」 | **无** | **guardrails-ai** 或 **LLM Guard** 用于 P2；与业务编排解耦，放在 API 层或 MCP 工具返回前。 |
| 编排与工作流 | 文中隐含大工作流 | **TaskDispatcher + SprintExecutor** | 若未来状态机极复杂，可评估 **LangGraph**；当前 **避免过早引入**，以免与 `SprintCycle` API 六方法重复抽象。 |

---

## 一、产品定位与市场机会（修订）

### 1.1 核心定位

**SprintCycle** 是 **PRD / 意图驱动的自我进化敏捷开发框架**：以结构化 PRD 为契约，串联诊断、规划、多 Agent 执行、测量与回滚，形成可重复、可观测的 Sprint 闭环。  
差异化表述：**开源、可自部署、质量门禁可配置、统一 API（plan/run/diagnose/status/rollback/stop）+ CLI / MCP / Dashboard**。  
对标叙事可保留「相对闭源『一键生成』工具，更强调**工程可控性与演进纪律**」，但避免过度承诺「全栈平台」已交付能力；**平台化**（多租户、组织知识库）放在路线图。

### 1.2 市场机会与竞品表（逻辑保留，措辞与事实核对）

竞品对比表结构可保留；补充脚注：**当前开源版本以框架 + 本地/自托管运行为主**，SaaS 为规划。

### 1.3 关键区分（框架自身 vs 客户产品）

| 场景 | 策略 | 质量等级 | 适用对象 |
|------|------|----------|----------|
| SprintCycle 自身演进 | 质量守护优先 | 门禁 **全量默认开启** | 框架维护者 |
| 客户产品开发 (product) | 快速验证与可配置门禁 | Level 0–3 可配置 | 业务应用团队 |

设计哲学（保留）：框架自身可靠优先；用户产品允许档位渐进提升。

---

## 二、核心能力体系（修订）

### 2.1 三大支柱（与代码一致）

1. **意图驱动开发**：`IntentParser` + `IntentPRDGenerator` + `PRDValidator`，自然语言 → 结构化 PRD，多轮由 `plan()` / Dashboard 交互承载。  
2. **多执行后端（非「多模型混绑」）**：**LiteLLM** 作为默认 LLM 网关；可选 **Cursor CLI** 等（`AgentExecutor.use_cursor`）；文档与实现统一表述。  
3. **智能质量保证**：静态分析（Ruff）、测试与测量（`MeasurementProvider`）、错误路由（`error_router`）、回滚（`RollbackManager` / Checkpoint）。

### 2.2 双模式执行体系（命名与代码对齐）

| 模式 | 代码类型 | 目标 | 风险 |
|------|------------|------|------|
| Normal Mode | `ExecutionMode.NORMAL` + `NormalStrategy` | 常规定制功能与修复 | 中 |
| Evolution Mode | `ExecutionMode.EVOLUTION` + `EvolutionStrategy` | 框架或高要求演进 | 高 |

与 `agents/evolver.py` 中的 **`EvolutionStrategy` Enum**（按问题类型选路径）区分：**前者是 PRD 级执行策略，后者是 Agent 侧进化策略**。

### 2.3 质量门禁 G1–G4（替代原 L1–L4 / Level 1–4 混用）

| 门禁 | 含义 | 典型实现/代码锚点 | 建议执行时机 |
|------|------|-------------------|--------------|
| **G1** | 静态与规范 | `static_analyzer`（Ruff）、可选 Mypy | 提交前 / CI |
| **G2** | 测试与覆盖 | `MeasurementProvider`、pytest | 功能合并前 |
| **G3** | 适应度与稳定性 | `measurement` 多维度、`feedback` | Sprint 末或进化轮次 |
| **G4** | 架构不变量 | Architect 产出 + **待增强**的依赖/接口契约检查 | 大变更与进化模式 |

客户产品 **Level 0–3** 映射到 G1–G4 的子集组合（配置表由 `RuntimeConfig` 扩展），框架自身默认 **G1–G4 全开**。

---

## 三、Sprint 闭环工作流程（六阶段，无重复）

```
Phase 1 诊断     → 项目扫描、诊断报告（ProjectDiagnostic）
Phase 2 意图生成 → 意图分类、人工确认（可选）
Phase 3 Sprint 规划 → 任务拆解、验收标准（plan / PRD）
Phase 4 执行与验证 → PRD 执行（TaskDispatcher）、编码、测试、错误路由与有限次重试、回滚
Phase 5 结果评估 → 测量维度、与目标对比、成功失败判定
Phase 6 知识沉淀 → MemoryStore / 报告、供下一轮 plan 使用
```

**原 Phase 4.4–4.5 与 Phase 5–6 重复部分删除**，仅保留上表六阶段。若需细化，在 Phase 4 下使用 **4.1 PRD 生成、4.2 编码、4.3 验证修复** 子编号，**不再**单独占用顶层 Phase 编号。

---

## 四、技术架构设计（与仓库对齐）

### 4.1 三层架构（修订表述）

| 层级 | 职责 | 主要模块 |
|------|------|----------|
| **Layer 1 API** | 统一入口 | `sprintcycle.api.SprintCycle`、`cli`、`mcp/server`、`dashboard/app` |
| **Layer 2 编排与执行** | 调度、状态、事件、回滚 | `scheduler/dispatcher.py`、`execution/sprint_executor.py`、`state_store`、`events`、`rollback` |
| **Layer 3 能力与策略** | Agent、诊断、PRD、进化管道 | `execution/agents/*`、`diagnostic/*`、`prd/*`、`evolution/pipeline.py` |

说明：**EvolutionPipeline** 与 **TaskDispatcher** 在 README 与部分路径中共存；文档与对外叙事应明确 **主执行路径以 `SprintCycle` + `TaskDispatcher` 为准**，`EvolutionPipeline` 为进化/实验管线时可与 Dispatcher **收敛或职责边界写清**（见改造方案 §6.2）。

### 4.2 三条进化主线与不变量（修订）

- **交付效率**：可进化调度与缓存；不变量：**对外六大 API 语义稳定**。  
- **代码质量**：可进化规则与阈值；不变量：**G1–G4 定义不随意删减，仅扩展**。  
- **架构完善**：可变模块实现；不变量：**分层依赖（API → 调度/执行 → 能力）**。

原「7 阶段」改为与 **六 Phase** 一致，或改为「**执行管线内含多子步骤**」而不与 Phase 数字冲突。

---

## 五、部署与生态（事实标注）

### 5.1 一键部署

- 若脚本在仓库 `docs-dev/dev-setup.sh`：**发布物与文档中的 URL 必须一致**（例如 Release 附件或 `raw.githubusercontent.com/.../docs-dev/dev-setup.sh`）。  
- **禁止**文档写「已 universal 支持 curl」而仓库无对应路径或未在 CI 校验。

### 5.2 企业部署（路线图）

PostgreSQL（元数据）、Redis（缓存/队列）、API 网关：**规划项**；当前核心依赖见 `pyproject.toml`（无 PG/Redis **硬依赖**）。

### 5.3 生态扩展

MCP 工具扩展、组织级知识库、审批流：**P2+**。

---

## 六、实施路线图（与优先级对齐）

- **P0**：G4 架构门禁的最小实现（Python 侧 import 边界 + 关键模块契约测试）；测量与回滚与主路径一致；文档与脚本路径一致。  
- **P1**：mutmut/cosmic-ray 择一 CI；Dashboard 与多引擎适配器文档化；import-linter/tach 集成。  
- **P2**：Guardrails 类库、审计持久化到 DB、K8s Helm。

---

## 七、商业模式（略）

开源 MIT 与商业化路线可保留；注意 **「核心 MIT + 企业 Apache 2.0」** 的许可兼容性需在法务上二选一或分模块拆分，避免同一用户混淆。

---

## 八、总结表（保留 Y Build 对比结构）

维度对比表可沿用 Word 第八节；「企业审计」等能力标为 **路线图已实现度** 百分比，避免与当前开源版过度承诺一致。

---

# 现有代码改造方案（详细）

以下按**优先级与依赖顺序**列出，便于排期与验收。

## 6.1 P0：文档与对外一致性（低成本）

1. **README / 本方案 / Word 回写**：统一产品一句、六 API、三入口（CLI/MCP/Dashboard）、双模式命名表。  
2. **部署脚本**：在 README 明确 `dev-setup.sh` 的**唯一 canonical URL**；CI 增加「该 raw 可访问」或「脚本存在性」检查。  
3. **质量章节**：用本文 **G1–G4** 替换原 L1–L4 与 ASCII图矛盾描述。

**验收**：新贡献者仅读 README + 本文件可搭建环境并理解架构。

## 6.2 P0：执行路径单一叙事（中等成本）

**现状**：`EvolutionPipeline.execute()` 与 `TaskDispatcher.execute_prd()` 可能让读者认为有两套「主执行链」。  
**改造**：

- 在 `evolution/pipeline.py` 或 `docs/API.md` 顶部增加 **「主生产路径：`SprintCycle.run` → `TaskDispatcher`」** 说明。  
- 选项 A：`EvolutionPipeline` 内部委托 `TaskDispatcher`（减少重复逻辑）。  
- 选项 B：将 `EvolutionPipeline` 重命名为 `EvolutionExperimentRunner` 等，避免与「唯一管道」语义冲突。  

**验收**：单测覆盖主路径；无两套并行且不文档化的执行语义。（已实现：`EvolutionPipeline.execute_async` 在有 `RuntimeConfig` 时委托 `TaskDispatcher`。）

## 6.3 P1：质量门禁配置模型（中等成本）

**改造**：

- 在 `RuntimeConfig` 增加 `quality_profile: Literal["off","fast","default","strict"]` 或显式 G1–G4 开关。  
- `MeasurementProvider` / `static_analyzer` 读取 profile；客户 product 默认 `fast`，框架 CI `strict`。  

**验收**：`tests/test_p0_runtime.py`（`quality_profile` / `effective_quality_level`）与配置合并单测。

## 6.4 P1：架构不变量最小实现（Python，中高成本）

**目标**：落实 G4，替代文档中不存在的「ArchitectureGuard 类名」与错误「Spoon」栈。

建议实现组合：

1. **import-linter** 或 **tach**：声明 `sprintcycle.api` 不得依赖 `dashboard` 等规则（YAML 配置入仓）。  
2. **pytest + Hypothesis**：对关键纯函数与 PRD 解析做属性测试。  
3. （可选）**semgrep**：安全与危险 API 规则集。

**验收**：CI job **`architecture-gate`**（`lint-imports`）失败则 PR 不可合并；`tests/test_g4_properties.py`（Hypothesis）覆盖质量解析与 PRD `parse_dict` 不变量；可选 Semgrep 工作流见 `.github/workflows/semgrep.yml`。与 Architect Agent 输出互补（Agent 偏软约束，G4 偏硬门禁）。**tach** 与 import-linter 二选一即可，当前以 import-linter 为准；多包边界可后续加 **tach.toml**。

## 6.5 P1：突变测试（低成本接入）

- 增加 optional dev dependency **mutmut**（或 cosmic-ray）。  
- Makefile / `pytest` 后阶段或独立 workflow，**不阻塞**默认 `pytest`（避免本地开发摩擦）。

**验收**：文档说明如何本地运行；CI weekly 或 manual dispatch。（已实现：`.github/workflows/mutation.yml` + `pip install -e ".[mutation]"`。）

## 6.6 P2：企业栈适配层（高成本）

- **StateStore / EventBus** 抽象后端：当前 diskcache → 可选 Redis。  
- **审计日志**：结构化 JSON 行 + 未来 PostgreSQL。  
- **Guardrails**：在 `llm_provider` 返回路径上加薄封装（输入/输出校验策略可插拔）。

**验收**：Docker Compose 示例一键起 Redis + SprintCycle（无 PG 亦可）。

## 6.7 命名债清理（建议与 6.2 同迭代）

- `execution/agents/evolver.py`：Enum 已重命名为 **`EvolutionPath`**（保留 **`EvolutionStrategy`** 别名），与 `strategies.EvolutionStrategy` 类名脱钩。  
- 全局 `grep` 更新引用与导出 `__all__`。

**验收**：mypy + 全量测试通过。

---

## 附录 A：原 Word 中建议直接替换的词条

| 原文 | 建议替换为 |
|------|------------|
| Spoon + Hypothesis | pytest + Hypothesis（+ import-linter / tach） |
| Nextpy Guardrails | NeMo Guardrails / guardrails-ai / LLM Guard（择一并说明场景） |
| SelfEvolutionStrategy / ProductEvolutionStrategy（若指执行层） | NormalStrategy / EvolutionStrategy（并脚注 agents 内 Enum 另名） |
| 100% 数据可控 | 自托管边界 + LLM 调用模式说明 |
| main/dev-setup.sh（若不符） | 仓库实际路径 + Release 策略 |

---

## 附录 B：与 `SprintCycle` 类方法的映射（便于 SDK/文档同步）

| 方法 | 职责 |
|------|------|
| `plan` | 意图 → PRD YAML，校验，不执行 |
| `run` | 执行 PRD，支持 resume |
| `diagnose` | 项目诊断 |
| `status` | 执行状态 |
| `rollback` | 检查点回滚 |
| `stop` | 安全停止 |

---

*文档维护：与版本发布同步更新「已实现 vs 路线图」列；质量门禁编号以本文 G1–G4 为准。*
