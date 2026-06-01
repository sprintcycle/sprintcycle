# SprintCycle

[English](README_EN.md)

**SprintCycle 是一个自进化的契约驱动敏捷开发平台——把"自然语言需求"变成"可追溯的软件交付"，用 LifecycleRoot 串起从意图到版本演化的完整闭环。

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
- **契约驱动**：`LifecycleRoot` 是全链路唯一事实载体，从需求到代码到测试到上线，一切围绕同一份 root 运转
- **自进化**：执行→观测→诊断→修复→交付→治理→晋升，形成可追溯、可回放、可晋升的进化循环

### 核心问题与解法

| 问题 | SprintCycle 解法 |
|------|-----------------|
| 意图断裂：需求只存在于对话历史里，AI 不知道上下文，每次从零开始 | `LifecycleRoot` 从需求阶段就创建，后续所有环节都围绕同一份 root |
| 执行断裂：AI 写了代码但没有证据链，不知道改了什么、为什么改、是否正确 | 统一状态机 + evidence 链，每个阶段产出可验证的证据 |
| 演进断裂：没有版本化的知识沉淀，改一次丢一次，无法形成积累 | 版本化演化（versioned evolution），每次晋升写入 version registry |

### 核心概念

#### LifecycleRoot（生命周期聚合根）

全链路唯一事实载体。从意图创建，贯穿所有阶段，最终沉淀为 versioned evolution。

```text
Intent → Contract → Plan → Execute → Observe → Repair → Deliver → Govern → Promote → Evolution
```

#### LifecycleStage（生命周期阶段）

采用 **Phase-Substage 架构**，覆盖从"新需求"到"已晋升"的完整闭环：

**初始化阶段（INITIALIZING）**：
```text
NEW → NORMALIZED → PLANNED → DECOMPOSED
```

**执行阶段（EXECUTING）**：
```text
RUNNING → OBSERVING → DIAGNOSED → REPAIRING → VERIFYING
```

**交付阶段（DELIVERING）**：
```text
DELIVERING → RUNTIME_LINKED
```

**治理阶段（GOVERNING）**：
```text
GOVERNING → PROMOTION_READY
```

**终止阶段（TERMINAL）**：
```text
PROMOTED, FAILED, ABORTED, CANCELLED
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
| 0.9.x | 六边形架构改造完成，DDD 聚合根设计，Phase-Substage 架构 | ✅ 当前 |
| 1.0.0 | OpenHands 集成 + 生产就绪 | ⏳ |
| 1.1.0 | 多项目工作空间支持 | 🔮 |
| 2.0.0 | 自进化闭环验证（measurement → evolution 自动循环） | 🔮 |

---

## 技术架构

### 一句话概括

六边形架构（Ports & Adapters）+ DDD（领域驱动设计），4 层分离（interfaces → application → domain → infrastructure），4 个核心子域（lifecycle / execution / evolution / governance），17 个端口抽象，469+ 个 Python 文件。

### 架构层次（六边形架构）

```
┌─────────────────────────────────────────────────────────────┐
│                    interfaces/http/                        │ ← 输入端口适配器
│   (dashboard/[execution, governance, lifecycle,           │
│    hitl, suggestions] / public/ / middleware/)            │
├─────────────────────────────────────────────────────────────┤
│                     application/                           │ ← 应用服务层
│   (services/: execution, governance, lifecycle, evolution, │
│    dashboard, observability, release)                     │
│   (composition/: http_factory, evolution_factory,         │
│                  orchestration_factory)                   │
├─────────────────────────────────────────────────────────────┤
│                       domain/                              │ ← 核心业务逻辑
│   (Core: lifecycle, execution, evolution, governance;     │
│    Supporting: intent, fitness;                           │
│    Generic: errors, prompts, models, platform, interfaces)│
│   (ports/: 端口协议定义 - 14个端口)                       │
├─────────────────────────────────────────────────────────────┤
│                  infrastructure/                           │ ← 输出端口适配器
│  (adapters/core/, adapters/generic/)                      │
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
- **统一状态机**：`LifecycleStateMachine` 定义生命周期阶段与迁移规则（Phase-Substage 架构）
- **统一恢复**：任一阶段失败都可进入 `repair → verify → observe` 恢复分支
- **统一快照**：`final_snapshot` 作为一次迭代的最终可交付状态
- **统一晋升**：promotion 只接受证据齐全、final snapshot 合法的 contract
- **统一沉淀**：晋升后的版本写入 version registry，形成 `versioned evolution`
- **闭环生产**：从意图到可用软件的完整闭环
- **端口-适配器模式**：通过 `domain/ports/` 定义接口，`infrastructure/adapters/` 实现

---

## DDD 领域驱动设计架构

### 子域划分

SprintCycle 采用 DDD 六边形架构，领域层按子域划分：

#### 核心子域（Core Domains）- 核心竞争力

| 子域 | 职责定位 | 聚合根 | 值对象 |
|------|---------|--------|--------|
| **lifecycle** | 生命周期契约与状态机（Phase-Substage 架构） | `LifecycleRoot` | `StageEvidence`, `CorrelationContext`, `LifecycleEvidence`, `FailureInfo`, `RuntimeRef`, `GovernanceRef`, `EvolutionRef` |
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
| **interfaces** | 通用接口协议定义 | `generic/interfaces/` |

#### 端口层（Ports）- 外部依赖抽象

所有外部依赖的协议接口定义位于 `domain/ports/`（17个端口）：

| 端口文件 | 协议接口 | 职责 |
|---------|---------|------|
| `state_store.py` | `StateStoreProtocol` | 状态持久化 |
| `llm.py` | `EngineAdapterProtocol` | LLM 引擎调用 |
| `cache.py` | `CacheBackendProtocol` | 缓存服务 |
| `governance.py` | `LinterAdapterProtocol` | 统一的代码检查/架构分析（合并了 ArchGuard, Grimp, ImportLinter, Ruff, TypeCheck） |
| `observability.py` | `ObservabilityFacadeProtocol` | 可观测性集成 |
| `registry.py` | `RuntimeRegistryProtocol` | 运行时注册 |
| `knowledge.py` | `KnowledgeRepositoryProtocol` | 知识管理 |
| `evolution.py` | `EvolutionRegistryProtocol`, `VersionManifestProtocol` | 版本演化 |
| `hitl.py` | `HitlStoreProtocol` | 人类在环 |
| `audit.py` | `AuditPort` | 审计日志 |
| `config.py` | `RuntimeConfigProtocol` | 运行时配置 |
| `deploy.py` | `PlatformLaunchServiceProtocol` | 部署服务 |
| `rate_limit.py` | `RateLimitPort` | 限流服务 |
| `diagnostics.py` | `DiagnosticPort` | 诊断服务 |
| `integrations.py` | `LangGraphRuntimeAdapterProtocol` | 第三方集成（精简了 AutoGPT, Phoenix 等协议） |
| `suggestion.py` | `SuggestionStoreProtocol` | 建议系统 |
| `orchestration.py` | `RuntimeConfigPort`, `TraceRuntimePort` | 执行编排 |

### 聚合根设计原则

1. **不可变设计**：所有状态修改返回新实例，保证线程安全（使用 `@dataclass(frozen=True)`）
2. **Phase-Substage 架构**：`LifecycleRoot` 采用阶段-子阶段分层架构，提供更好的组织结构
3. **值对象**：无身份标识，通过属性值相等判断
4. **事件驱动**：子域间通过 `DomainEvent` 通信，解耦依赖
5. **ID 引用**：跨聚合引用使用 ID 而非直接对象引用，防止循环依赖

### 领域服务

| 服务 | 职责 | 位置 |
|------|------|------|
| `LifecycleStateMachineService` | 状态机转换规则（Phase-Substage 架构） | `domain/core/lifecycle/services.py` |
| `EventBus` | 事件发布/订阅机制 | `domain/core/events/handlers.py` |

### 端口-适配器模式

```python
# 端口定义（domain/ports/）
class StateStoreProtocol(Protocol):
    def save(self, state: ExecutionState) -> None: ...
    def load(self, execution_id: str) -> Optional[ExecutionState]: ...

# 适配器实现（infrastructure/adapters/）
class SqliteStateStore(StateStoreProtocol):
    def save(self, state: ExecutionState) -> None:
        # SQLite 实现
        ...
```

### 组合根模式

```python
# application/composition/http_factory.py
class InfrastructureFactory:
    """基础设施工厂注册器 - 负责注册所有 Domain 层依赖的 Infrastructure 工厂函数"""
    
    def _register_infrastructure_factories(self) -> None:
        # 注册状态存储工厂
        register_state_store_factory(create_state_store)
        # 注册缓存工厂
        register_cache_backend_factory(create_cache_backend)
        # 注册配置工厂
        register_runtime_config_factory(create_runtime_config)
        # ... 更多工厂注册
```

---

## 主要能力

### 1. 意图驱动的开发闭环
- 通过自然语言描述目标
- 生成 Release Plan（YAML / 结构化计划）
- 支持 Sprint 编排、断点续跑与恢复
- 支持标准化生命周期状态迁移（Phase-Substage 架构）
- HTTP 入口由 `interfaces/http/` 负责适配 public / internal 路由

### 2. 标准生命周期契约
- `LifecycleStateMachine` 负责阶段迁移规则（Phase-Substage 架构）
- `LifecycleContract` 负责跨服务状态事实载体
- 统一 correlation model 串联 `execution_id`、`task_id`、`suggestion_id`、`runtime_id`、`version_id`、`trace_id`
- `final_snapshot` 聚合执行、观测、治理、修复、交付、运行时与 promotion 证据
- **DDD 聚合根**：`LifecycleRoot` 作为生命周期领域的聚合根，采用不可变设计模式和 Phase-Substage 架构

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

### 8. Skills 子系统
- 场景识别、skill 匹配、skill 注入、review checklist 增强、复盘清理
- 通过 `SprintOrchestrator` 的 sprint hooks 接入主流程
- skill artifacts 与执行 trace 可持久化
- **DDD 聚合根**：`SprintAggregate`、`ReleasePlanAggregate` 管理执行聚合

---

## 环境要求

- Python **≥ 3.11**

---

## 安装

### 基础安装

```bash
uv sync
```

### 完整安装（推荐）

```bash
uv sync --extra full --extra dev
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

### 环境变量配置

创建 `.env.prod` 配置文件：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./prod.db
# 或使用 PostgreSQL（推荐）
# DATABASE_URL=postgresql://user:password@host:5432/sprintcycle

# 日志配置
LOG_LEVEL=INFO

# 安全配置
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com

# LLM 配置
SPRINTCYCLE_CLAUDE_BIN=/path/to/claude

# 端口配置
PORT=8000
```

### 正式启动命令

生产环境推荐使用 Gunicorn：

```bash
gunicorn sprintcycle.interfaces.http.app:create_app \
    --workers=5 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --bind=0.0.0.0:8000
```

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

**DDD 核心组件**：

```python
from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleStateMachine,
    LifecyclePhase,
    LifecycleSubstage,
    ExecutionStatus,
    create_lifecycle,
    StageEvidence,
    CorrelationContext,
)

# 创建生命周期聚合根（Phase-Substage 架构）
lifecycle = create_lifecycle(
    execution_id="exec-123",
    task_id="task-456",
    project_path="/workspace",
    intent="优化代码"
)

# 统一状态机（通过 context 参数区分执行/生命周期上下文）
machine = LifecycleStateMachine(context="lifecycle")
print(machine.STAGES)

# 执行上下文状态机
exec_machine = LifecycleStateMachine(context="execution")
print(exec_machine.EXECUTION_STATES)
```

---

## 代码结构

```
sprintcycle/
├── __init__.py                 # 模块入口
├── api.py                      # 统一 API 入口
├── application/                # 应用服务层（DDD 应用层）
│   ├── services/               # 核心业务服务（按领域组织）
│   │   ├── execution/          # 执行相关服务（phase_workflow, evaluator_agent）
│   │   ├── governance/         # 治理相关服务（governance_facade, repair_orchestration, suggestion_facade）
│   │   ├── lifecycle/          # 生命周期相关服务（lifecycle_service, delivery_service, hook_service, lifecycle_evolution, promotion_policy_service, recovery_lifecycle_service）
│   │   ├── evolution/          # 版本演化服务（evolution_promotion, evolution_version）
│   │   ├── dashboard/          # 仪表盘视图服务（dashboard_view, management_overview, platform_summary）
│   │   ├── observability/      # 可观测性服务
│   │   └── release/            # 发布编排服务（orchestrator）
│   ├── orchestration/          # 编排层（sprint_orchestrator）
│   ├── dto/                    # 数据传输对象（results）
│   ├── events/                 # 应用层事件
│   └── composition/            # 组合根（依赖注入）
│       ├── http_factory.py     # HTTP 服务依赖注入
│       ├── evolution_factory.py # Evolution Facade 工厂
│       └── orchestration_factory.py # 编排器依赖组装
├── domain/                     # 领域模型（DDD 领域层）
│   ├── core/                   # 核心子域
│   │   ├── lifecycle/          # 生命周期契约与状态机（统一状态机 - Phase-Substage 架构）
│   │   │   ├── lifecycle_root.py    # LifecycleRoot 聚合根（不可变设计）
│   │   │   ├── state_machine.py     # LifecycleStateMachine（统一状态机，context 切换）
│   │   │   ├── services.py          # 领域服务（StateTransition）
│   │   │   ├── values.py            # 值对象（StageEvidence, CorrelationContext, GovernanceRef, EvolutionRef, RuntimeRef, LifecycleEvidence, FailureInfo）
│   │   │   ├── models.py            # 业务常量（证据 schema、阶段序列）
│   │   │   └── requests.py          # 请求数据类（BuildLifecycleRequest, TransitionRequest）
│   │   ├── execution/          # 执行引擎与任务编排
│   │   │   ├── aggregates/          # SprintAggregate, ReleasePlanAggregate（不可变设计）
│   │   │   ├── agents/              # 5类 Agent（coder/tester/architect/analyzer/regression_tester）
│   │   │   ├── hooks/               # 执行钩子（governance_context, hook_context, lifecycle_hooks, quality_hooks, skill_hooks）
│   │   │   ├── orchestrator/        # SprintOrchestrator（策略模式：architect_strategy, coder_strategy, regression_tester_strategy, tester_strategy）
│   │   │   ├── planners/            # 计划生成器（builders, execution_planners, expand, generator, parser, validator, work_item_splitter）
│   │   │   ├── core/                # 核心执行（policies, context, error_handler, events, feedback, hooks, lifecycle_transitions, protocols, run_workspace, sprint_types, state_machine, static_analyzer）
│   │   │   └── skills/              # Skills 子系统（marketplace, models, orchestrator, store）
│   │   ├── evolution/          # 版本演化与晋升
│   │   │   ├── aggregates/          # EvolutionRequest, SandboxSession（不可变设计）
│   │   │   ├── activator.py         # 演化激活器
│   │   │   ├── controller.py        # 演化控制器
│   │   │   ├── facade.py            # 演化门面
│   │   │   ├── rollback_manager.py  # 回滚管理器
│   │   │   └── intent_evolution_loop.py # 意图演化循环
│   │   ├── governance/         # 治理与建议处理
│   │   │   ├── aggregates/          # GovernanceSession, RuleSetAggregate（不可变设计）
│   │   │   ├── arch_guard/          # 架构守卫（architecture_checker, architecture_guard, architecture_layers, cli, compose_hint, config, engine, loader, model, registry, reporter, yaml_checks）
│   │   │   ├── hitl/                # 人类在环（coordinator, decision_normalize, facade, hooks, policy, service, session）
│   │   │   ├── suggestion/          # 建议系统（analyzer, approval, bridge, classifier, facade, reviewer, service）
│   │   │   ├── verification/        # 验证引擎（engine, model, providers）
│   │   │   ├── quality_spec/        # 质量规范（adapters, hooks, providers, rules, spec）
│   │   │   ├── core/                # 治理核心（facade, history, plugin_host, report, runner, yaml_merge）
│   │   │   └── hooks/               # 治理钩子（sprint_hooks, task_hooks）
│   │   └── events/             # 领域事件（common, handlers）
│   ├── supporting/             # 支撑子域
│   │   ├── intent/             # 意图解析
│   │   └── fitness/            # 健康度评估
│   ├── generic/                # 通用子域
│   │   ├── errors/             # 错误处理与知识路由
│   │   ├── prompts/            # 提示词管理
│   │   ├── models/             # 通用数据模型
│   │   ├── platform/           # 平台视图
│   │   └── interfaces/         # 通用接口定义
│   └── ports/                  # 端口定义层（14个端口）
│       ├── __init__.py         # 端口模块入口
│       ├── state_store.py      # StateStoreProtocol, ExecutionState
│       ├── llm.py              # EngineAdapterProtocol, EngineResult, EngineAdapterConfig
│       ├── cache.py            # CacheBackendProtocol
│       ├── governance.py       # LinterAdapterProtocol（统一了 ArchGuard, Grimp, ImportLinter, Ruff, TypeCheck）
│       ├── observability.py    # ObservabilityFacadeProtocol
│       ├── registry.py         # RuntimeRegistryProtocol
│       ├── knowledge.py        # KnowledgeRepositoryProtocol, SprintOutcomeCardAdapter
│       ├── evolution.py        # EvolutionRegistryProtocol, VersionManifestProtocol
│       ├── hitl.py             # HitlStoreProtocol
│       ├── audit.py            # AuditPort, AuditRecord
│       ├── config.py           # RuntimeConfigProtocol
│       ├── deploy.py           # PlatformLaunchServiceProtocol
│       ├── rate_limit.py       # RateLimitPort, RateLimitState
│       ├── diagnostics.py      # DiagnosticPort
│       ├── integrations.py     # LangGraphRuntimeAdapterProtocol（精简了 AutoGPT, Phoenix 等协议）
│       ├── suggestion.py       # SuggestionStoreProtocol
│       └── orchestration.py    # RuntimeConfigPort, TraceRuntimePort
├── infrastructure/             # 适配器层（DDD 基础设施层）
│   ├── shared/                 # 共享基础设施
│   │   └── persistence/        # 持久化（sqlite_store, sync_sqlite_store, session, models）
│   └── adapters/               # 适配器实现
│       ├── core/               # 核心子域适配器
│       │   ├── execution/      # 执行引擎适配器（state_store, checkpoint, cache, sqlite_event_backend）
│       │   ├── evolution/      # 版本演化适配器（version_store, rollback_store, health_check, evolution_registry_access）
│       │   ├── governance/     # 治理适配器（arch_guard, hitl_store, suggestion_store）
│       │   └── orchestration/  # 编排适配器（adapters）
│       └── generic/            # 通用子域适配器
│           ├── config/         # 配置实现（runtime_config, runtime_registry, manager, quality, llm_config, rate_limit）
│           ├── cache/          # 缓存实现（RedisCache, DiskCache, NullCache）
│           ├── integrations/   # 第三方集成（LangGraph, Phoenix, LLM provider）
│           ├── observability/  # 可观测性实现（facade, diagnostics, event_models）
│           ├── deploy/         # 部署实现（platform_launch_service, deployment_spec_service, auto_deployer, compose_manager）
│           ├── knowledge/      # 知识管理（knowledge_repository, knowledge_injector