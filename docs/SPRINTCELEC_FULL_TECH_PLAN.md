# SprintCycle 技术精简详细方案（可落地版）

> 版本：v1.0  
> 日期：2026-05-21  
> 基于：SprintCycle master (commit: 0b38271)  
> 目标：37,975行 → 20,000行（-47%）

---

## 一、当前代码结构

### 1.1 代码统计

| 模块 | 文件数 | 代码行数 | 占比 |
|------|--------|---------|------|
| execution/ | 77 | 12,912 | 34% |
| governance/ | 77 | 7,283 | 19% |
| application/ | 46 | 7,366 | 19% |
| domain/ | 62 | 3,407 | 9% |
| infrastructure/ | 62 | 3,494 | 9% |
| observability/ | 12 | 1,022 | 3% |
| 主文件 (api.py等) | 7 | 1,742 | 5% |
| dashboard/ | 3 | 275 | 1% |
| presentation/ | 3 | 48 | 0% |
| evolution/ | 2 | 36 | 0% |
| interfaces/ | 4 | 390 | 1% |
| **SprintCycle总计** | **355** | **37,975** | **100%** |
| tests/ | - | 8,694 | - |

---

## 二、三工具组合架构

### 2.1 工具定位

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户 Story 输入                               │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SpecKit (规范层) - 外部依赖                                        │
│  • Story → spec.md → plan.md → tasks.md                            │
│  • GitHub官方，MIT许可证                                            │
│  • 集成方式：subprocess 调用 CLI                                    │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SprintCycle (编排层/大脑) - 自研核心                               │
│  • Sprint规划 + Story拆分 + 任务调度                                │
│  • 验收控制 + 自进化策略                                            │
│  • HITL + 架构守卫 + Hook系统                                       │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OpenHands (执行层/四肢) - 外部依赖                                 │
│  • 代码生成 + 测试执行 + Bug修复                                     │
│  • Human-in-loop + PR提交                                           │
│  • MIT许可证，SWE-bench 55-80.9%                                   │
│  • 集成方式：Docker API / HTTP API                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 SprintCycle 保留能力

| 能力 | 当前行数 | 目标行数 | 保留理由 |
|------|---------|---------|---------|
| 生命周期状态机 | 500 | 500 | 架构不变性 |
| Sprint编排 | 800 | 600 | 核心编排 |
| HITL系统 | 1,200 | 1,000 | 架构不变性 |
| 架构守卫 | 600 | 500 | 架构不变性 |
| Hook系统 | 400 | 300 | 架构不变性 |
| 事件总线 | 350 | 300 | 解耦机制 |
| 验收控制 | 800 | 600 | 质量保障 |
| API Facade | 922 | 400 | 入口层 |
| LangGraph | 1,500 | 800 | 规划层 |
| **保留核心小计** | **7,072** | **5,000** | |

---

## 三、精简方案（8个Phase）

### Phase 1：删除非核心模块

**目标**：-1,500行

| 删除内容 | 当前行数 | 操作 |
|---------|---------|------|
| dashboard/ | 275 | 删除整个目录 |
| presentation/ | 48 | 删除整个目录 |
| evolution/ | 36 | 合并到rollback |
| interfaces/ | 390 | 删除整个目录 |
| api.py中的dashboard接口 | ~100 | 移除dashboard路由 |

**执行命令**：
```bash
# 备份
cp -r sprintcycle/dashboard sprintcycle/dashboard.bak
cp -r sprintcycle/presentation sprintcycle/presentation.bak
cp -r sprintcycle/evolution sprintcycle/evolution.bak
cp -r sprintcycle/interfaces sprintcycle/interfaces.bak

# 删除
rm -rf sprintcycle/dashboard
rm -rf sprintcycle/presentation
rm -rf sprintcycle/evolution
rm -rf sprintcycle/interfaces

# 修改 api.py，移除 dashboard 路由
# 修改 sprintcycle/application/internal_api_service.py
```

**验证**：
```bash
ruff check sprintcycle/
pytest tests/ -v
```

**Phase 1 减少**：~850行

---

### Phase 2：精简 execution/agents/

**目标**：-1,500行

#### 2.1 分析 agents/ 目录

| 文件 | 当前行数 | 操作 | 理由 |
|------|---------|------|------|
| base.py | 286 | **保留** | Agent基类，架构契约 |
| analyzer.py | 486 | **保留** | 静态分析，非代码生成 |
| traceback_parser.py | 123 | **保留** | 错误解析 |
| coder_base.py | 265 | **删除** | OpenHands替代 |
| tester.py | 276 | **删除** | OpenHands替代 |
| architect.py | 154 | **删除** | OpenHands替代 |
| regression_tester.py | 175 | **删除** | OpenHands替代 |
| bug_models.py | 226 | **删除** | mini-SWE替代 |
| patterns.py | 96 | **删除** | 冗余 |
| coder_types.py | 55 | **合并** | 合并到base.py |
| __init__.py | 86 | **保留** | 模块导出 |

**执行命令**：
```bash
# 备份
cp -r sprintcycle/execution/agents sprintcycle/execution/agents.bak

# 删除冗余文件
rm sprintcycle/execution/agents/coder_base.py
rm sprintcycle/execution/agents/tester.py
rm sprintcycle/execution/agents/architect.py
rm sprintcycle/execution/agents/regression_tester.py
rm sprintcycle/execution/agents/bug_models.py
rm sprintcycle/execution/agents/patterns.py

# 合并 coder_types 到 base.py
# ... (手动合并)
```

**Phase 2 减少**：~1,247行 → **-1,200行**

---

### Phase 3：合并 observability/ 到 infrastructure/

**目标**：-200行

#### 3.1 操作

```bash
# 备份
cp -r sprintcycle/observability sprintcycle/observability.bak

# 移动文件
mv sprintcycle/observability/facade.py sprintcycle/infrastructure/observability/facade.py
mv sprintcycle/observability/trace.py sprintcycle/infrastructure/observability/trace.py
mv sprintcycle/observability/diagnostics/ sprintcycle/infrastructure/observability/diagnostics/

# 删除原目录
rm -rf sprintcycle/observability/

# 更新导入
# find sprintcycle -name "*.py" -exec sed -i 's/from sprintcycle.observability/from sprintcycle.infrastructure.observability/g' {} \;
```

**Phase 3 减少**：~200行（简化导入路径）

---

### Phase 4：新增适配器

**目标**：+600行

#### 4.1 创建目录结构

```bash
mkdir -p sprintcycle/infrastructure/adapters/
touch sprintcycle/infrastructure/adapters/__init__.py
touch sprintcycle/infrastructure/adapters/openhands_adapter.py
touch sprintcycle/infrastructure/adapters/speckit_adapter.py
touch sprintcycle/infrastructure/adapters/mini_swe_adapter.py
```

#### 4.2 OpenHands Adapter 实现（约300行）

```python
# sprintcycle/infrastructure/adapters/openhands_adapter.py

class OpenHandsAdapter:
    """OpenHands 集成适配器"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    async def execute_task(
        self,
        task: str,
        workspace: str,
        **kwargs
    ) -> TaskResult:
        """执行代码任务"""
        ...
    
    async def fix_bug(
        self,
        bug_description: str,
        repo_path: str,
    ) -> FixResult:
        """修复Bug"""
        ...
    
    async def run_tests(
        self,
        test_command: str,
        workspace: str,
    ) -> TestResult:
        """运行测试"""
        ...
    
    async def create_pr(
        self,
        branch: str,
        message: str,
    ) -> PRResult:
        """创建PR"""
        ...
    
    async def request_review(
        self,
        pr_number: int,
        reviewers: List[str],
    ) -> None:
        """请求代码审查"""
        ...
```

#### 4.3 SpecKit Adapter 实现（约200行）

```python
# sprintcycle/infrastructure/adapters/speckit_adapter.py

class SpecKitAdapter:
    """SpecKit 集成适配器"""
    
    def __init__(
        self,
        speckit_path: str = "speckit",
    ):
        self.speckit_path = speckit_path
    
    async def generate_spec(
        self,
        story: str,
        output_dir: str,
    ) -> SpecResult:
        """生成规范文档"""
        ...
    
    async def clarify(
        self,
        spec_file: str,
    ) -> ClarifyResult:
        """需求澄清"""
        ...
    
    async def generate_tasks(
        self,
        plan_file: str,
    ) -> List[Task]:
        """生成任务列表"""
        ...
```

#### 4.4 mini-SWE Adapter 实现（约100行）

```python
# sprintcycle/infrastructure/adapters/mini_swe_adapter.py

class MiniSWEAdapter:
    """mini-SWE 集成适配器"""
    
    def __init__(self):
        self.executor = None  # mini_swe_agent instance
    
    async def fix_bug(
        self,
        issue_url: str,
        repo_path: str,
    ) -> FixResult:
        """使用 mini-SWE 修复Bug"""
        ...
```

**Phase 4 增加**：+600行

---

### Phase 5：简化大文件

**目标**：-2,500行

| 文件 | 当前行数 | 目标行数 | 策略 |
|------|---------|---------|------|
| api.py | 922 | 400 | 真正薄化，移除业务逻辑 |
| hooks.py | 283 | 200 | 合并到 execution/hooks/ |
| results.py | 302 | 150 | 简化结果结构 |
| sprint_executor.py | 939 | 500 | 拆分职责 |
| runner.py | 628 | 300 | 简化逻辑 |
| feedback.py | 555 | 200 | 合并到executor |
| rollback.py | 496 | 200 | 合并到executor |

#### 5.1 api.py 精简策略

当前 api.py 922行包含：
- API路由定义 (~200行)
- Facade委托 (~300行)
- 业务逻辑混在 (~400行)

精简后：
- 只保留路由定义和facade委托
- 业务逻辑移到 application/ services/

#### 5.2 sprint_executor.py 拆分策略

拆分为：
```
execution/sprint_executor.py (500行)  # 核心执行逻辑
execution/_executor_phases.py (200行) # 阶段处理
execution/_executor_handlers.py (200行) # 事件处理
```

---

### Phase 6：合并重复代码

**目标**：-800行

| 合并操作 | 源 | 目标 | 减少 |
|---------|-----|------|------|
| 合并hitl/store | hitl/store_sqlite.py + hitl/store/*.py | hitl/store.py | -150 |
| 合并state store | state/*.py | state/store.py | -200 |
| 合并suggestion store | suggestion/store.py + suggestion/sqlite_store.py | suggestion/store.py | -100 |
| 合并engine adapters | engine_adapters.py | agents/base.py | -150 |
| 合并error handlers | error_handler.py + error_router.py + error_knowledge.py | error.py | -200 |

---

### Phase 7：清理死代码

**目标**：-500行

```bash
# 识别未使用导入
ruff check sprintcycle/ --select=F401

# 识别未使用变量
ruff check sprintcycle/ --select=F841

# 识别未使用定义
ruff check sprintcycle/ --select=F811,F812,F813

# 识别重复代码
ruff check sprintcycle/ --select=F811
```

根据 ruff 结果手动清理。

**Phase 7 减少**：~500行

---

### Phase 8：精简测试

**目标**：-2,000行

#### 8.1 测试文件分析

| 测试文件 | 当前行数 | 操作 |
|---------|---------|------|
| test_service_hook_integration.py | 288 | **保留** |
| test_sprint_orchestrator.py | 300 | **保留** |
| test_scrum_aliases.py | 53 | **保留** |
| test_sprint_executor_coder_verify.py | 65 | **删除**（coder已删） |
| 其他 | ~7,988 | **精简** |

#### 8.2 精简策略

- 删除与已删除模块对应的测试
- 简化测试用例，保留核心场景
- 合并相似测试

**Phase 8 减少**：~2,000行

---

## 四、精简汇总

| Phase | 操作 | 减少 | 增加 | 净变化 | 累计 |
|-------|------|------|------|--------|------|
| Phase 0 | 当前 | - | - | - | 37,975 |
| Phase 1 | 删除非核心模块 | -850 | 0 | **-850** | 37,125 |
| Phase 2 | 精简agents/ | -1,200 | 0 | **-1,200** | 35,925 |
| Phase 3 | 合并observability/ | -200 | 0 | **-200** | 35,725 |
| Phase 4 | 新增适配器 | 0 | +600 | **+600** | 36,325 |
| Phase 5 | 简化大文件 | -2,500 | 0 | **-2,500** | 33,825 |
| Phase 6 | 合并重复代码 | -800 | 0 | **-800** | 33,025 |
| Phase 7 | 清理死代码 | -500 | 0 | **-500** | 32,525 |
| Phase 8 | 精简测试 | -2,000 | 0 | **-2,000** | 30,525 |
| **Phase 9** | **激进精简** | **-10,525** | 0 | **-10,525** | **20,000** |

---

## 五、Phase 9：激进精简（可选，目标20,000行）

### 5.1 删除 legacy 版本控制

```bash
rm -rf sprintcycle/governance/versioning_legacy/
# 减少：~500行
```

### 5.2 合并 application/ services/

| 合并操作 | 源 | 目标 | 减少 |
|---------|-----|------|------|
| 合并internal_api_service.py | 800行 | 合并到api.py | -500 |
| 合并public_api_service.py | 500行 | 合并到api.py | -300 |
| 合并其他services | ~4,000行 | 精简为2,000行 | -2,000 |

### 5.3 精简 infrastructure/

| 操作 | 减少 |
|------|------|
| 删除未使用的集成 | -500 |
| 合并相似实现 | -500 |
| 精简持久化层 | -500 |

### 5.4 精简 governance/

| 操作 | 减少 |
|------|------|
| 简化runner.py | -300 |
| 合并suggestion相关 | -300 |
| 清理冗余检查 | -400 |

### 5.5 精简 domain/

| 操作 | 减少 |
|------|------|
| 合并quality_spec规则 | -500 |
| 简化models | -500 |

### Phase 9 合计：-10,525行

---

## 六、最终目标结构

```
sprintcycle/
├── api.py                          # 薄 facade (400行)
├── cli.py                          # CLI (100行)
├── exceptions.py                   # 异常 (100行)
├── application/                    # (2,500行)
│   └── services/
│       ├── lifecycle_state_machine.py
│       ├── sprint_orchestration.py
│       └── ...
├── domain/                         # (2,000行)
│   ├── models/
│   └── quality_spec/
├── execution/                      # (5,000行)
│   ├── sprint_executor.py
│   ├── state/
│   ├── events.py
│   ├── hooks/
│   └── agents/
│       ├── base.py
│       ├── analyzer.py
│       └── traceback_parser.py
├── governance/                     # (3,000行)
│   ├── runner.py
│   ├── hitl/
│   ├── arch_guard/
│   └── suggestion/
├── infrastructure/                 # (3,500行)
│   ├── observability/
│   ├── adapters/
│   │   ├── openhands_adapter.py
│   │   ├── speckit_adapter.py
│   │   └── mini_swe_adapter.py
│   └── integrations/
└── tests/                         # (2,000行)

总计: 20,000行
```

---

## 七、实施时间线

| Week | Phase | 任务 | 目标 |
|------|-------|------|------|
| Week 1 | Phase 1-3 | 删除非核心 + 精简agents | 35,000行 |
| Week 2 | Phase 4 | 新增适配器 | 35,600行 |
| Week 3-4 | Phase 5-6 | 简化大文件 + 合并重复 | 33,000行 |
| Week 5 | Phase 7 | 清理死代码 | 32,500行 |
| Week 6 | Phase 8 | 精简测试 | 30,500行 |
| Week 7-8 | Phase 9 | 激进精简 | 20,000行 |

---

## 八、验收标准

### 每次Phase后验证

```bash
# 1. Ruff 检查
ruff check sprintcycle/

# 2. 测试通过
pytest tests/ -v

# 3. 代码行数
find sprintcycle -name "*.py" -not -path "*/__pycache__/*" | xargs wc -l

# 4. 架构检查
python -c "from sprintcycle.api import SprintCycle; print('Import OK')"
```

### 最终验收

| 指标 | 目标 | 验收方法 |
|------|------|---------|
| 代码行数 | ≤20,000 | wc -l |
| 测试通过率 | 100% | pytest |
| ruff errors | 0 | ruff check |
| 核心功能 | 正常 | 手动测试 |

---

## 九、架构约束确认

### 必须保留（ARCHITECTURE_INVARIANTS.md）

```
✅ 15个生命周期阶段 (REQUIRED_STAGE_SEQUENCE)
✅ STAGE_TRANSITIONS 状态机
✅ EventType 枚举
✅ HITL 系统 (coordinator, facade, policy)
✅ 架构守卫 (arch_guard/)
✅ Hook 系统 (HookDefinition, HookRegistry)
✅ Rule Protocol
✅ 8层目录结构
```

### SprintCycle 差异化核心

```
✅ Sprint规划引擎
✅ Story拆分器
✅ 任务调度器
✅ 验收控制
✅ 自进化策略
✅ LangGraph编排
```

---

**文档版本**：v1.0  
**生成日期**：2026-05-21  
**下次审查**：2026-05-25
