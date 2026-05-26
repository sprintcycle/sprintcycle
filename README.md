# SprintCycle

[English](README_EN.md)

**SprintCycle** 是一个自进化的契约驱动敏捷开发平台——把"自然语言需求"变成"可追溯的软件交付"，用 `LifecycleContract` 串起从意图到版本演化的完整闭环。

当前版本：**0.9.2**（与 `sprintcycle.__version__` 一致）

---

## 产品定义

### 一句话定义

SprintCycle 是一个自进化的契约驱动敏捷开发平台——把"自然语言需求"变成"可追溯的软件交付"，用 LifecycleContract 串起从意图到版本演化的完整闭环。

### 产品本质

**SprintCycle 不是：**

- 不是代码生成器（不直接写代码）
- 不是 CI/CD 工具（不做构建部署管道）
- 不是项目管理工具（不做看板和工单）

**SprintCycle 是：**

- **意图→交付的闭环编排器**：输入自然语言意图，输出带证据的版本化交付物
- **契约驱动**：`LifecycleContract` 是全链路唯一事实载体，从需求到代码到测试到上线，一切围绕同一份 contract 运转
- **自进化**：执行→观测→诊断→修复→交付→治理→晋升，形成可追溯、可回放、可晋升的进化循环

### 核心问题与解法

| 问题 | SprintCycle 解法 |
|------|-----------------|
| 意图断裂：需求只存在于对话历史里，AI 不知道上下文，每次从零开始 | `LifecycleContract` 从需求阶段就创建，后续所有环节都围绕同一份 contract |
| 执行断裂：AI 写了代码但没有证据链，不知道改了什么、为什么改、是否正确 | 统一状态机 + evidence 链，每个阶段产出可验证的证据 |
| 演进断裂：没有版本化的知识沉淀，改一次丢一次，无法形成积累 | 版本化演化（versioned evolution），每次晋升写入 version registry |

### 核心概念

#### LifecycleContract（生命周期契约）

全链路唯一事实载体。从意图创建，贯穿所有阶段，最终沉淀为 versioned evolution。

```text
Intent → Contract → Plan → Execute → Observe → Repair → Deliver → Govern → Promote → Evolution
```

#### LifecycleStage（生命周期阶段）

18 个阶段，覆盖从"新需求"到"已晋升"的完整闭环：

```text
NEW → NORMALIZED → PLANNED → PREPARED → DECOMPOSED → EXECUTING
   ↕                                                    ↕
OBSERVING ← VERIFYING ← REPAIRING ← DIAGNOSED         │
   ↓                                                     │
DELIVERING → RUNTIME_LINKED → GOVERNING → PROMOTION_READY → PROMOTED
```

**关键恢复路径**：任一阶段失败 → DIAGNOSED → REPAIRING → VERIFYING → OBSERVING → 继续

#### PromotionPolicy（晋升门禁）

不是所有 contract 都能晋升。必须同时满足：

- 评分 ≥ 70（可配置）
- 运行时健康
- 治理审批通过
- 证据链完整（有 final_snapshot）
- 修复闭环确认

### 产品能力矩阵

| 能力 | 描述 | 技术实现 |
|------|------|----------|
| 意图驱动 | 自然语言 → 结构化 ReleasePlan | IntentParser + ReleasePlanGenerator |
| Sprint 编排 | 按 Scrum 拆分多 Sprint 顺序执行 | SprintOrchestrator + SprintExecutor |
| 多 Agent 协作 | Coder/Tester/Architect/Analyzer/RegressionTester 5类 Agent | AgentStrategy 模式 |
| 断点续跑 | 任意阶段中断后可恢复 | StateStore + checkpoint |
| 自动修复 | 执行失败自动进入 diagnose→repair→verify 循环 | RepairOrchestrationService |
| 治理检查 | 架构契约/静态分析/安全扫描/突变测试 | pluggy 插件系统，7个内置插件 |
| HITL 人工审批 | 关键决策点可请求人工确认 | HitlFacade + Coordinator |
| 版本化演化 | 晋升后写入 version registry，可回滚 | EvolutionRequest + VersionStore |
| 观测与审计 | 实时事件流、trace、replay、健康度 | ObservabilityService + Phoenix 集成 |
| Skills 子系统 | 场景识别→skill 匹配→注入→review | SkillStore + SkillOrchestrator |

### 用户旅程：一个独立开发者的一天

```text
09:00  sprintcycle run "为用户认证模块增加 JWT 刷新令牌"
        → 系统创建 LifecycleContract
        → 意图归一化 → 生成 ReleasePlan（2 个 Sprint）
        
09:02  Sprint 1 开始执行
        → Architect Agent 分析现有代码
        → Coder Agent 实现 JWT 刷新逻辑
        → Tester Agent 生成测试
        
09:15  执行完成 → OBSERVING → 评分 82
        → DELIVERING → RUNTIME_LINKED
        
09:16  治理检查自动运行
        → 架构分层 ✅
        → 静态分析 ✅
        → 安全扫描 ⚠️（发现 1 个潜在问题）
        
09:17  进入 GOVERNING → 人工审批（HITL）
        → 开发者确认安全扫描结果可接受
        
09:18  PROMOTION_READY → PromotionPolicy 评估 → 通过
        → 写入 version registry → v0.3.1
```

### 与同类产品的差异

| 维度 | Cursor/Copilot | CI/CD（GitHub Actions） | 项目管理（Jira/Linear） | SprintCycle |
|------|----------------|------------------------|------------------------|-------------|
| 关注点 | 代码生成 | 构建/部署 | 任务管理 | 意图→交付闭环 |
| 上下文 | 当前对话窗口 | 无 | 无 | LifecycleContract 全链路 |
| 可追溯性 | ❌ 对话消失即丢失 | ✅ 构建日志 | ⚠️ 任务状态 | ✅ 证据链 + version registry |
| 自修复 | ❌ | ❌ | ❌ | ✅ diagnose→repair→verify |
| 治理 | ❌ | ⚠️ Lint | ❌ | ✅ 7层治理 + HITL |
| 版本演化 | ❌ | ✅ Git tag | ❌ | ✅ versioned evolution + 晋升门禁 |

**SprintCycle 填补的空白**：AI 编码和正式交付之间的断层。

### 产品定位

SprintCycle 是 AI 时代的敏捷交付引擎。

它不是让 AI 写代码更快，而是让 AI 写的每一行代码都有来源、有证据、有治理、有版本——从意图到版本演化，形成可进化的软件交付闭环。

### 目标用户

- **一人公司开发者**：用 AI 加速开发，但需要结构化的交付流程而非纯 vibe coding
- **AI 辅助开发团队**：需要治理和审批机制来约束 AI 生成代码的质量
- **自进化系统构建者**：需要 measurement + evolution 循环来持续改进系统

### 商业模式方向

- **开源核心**：SprintCycle 框架本体 MIT 开源
- **增值服务**：Cloud Dashboard / Team Collaboration / Enterprise Governance（未来）
- **生态**：Skills Marketplace / Agent Plugin 生态

### 版本路线图

| 版本 | 里程碑 | 状态 |
|------|--------|------|
| 0.9.x | 架构治理完成，洋葱架构合规 | ✅ 当前 |
| 1.0.0 | OpenHands 集成 + 生产就绪 | ⏳ |
| 1.1.0 | 多项目工作空间支持 | 🔮 |
| 2.0.0 | 自进化闭环验证（measurement → evolution 自动循环） | 🔮 |

---

## 技术架构

### 一句话概括

洋葱架构 + DDD + Port/Adapter，5 层分离（interfaces → composition → application → domain → infrastructure），4 个核心子域（lifecycle / execution / evolution / governance），14 个端口抽象，469+ 个 Python 文件。

### 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    interfaces/http/                        │
├─────────────────────────────────────────────────────────────┤
│                     composition/                           │
├─────────────────────────────────────────────────────────────┤
│                     application/                           │
├─────────────────────────────────────────────────────────────┤
│                       domain/                              │
│   ├── generic/                                            │
│   ├── core/                                               │
│   │   └── governance/verification/                        │
│   └── supporting/ (intent/fitness)                        │
├─────────────────────────────────────────────────────────────┤
│                  infrastructure/                           │
└─────────────────────────────────────────────────────────────┘
```

### 核心定位

SprintCycle 不是单一任务执行器，而是一个 **intent-driven closed-loop production platform**。系统围绕同一份 `LifecycleContract` 组织全流程，并用统一状态机与恢复/晋升门禁保证 Dashboard / REST API / Python SDK 发起任务可以稳定闭环。

### 端到端链路

```text
Intent → Normalize → Plan → Prepare → Decompose → Execute → Observe → Diagnose → Repair → Deliver → Link Runtime → Govern → Promote Versioned Evolution
```

### 当前实现的关键原则

- **意图驱动**：从自然语言意图出发，生成可执行计划
- **统一契约**：`LifecycleContract` 作为全链路唯一事实载体
- **统一状态机**：`LifecycleStateMachine` 定义生命周期阶段与迁移规则
- **统一恢复**：任一阶段失败都可进入 `repair → verify → observe` 恢复分支
- **统一快照**：`final_snapshot` 作为一次迭代的最终可交付状态
- **统一晋升**：promotion 只接受证据齐全、final snapshot 合法的 contract
- **统一沉淀**：晋升后的版本写入 version registry，形成 `versioned evolution`
- **闭环生产**：从意图到可用软件的完整闭环

---

## 主要能力

### 1. 意图驱动的开发闭环
- 通过自然语言描述目标
- 生成 Release Plan（YAML / 结构化计划）
- 支持 Sprint 编排、断点续跑与恢复
- 支持标准化生命周期状态迁移
- 入口以 Dashboard、REST API 和 Python SDK 为主，CLI / MCP 不再是主路径
- 计划与执行现在主要通过 `application/services/execution/`、`application/services/lifecycle/`、`domain/core/execution/orchestrator/` 协同完成

### 2. 标准生命周期契约
- `LifecycleStateMachine` 负责阶段迁移规则
- `LifecycleContract` 负责跨服务状态事实载体
- 统一 correlation model 串联 `execution_id`、`task_id`、`suggestion_id`、`runtime_id`、`version_id`、`trace_id`
- `final_snapshot` 聚合执行、观测、治理、修复、交付、运行时与 promotion 证据
- **DDD 聚合根**：`LifecycleRoot` 作为生命周期领域的聚合根，采用不可变设计模式

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
- **DDD 聚合根**：`GovernanceSession`、`RuleSetAggregate` 管理治理会话与规则集
- **验证引擎**：已整合到 governance 子域，支持多种验证提供者

### 5. 观测、审计与运行时
- 执行事件、trace、replay、摘要与健康状态读模型
- Observability trace 会写入审计信息（audit payload）
- 运行时注册表与部署联动
- `lifecycle_contract(...)` 与 `evolution_overview(...)` 可以直接查询 final snapshot / active version / promotion guard
- 观测与运行时读取主要由 `application/services/observability/observability_service.py`、`infrastructure/adapters/generic/observability/` 和 `infrastructure/adapters/generic/integrations/phoenix/` 协同提供

### 6. 版本化演化
- promotion 成功后写入 SQLite version registry
- active version 与 final snapshot 互链
- `EvolutionOverviewResult` 同时展示 recent versions、active versions 和 final snapshot versions
- 版本产物持有 final snapshot contract 证据，便于审计与回滚
- **DDD 聚合根**：`EvolutionRequest`、`SandboxSession` 管理版本演化与沙箱会话

### 7. Dashboard 与集成
- Vue 3 + Element Plus Web Dashboard
- FastAPI 后端
- Dashboard、REST API 与 Python SDK 共享同一套核心契约入口
- 结合独立 Evaluator Agent 与 Sprint Contract，将质量判断、评分与交付证据显式化
- HTTP 入口由 `interfaces/http/` 负责适配 public / internal 路由
- Dashboard 基于 `interfaces/http/dashboard/` 和前端工程实现

### 8. Skills 子系统
- 场景识别、skill 匹配、skill 注入、review checklist 增强、复盘清理
- 通过 `SprintOrchestrator` 的 sprint hooks 接入主流程
- skill artifacts 与执行 trace 可持久化
- **DDD 聚合根**：`SprintAggregate`、`ReleasePlanAggregate` 管理执行聚合

---

## DDD 领域驱动设计架构

### 子域划分

SprintCycle 采用 DDD 洋葱架构，领域层按子域划分：

#### 核心子域（Core Domains）- 核心竞争力

| 子域 | 职责定位 | 聚合根 | 值对象 |
|------|---------|--------|--------|
| **lifecycle** | 生命周期契约与状态机 | `LifecycleRoot` | `StageEvidence`, `CorrelationContext`, `LifecycleEvidence`, `FailureInfo`, `RuntimeRef`, `GovernanceRef`, `EvolutionRef` |
| **execution** | 执行引擎与任务编排 | `SprintAggregate`, `ReleasePlanAggregate` | `TaskResult`, `SprintResult` |
| **evolution** | 版本演化与晋升 | `EvolutionRequest`, `SandboxSession` | `VersionArtifact`, `EvolutionEvidence` |
| **governance** | 治理与建议处理（含验证引擎） | `GovernanceSession`, `RuleSetAggregate` | `GovernanceRule`, `RuleEvaluation`, `Finding`, `VerificationFinding`, `VerificationRule`, `VerificationReport` |

#### 支撑子域（Supporting Domains）- 业务支撑

| 子域 | 职责定位 | 主要模块 |
|------|---------|---------|
| **intent** | 意图解析与归一化 | `supporting/intent/` |
| **fitness** | 健康度评估 | `supporting/fitness/` |

#### 通用子域（Generic Domains）- 基础设施抽象

| 子域 | 职责定位 | 主要模块 |
|------|---------|---------|
| **errors** | 错误处理与知识路由 | `generic/errors/` |
| **prompts** | 提示词管理 | `generic/prompts/` |
| **models** | 通用数据模型 | `generic/models/` |
| **platform** | 平台视图 | `generic/platform/` |
| **ports** | 基础设施端口抽象 | `generic/ports/` |
| **interfaces** | 通用接口协议定义 | `generic/interfaces/` |

### 聚合根设计原则

1. **不可变设计**：所有状态修改返回新实例，保证线程安全
2. **值对象**：无身份标识，通过属性值相等判断
3. **事件驱动**：子域间通过 `DomainEvent` 通信，解耦依赖
4. **ID 引用**：跨聚合引用使用 ID 而非直接对象引用，防止循环依赖

### 领域服务

| 服务 | 职责 | 位置 |
|------|------|------|
| `LifecycleStateMachineService` | 状态机转换规则 | `domain/core/lifecycle/services.py` |
| `EventBus` | 事件发布/订阅机制 | `domain/core/events/handlers.py` |

### 事件驱动架构

系统使用事件驱动进行子域间解耦：

| 事件类型 | 来源子域 | 目标子域 |
|----------|----------|----------|
| `SprintCompleted` | execution | governance |
| `GovernanceCompleted` | governance | evolution |
| `EvolutionPromoted` | evolution | lifecycle |

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
- 生产构建尽量使用固定版本依赖，减少"今天能装、明天失效"的风险
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

**DDD 核心组件**：

```python
from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
    LifecycleStateMachineService,
    StageEvidence,
    CorrelationContext,
)

# 创建生命周期聚合根
lifecycle = create_lifecycle(
    execution_id="exec-123",
    task_id="task-456",
    project_path="/workspace",
    intent="优化代码"
)

# 状态转换（不可变，返回新实例）
lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
lifecycle = lifecycle.transition_to(LifecycleStage.PLANNED)
```

---

## 代码结构

```
sprintcycle/
├── api.py                    # 统一 API 入口
├── application/              # 用例编排与服务层（DDD 应用层）
│   ├── services/            # 核心业务服务（按领域组织）
│   │   ├── execution/       # 执行相关服务（phase_workflow, evaluator_agent）
│   │   ├── governance/      # 治理相关服务（governance_orchestration, promotion_policy）
│   │   ├── lifecycle/       # 生命周期相关服务（state_machine, contracts, evolution, delivery）
│   │   ├── evolution/       # 版本演化服务（promotion_service, version_service）
│   │   ├── dashboard/       # 仪表盘视图服务（platform_summary, view_service, workbench）
│   │   ├── observability/   # 可观测性服务（observability_service）
│   │   └── release/         # 发布编排服务（orchestrator）
│   ├── orchestration/       # 编排层（sprint_orchestrator）
│   └── dto/                 # 数据传输对象（results.py）
├── composition/              # 组合根层（依赖注入）
│   ├── http_factory.py      # HTTP 服务依赖注入
│   ├── evolution_factory.py # Evolution Facade 工厂
│   └── orchestration_factory.py # 编排器依赖组装
├── domain/                   # 领域模型（DDD 领域层 - 按子域划分）
│   ├── core/                # 核心子域（核心竞争力）
│   │   ├── lifecycle/       # 生命周期契约与状态机
│   │   │   ├── __init__.py
│   │   │   ├── lifecycle_root.py    # LifecycleRoot 聚合根
│   │   │   ├── services.py          # LifecycleStateMachineService
│   │   │   ├── values.py            # 值对象
│   │   │   └── models.py            # 业务常量
│   │   ├── execution/       # 执行引擎与任务编排（agents, core, hooks, orchestrator, planners）
│   │   │   └── aggregates/          # SprintAggregate, ReleasePlanAggregate
│   │   ├── evolution/       # 版本演化与晋升
│   │   │   └── aggregates/          # EvolutionRequest, SandboxSession
│   │   ├── governance/      # 治理与建议处理（arch_guard, hitl, quality_spec, suggestion, verification）
│   │   │   ├── aggregates/          # GovernanceSession, RuleSetAggregate
│   │   │   └── verification/        # 验证引擎（已从 supporting 移入）
│   │   └── events/          # 领域事件（DomainEvent, EventBus）
│   ├── supporting/          # 支撑子域（业务支撑）
│   │   ├── intent/          # 意图解析与归一化
│   │   └── fitness/         # 健康度评估
│   └── generic/             # 通用子域（基础设施抽象）
│       ├── errors/          # 错误处理与知识路由
│       ├── prompts/         # 提示词管理与模板
│       ├── models/          # 通用数据模型（release_plan, sprint_models, constraint_spec 等）
│       ├── platform/        # 平台视图与总览
│       ├── interfaces/      # 通用接口协议定义（diagnostics, validators 等）
│       └── ports/           # 基础设施端口抽象（config, registry, deploy, orchestration 等）
├── infrastructure/          # 适配器层（DDD 基础设施层 - 按子域组织）
│   ├── shared/              # 共享基础设施（persistence）
│   └── adapters/            # 子域适配器实现（实现 domain 端口）
│       ├── core/           # 核心子域适配器
│       │   ├── execution/  # 执行引擎适配器（state_store, event_backend）
│       │   ├── evolution/  # 版本演化适配器（version_store, rollback_store）
│       │   ├── governance/ # 治理适配器（hitl_store, suggestion_store, arch_guard）
│       │   └── orchestration/ # 编排适配器（GraphCompiler, RuntimeConfig 等）
│       └── generic/        # 通用子域适配器
│           ├── config/      # 配置实现（runtime_config, sprintcycle_config）
│           ├── cache/       # 缓存实现（redis_backend, disk_backend）
│           ├── deploy/      # 部署实现（compose_manager, runtime_registry）
│           └── integrations/ # 第三方集成（langgraph, phoenix, autogpt）
└── interfaces/              # HTTP 接口层（DDD 接口适配器层）
    └── http/                # HTTP 适配层
        ├── app.py           # FastAPI 应用工厂
        ├── request_context.py # 请求上下文
        ├── middleware/      # 中间件（rate_limit, audit）
        ├── dashboard/       # Dashboard 专用 HTTP 路由（按领域划分）
        │   ├── execution/   # 执行领域路由（trace, detail, replay）
        │   ├── governance/  # 治理领域路由（check, history, latest）
        │   ├── lifecycle/   # 生命周期领域路由（contract, delivery）
        │   ├── hitl/        # HITL 领域路由（pending, history, decision）
        │   └── suggestions/ # 建议领域路由（approve, reject, promoted）
        └── public/          # 公共 API 端点（外部集成）
            ├── execution.py # Plan、run、status、rollback、stop 端点
            └── health.py    # 健康检查端点
```

### 架构分层说明

| 层级 | 职责 | 关键约束 |
|------|------|----------|
| **interfaces** | HTTP 接口、请求路由 | 仅转发，无业务逻辑 |
| **composition** | 组合根、依赖注入 | 纯组装逻辑 |
| **application** | 用例编排、服务协调 | 依赖 domain，无基础设施依赖 |
| **domain** | 领域模型、业务规则、端口定义 | 无外部依赖 |
| **infrastructure** | 适配器实现、基础设施 | 实现 domain 端口 |

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

### 验证提供者

| 提供者 | 功能 | 位置 |
|--------|------|------|
| `ArchProvider` | 架构检查（import-linter, ruff, grimp） | `domain/core/governance/verification/providers/` |
| `CliProvider` | CLI 命令验证 | `domain/core/governance/verification/providers/` |
| `PlaywrightProvider` | Playwright 端到端测试 | `domain/core/governance/verification/providers/` |
| `PytestProvider` | pytest 单元测试 | `domain/core/governance/verification/providers/` |
| `SecurityProvider` | 安全扫描（gitleaks） | `domain/core/governance/verification/providers/` |
| `VisualProvider` | 视觉验证 | `domain/core/governance/verification/providers/` |

---

## 文档

- `docs/SYSTEM_OVERVIEW.md` — 系统总览与目标成熟架构
- `docs/RELEASE_CHECKLIST.md` — 发布检查清单
- `docs/GOVERNANCE_HEAVY_CHECKS.md` — 重量级治理检查说明
- `docs/ARCHITECTURE_INVARIANTS.md` — 架构不变性文档（包含 DDD 聚合根设计）

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