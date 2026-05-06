## [Unreleased]

### Changed defaults（普通产品迭代）
- **`RuntimeConfig` 默认**：`quality_level` **L1 → L2**（启用 pytest 与覆盖率门禁，利于自动化测试与回归）；`storage_backend` **json → sqlite**（执行状态与知识卡片默认同库，路径默认 `.sprintcycle/data/sprintcycle.db`，见 `state_store.resolve_sqlite_database_path`）。`normalize_quality_level` 对空/非法输入的回退档位同步为 **L2**。
- **`sprintcycle.toml` / `sprintcycle.toml.example`**：与上述默认对齐；示例增加产品迭代说明与可选 `[governance]`。
- **`release_plan/templates/normal_task.yaml`**：补充 Python + Vue 3、SQLite/自闭环依赖、自动化测试与部署相关的目标与约束说明。
- **治理示例**：`release_plan/templates/governance_product_iteration.example.yaml`（可复制为 `.sprintcycle/governance.yaml`）。

### Breaking / 命名收敛
- **移除 ``prd_*`` 执行态兼容**：断点、状态 JSON、反馈文件、metadata 与上下文字段 **仅** 识别 **`release_plan_yaml` / `release_plan_id` / `release_plan_name`**；不再读取或折叠历史键 **`prd_yaml` / `prd_id` / `prd_name`**。**`init_db`** 不再将 SQLite **`executions.prd_name`** 列重命名为 **`release_plan_name`**；若库表仍为旧列名，请自行迁移后再使用当前 ORM。
- **`IntentResult`**：字段 **`prd` → `release_plan`**；**`IntentHandler.validate_prd` → `validate_release_plan`**；**`execute(release_plan=…)`**（原 `prd` 参数名）。**`RunnerHandler`** 不再自建无配置的 ``SprintOrchestrator``，默认构造内建 **`SprintCycle(project_path, config)`** 并委托 **`SprintCycle._run_resolved_plan`**（与 **`run()`** 共用知识门与 **`parallel_tasks`**）；可选 **`RunnerHandler(api=existing_sprint_cycle)`** 注入同一 API 实例。**`RunnerHandler.parse_prd_file`** 重命名为 **`parse_release_plan_file`**。
- **根包 `from sprintcycle import …`**：不再导出 `PRD`、`PRDProject`、`PRDSprint`、`PRDTask`、`PRDParser`、`PRDValidator`。请改用 **`ReleasePlan`、`ProductAnchor`、`SprintDefinition`、`SprintBacklogItem`、`EvolutionParams`、`ExecutionMode`、`ReleasePlanParser`、`ReleasePlanValidator`、`ReleasePlanParseError`**；实现类名未改时可用 **`from sprintcycle.release_plan.models import PRD`**。`sprintcycle.scrum` 仅导出 Scrum 别名（含 `EvolutionParams`），不再导出 `PRD*`。
- **`ManualPRDSource`**：默认扫描目录由项目根下 **`prd/`** 改为 **`release_plan/`**；构造参数由 **`prd_dir`** 改为 **`plan_subdir`**（默认 ``"release_plan"``）。使用进化管道且依赖磁盘 YAML 的项目请将计划文件迁入 **`release_plan/*.yaml`** 或传入自定义子路径。
- 知识注入落盘文件：**`prd_overlay.yaml` → `release_plan_overlay.yaml`**（项目根；`KnowledgeInjector` 常量 `RELEASE_PLAN_OVERLAY_FILENAME`）。
- 知识注入运行时上下文：**`prd_overlay_yaml` → `release_plan_overlay_yaml`**、**`prd_overlay_written` → `release_plan_overlay_written`**；Coder / Cookbook 路径 **`codebase_context["prd_overlay"]` → `["release_plan_overlay"]`**；**`prd_overlay_hint` → `release_plan_overlay_hint`**（`build_cookbook_body` / `run_cursor_cookbook_flow`）。
- 包与模块路径（Scrum 对等工程名）：**`sprintcycle.prd` → `sprintcycle.release_plan`**；**`orchestration/dispatcher.py` → `sprint_orchestrator.py`**；**`evolution/prd_source.py` → `evolution_plan_source.py`**；**`evolution/prd_adapter.py` → `release_plan_adapter.py`**；**`diagnostic/prd_*.py` → `release_plan_*.py`**；**`execution/task_splitter.py` → `work_item_splitter.py`**（`TaskSplitter`/`Task` → **`WorkItemSplitter`** / **`IntentWorkItem`**）；对应测试文件已改名
- 移除 `sprintcycle.scheduler` 包；统一自 **`SprintOrchestrator`**（`from sprintcycle.orchestration.sprint_orchestrator import …` 或 `from sprintcycle import SprintOrchestrator`）
- `SprintCycle.dispatcher` → **`orchestrator`**（`SprintOrchestrator` 实例）
- `TaskResult.task` → **`work_item`**（`PRDTask`）；`TaskResult.to_dict` 与事件负载使用 **`description`**；`create_event(..., description=…)`（不再使用 `task` 参数名）
- `PRDParser`：Sprint Backlog 项 **仅**接受 YAML 键 **`description`**（不再接受 `task` / `name`）
- 移除 **`DeliveryMode`** 与 **`delivery_mode_to_execution_mode`**（`release_plan.models`、`scrum`、根包导出）
- `execution` 包不再导出 **`TaskStatus`**（请使用 `ExecutionStatus`）

### Refactor
- `orchestration/sprint_orchestrator`：内部钩子类 **`_DispatcherSprintHooks` → `_OrchestratorSprintHooks`**（与已移除的 scheduler/dispatcher 脱钩）。
- `execution/sprint_types`：在模块与 **`ExecutionStatus`** docstring 中写明 **对外稳定 status 子集**（CLI/MCP/任务与 Sprint JSON）与 **执行会话轴**、**内部取值**的边界，避免前端分支膨胀。
- `SprintCycle`：断点续跑成功路径与首跑共用 **`_build_run_result`** / **`_serialize_sprint_results`**；**续跑不经知识注入确认门**（与 ``_run_resolved_plan`` 区分）在 **`_resume_execution`** docstring 中写明。
- **Evolution 子域 Scrum 对等命名（无旧名导出）**：仅保留 `EvolutionReleasePlan`、`EvolutionPlanSource`、`EvolutionPlanSourceType`、`EvolutionReleasePlanResult`（字段 `release_plan`）、`evolution_release_plan_to_prd`、`EvolutionPipeline(plan_source=…)`；`EvolutionReleasePlanResult.to_dict()` 使用 `release_plan_name` / `release_plan_version`。边界说明见 `evolution/pipeline.py`、`evolution/evolution_plan_source.py`。

### Features
- **人机卡点（HITL）**：`[hitl]` 配置（`sprintcycle.toml` / `SPRINTCYCLE_HITL_*`）；SQLite 持久化请求（默认 `.sprintcycle/hitl.db`）；编排钩子在 **before_sprint / after_sprint / after_task** 等门阻塞并轮询等待决策；**`approve` / `skip_sprint` / `abort_execution`** 与超时策略 **`timeout_behavior`**；事件 **`hitl_request_open` / `hitl_request_resolved`**；Dashboard 页签 **「人机卡点」**、`GET/POST /api/hitl/*`；CLI **`sprintcycle hitl pending|submit|history`**；MCP **`sprintcycle_hitl_pending` / `sprintcycle_hitl_submit`**；`SprintExecutor` 识别 **`_hitl_sprint_action`** / **`_hitl_abort_execution`** 与 **`context["execution_id"]`**；使用说明见 **`docs/QUICKSTART.md`**
- **统一缓存抽象**：新包 **`sprintcycle.cache`**；**`docs/CACHE.md`** 说明 **`sprintcycle.toml` / `SPRINTCYCLE_CACHE_*` / 代码** 三种切换方式；**`[cache] url`** 与 **`redis_url`** 等价（后者优先）；**`ExecutionCache`** 委托 **`CacheBackend`**；**`configure_execution_cache_from_runtime`** 在 **`SprintCycle`** 初始化时应用；**`CoderAgent`** / **`StaticAnalyzer`** 接入；可选 extra **`cache-redis`**
- **Dashboard**：Vue 3 + Vite 按需组件（`unplugin-vue-components`）、产物分包；CLI **`sprintcycle dashboard --dev`** 同启 Vite；文档 **`docs/RELEASE_CHECKLIST.md`**（发布前 `npm run build`）、**`docs/QUICKSTART.md`** / **`README`** 补充开发与发版说明
- **治理与质量门禁（阶段 A/B/C）**：`sprintcycle.governance`（`GovernanceRunner`、`GovernanceReport`、YAML `argv`、`adr_check` README 索引、`model_compare` 双跑 pytest）；`[governance]` 增加 **`task_hooks`**；`GovernanceTaskLifecycleHooks` + `TaskLifecycleHooks` / `ChainedTaskHooks` 挂入 `SprintExecutor`；CLI **`sprintcycle governance check`** / **`model-compare`** / **`product`**（docker compose）；文档 **`docs/GOVERNANCE_GOLDEN.md`**；`pyproject` 注册 **`golden`** pytest marker；详见 `docs/GOVERNANCE_ENGINEERING.md`
- **治理「开箱即审」保守组合**：`block_on = "none"` 时 `governance check` **不因** Planning/Review 的 error 退出失败，且不阻断 Sprint；**`downgrade_errors_to_warnings`**（`RuntimeConfig.governance_downgrade_errors_to_warnings`，默认 **true**）在 Planning/Review **返回前**将聚合包内 `error` 降为 `warning`（仍落盘/日志/SSE）。**`sprintcycle.toml.example`** 含可复制 `[governance]` 段；本仓库 **`sprintcycle.toml`** 已启用观察模式。
- **Sprint 后测量元数据（F-3 v0）**：`_post_sprint_measurement` 在 `MeasurementResult.details["run_metadata"]` 写入 **`llm_provider` / `llm_model` / `coding_engine` / `quality_level`**；`persist_sprint_outcome_card` 将同名摘要写入知识卡片 **`scores.run_metadata`**
- **治理 D-2 v1（ADR 严格 glob）**：`[governance] adr_glob` → `governance_adr_glob`；`check_adr=true` 且非空时走 `check_adr_readme_strict_glob`（README 与 glob 匹配集一致；缺 README 报 `adr:readme_required`）
- **治理 G-3（任务钩子 `task_after`）**：治理 YAML 顶层 ``task_after`` 列表；每项可设 ``run_when``（success / failure / always）；子进程注入 ``SPRINTCYCLE_TASK_*`` 环境；失败按 severity 打日志（不修改 ``TaskResult``）；``yaml_checks.run_argv_item`` / ``run_argv_checks`` 支持 ``extra_env``；``GovernanceTaskLifecycleHooks(config, project_root, event_bus?)``
- **治理 G-4 / F-3 v1**：``EventType.GOVERNANCE_TASK_CHECK`` + Dashboard SSE；Sprint 后 ``run_metadata`` 增加 ``config_fingerprint``、``dry_run``、``project_path``、可选 ``llm_model_env``（``LLM_MODEL`` 与配置并存时写入）
- **治理 G-5 / F-3 v2 / E-3 v1**：``[governance] task_after_block_on_failure`` + YAML ``block_on_failure`` → 成功后 ``task_after`` 失败将任务标为 **failed**；``run_metadata`` 纳入 ``EVOLUTION_LLM_PROVIDER`` / ``EVOLUTION_LLM_MODEL`` 环境值与指纹；Compose 门禁解析 YAML 后逐服务提示 ``restart`` 与 ``healthcheck``（``compose_hint``）
- **F-3 v3（测量与 Sprint 绑定）**：``run_metadata`` 增加 ``release_plan_name``、``execution_id``、``sprint_index``、``sprint_name``、``task_outcome_digest``（任务 agent/描述摘要/状态）、``measurement_context_hash``（与配置指纹组合；不含全文 prompt）
- **F-3 v4（稳定 prompt 模板摘要 + 治理门事件）**：新增 ``sprintcycle.prompt_sources``（Coder 生成模板、Analyzer Bug LLM 模板；与运行时 ``format_*`` 共用常量）；``run_metadata`` 写入 ``prompt_source_digests`` / ``prompt_sources_aggregate_sha256`` / ``prompt_sources_schema``，并纳入 ``measurement_context_hash`` 绑定；``EventType.GOVERNANCE_GATE`` + ``GovernanceSprintHooks`` 在 Planning/Review 后广播（含 ``compose:*`` 命中列表）；Dashboard 实时事件展示 **GOV GATE** 与 compose 摘要；``docs/QUICKSTART.md`` 增加 ``model-compare --quick`` 示例
- **CLI**：``sprintcycle governance model-compare --quick`` 在未传 pytest 参数时默认 ``-m golden``；``docs/GOVERNANCE_GOLDEN.md`` 同步说明
- **工程卫生**：移除 ``SprintExecutor.execute_sprint_parallel`` 未使用变量；修正若干 docstring 空行尾随空格（W293）
- P1 Scrum：`scrum` 根包导出；CLI/MCP/Dashboard「执行计划」话术；`SprintResult`/`TaskResult` Scrum docstring（`docs/DESIGN_SCRUM_NAMING_MIGRATION.md`）
- V4.0：`require_knowledge_injection_confirm` / `persist_sprint_knowledge_cards`（`[behavior]` + `SPRINTCYCLE_*`）；`KnowledgeInjector.inject_for_sprint(..., persist_overlay=False)` 预览；`RunResult.pending_knowledge_confirmation`；CLI `run --yes`；MCP `confirm_knowledge`
- V4.0：Coder 任务按 `max_verify_fix_rounds` 验证-修复重试；单 Sprint 锁定 `_sprint_coding_engine`；Sprint 结束可选写入 `knowledge_cards`（`sprint_knowledge_card.persist_sprint_outcome_card`）
- docs: `docs/EXTENSION_POINTS.md`（Authlib / Helm / 审计等企业能力接入位，无默认实现）
- config: `quality_profile`（off/fast/default/strict）与 `RuntimeConfig.effective_quality_level()`（V4.0 §6.3）；`sprintcycle.toml` `[quality] profile`
- evolution: `EvolutionPipeline.execute_async` 在有 `RuntimeConfig` 时委托 `SprintOrchestrator`；`evolve_sprint` 供 `SprintExecutor` 进化模式调用（§6.2）
- agents: `EvolutionPath` 枚举（保留 `EvolutionStrategy` 别名，§6.7）
- ci: 校验 `docs-dev/dev-setup.sh` 存在；独立 **`architecture-gate`** job（import-linter）；可选 `mutation.yml` + `semgrep.yml`；`pyproject` `[mutation]`、`dev` 含 **hypothesis**
- g4: `tests/test_g4_properties.py`（Hypothesis）；import-linter 增加 **release_plan** / **execution** 不得依赖 `dashboard`

### Bug Fixes
- `diagnostic`：`ReleasePlanRulePriority` 从 `release_plan_rules` 导出（修复 `release_plan_generator` 误导出导致的导入错误）；`tests/test_diagnostic.py` 同步调整 import

### Documentation
- docs: `docs/GOVERNANCE_GOLDEN.md`（golden / model-compare）；`docs/GOVERNANCE_ENGINEERING.md` 与 QUICKSTART 互链更新
- docs: V4.0 canonical entry `docs/PRODUCT_TECH_V4.md`；README 真理源；`SPRINTCYCLE_PRODUCT_TECH_PLAN.md` 顶栏；`evolution/pipeline`、`orchestration/sprint_orchestrator`、`config/quality` 与 G1–G4 说明

## [v0.9.2] - 2025-12-20

### Features
- feat: integration tests for CLI/MCP/API/Dashboard entry points
- feat: Dashboard frontend enhancement - PRD editor, execution history, diagnostics, live events
- feat: EventBus→SSE real-time execution progress streaming
- feat: MCP SSE transport mode for remote agent access
- feat: end-to-end resume support - reconnect api to SprintExecutor
- feat: P2 - Dashboard (FastAPI + SSE + Web UI)
- feat: P1 - stop/resume/status enhancement
- feat: unified SprintCycle API + refactored CLI & MCP entry points
- feat: Phase 5 - persist sprint results to StateStore + task execution logging
- feat: Phase 4 - differentiated evolution strategies + full task chain in evolution mode
- feat: add RegressionTestAgent for Step 5.5 regression testing
- feat: add ArchitectureAgent for Step 5.1 architecture design
- feat: add MCP Server entry point
- feat: close FeedbackLoop + remove Step7 empty shell
- feat: Phase 15 - evolution report and skill self-iteration
- feat: P0.7 - Config桥接 - 5个小Config新增from_runtime_config工厂方法
- feat: P1+P2 - 补测试、异常体系、pyproject.toml、消灭type:ignore

### Refactors
- refactor: consolidate TextContent type:ignore into helper, restore 21/21 validation
- refactor: Phase 1-4 architecture optimization
- refactor: Phase 1-4 architecture optimization
- refactor: Phase 12 - architecture optimization
- refactor: Phase 11 - code quality
- refactor: P0.6 - Config精简 - LLMProviderConfig合并进LLMConfig, EvolutionConfig→RollbackConfig
- refactor: P0.5 - 移除GEPA/Hermes/Pareto全部残留

### Bug Fixes
- fix: Phase 1 - Fix import errors and test failures

### Tests
- test: Phase 13 - end-to-end integration verification
- test: Phase 10 - improve coverage
- test: Phase 4 - Add tests for agents, bug_models, patterns, and prd_generator modules
- test: Phase 4 - Add integrations and diagnostic tests

### Documentation
- docs: Phase 15 - evolution report and skill self-iteration

### Chores
- chore: Phase 14 - rollback fallback (N/A)

# Changelog

All notable project changes will be documented in this file.

## [v0.6.0] - 2025-04-29

### Architecture Upgrade
- **Plan A**: Evolution becomes Sprint enhancement capability
- `EvolutionEngine.evolve_sprint()`: Evolve Sprint targets
- `SprintExecutor` supports Normal and Evolution modes

### New Features
- `evolve_sprint()`: Multi-generation evolution with target extraction
- `execute_sprints(mode="normal"|"evolution")`: Dual-mode execution
- `set_evolution_engine()`: Inject EvolutionEngine
- `_convert_evolution_result()`: Result format conversion

### Refactoring
- Agent tasks simplified to placeholder implementations
- Code organization improvements

---

## [v0.5.0] - 2025-04-28

### Initial Release
- PRD module: PRDDraft, PRD, PRDSprint, PRDTask
- Intent module: Intent parsing and task routing
- Execution module: Sprint executor with parallel/serial support
- Config module: Multi-provider configuration
- Coding module: Code generation engine
- Evolution module: Self-evolution engine (GEPA)
