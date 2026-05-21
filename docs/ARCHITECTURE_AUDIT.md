# SprintCycle 架构审计报告

> 版本: v1.0
> 日期: 2026-05-21
> 状态: 完整

---

## 一、架构总览

### 1.1 代码规模

| 指标 | 数值 |
|------|------|
| 源码总行数 | 38,262 行 |
| 测试总行数 | 8,694 行 |
| 总计 | 46,956 行 |
| Python 模块数 | ~200+ |
| 测试用例数 | 487 个 |

### 1.2 架构分层

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          SprintCycle 架构分层                              ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                                             ┃
┃  ┌─────────────────────────────────────────────────────────────────────┐   ┃
┃  │                    L7: 接口层 (Interface)                            │   ┃
┃  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   ┃
┃  │  │   api.py    │  │    cli.py   │  │ dashboard/ │                 │   ┃
┃  │  │   929行     │  │   122行     │  │  Web UI    │                 │   ┃
┃  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   ┃
┃  └─────────────────────────────────────────────────────────────────────┘   ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  ┌─────────────────────────────────────────────────────────────────────┐   ┃
┃  │                 L6: 应用服务层 (Application Services)                │   ┃
┃  │  ┌───────────────────────────────────────────────────────────────┐   │   ┃
┃  │  │ sprint_orchestrator.py (514行) - Sprint 编排核心              │   │   ┃
┃  │  └───────────────────────────────────────────────────────────────┘   │   ┃
┃  │  ┌───────────────────────────────────────────────────────────────┐   │   ┃
┃  │  │ phase_workflow.py (378行) - 阶段工作流                     │   │   ┃
┃  │  └───────────────────────────────────────────────────────────────┘   │   ┃
┃  │  ┌───────────────────────────────────────────────────────────────┐   │   ┃
┃  │  │ web_lifecycle_orchestration_service.py (403行)               │   │   ┃
┃  │  └───────────────────────────────────────────────────────────────┘   │   ┃
┃  │  ┌───────────────────────────────────────────────────────────────┐   │   ┃
┃  │  │ suggestion_application_service.py (444行)                     │   │   ┃
┃  │  └───────────────────────────────────────────────────────────────┘   │   ┃
┃  └─────────────────────────────────────────────────────────────────────┘   ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  ┌─────────────────────────────────────────────────────────────────────┐   ┃
┃  │                    L5: 领域层 (Domain)                               │   ┃
┃  │                                                                       ┃   ┃
┃  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               ┃   ┃
┃  │  │  domain/     │  │  domain/    │  │  domain/    │               ┃   ┃
┃  │  │  fitness/    │  │  intent/    │  │  quality_   │               ┃   ┃
┃  │  │  (健康评估)  │  │  (意图解析)  │  │  spec/      │               ┃   ┃
┃  │  │              │  │              │  │  (质量规格)  │               ┃   ┃
┃  │  │  multi_dim   │  │  base.py    │  │  reports/   │               ┃   ┃
┃  │  │  evaluator   │  │  parser     │  │  rules/     │               ┃   ┃
┃  │  └──────────────┘  └──────────────┘  └──────────────┘               ┃   ┃
┃  │                                                                       ┃   ┃
┃  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               ┃   ┃
┃  │  │  domain/     │  │  domain/    │  │  domain/    │               ┃   ┃
┃  │  │  evolution/  │  │  platform/  │  │  verification/              ┃   ┃
┃  │  │  (版本演进)  │  │  (平台信息)  │  │  (验证引擎)  │               ┃   ┃
┃  │  └──────────────┘  └──────────────┘  └──────────────┘               ┃   ┃
┃  └─────────────────────────────────────────────────────────────────────┘   ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  ┌─────────────────────────────────────────────────────────────────────┐   ┃
┃  │                    L4: 执行层 (Execution)                            │   ┃
┃  │                                                                       ┃   ┃
┃  │  ┌───────────────────────────────────────────────────────────────┐   │   ┃
┃  │  │ sprint_executor.py (939行) - Sprint 执行核心                  │   │   ┃
┃  │  └───────────────────────────────────────────────────────────────┘   │   ┃
┃  │  ┌───────────────────────────────────────────────────────────────┐   │   ┃
┃  │  │ feedback.py (555行) - 反馈循环                               │   │   ┃
┃  │  └───────────────────────────────────────────────────────────────┘   │   ┃
┃  │                                                                       ┃   ┃
┃  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   ┃   ┃
┃  │  │  agents/    │  │  engines/   │  │  hooks/    │                   ┃   ┃
┃  │  │  (AI Agent) │  │  (执行引擎) │  │  (生命周期) │                   ┃   ┃
┃  │  └─────────────┘  └─────────────┘  └─────────────┘                   ┃   ┃
┃  │                                                                       ┃   ┃
┃  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   ┃   ┃
┃  │  │  planners/  │  │   state/   │  │  events.py │                   ┃   ┃
┃  │  │  (计划生成) │  │  (状态存储) │  │  (事件总线) │                   ┃   ┃
┃  │  └─────────────┘  └─────────────┘  └─────────────┘                   ┃   ┃
┃  └─────────────────────────────────────────────────────────────────────┘   ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  ┌─────────────────────────────────────────────────────────────────────┐   ┃
┃  │                   L3: 治理层 (Governance)                            │   ┃
┃  │                                                                       ┃   ┃
┃  │  ┌───────────────────────────────────────────────────────────────┐   │   ┃
┃  │  │ runner.py (628行) - 治理运行器                               │   │   ┃
┃  │  └───────────────────────────────────────────────────────────────┘   │   ┃
┃  │  ┌───────────────────────────────────────────────────────────────┐   │   ┃
┃  │  │ hitl/ (HITL 人机回环)                                       │   │   ┃
┃  │  │  coordinator.py (281行)                                     │   │   ┃
┃  │  │  facade.py (292行)                                          │   │   ┃
┃  │  └───────────────────────────────────────────────────────────────┘   │   ┃
┃  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   ┃   ┃
┃  │  │ arch_guard/ │  │ suggestion/ │  │ versioning/│                   ┃   ┃
┃  │  │ (架构守护)  │  │ (建议管理)  │  │ (版本控制) │                   ┃   ┃
┃  │  └─────────────┘  └─────────────┘  └─────────────┘                   ┃   ┃
┃  └─────────────────────────────────────────────────────────────────────┘   ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  ┌─────────────────────────────────────────────────────────────────────┐   ┃
┃  │                    L2: 基础设施层 (Infrastructure)                   │   ┃
┃  │                                                                       ┃   ┃
┃  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   ┃   ┃
┃  │  │   config/   │  │    mq/     │  │ persistence/│                   ┃   ┃
┃  │  │  (配置管理) │  │  (消息队列) │  │  (持久化)  │                   ┃   ┃
┃  │  └─────────────┘  └─────────────┘  └─────────────┘                   ┃   ┃
┃  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   ┃   ┃
┃  │  │ integrations/│  │ deployment/ │  │  sandbox/  │                   ┃   ┃
┃  │  │ (集成)      │  │  (部署)    │  │  (沙箱)   │                   ┃   ┃
┃  │  └─────────────┘  └─────────────┘  └─────────────┘                   ┃   ┃
┃  └─────────────────────────────────────────────────────────────────────┘   ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  ┌─────────────────────────────────────────────────────────────────────┐   ┃
┃  │                    L1: 观测层 (Observability)                        │   ┃
┃  │                                                                       ┃   ┃
┃  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   ┃   ┃
┃  │  │  diagnostics/│  │    mq/     │  │   facade/  │                   ┃   ┃
┃  │  │  (诊断)     │  │  (消息追踪) │  │  (观测门面) │                   ┃   ┃
┃  │  └─────────────┘  └─────────────┘  └─────────────┘                   ┃   ┃
┃  └─────────────────────────────────────────────────────────────────────┘   ┃
┃                                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 二、核心模块详解

### 2.1 API 层 (api.py - 929行)

```python
class SprintCycle:
    """SprintCycle 统一 API"""
    
    # 核心服务
    _sprint_orchestrator: SprintOrchestrator      # Sprint 编排器
    _execution_service: ExecutionLifecycleService  # 执行生命周期
    _lifecycle_evolution: LifecycleEvolutionService # 生命周期演进
    _lifecycle_delivery: LifecycleDeliveryService  # 生命周期交付
    _lifecycle_assembly: LifecycleAssemblyService   # 生命周期组装
    
    # 治理服务
    _governance: GovernanceFacade                 # 治理门面
    _hitl_coordinator: HitlCoordinator             # HITL 协调器
    
    # 建议服务
    _suggestion: SuggestionFacade                 # 建议门面
    _evolution_promotion: EvolutionPromotionService # 版本推广
    
    # 观测服务
    _observability: ObservabilityService           # 观测服务
    _platform_summary: PlatformSummaryService       # 平台汇总
```

**API 方法分类**:

| 分类 | 方法数 | 说明 |
|------|--------|------|
| 执行 | 15+ | start/run/stop/diagnose/repair |
| 生命周期 | 10+ | promote/evaluate/deliver |
| 治理 | 5+ | governance/hitl |
| 建议 | 8+ | suggestion/capture |
| 观测 | 5+ | fitness/platform |
| 演进 | 5+ | evolution/memory |

### 2.2 Sprint 编排器 (sprint_orchestrator.py - 514行)

```python
class SprintOrchestrator:
    """Sprint 交付编排器"""
    
    async def execute_release_plan(release_plan: ReleasePlan) -> SprintResult
    async def resume_from_sprint(release_plan: ReleasePlan, from_sprint: int) -> SprintResult
    
    # 内部方法
    def _make_sprint_executor() -> SprintExecutor
    def _build_sprint_hooks(release_plan: ReleasePlan) -> SprintLifecycleHooks
    def _base_runner_context(release_plan: ReleasePlan) -> ExecutionContext
```

### 2.3 Sprint 执行器 (sprint_executor.py - 939行)

```python
class SprintExecutor:
    """Sprint 执行器 - 核心执行引擎"""
    
    # 执行方法
    async def execute_sprint(sprint: SprintDefinition) -> SprintResult
    async def execute_task(task: SprintBacklogItem) -> TaskResult
    async def verify_task(task: SprintBacklogItem, output: Any) -> VerifyResult
    
    # 修复循环
    async def repair_and_retry(task: SprintBacklogItem, error: Error) -> TaskResult
    async def run_verification_loop(task: SprintBacklogItem) -> VerifyResult
    
    # 事件处理
    def emit_sprint_event(event: SprintEvent)
    def set_event_bus(event_bus: EventBus)
```

### 2.4 反馈循环 (feedback.py - 555行)

```python
class FeedbackLoop:
    """反馈循环 - Verify-Fix 机制"""
    
    async def verify_and_fix(task: SprintBacklogItem) -> TaskResult
    
    # 反馈类型
    def analyze_error(error: Error) -> ErrorAnalysis
    def generate_fix_suggestion(analysis: ErrorAnalysis) -> FixSuggestion
    def apply_fix(task: SprintBacklogItem, fix: FixSuggestion) -> ApplyResult
```

### 2.5 AI Agent 层 (agents/)

| Agent | 行数 | 职责 |
|-------|------|------|
| coder_base.py | 265 | 代码生成基类 |
| tester.py | 276 | 测试生成 |
| analyzer.py | 486 | 错误分析 |
| base.py | 286 | Agent 基类 |

```python
# agents/analyzer.py (486行)
class BugAnalyzerAgent:
    """Bug 分析 Agent"""
    
    async def analyze(request: AnalysisRequest) -> AnalysisResult
    async def analyze_with_llm(error_log: str, context: Dict) -> LLMAnalysis
    
# agents/coder_base.py (265行)
class CoderAgent:
    """代码生成 Agent"""
    
    async def generate_code(spec: CodeSpec) -> CodeResult
    async def apply_changes(file: str, diff: Diff) -> ApplyResult
```

---

## 三、完整数据流

### 3.1 用户请求 → Sprint 执行完整链路

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        用户请求完整生命周期                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    用户意图
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ L7: 接口层 (api.py)                                                       │
│      │                                                                     │
│      ├── SprintCycle.start()                                              │
│      ├── SprintCycle.run_phase_workflow()                                 │
│      └── SprintCycle.orchestrate_web_request()                            │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ L6: 应用服务层 (application/services/)                                     │
│      │                                                                     │
│      ├── SprintOrchestrator.execute_release_plan()                        │
│      │    │                                                               │
│      │    ├── _make_sprint_executor() → SprintExecutor                    │
│      │    ├── _build_sprint_hooks() → ChainedSprintHooks                 │
│      │    └── _base_runner_context() → ExecutionContext                   │
│      │                                                                     │
│      ├── WebLifecycleOrchestrationService                                  │
│      ├── PhaseWorkflowService                                             │
│      └── ExecutionLifecycleService                                         │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ L4: 执行层 (execution/)                                                    │
│      │                                                                     │
│      ├── SprintExecutor.execute_sprint()                                  │
│      │    │                                                               │
│      │    ├── for task in sprint.tasks:                                   │
│      │    │    ├── execute_task() → CoderAgent                           │
│      │    │    └── verify_task() → TesterAgent                           │
│      │    │         │                                                    │
│      │    │         ▼                                                    │
│      │    │         if verify failed:                                     │
│      │    │              FeedbackLoop.verify_and_fix()                   │
│      │    │                   │                                          │
│      │    │                   ├── analyze_error()                        │
│      │    │                   ├── generate_fix_suggestion()              │
│      │    │                   └── apply_fix()                            │
│      │    │                                                                │
│      │    └── aggregate_sprint_result()                                   │
│      │                                                                     │
│      ├── Events.emit() → EventBus                                          │
│      ├── StateStore.save() → SQLite                                        │
│      └── Hooks.emit() → LifecycleHooks                                    │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ├──► 执行成功
        │        │
        │        ▼
        │    ┌─────────────────────────────────────────────────────────────────────────┐
        │    │ L5: 领域层 (domain/)                                                  │
        │    │      │                                                                 │
        │    │      ├── FitnessEvaluator.evaluate() → 健康评估                        │
        │    │      ├── QualitySpec.validate() → 质量验证                             │
        │    │      └── IntentParser.parse() → 意图解析                               │
        │    └─────────────────────────────────────────────────────────────────────────┘
        │        │
        │        ▼
        │    ┌─────────────────────────────────────────────────────────────────────────┐
        │    │ L3: 治理层 (governance/)                                              │
        │    │      │                                                                 │
        │    │      ├── GovernanceRunner.run() → 架构守护/SDD检查                   │
        │    │      ├── HitlCoordinator.review() → 人工审核                         │
        │    │      ├── SuggestionFacade.create() → 建议生成                          │
        │    │      └── VersionRegistry.register() → 版本注册                         │
        │    └─────────────────────────────────────────────────────────────────────────┘
        │        │
        │        ▼
        │    ┌─────────────────────────────────────────────────────────────────────────┐
        │    │ L1: 观测层 (observability/)                                           │
        │    │      │                                                                 │
        │    │      ├── DiagnosticsProvider.diagnose() → 诊断                        │
        │    │      ├── EventBackend.emit() → 事件记录                                │
        │    │      └── PhoenixTrace.emit() → 追踪                                  │
        │    └─────────────────────────────────────────────────────────────────────────┘
        │        │
        │        ▼
        │    ┌─────────────────────────────────────────────────────────────────────────┐
        │    │ L2: 基础设施层 (infrastructure/)                                      │
        │    │      │                                                                 │
        │    │      ├── Persistence.KnowledgeRepository → 知识存储                     │
        │    │      ├── Cache.ExecutionCache → 缓存                                  │
        │    │      └── MQ.EventBridge → 消息队列                                     │
        │    └─────────────────────────────────────────────────────────────────────────┘
        │
        └──► 执行失败 / 需要修复
                 │
                 ▼
        ┌─────────────────────────────────────────────────────────────────────────────┐
        │ L3: 治理层 - 修复循环                                                        │
│      │      │                                                                     │
│      │      ├── GovernanceRunner.check_policy() → 策略检查                        │
│      │      ├── HitlCoordinator.requires_human() → 人工确认                        │
│      │      └── SuggestionFacade.create_from_failure() → 失败建议                   │
│      └─────────────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
        ┌─────────────────────────────────────────────────────────────────────────────┐
        │ L4: 执行层 - 重新执行                                                       │
│      │      │                                                                     │
│      │      ├── FeedbackLoop.verify_and_fix() → 验证修复                          │
│      │      ├── SprintExecutor.repair_and_retry() → 修复重试                      │
│      │      └── Agents.apply_fix() → 应用修复                                      │
│      └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、模块依赖矩阵

```
依赖方向 ──────────────────────────────────────────────────────► 消费者

提供者:
     │   api  app  domain  execution  governance  infra  observ
─────┼───────────────────────────────────────────────────────────
api  │   -    -     -       -         -          -       -
app  │   ✅   -     -       -         -          -       -
domain│   ✅   ✅    -       -         -          -       -
exec │   ✅   ✅    ✅      -         -          -       -
gov  │   ✅   ✅    ✅      ✅        -          -       -
infra│   ✅   ✅    ✅      ✅        ✅         -       -
observ│   ✅   ✅    ✅      ✅        ✅         ✅      -
```

### 依赖规则验证

```bash
# Import-Linter 合约验证结果
✅ API 层不得依赖 dashboard (4/4)
✅ 编排层不得依赖 dashboard
✅ Release plan 层不得依赖 dashboard
✅ 执行层不得依赖 dashboard
```

---

## 五、架构与设定对比

### 5.1 原始设定 vs 实际实现

| 设定项 | 原始设计 | 实际实现 | 状态 |
|--------|---------|---------|------|
| **分层架构** | 7层 | 7层 | ✅ 符合 |
| **单向依赖** | 上层→下层 | 大部分符合 | ⚠️ 需审查 |
| **事件驱动** | EventBus | events.py (342行) | ✅ 符合 |
| **Hook系统** | 生命周期Hook | hooks.py (283行) | ✅ 符合 |
| **治理能力** | SDD + 架构守护 | governance/ | ✅ 符合 |
| **质量评估** | FitnessEvaluator | domain/fitness/ | ✅ 符合 |
| **建议系统** | SuggestionFacade | governance/suggestion/ | ✅ 符合 |
| **HITL** | 人工回环 | governance/hitl/ | ✅ 符合 |
| **LangGraph** | 编排骨架 | infrastructure/integrations/langgraph/ | ✅ 符合 |

### 5.2 架构约束检查

```markdown
## CONSTITUTION.md 架构宪法检查

### 一、核心原则

1. ✅ 分层清晰: API → Service → Domain → Infrastructure
2. ⚠️ 单向依赖: 大部分符合，个别需审查
3. ✅ 事件驱动: 事件总线已实现
4. ✅ 可测试: 487个测试，23%覆盖率

### 二、架构边界

#### 允许的依赖 ✅
- ✅ `api.py` → `application/services/`
- ✅ `application/services/` → `domain/`
- ✅ `domain/` → `infrastructure/adapters/`
- ✅ `governance/` → `domain/`

#### 禁止的依赖 ✅
- ✅ `domain/` ↛ `application/services/` (无反向依赖)
- ✅ `infrastructure/` ↛ `domain/` (无反向依赖)
- ✅ `execution/` ↛ `dashboard/` (Import-Linter 验证通过)
- ✅ `api.py` ↛ `dashboard/` (Import-Linter 验证通过)
```

---

## 六、详细模块清单

### 6.1 接口层 (L7)

| 模块 | 文件 | 行数 | 职责 |
|------|------|------|------|
| api.py | 统一API | 929 | Dashboard/REST/SDK共用 |
| cli.py | 命令行 | 122 | CLI入口 |
| dashboard/ | Web UI | 2000+ | 前端+后端服务 |

### 6.2 应用服务层 (L6)

| 模块 | 文件 | 行数 | 职责 |
|------|------|------|------|
| sprint_orchestrator.py | Sprint编排 | 514 | ReleasePlan→Sprint执行 |
| phase_workflow.py | 阶段工作流 | 378 | 生命周期阶段 |
| web_lifecycle_orchestration_service.py | Web编排 | 403 | Web触发编排 |
| suggestion_application_service.py | 建议服务 | 444 | 建议生命周期 |
| lifecycle_contracts.py | 生命周期合约 | 431 | 合约验证 |
| lifecycle_state_machine.py | 状态机 | 263 | 状态转换 |
| execution_lifecycle_service.py | 执行生命周期 | 200+ | 执行状态管理 |

### 6.3 领域层 (L5)

| 模块 | 文件 | 行数 | 职责 |
|------|------|------|------|
| fitness/multi_dimension.py | 多维评估 | 310 | 健康度评估 |
| fitness/evaluator.py | 评估器 | 200+ | Fitness计算 |
| intent/ | 意图解析 | 500+ | 意图理解 |
| quality_spec/ | 质量规格 | 1000+ | 规格验证 |
| quality_spec/reports/ | 报告 | 200+ | Finding/Report |
| evolution/ | 版本演进 | 500+ | 版本管理 |

### 6.4 执行层 (L4)

| 模块 | 文件 | 行数 | 职责 |
|------|------|------|------|
| sprint_executor.py | Sprint执行 | 939 | 核心执行引擎 |
| feedback.py | 反馈循环 | 555 | Verify-Fix |
| agents/coder_base.py | 代码Agent | 265 | 代码生成 |
| agents/tester.py | 测试Agent | 276 | 测试生成 |
| agents/analyzer.py | 分析Agent | 486 | 错误分析 |
| engines/ | 执行引擎 | 500+ | Cursor等 |
| planners/ | 计划生成 | 800+ | ReleasePlan生成 |
| state/state_store.py | 状态存储 | 350 | SQLite |
| events.py | 事件总线 | 342 | 事件驱动 |
| rollback.py | 回滚 | 496 | 错误恢复 |
| hooks/ | 生命周期钩子 | 500+ | Hook系统 |
| error_handler.py | 错误处理 | 329 | 错误路由 |
| error_router.py | 错误路由 | 300+ | 分层错误处理 |
| error_knowledge.py | 错误知识 | 340+ | 知识库 |

### 6.5 治理层 (L3)

| 模块 | 文件 | 行数 | 职责 |
|------|------|------|------|
| runner.py | 治理运行 | 628 | 治理执行 |
| hitl/coordinator.py | HITL协调 | 281 | 人机回环 |
| hitl/facade.py | HITL门面 | 292 | HITL接口 |
| suggestion/ | 建议管理 | 1000+ | 建议生命周期 |
| arch_guard/ | 架构守护 | 500+ | 架构检查 |
| versioning/ | 版本控制 | 500+ | 版本管理 |

### 6.6 基础设施层 (L2)

| 模块 | 文件 | 行数 | 职责 |
|------|------|------|------|
| config/ | 配置管理 | 500+ | 运行时配置 |
| persistence/ | 持久化 | 500+ | 知识存储 |
| mq/ | 消息队列 | 300+ | 事件桥接 |
| integrations/langgraph/ | LangGraph | 500+ | 编排集成 |

### 6.7 观测层 (L1)

| 模块 | 文件 | 行数 | 职责 |
|------|------|------|------|
| diagnostics/provider.py | 诊断 | 300+ | 项目诊断 |
| facade/ | 观测门面 | 200+ | 统一接口 |
| mq/ | 追踪 | 200+ | 消息追踪 |

---

## 七、问题与建议

### 7.1 架构问题

| 问题 | 严重性 | 建议 |
|------|--------|------|
| 代码量过大 (38k行) | 中 | Phase 3 重构目标 |
| 测试覆盖率低 (23%) | 高 | Phase 2 提升覆盖 |
| 循环依赖风险 | 低 | 持续监控 Import-Linter |
| 文档缺失 | 中 | 完善模块文档 |

### 7.2 优化建议

```markdown
## 短期优化 (Phase 2)
1. 测试覆盖率提升至 60%+
2. 补充关键模块单元测试
3. 完善 API 文档

## 中期优化 (Phase 3)
1. 代码量减少至 30k 行
2. 合并冗余模块
3. 简化执行引擎

## 长期优化 (Phase 4)
1. 性能优化 (P99 < 200ms)
2. 安全加固
3. 生产监控
```

---

## 八、架构健康度评分

| 维度 | 评分 | 说明 |
|------|------|------|
| **分层清晰度** | 9/10 | 7层分层清晰 |
| **单向依赖** | 8/10 | 大部分符合，个别需优化 |
| **模块内聚** | 7/10 | 部分模块过大 |
| **可测试性** | 6/10 | 覆盖率23%，需提升 |
| **可维护性** | 7/10 | 文档需完善 |
| **可扩展性** | 8/10 | Hook/Adapter机制完善 |

**综合评分: 7.5/10**

---

## 九、附录

### A. 关键文件清单

```
核心文件 (>300行):
├── sprintcycle/api.py (929)
├── sprintcycle/execution/sprint_executor.py (939)
├── sprintcycle/governance/runner.py (628)
├── sprintcycle/execution/feedback.py (555)
├── sprintcycle/application/sprint_orchestrator.py (514)
├── sprintcycle/execution/rollback.py (496)
├── sprintcycle/execution/agents/analyzer.py (486)
├── sprintcycle/application/services/suggestion_application_service.py (444)
├── sprintcycle/execution/engine_adapters.py (424)
├── sprintcycle/application/services/web_lifecycle_orchestration_service.py (403)
├── sprintcycle/application/services/phase_workflow.py (378)
├── sprintcycle/execution/state/state_store.py (350)
├── sprintcycle/execution/error_knowledge.py (340+)
├── sprintcycle/execution/error_handler.py (329)
├── sprintcycle/execution/events.py (342)
├── sprintcycle/domain/fitness/multi_dimension.py (310)
├── sprintcycle/governance/hitl/facade.py (292)
├── sprintcycle/execution/agents/base.py (286)
├── sprintcycle/governance/hitl/coordinator.py (281)
├── sprintcycle/execution/agents/tester.py (276)
└── sprintcycle/execution/agents/coder_base.py (265)
```

### B. Import-Linter 合约

```toml
[tool.importlinter.contracts]
name = "API 层不得依赖 dashboard"
type = "forbidden"
source_modules = ["sprintcycle.api"]
forbidden_modules = ["sprintcycle.dashboard"]

name = "编排层不得依赖 dashboard"
type = "forbidden"
source_modules = ["sprintcycle.application.sprint_orchestrator"]
forbidden_modules = ["sprintcycle.dashboard"]

name = "Release plan 层不得依赖 dashboard"
type = "forbidden"
source_modules = ["sprintcycle.application.release_plan"]
forbidden_modules = ["sprintcycle.dashboard"]

name = "执行层不得依赖 dashboard"
type = "forbidden"
source_modules = ["sprintcycle.execution"]
forbidden_modules = ["sprintcycle.dashboard"]
```

### C. 架构图生成命令

```bash
# 生成模块依赖图
cd sprintcycle
import-linter drawgraph > architecture.dot

# 查看导入关系
ruff check sprintcycle/ --select=F401 --output-format=concise

# 查看未使用导入
ruff check sprintcycle/ --select=F401 --output-format=concise
```
