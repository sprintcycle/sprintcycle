# SprintCycle

[English](README_EN.md)

**SprintCycle** 是一个面向 Dashboard / REST API / Python SDK 的契约驱动生命周期编排平台（a contract-driven lifecycle orchestration platform for Dashboard / REST API / Python SDK）。它以单一 `LifecycleContract` 串联意图归一化、计划、准备、拆解、执行、观测、诊断、修复、交付、运行时联动、治理和版本化演化，最终形成可追溯、可回放、可晋升的 `final snapshot` 与 `versioned evolution`（final snapshot and versioned evolution）。

当前版本：**0.9.2**（与 `sprintcycle.__version__` 一致）

---

## 核心定位

SprintCycle 不是单一任务执行器，而是一个 **contract-driven lifecycle platform**。系统围绕同一份 `LifecycleContract` 组织全流程，并用统一状态机与恢复/晋升门禁保证 Dashboard / REST API / Python SDK 发起任务可以稳定闭环。

它的当前代码结构更接近“薄入口 + 应用编排 + 执行层 + 治理/观测/基础设施”的组合。`SprintCycle` 仍然是统一入口，但主要负责协调、路由和聚合。

### 端到端链路

```text
Web Request → Normalize → Plan → Prepare → Decompose → Execute → Observe → Diagnose → Repair → Deliver → Link Runtime → Govern Suggestions → Promote Versioned Evolution
```

### 当前实现的关键原则

- **统一入口**：Dashboard / REST API / SDK 最终进入同一套 `SprintCycle` 入口
- **统一契约**：`LifecycleContract` 作为全链路唯一事实载体
- **统一状态机**：`LifecycleStateMachine` 定义生命周期阶段与迁移规则
- **统一恢复**：任一阶段失败都可进入 `repair → verify → observe` 恢复分支
- **统一快照**：`final_snapshot` 作为一次迭代的最终可交付状态
- **统一晋升**：promotion 只接受证据齐全、final snapshot 合法的 contract
- **统一沉淀**：晋升后的版本写入 version registry，形成 `versioned evolution`

---

## 主要能力

### 1. 意图驱动的开发闭环
- 通过自然语言描述目标
- 生成 Release Plan（YAML / 结构化计划）
- 支持 Sprint 编排、断点续跑与恢复
- 支持标准化生命周期状态迁移
- 入口以 Dashboard、REST API 和 Python SDK 为主，CLI / MCP 不再是主路径
- 计划与执行现在主要通过 `application/release_plan/`、`application/orchestration/`、`execution/` 和 `application/services/` 协同完成

### 2. 标准生命周期契约
- `LifecycleStateMachine` 负责阶段迁移规则
- `LifecycleContract` 负责跨服务状态事实载体
- 统一 correlation model 串联 `execution_id`、`task_id`、`suggestion_id`、`runtime_id`、`version_id`、`trace_id`
- `final_snapshot` 聚合执行、观测、治理、修复、交付、运行时与 promotion 证据
- 契约构建与汇总主要由 `application/services/lifecycle_contracts.py`、`application/services/lifecycle_contract_assembly_service.py` 等服务完成

### 3. 修复与交付闭环
- 显式支持 `diagnosed → repairing → verifying → observing` 恢复闭环
- 显式支持 `delivering → runtime_linked → governing → promotion_ready → promoted` 晋升链路
- `RepairOrchestrationService` 提供统一 recovery 路由
- `PromotionPolicy` 作为 promotion 门禁，阻止不完整 contract 晋升

### 4. 治理与建议处理
- 多源验证插件系统（基于 pluggy）
- 架构契约检查、静态分析、YAML 校验、ADR 检查、突变测试、依赖安全扫描
- 建议审查、批准、拒绝、归档与 HITL 晋升
- suggestion / governance / promotion 全部围绕同一份 contract 运行

### 5. 观测、审计与运行时
- 执行事件、trace、replay、摘要与健康状态读模型
- Observability trace 会写入审计信息（audit payload）
- 运行时注册表与部署联动
- `lifecycle_contract(...)` 与 `evolution_overview(...)` 可以直接查询 final snapshot / active version / promotion guard
- 观测与运行时读取主要由 `application/services/observability_service.py`、`observability/` 和 `infrastructure/integrations/phoenix/` 协同提供

### 6. 版本化演化
- promotion 成功后写入 SQLite version registry
- active version 与 final snapshot 互链
- `EvolutionOverviewResult` 同时展示 recent versions、active versions 和 final snapshot versions
- 版本产物持有 final snapshot contract 证据，便于审计与回滚
- 版本与演化能力主要由 `application/services/lifecycle_evolution_service.py`、`application/services/evolution_version_service.py` 和 `governance/versioning/` 提供

### 7. Dashboard 与集成
- Vue 3 + Element Plus Web Dashboard
- FastAPI 后端
- Dashboard、REST API 与 Python SDK 共享同一套核心契约入口
- 结合独立 Evaluator Agent 与 Sprint Contract，将质量判断、评分与交付证据显式化
- HTTP 入口由 `interfaces/http/` 负责适配 public / internal 路由
- Dashboard 基于 `interfaces/http/` 和前端工程实现

### 8. Skills 子系统
- 场景识别、skill 匹配、skill 注入、review checklist 增强、复盘清理
- 通过 `SprintOrchestrator` 的 sprint hooks 接入主流程
- skill artifacts 与执行 trace 可持久化
- 这部分逻辑主要分布在 `execution/skills.py`、`execution/hooks/skill_hooks.py`、`execution/skill_store.py` 和 `execution/orchestrator/sprint_orchestrator.py`


---

## 环境要求

- Python **≥ 3.11**

---

## 安装

### 基础安装

```bash
pip install -e .
```

### 完整安装（推荐）

```bash
pip install -e "[full,dev]"
```

### 常用可选能力

| Extra | 用途 |
|------|------|
| `dashboard` / `full` | Web Dashboard（FastAPI + Uvicorn） |
| `cache-redis` | 执行缓存 Redis 后端 |
| `dev` | 测试、类型检查、import-linter 等开发依赖 |
| `mutation` | 突变测试（`mutmut`） |

---

## 快速开始

### 初始化项目数据目录

```bash
sprintcycle init
```

### 生成计划但不执行

```bash
sprintcycle plan "为登录流程增加单元测试" -m auto
```

### 直接执行

```bash
sprintcycle run "修复 README 中的死链"
# 等价于：
sprintcycle "修复 README 中的死链"
```

### 启用治理检查

```bash
sprintcycle run "重构配置模块" --governance-level standard
```

### 启动 Dashboard

```bash
# 生产模式（通常需要先构建前端）
sprintcycle dashboard

# 开发模式（同时启动 FastAPI + Vite）
sprintcycle dashboard --dev
```

### 本地 Docker 部署

如果你希望直接把 SprintCycle 部署到本地机器上的 Docker 中，推荐使用仓库内置的本地编排：

```bash
cp .env.example .env
scripts/deploy.sh local up
```

启动后访问：

```text
http://localhost:3000
```

常用本地命令：

```bash
scripts/check.sh local
scripts/deploy.sh local logs
scripts/deploy.sh local restart
scripts/deploy.sh local down
```

### 提交前密钥扫描

为了防止 `DEEPSEEK_API_KEY` 之类的密钥被误提交到 GitHub，仓库提供了提交前检查脚本与 Git hooks：

```bash
scripts/check-secrets.sh
scripts/install-githooks.sh
```

安装 hooks 后，每次提交都会自动扫描疑似密钥字符串。

---

## 生产部署

### 推荐部署拓扑

- `frontend`：Vue Dashboard + Nginx 静态站点，负责 `/` 和 `/api` 统一入口
- `backend`：FastAPI + SprintCycle 核心服务，负责业务编排、SSE、治理、执行与观测
- `edge proxy`（可选）：外层 Nginx / Traefik，负责 TLS、域名、限流与统一 HTTPS 出口

### 正式启动命令

生产环境推荐：

```bash
cp .env.example .env
# 根据实际域名和路径调整 .env

docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

本地开发环境：

```bash
docker compose -f docker-compose.local.yml --env-file .env up --build
```

### 健康检查说明

- 后端健康检查：`http://backend:8000/health`
- 前端健康检查：`http://localhost:3000/health`
- 对外访问入口：`http://localhost:3000`

建议在外层编排或监控系统里同时检查：
- `backend` 容器是否健康
- `frontend` 容器是否健康
- `/api` 是否可用
- SSE 连接是否可持续

### 升级 / 回滚说明

#### 升级

1. 更新代码或镜像标签
2. 重新构建镜像
3. 滚动重启：

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

#### 回滚

1. 切回上一版镜像 tag
2. 保持 `sprintcycle-data` 卷不变
3. 重新启动编排：

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

4. 如果需要快速回退到旧镜像，直接把 `.env` 里的镜像标签改回旧版本

### 环境变量分层

建议分三层管理：

- **基础层**：`.env.example`，记录默认值和变量说明
- **开发层**：`.env`，本地和联调使用
- **生产层**：部署平台环境变量或密钥系统，不直接提交到仓库

推荐优先级：

1. 平台注入的环境变量
2. `.env`
3. Compose 默认值

### 镜像缓存策略

- 前端：优先缓存 `package-lock.json`，再安装依赖，再复制源码
- 后端：优先缓存 `pyproject.toml`，再安装 Python 依赖，再复制业务代码
- 生产构建尽量使用固定版本依赖，减少“今天能装、明天失效”的风险
- 如果 CI 支持，建议启用 BuildKit cache

### 端口统一规范

建议统一成：

- `3000`：对外 HTTP 入口，前端容器暴露
- `8000`：后端服务内部端口，仅容器网络内访问
- `443`：外层 HTTPS 入口，由 Nginx / Traefik / LB 承载
- `80`：仅用于跳转到 HTTPS

### 外层反向代理与 HTTPS

如果要正式上线，推荐在前面再加一层 edge proxy：

- `/` → `frontend:80`
- `/api/` → `backend:8000`
- TLS 终止在 edge proxy
- HSTS、HTTP/2、证书自动续期都由 edge proxy 负责

这样浏览器只面对一个统一站点地址，例如：

```text
https://sprintcycle.example.com
```

### Nginx / TLS / 统一入口

推荐外层 Nginx 配置思路：

- `location /` 代理到前端静态站点
- `location /api/` 代理到后端 API
- `location /health` 可代理到前端健康页或后端健康页
- `listen 443 ssl http2`
- 配置证书文件与自动续期
- 启用安全头：`Strict-Transport-Security`、`X-Frame-Options`、`X-Content-Type-Options`

如果你要把外层 Nginx 也放进仓库，我可以继续补一个 `deploy/nginx/` 目录和对应的 TLS 模板。

---

## 命令速查

### 核心流程

| 命令 | 说明 |
|------|------|
| `sprintcycle wizard` | 交互式选择 plan / run / diagnose / status |
| `sprintcycle plan <意图>` | 生成执行计划 |
| `sprintcycle run [意图]` | 执行 Sprint |
| `sprintcycle validate` | 运行治理验证 |

### 项目管理

| 命令 | 说明 |
|------|------|
| `sprintcycle diagnose` | 项目健康度分析 |
| `sprintcycle status [execution_id]` | 单条执行状态或历史列表 |
| `sprintcycle rollback <execution_id>` | 回滚执行 |
| `sprintcycle stop <execution_id>` | 停止运行中的任务 |

### 知识管理

| 命令 | 说明 |
|------|------|
| `sprintcycle knowledge search` | 检索知识卡片 |
| `sprintcycle knowledge list` | 列出所有知识卡片 |

### 配置管理

| 命令 | 说明 |
|------|------|
| `sprintcycle config show` | 显示当前配置 |
| `sprintcycle config set <key> <value>` | 设置配置项 |
| `sprintcycle config get <key>` | 获取配置项 |

### 服务与集成

| 命令 | 说明 |
|------|------|
| `sprintcycle dashboard` | 启动 Web UI |
| HTTP API | 通过 `sprintcycle.interfaces.http` 暴露 public / internal 路由 |

### 系统命令

| 命令 | 说明 |
|------|------|
| `sprintcycle init [path]` | 初始化 `.sprintcycle` 目录结构 |
| `sprintcycle import-state` | 将 JSON 状态目录导入 SQLite |

**全局选项**：`-p/--project`（项目路径）、`--format text|json`（输出格式）、`-v/--verbose`（详细日志）

---

## Python API

Python API 与 Dashboard / REST API 共享同一个 `SprintCycle` 入口，`plan`、`run`、`diagnose`、`status`、`rollback`、`stop` 等能力语义一致，方便在脚本、服务和自动化流水线中调用。

---

## 生产部署

如果你要把 SprintCycle 作为长期稳定服务部署，推荐使用前后端分离 + 外层反向代理的方式：

- 前端独立容器：Vue Dashboard + Nginx
- 后端独立容器：FastAPI + SprintCycle 编排与 API
- 外层代理：统一域名、TLS、`/` 和 `/api` 入口
- 持久化卷：保存 `.sprintcycle`、治理产物、执行记录

### 快速启动

```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

### 健康检查

- 后端：`curl http://127.0.0.1:8000/health`
- 前端：`curl http://127.0.0.1:3000/health`
- 页面：`http://localhost:3000`

### 升级

```bash
cd /opt/sprintcycle
git pull
docker compose -f docker-compose.prod.yml --env-file .env build
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

### 回滚

- 回退到上一个稳定镜像标签
- 保留 `.sprintcycle` 卷数据
- 重启 `docker compose -f docker-compose.prod.yml --env-file .env up -d`

更多细节见 `docs/PRODUCTION_DEPLOYMENT_GUIDE.md` 与 `docs/PRODUCTION_NGINX_TLS.md`。

```python
from sprintcycle import SprintCycle

api = SprintCycle(project_path="./my-project")
result = await api.run("重构认证模块")
```

常见导出对象包括：

- `SprintCycle`
- `ReleasePlan`
- `ReleasePlanParser`
- `ReleasePlanValidator`
- `SprintOrchestrator`
- `SprintExecutor`

---

## 代码结构

```
sprintcycle/
├── api.py                    # 统一 API 入口
├── application/              # 用例编排与服务层
├── execution/                # 执行引擎与状态机
├── governance/               # 治理、审计、版本与建议
├── observability/            # 观测、回放与诊断
├── domain/                   # 领域模型、规则与协议
├── infrastructure/           # 适配器、存储、缓存、外部集成
└── interfaces/               # HTTP 接口层（public / internal）
```

---

## 最新代码中的关键服务

### 生命周期中枢

- `sprintcycle/services/lifecycle_state_machine.py`
  - 定义统一阶段：`new → normalized → planned → prepared → decomposed → executing → observing → diagnosed → repairing → verifying → delivering → runtime_linked → governing → promotion_ready → promoted`
  - 提供状态迁移、事件构建与关联信息

- `sprintcycle/services/lifecycle_contracts.py`
  - 定义 `LifecycleContract`
  - 统一承载 execution、task、project、trace、diagnostics、runtime、suggestion、governance、evolution、recovery、validation_refs 等字段
  - 提供 `final_snapshot` / evidence 校验和契约构建

- `sprintcycle/services/phase_workflow.py`
  - 提供 plan / prepare / decompose / observe / diagnose / repair / deliver 阶段性结构化 artifact

### 运行生命周期

- `sprintcycle/services/execution_lifecycle_service.py`
  - 负责执行启动、状态归一、运行时注册、观测事件发射和执行详情读取

- `sprintcycle/orchestration/sprint_orchestrator.py`
  - 负责 Release Plan 扩展、Sprint 编排、任务执行与运行时事件协调

### 恢复、治理与演化

- `sprintcycle/services/repair_orchestration_service.py`
  - 负责统一 recovery 路由，支持 `diagnose → repair → verify → observe` 闭环

- `sprintcycle/services/promotion_policy.py`
  - 负责 promotion 门禁，只允许证据齐全且 stage 正确的 contract 晋升

- `sprintcycle/services/lifecycle_evolution_service.py`
  - 负责 lifecycle contract 构建、promotion 评估、promotion 执行和 version artifact 注册

- `sprintcycle/versioning/sqlite_registry.py`
  - 负责版本注册、active version 指针与 manifest 索引

### 观测、治理与建议

- `sprintcycle/services/observability_service.py`
  - 负责 trace、replay、执行详情与审计信息装配

- `sprintcycle/services/governance_orchestration_service.py`
  - 负责治理检查与治理读流程

- `sprintcycle/services/suggestion_application_service.py`
  - 负责建议的审查、批准、拒绝、归档与 HITL 晋升

### Dashboard / 总览 / 视图

- `sprintcycle/services/platform_summary_service.py`
  - 负责 dashboard/platform-facing summary payloads

- `sprintcycle/results.py`
  - 统一返回值模型
  - 包含 `FinalSnapshotResult`、`FinalSnapshotVersionSummary`、`EvolutionOverviewResult` 等结构化结果

### Skills 子系统

- `sprintcycle/execution/skills.py`
  - 负责场景识别、skill 匹配、skill 注入前准备、review checklist 增强和复盘清理

- `sprintcycle/execution/hooks/skill_hooks.py`
  - 负责把 skill 编排挂接到 sprint 生命周期的 before/after/before_review/after_retro 节点

- `sprintcycle/execution/skill_store.py`
  - 负责 skill artifact、injection state、execution record 和 task trace 的持久化

skills 子系统通过 `SprintOrchestrator._build_sprint_hooks()` 接入主流程，在计划后、执行前、评审前、复盘后参与上下文增强与证据沉淀。它不是旁路执行器，而是主生命周期上的一个执行时能力层。

---

## 治理与验证

### 治理级别

| 级别 | 检查项 | 适用场景 |
|------|--------|----------|
| `minimal` | 仅基础语法检查 | 快速迭代 |
| `standard` | 静态分析 + 架构检查 | 日常开发 |
| `strict` | 全部检查 + 突变测试 | 发布前验证 |

### 内置验证插件

| 插件 | 功能 | 依赖 |
|------|------|------|
| Architecture | 导入分层契约检查 | import-linter |
| StaticAnalysis | ruff + mypy 静态检查 | ruff, mypy |
| YAMLValidation | YAML 文件语法校验 | pyyaml |
| ComposeHint | Docker Compose 文件检查 | PyYAML |
| ADRCheck | 架构决策记录一致性 | - |
| MutmutPlugin | 突变测试（可选） | mutmut |
| PipAuditPlugin | 依赖安全扫描（可选） | pip-audit |

---

## 文档

- `docs/SYSTEM_OVERVIEW.md` — 系统总览与目标成熟架构
- `docs/RELEASE_CHECKLIST.md` — 发布检查清单
- `docs/GOVERNANCE_HEAVY_CHECKS.md` — 重量级治理检查说明

---

## 开发与测试

### 框架开发

```bash
./tools/start_develop/dev-setup.sh
source tools/start_develop/activate.sh
.venv/bin/python -m pytest tests/test_p0_runtime.py -v
.venv/bin/python -m pytest tests/ -v
./tools/start_develop/run-lint.sh
```

### 用 SprintCycle 开发产品

```bash
pip install sprintcycle
# 或：
pip install "sprintcycle[dashboard]"

sprintcycle init
sprintcycle run "为登录模块添加单元测试"
sprintcycle dashboard
```

---

## License

MIT License

---

## 社区与反馈

欢迎提交 Issue 和 Pull Request。

---

**SprintCycle — 让 AI 成为你的敏捷开发伙伴**
