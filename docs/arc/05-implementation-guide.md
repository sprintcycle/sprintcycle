# SprintCycle 重新实现指南（单人开发者版）

> **目标**：为单人开发者提供可实现的重新实现蓝图
> 
> **核心原则**：
> - ✅ 先跑通核心链路，再添加功能
> - ✅ 简化架构，去掉不必要的抽象层
> - ✅ 每个阶段都有可运行的成果
> - ✅ 标注"必须有"vs"可以有"的决策
>
> **组织方式**：核心链路 → 分阶段实现 → 架构简化建议 → 决策评估

---

## 第一部分：核心链路（必须先跑通）

### 1. 最小可行产品定义

**一句话**：输入自然语言需求 → 拆解为 Sprint 计划 → 按顺序执行 → 产出结果

**核心数据流**（仅 4 步）：
```
用户意图 → ReleasePlan → SprintExecutor → TaskResult
```

**MVP 范围**（第 1 周必须完成）：

| 组件 | 状态 | 说明 |
|------|------|------|
| ReleasePlan 模型 | ✅ 必须有 | 多 Sprint 计划定义 |
| SprintExecutor | ✅ 必须有 | 单 Sprint 执行器 |
| Coder Agent | ✅ 必须有 | 代码生成 Agent（先实现 1 个） |
| TaskResult | ✅ 必须有 | 任务执行结果 |
| 状态机 | ⚠️ 简化版 | 仅 5 个状态：pending→running→success/failed |
| 端口层 | ❌ 暂缓 | 直接调用，不定义 Protocol |
| DI 容器 | ❌ 暂缓 | 直接实例化 |

### 2. MVP 核心模型

#### 2.1 ReleasePlan（发布计划）

```python
@dataclass
class ReleasePlan:
    project_name: str
    project_path: str
    mode: str  # "normal" | "evolution"
    sprints: List[SprintDefinition]

@dataclass  
class SprintDefinition:
    name: str
    goals: List[str]
    tasks: List[SprintBacklogItem]

@dataclass
class SprintBacklogItem:
    description: str
    agent: str  # "coder" | "tester" | "architect"
    target: Optional[str] = None
```

#### 2.2 执行结果

```python
@dataclass(frozen=True)
class TaskResult:
    task_id: str
    agent: str
    status: str  # "success" | "failed"
    output: str
    error: Optional[str] = None
    duration: float = 0.0

@dataclass(frozen=True)
class SprintResult:
    sprint_id: str
    sprint_name: str
    status: str
    task_results: List[TaskResult]
```

#### 2.3 简化版状态机

**MVP 仅需要 5 个状态**：

```python
class SimpleStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**迁移规则**：
```
PENDING → RUNNING → SUCCESS
                  → FAILED → RUNNING (重试)
                  → CANCELLED
```

> 📌 **决策评估**：当前版本的 Phase-Substage 状态机（5阶段×17子阶段）对单人开发者来说过于复杂。建议 MVP 使用简单状态机，后续按需扩展。

### 3. MVP 执行流程

```python
async def execute_release_plan(plan: ReleasePlan):
    for sprint in plan.sprints:
        result = await execute_sprint(sprint)
        print(f"Sprint {sprint.name}: {result.status}")
        
async def execute_sprint(sprint: SprintDefinition):
    results = []
    for task in sprint.tasks:
        result = await execute_task(task)
        results.append(result)
    return SprintResult(...)
    
async def execute_task(task: SprintBacklogItem):
    agent = get_agent(task.agent)  # 简单工厂
    return await agent.execute(task)
```

---

## 第二部分：分阶段实现路线图

### Phase 1: 核心链路（Week 1-2）✅ 优先级 P0

**目标**：跑通"意图→计划→执行→结果"完整链路

| 任务 | 文件 | 复杂度 | 说明 |
|------|------|--------|------|
| 数据模型 | `domain/models.py` | ⭐ | ReleasePlan, SprintDefinition, TaskResult |
| YAML 解析 | `domain/parsers.py` | ⭐ | 解析 YAML 为 ReleasePlan |
| Coder Agent | `domain/agents/coder.py` | ⭐⭐ | 先实现 1 个 Agent，支持 mock 模式 |
| SprintExecutor | `domain/executor.py` | ⭐⭐ | 顺序执行任务，聚合结果 |
| CLI 入口 | `cli/main.py` | ⭐ | `sprintcycle run plan.yaml` |

**验收标准**：
```bash
$ sprintcycle run examples/simple.yaml
Sprint 1: success (3/3 tasks)
Sprint 2: success (2/2 tasks)
```

**暂缓功能**：
- ❌ 多 Agent 类型（先只实现 Coder）
- ❌ 并行执行
- ❌ 断点续传
- ❌ 状态持久化

---

### Phase 2: 状态机与生命周期（Week 3-4）⚠️ 优先级 P1

**目标**：添加状态追踪，支持失败重试

| 任务 | 文件 | 复杂度 | 说明 |
|------|------|--------|------|
| 简化状态机 | `domain/state_machine.py` | ⭐⭐ | 5 状态版本 |
| LifecycleRoot | `domain/lifecycle_root.py` | ⭐⭐ | 聚合根，记录状态历史 |
| 重试机制 | `domain/retry.py` | ⭐ | 简单重试，最多 3 次 |
| 错误处理 | `domain/error_handler.py` | ⭐⭐ | 错误分类、日志 |

> 📌 **决策评估**：当前 17 子阶段状态机可以简化为：
> - Phase 1: 5 状态（MVP）
> - Phase 2: 9 状态（添加 diagnosed/repairing/verifying）
> - Phase 3: 17 状态（完整版，按需扩展）

**简化版状态迁移**：
```
new → running → success
              → failed → repairing → running
              → cancelled
```

---

### Phase 3: 多 Agent 与编排（Week 5-6）⚠️ 优先级 P1

**目标**：实现 5 类 Agent，支持策略模式

| 任务 | 文件 | 复杂度 | 说明 |
|------|------|--------|------|
| Agent 基类 | `domain/agents/base.py` | ⭐⭐ | 抽象基类 + 配置 |
| Architect | `domain/agents/architect.py` | ⭐⭐ | 架构设计 Agent |
| Tester | `domain/agents/tester.py` | ⭐⭐ | 测试生成 Agent |
| 策略模式 | `domain/strategies/` | ⭐⭐ | 不同 Agent 的执行策略 |
| 并行执行 | `domain/executor.py` | ⭐⭐⭐ | asyncio.gather 控制并发 |

> 📌 **决策评估**：
> - 当前 5 类 Agent 是否都需要？建议优先级：Coder > Tester > Architect > RegressionTester > Analyzer
> - Agent 配置是否太复杂？建议简化为：`model`, `api_key`, `temperature` 三个核心参数
> - tenacity 重试是否必要？建议先用简单 `for` 循环重试

---

### Phase 4: 治理与质量门禁（Week 7-8）❌ 优先级 P2

**目标**：添加代码质量检查，通过后才可交付

| 任务 | 文件 | 复杂度 | 说明 |
|------|------|--------|------|
| PromotionPolicy | `domain/governance/promotion.py` | ⭐⭐ | 简化版：仅检查分数 |
| 代码检查 | `domain/governance/linters.py` | ⭐⭐ | ruff 检查 |
| 测试覆盖 | `domain/governance/coverage.py` | ⭐⭐ | pytest 覆盖率 |

> 📌 **决策评估**：
> - 当前 6 项门禁检查是否都需要？建议 MVP 仅保留：分数≥70
> - 7 层治理插件是否过度？建议先用简单函数调用，后续按需改为插件
> - pluggy 框架是否必要？建议暂缓，用普通 Python 函数替代

**简化版门禁**：
```python
def check_promotion(score: int) -> bool:
    return score >= 70
```

---

### Phase 5: HITL 人机协同（Week 9-10）❌ 优先级 P2

**目标**：关键决策点支持人工介入

| 任务 | 文件 | 复杂度 | 说明 |
|------|------|--------|------|
| HITL 协调器 | `domain/hitl/coordinator.py` | ⭐⭐⭐ | 阻塞等待决策 |
| 决策存储 | `domain/hitl/store.py` | ⭐⭐ | SQLite 存储 |
| 超时机制 | `domain/hitl/timeout.py` | ⭐⭐ | 超时自动决策 |

> 📌 **决策评估**：
> - HITL 是否 MVP 必需？建议 Phase 5 再实现
> - 5 种决策类型是否都需要？建议先实现 approve/reject
> - 跨进程安全是否必要？单人使用时可以简化

---

### Phase 6: 演化与版本管理（Week 11-12）❌ 优先级 P3

**目标**：支持意图漂移检测和版本回滚

| 任务 | 文件 | 复杂度 | 说明 |
|------|------|--------|------|
| 意图演化 | `domain/evolution/intent_loop.py` | ⭐⭐⭐ | 检测意图变化 |
| 版本注册 | `domain/evolution/registry.py` | ⭐⭐ | 版本管理 |
| Git 回滚 | `domain/evolution/rollback.py` | ⭐⭐⭐ | Git 分支回滚 |

> 📌 **决策评估**：
> - 自进化闭环是否 MVP 必需？建议最后实现
> - 沙箱验证是否复杂？建议先用 Git worktree，Docker 暂缓
> - 意图漂移检测算法是否过度？建议简单文本对比即可

---

### Phase 7: Web 界面与 API（Week 13-14）❌ 优先级 P3

**目标**：提供 HTTP API 和 Dashboard

| 任务 | 文件 | 复杂度 | 说明 |
|------|------|--------|------|
| FastAPI 应用 | `interfaces/http/app.py` | ⭐⭐ | HTTP 服务 |
| API 路由 | `interfaces/http/routes.py` | ⭐⭐ | RESTful API |
| Dashboard | `dashboard/` | ⭐⭐⭐ | Vue 3 前端 |

> 📌 **决策评估**：
> - Web 界面是否 MVP 必需？建议先用 CLI，后续再加 Web
> - 是否需要完整的前后端分离？建议先用服务端渲染简单页面

---

## 第三部分：架构简化建议

### 1. 端口层简化

**当前问题**：19 个端口 Protocol 对单人项目来说过度抽象

**简化方案**：

| 阶段 | 方案 | 说明 |
|------|------|------|
| Phase 1-2 | ❌ 不用端口 | 直接调用具体实现 |
| Phase 3-4 | ⚠️ 仅核心端口 | 保留 3-5 个核心端口 |
| Phase 5+ | ✅ 完整端口 | 按需添加 |

**核心端口**（Phase 3 开始）：
1. `StateStoreProtocol` - 状态存储
2. `EngineAdapterProtocol` - LLM 引擎
3. `CacheBackendProtocol` - 缓存

**暂缓端口**（16 个）：
- `HitlStoreProtocol`, `SuggestionStoreProtocol` - HITL 相关
- `EvolutionRegistryProtocol`, `VersionManifestProtocol` - 演化相关
- `ObservabilityFacadeProtocol`, `DiagnosticPort` - 可观测性
- `AuditPort`, `RateLimitPort` - 运维相关
- 其他集成类端口

---

### 2. 依赖注入简化

**当前问题**：`dependency-injector` + 工厂函数混合模式复杂度高

**简化方案**：

```python
# Phase 1-2: 直接实例化
executor = SprintExecutor()
agent = CoderAgent(config)

# Phase 3-4: 简单工厂
def create_executor(config):
    return SprintExecutor(
        state_store=create_state_store(config),
        runtime_config=config,
    )

# Phase 5+: 按需引入 DI 容器
```

> 📌 **决策评估**：`dependency-injector` 库是否必要？建议 Phase 4 之前不用 DI 框架

---

### 3. 治理插件简化

**当前问题**：pluggy 框架 + 7 层插件对单人项目过重

**简化方案**：

```python
# Phase 1-4: 简单函数调用
def run_governance_checks(context):
    results = []
    results.append(check_code_quality(context))
    results.append(check_security(context))
    return results

# Phase 5+: 按需改为插件模式
```

> 📌 **决策评估**：
> - pluggy 框架是否必要？建议暂缓
> - 7 层插件是否都需要？建议合并为 2-3 个检查函数
> - 治理适配器注册是否复杂？建议用简单字典替代

---

### 4. 事件系统简化

**当前问题**：`ExecutionEventBackend` + 事件总线对单人项目过重

**简化方案**：

```python
# Phase 1-3: 简单日志
logger.info(f"Task {task_id} completed: {status}")

# Phase 4-5: 按需添加事件系统
```

---

### 5. 可观测性简化

**当前问题**：Phoenix + 完整可观测性栈对单人项目过重

**简化方案**：

```python
# Phase 1-4: 日志 + 简单指标
logger.info(...)
metrics = {"duration": ..., "success_rate": ...}

# Phase 5+: 按需添加 Phoenix
```

---

## 第四部分：可复用的高质量决策

### 1. 领域建模决策

#### 1.1 DDD 聚合根设计 ✅ 强烈推荐保留

**决策**：使用聚合根封装业务逻辑，而非贫血模型

**实际代码体现**：
- `LifecycleRoot`：封装状态转换、证据记录、失败处理
- `SprintAggregate`：封装 Sprint 执行生命周期
- `ReleasePlanAggregate`：封装多 Sprint 编排

**为什么值得保留**：
```python
# ✅ 聚合根模式：行为与数据在一起
lifecycle = lifecycle.transition_to_substage(new_substage, reason)
lifecycle = lifecycle.record_evidence(stage, **kwargs)

# ❌ 贫血模型：行为与数据分离
transition_lifecycle(lifecycle, new_substage)
record_evidence(lifecycle, stage, **kwargs)
```

**收益**：
- 业务逻辑集中在聚合根，易于理解和测试
- 不可变更新保证线程安全
- 状态转换规则内聚，避免外部篡改

---

#### 1.2 不可变值对象 ✅ 强烈推荐保留

**决策**：使用 `@dataclass(frozen=True)` 定义值对象

**实际代码体现**：
```python
@dataclass(frozen=True)
class TaskResult:
    task_id: str
    description: str
    agent: str
    status: ExecutionStatus
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
```

**为什么值得保留**：
- 线程安全：不可变对象天然线程安全
- 易于测试：相同输入总是产生相同输出
- 避免副作用：函数式编程风格，减少 bug
- 哈希可用：可作为字典键或集合元素

---

#### 1.3 Phase-Substage 两层状态机 ⚠️ 简化后保留

**决策**：使用 Phase（阶段）+ Substage（子阶段）两层结构

**实际代码体现**：
```python
class LifecyclePhase(Enum):
    INITIALIZING = "initializing"
    EXECUTING = "executing"
    DELIVERING = "delivering"
    GOVERNING = "governing"
    TERMINAL = "terminal"

class LifecycleSubstage(Enum):
    # INITIALIZING 子阶段
    NEW = "new"
    NORMALIZED = "normalized"
    PLANNED = "planned"
    DECOMPOSED = "decomposed"
    
    # EXECUTING 子阶段
    RUNNING = "running"
    OBSERVING = "observing"
    DIAGNOSED = "diagnosed"
    REPAIRING = "repairing"
    VERIFYING = "verifying"
    # ... 更多子阶段
```

**为什么值得保留（简化版）**：
- 清晰的业务语义：Phase 表示大阶段，Substage 表示详细状态
- 迁移规则集中：`SUBSTAGE_TRANSITIONS` 字典统一管理
- 上下文切换：支持 `context` 参数切换不同上下文

**简化建议**：
- MVP 仅使用 5 个状态
- Phase 2 扩展到 9 个状态
- Phase 3 按需扩展到完整 17 子阶段

---

#### 1.4 跨域引用使用 ID 而非对象 ✅ 强烈推荐保留

**决策**：聚合根之间通过 ID 引用，而非直接持有对象

**实际代码体现**：
```python
@dataclass
class LifecycleRoot:
    # 跨域引用使用 ID
    governance_ref: Optional[GovernanceRef] = None
    evolution_ref: Optional[EvolutionRef] = None
    runtime_ref: Optional[RuntimeRef] = None

@dataclass(frozen=True)
class GovernanceRef:
    governance_id: str
```

**为什么值得保留**：
- 解耦：领域之间不直接依赖
- 延迟加载：按需加载关联数据
- 序列化友好：ID 引用易于 JSON 序列化
- 避免循环依赖：清晰的依赖方向

---

### 2. Agent 架构决策

#### 2.1 模板方法模式 + 重试机制 ✅ 强烈推荐保留

**决策**：Agent 基类使用模板方法模式，内置重试机制

**实际代码体现**：
```python
class AgentExecutor(ABC):
    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        pass

    @retry(
        retry=retry_if_exception_type(_AgentRetryableError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        before_sleep=before_sleep_log(_STD_RETRY_LOGGER, logging.WARNING),
    )
    def execute_with_retry(self, context: AgentContext) -> AgentResult:
        return self.execute(context)
```

**为什么值得保留**：
- 模板方法：子类只需实现 `execute` 方法
- 重试机制：tenacity 库提供指数退避重试
- 统一错误处理：可重试错误 vs 不可重试错误
- 配置灵活：`AgentConfig` 支持多种配置项

---

#### 2.2 Agent 配置集中管理 ✅ 推荐保留

**决策**：使用 `AgentConfig` dataclass 集中管理配置

**实际代码体现**：
```python
@dataclass
class AgentConfig:
    llm_provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""
    api_base: str = ""
    max_retries: int = 3
    timeout: int = 300
    temperature: float = 0.7
    mock_mode: bool = False

    def __post_init__(self):
        # 自动从环境变量加载配置
        if not self.api_key:
            self.api_key = os.environ.get("LLM_API_KEY", "")
```

**为什么值得保留**：
- 集中管理：所有配置在一个地方
- 默认值合理：开箱即用
- 环境变量支持：`__post_init__` 自动加载
- 类型安全：dataclass 提供类型提示

---

#### 2.3 Agent 类型枚举 ✅ 推荐保留

**决策**：使用枚举定义 Agent 类型

**实际代码体现**：
```python
class AgentType(Enum):
    CODER = "coder"
    TESTER = "tester"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    REGRESSION_TESTER = "regression_tester"
    CUSTOM = "custom"
```

**为什么值得保留**：
- 类型安全：避免字符串拼写错误
- IDE 支持：自动补全和重构
- 易于扩展：添加新类型只需加枚举值

---

### 3. 治理与质量决策

#### 3.1 PromotionPolicy 6 项门禁 ⚠️ 简化后保留

**决策**：使用 6 项检查决定是否允许晋升

**实际代码体现**：
```python
@dataclass
class PromotionPolicy:
    min_score: int = 70

    def evaluate(self, contract, runtime, governance, evidence):
        # 6 项检查
        # 1. 分数检查
        # 2. 运行时健康
        # 3. 治理审批
        # 4. 证据规范化
        # 5. 最终快照
        # 6. 阶段历史
        return {
            "allowed": passed,
            "score": score,
            "reasons": reasons,
            "status": "promotable" if passed else "blocked",
        }
```

**为什么值得保留（简化版）**：
- 清晰的门禁规则：6 项检查覆盖关键质量维度
- 可扩展：易于添加新的检查项
- 返回值丰富：包含分数、原因、状态

**简化建议**：
- MVP 仅保留：分数≥70
- Phase 2 添加：运行时健康
- Phase 3 按需添加其他检查

---

#### 3.2 HITL 决策类型 ✅ 推荐保留

**决策**：使用枚举定义 HITL 决策类型和门禁

**实际代码体现**：
```python
class HitlDecision(str, Enum):
    APPROVE = "approve"
    SKIP_SPRINT = "skip_sprint"
    ABORT_EXECUTION = "abort_execution"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    MODIFY = "modify"
    RETRY = "retry"
    RESUME = "resume"

class HitlGate(str, Enum):
    BEFORE_SPRINT = "before_sprint"
    AFTER_SPRINT = "after_sprint"
    AFTER_TASK = "after_task"
    SPEC_CONFIRM = "spec_confirm"
    EXECUTION_APPROVAL = "execution_approval"
    RELEASE_APPROVAL = "release_approval"
```

**为什么值得保留**：
- 决策规范化：统一的决策类型
- 门禁清晰：不同阶段有不同的 HITL 门禁
- 支持修正：`HitlCorrection` 支持修改目标
- 支持重放：`HitlReplayDirective` 支持重放指令

**简化建议**：
- MVP 仅实现：APPROVE / REJECT
- Phase 2 添加：REQUEST_CHANGES
- Phase 3 按需添加其他决策

---

### 4. 依赖注入决策

#### 4.1 组合根模式 ⚠️ 简化后保留

**决策**：使用组合根模式集中组装依赖

**实际代码体现**：
```python
def create_container(project_path: str) -> "Container":
    _container_instance = Container(project_path=project_path)
    
    # 注册治理适配器到领域层
    governance_hooks.register_governance_adapters({
        "import_linter": _container_instance.governance.import_linter_adapter(),
        "grimp": _container_instance.governance.grimp_adapter(),
        "archguard": _container_instance.governance.archguard_adapter(),
        "ruff": _container_instance.governance.ruff_adapter(),
        "typecheck": _container_instance.governance.typecheck_adapter(),
    })
    
    return _container_instance
```

**为什么值得保留（简化版）**：
- 集中组装：所有依赖在一个地方组装
- 懒加载：按需解析服务
- 缓存机制：避免重复创建

**简化建议**：
- Phase 1-2：直接实例化，不用 DI
- Phase 3-4：简单工厂模式
- Phase 5+：按需引入组合根

---

### 5. 错误处理决策

#### 5.1 统一错误上下文 ✅ 推荐保留

**决策**：使用 `ErrorContext` dataclass 封装错误信息

**实际代码体现**：
```python
@dataclass
class ErrorContext:
    error_log: str
    project_path: str
    file_paths: List[str]
    language: str
    max_level: int
    enable_rollback: bool
    enable_cache: bool
```

**为什么值得保留**：
- 上下文完整：包含错误相关的所有信息
- 配置灵活：支持回滚、缓存等开关
- 易于扩展：添加新字段不影响现有代码

---

### 6. 可复用的设计模式总结

| 模式 | 应用场景 | 推荐度 | 说明 |
|------|---------|--------|------|
| 聚合根 | 领域模型 | ✅ 强烈推荐 | 封装业务逻辑，不可变更新 |
| 值对象 | 结果对象 | ✅ 强烈推荐 | frozen dataclass，线程安全 |
| 模板方法 | Agent 执行 | ✅ 强烈推荐 | 统一执行流程，内置重试 |
| 策略模式 | 不同 Agent | ✅ 推荐 | 不同 Agent 有不同执行策略 |
| 工厂模式 | 对象创建 | ✅ 推荐 | 集中创建逻辑 |
| 枚举类型 | 状态/类型定义 | ✅ 推荐 | 类型安全，IDE 支持 |
| 组合根 | 依赖注入 | ⚠️ 简化使用 | Phase 3 后再引入 |
| 插件模式 | 治理检查 | ⚠️ 简化使用 | Phase 4 后再引入 |

---

## 第五部分：决策评估清单

### 必须重新评估的决策

| 决策 | 当前方案 | 建议方案 | 理由 |
|------|---------|---------|------|
| 状态机复杂度 | 5阶段×17子阶段 | 5状态→9状态→17状态 | 单人开发者无法一次性实现 |
| 端口数量 | 19 个 Protocol | 3 个核心端口 | 过度抽象，增加维护成本 |
| DI 框架 | dependency-injector | 简单工厂 | 学习曲线陡峭，MVP 不需要 |
| 治理插件 | pluggy + 7 层 | 简单函数 | 插件系统复杂度高 |
| Agent 数量 | 5 类 Agent | 1→3→5 逐步实现 | 先跑通核心链路 |
| HITL 实现 | 跨进程安全 | 单进程简单实现 | 单人使用场景简单 |
| 事件系统 | 完整事件总线 | 日志记录 | 事件系统维护成本高 |
| 可观测性 | Phoenix + 完整栈 | 日志 + 指标 | 可观测性栈过重 |

### 可以保留的决策

| 决策 | 说明 | 理由 |
|------|------|------|
| DDD 聚合根 | LifecycleRoot, SprintAggregate | 清晰的边界，值得保留 |
| 不可变值对象 | frozen dataclass | 线程安全，易于测试 |
| 六边形架构思想 | 端口与适配器 | 方向正确，但简化实现 |
| YAML 入站格式 | ReleasePlan YAML | 用户友好，值得保留 |
| 重试机制 | 失败后自动重试 | 核心功能，必须保留 |
| 模板方法模式 | Agent 基类 | 统一执行流程，值得保留 |
| Agent 配置集中管理 | AgentConfig | 开箱即用，值得保留 |
| 跨域 ID 引用 | GovernanceRef 等 | 解耦领域，值得保留 |
| HITL 决策类型 | HitlDecision 枚举 | 规范化决策，值得保留 |
| PromotionPolicy 门禁 | 6 项检查 | 质量保障，简化后保留 |

---

## 第六部分：实现检查清单

### Phase 1 检查清单

- [ ] 定义 ReleasePlan 数据模型
- [ ] 实现 YAML 解析器
- [ ] 实现 Coder Agent（mock 模式）
- [ ] 实现 SprintExecutor（顺序执行）
- [ ] 实现 CLI 入口
- [ ] 编写 3 个测试用例
- [ ] 跑通完整链路

### Phase 2 检查清单

- [ ] 实现简化版状态机（5 状态）
- [ ] 实现 LifecycleRoot
- [ ] 添加重试机制
- [ ] 添加错误处理
- [ ] 编写状态机测试

### Phase 3 检查清单

- [ ] 实现 Agent 基类
- [ ] 实现 Architect Agent
- [ ] 实现 Tester Agent
- [ ] 实现策略模式
- [ ] 添加并行执行支持

### Phase 4 检查清单

- [ ] 实现简化版 PromotionPolicy
- [ ] 添加代码质量检查
- [ ] 添加测试覆盖率检查

### Phase 5 检查清单

- [ ] 实现 HITL 协调器
- [ ] 实现决策存储
- [ ] 添加超时机制

### Phase 6 检查清单

- [ ] 实现意图演化循环
- [ ] 实现版本注册
- [ ] 实现 Git 回滚

### Phase 7 检查清单

- [ ] 实现 FastAPI 应用
- [ ] 实现 API 路由
- [ ] 实现 Dashboard

---

## 附录：快速参考

### 核心模型关系

```
ReleasePlan
  └── SprintDefinition (多个)
        └── SprintBacklogItem (多个)
              └── TaskResult (执行产出)
```

### 状态迁移（简化版）

```
pending → running → success
                  → failed → repairing → running
                  → cancelled
```

### 端口优先级

| 优先级 | 端口 | 阶段 |
|--------|------|------|
| P0 | 无 | Phase 1-2 |
| P1 | StateStore, EngineAdapter, CacheBackend | Phase 3-4 |
| P2 | 其他核心端口 | Phase 5-6 |
| P3 | 集成类端口 | Phase 7+ |

### 文件结构建议（Phase 1）

```
sprintcycle/
├── cli/
│   └── main.py              # CLI 入口
├── domain/
│   ├── models.py            # 数据模型
│   ├── parsers.py           # YAML 解析
│   ├── agents/
│   │   ├── base.py          # Agent 基类
│   │   └── coder.py         # Coder Agent
│   └── executor.py          # Sprint 执行器
└── examples/
    └── simple.yaml          # 示例计划
```

---

**文档版本**: v2.0 (单人开发者版)  
**最后更新**: 2026-10-19  
**状态**: ✅ 已重构，适合单人开发者重新实现