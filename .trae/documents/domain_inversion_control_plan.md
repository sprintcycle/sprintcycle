# Domain 层反向依赖治理方案

## 现状分析

当前发现 **5 处** Domain 层违反洋葱架构原则的反向依赖：

| 文件 | 问题 | 优先级 |
|------|------|--------|
| `domain/intent/runner.py` | 导入 `application.sprint_orchestrator`, `application.release_plan.parser` | P0 |
| `domain/evolution/default.py` | 导入 `execution.planners.generator` | P1 |
| `domain/evolution/rollback_manager.py` | 导入 `execution.state.rollback` | P1 |
| `domain/fitness/evaluator.py` | 导入 `application.services.evaluator_agent` | P0 |
| `domain/interfaces/validators.py` | 导入 `application.release_plan.validator` | P0 |

## 治理原则

1. **Domain 层应该是纯净的** - 只依赖自身和 Python 标准库
2. **依赖倒置** - Domain 层定义协议（Protocol），外层实现并注入
3. **最小改动** - 保持现有行为一致，只调整依赖方向
4. **向后兼容** - 保持公开 API 不变

## 详细治理方案

---

### 方案 1: `domain/intent/runner.py` - RunnerHandler 治理

**现状**
- `RunnerHandler` 已标记为弃用（DeprecationWarning）
- 主要功能是委托 `SprintOrchestrator`，并返回 `IntentResult`

**问题**
- 在 `__init__` 和模块级函数中动态导入 Application 层
- TYPE_CHECKING 导入也属于依赖声明

**治理方案**

1. **分析调用方** - 首先找出谁在使用这个弃用的 API
2. **保持弃用状态** - 由于已标记弃用，无需重构，保持现状
3. **依赖关系** - 明确注释说明这是过渡代码，未来会删除

---

### 方案 2: `domain/fitness/evaluator.py` - FitnessEvaluator 治理

**现状**
- 已有 `EvaluatorAgentProtocol` 定义在文件中
- 支持通过 `evaluator_agent` 参数注入
- 默认值在 `__post_init__` 中动态导入 Application 层

**治理方案**

1. **创建协议文件** - 将 `EvaluatorAgentProtocol` 移到 `domain/interfaces/`
2. **完善工厂模式** - 提供标准的工厂函数，由外层注入默认实现
3. **消除默认导入** - 要求调用方显式注入，或使用工厂函数获取

**实施步骤**

```python
# 1. 在 domain/interfaces/evaluation.py 中新增协议
class EvaluatorAgentProtocol(ABC):
    @abstractmethod
    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

# 2. 修改 domain/fitness/evaluator.py，移除默认导入
@dataclass
class FitnessEvaluator:
    aggregator: FitnessAggregator = field(default_factory=FitnessAggregator)
    evaluator_agent: EvaluatorAgentProtocol  # 必填
    
    def __post_init__(self) -> None:
        # 不再有默认导入逻辑
        pass

# 3. 在 application/services/ 中提供工厂函数
def create_fitness_evaluator(
    evaluator_agent: EvaluatorAgentProtocol | None = None
) -> FitnessEvaluator:
    if evaluator_agent is None:
        evaluator_agent = EvaluatorAgent()
    return FitnessEvaluator(evaluator_agent=evaluator_agent)
```

---

### 方案 3: `domain/interfaces/validators.py` - Validator 治理

**现状**
- 已有 `ValidatorProtocol` 协议
- 工厂函数 `create_validator()` 在内部导入 Application 层

**用户明确要求** - 将 Validator 下沉到 `domain/quality_spec/plan`

**治理方案**

1. **将验证逻辑下沉** - 把纯领域验证逻辑移到 `domain/quality_spec/plan_validator.py`
2. **保留协议** - 在 `domain/interfaces/` 保留协议定义
3. **提供两个实现**
   - 领域层：纯业务验证（无基础设施依赖）
   - 应用层：完整验证（含文件读取等）
4. **更新工厂** - 修改工厂函数让调用方选择

**文件结构**

```
domain/
├── interfaces/
│   └── validators.py          # 协议保持不变
└── quality_spec/
    └── plan/                  # 新增目录
        ├── __init__.py
        ├── validator.py       # 纯领域验证器
        └── rules.py           # 验证规则定义
```

---

### 方案 4: `domain/evolution/rollback_manager.py` - RollbackManager 治理

**现状**
- 导入 `execution.state.rollback` 获取 `GitRollbackMixin` 等
- 使用 try-except 导入机制做降级处理
- 核心是 Git 分支管理和文件备份功能

**治理方案**

1. **抽象 Git 操作** - 在 `domain/interfaces/version_registry.py` 新增 `GitOperationsProtocol`
2. **内联核心逻辑** - 将简单的 Git 命令包装和文件备份逻辑内联到 Domain 层
3. **注入实现** - 复杂功能（如 `GitRollbackMixin`）通过协议注入
4. **保留降级机制** - 保持现有的 try-except 导入，但改为注入方式

**协议设计**

```python
# domain/interfaces/version_registry.py
class GitOperationsProtocol(ABC):
    @abstractmethod
    def is_git_repo(self, path: str) -> bool: ...
    
    @abstractmethod
    def run_git_command(self, args: List[str], cwd: str) -> Tuple[int, str, str]: ...
    
    @abstractmethod
    def create_branch(self, branch_name: str, cwd: str) -> bool: ...
```

---

### 方案 5: `domain/evolution/default.py` - Evolution 工厂治理

**现状**
- `_create_default_evolution_facade_internal` 内部导入多外层模块
- 该函数仅供弃用的 `create_default_evolution_facade` 使用
- 正确做法是使用 `create_evolution_facade` 显式注入

**治理方案**

1. **标记内联函数** - 明确 `_create_default_evolution_facade_internal` 为过渡代码
2. **添加详细注释** - 说明这是为了向后兼容，新代码应使用依赖注入
3. **保持不变** - 由于主要使用方式已正确，无需大规模重构

---

## 实施优先级与步骤

### Phase 1: 高优先级（P0）- 立即执行

1. [ ] **方案 3**: Validator 下沉到 `domain/quality_spec/plan`
   - 创建 `domain/quality_spec/plan/` 目录
   - 迁移纯验证规则
   - 更新协议和工厂函数
2. [ ] **方案 2**: FitnessEvaluator 协议化
   - 迁移协议到 `domain/interfaces/`
   - 重构默认值逻辑
   - 更新调用方

### Phase 2: 中优先级（P1）- 随后执行

3. [ ] **方案 4**: Evolution RollbackManager 协议化
   - 定义 Git 操作协议
   - 重构实现使用注入
4. [ ] **方案 1**: RunnerHandler - 保持弃用，准备删除
   - 检查调用方
   - 制定删除时间表

### Phase 3: 清理与验证

5. [ ] 运行架构守护验证
6. [ ] 更新文档
7. [ ] 完整回归测试

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 改变现有行为 | 高 | 保持公开 API 不变，新增工厂函数作为默认路径 |
| 破坏依赖注入链 | 中 | 先完善测试，再逐步迁移 |
| 向后兼容性 | 高 | 保留旧工厂函数作为兼容包装器 |

---

## 验证标准

1. [ ] 运行 `archguard` 检查，无 Domain → Application/Execution 的导入
2. [ ] 所有现有测试通过
3. [ ] 公开 API 签名保持兼容
4. [ ] 新增或更新的文档说明新的依赖注入方式
