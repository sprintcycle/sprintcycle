# Agent 系统治理方案

> 遵循 DDD + 六边形架构原则，合并功能重叠的 Agent

---

## 1. 现状分析

### 1.1 当前结构

```
sprintcycle/domain/core/execution/agents/
├── __init__.py
├── base/
│   ├── __init__.py
│   └── base.py              # AgentExecutor 基类 (283行)
├── analyzer/
│   ├── __init__.py
│   ├── agent.py             # BugAnalyzerAgent (474行)
│   ├── models.py
│   ├── patterns.py
│   └── traceback_parser.py
├── architect/
│   ├── __init__.py
│   └── agent.py             # ArchitectureAgent (156行)
├── coder/
│   ├── __init__.py
│   ├── agent.py             # CoderAgent (358行)
│   └── types.py
├── regression_tester/
│   ├── __init__.py
│   └── agent.py             # RegressionTestAgent (177行)
└── tester/
    ├── __init__.py
    ├── agent.py             # TesterAgent (242行)
    └── types.py
```

**总计：15个文件，约1700+行代码**

### 1.2 Agent 功能概述

| Agent | 主要功能 | 依赖关系 |
|-------|---------|---------|
| [BugAnalyzerAgent](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/analyzer/agent.py) | 错误分析、堆栈解析、修复建议生成 | 独立 |
| [CoderAgent](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/coder/agent.py) | 代码生成、架构实现 | 可接收 Architect 的设计 |
| [TesterAgent](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/tester/agent.py) | 测试用例生成、测试执行、覆盖率分析 | 独立 |
| [RegressionTestAgent](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/regression_tester/agent.py) | 回归测试对比、结果差异分析 | 依赖 Tester 结果 |
| [ArchitectureAgent](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/architect/agent.py) | 架构设计、需求分析 | 独立 |

### 1.3 存在的问题

1. **功能重叠**
   - `BugAnalyzerAgent` 的错误分析和修复建议与 `CoderAgent` 功能高度相关
   - `RegressionTestAgent` 是 `TesterAgent` 的专项扩展，两者在测试领域有重叠

2. **文件分散**
   - `analyzer` 模块有5个文件，但核心逻辑都在 `agent.py` 中
   - `tester` 和 `regression_tester` 分离，增加理解成本

3. **职责不清**
   - 错误修复流程需要在 Analyzer 和 Coder 之间切换
   - 测试流程需要在 Tester 和 RegressionTester 之间协调

---

## 2. 治理方案

### 2.1 核心策略

**合并功能重叠的 Agent，保持向后兼容**

1. **将 `BugAnalyzerAgent` 合并到 `CoderAgent`**
   - Analyzer 的错误分析是代码修复的前置步骤
   - Coder 可以直接利用 Analyzer 的分析结果生成修复代码

2. **将 `RegressionTestAgent` 合并到 `TesterAgent`**
   - 回归测试是测试的一种特殊形式
   - Tester 可以支持多种测试模式（单元测试、回归测试等）

3. **保留 `ArchitectureAgent` 作为可选插件**
   - 架构设计是可选步骤，不是所有任务都需要
   - 保持灵活性，用户可以选择是否启用

### 2.2 目标结构

```
sprintcycle/domain/core/execution/agents/
├── __init__.py
├── base/
│   ├── __init__.py
│   └── base.py              # 保持不变
├── coder/
│   ├── __init__.py
│   ├── agent.py             # 合并 Coder + Analyzer
│   ├── types.py
│   ├── analyzer_models.py   # 从 analyzer/models.py 迁移
│   ├── error_patterns.py    # 从 analyzer/patterns.py 迁移
│   └── traceback_parser.py  # 从 analyzer/traceback_parser.py 迁移
├── tester/
│   ├── __init__.py
│   ├── agent.py             # 合并 Tester + RegressionTester
│   └── types.py
└── architect/
    ├── __init__.py
    └── agent.py             # 保持不变（可选插件）
```

**预期：减少到8个文件，代码行数基本不变但更集中**

---

## 3. 详细设计

### 3.1 CoderAgent 增强（合并 BugAnalyzerAgent）

**文件：[coder/agent.py](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/coder/agent.py)**

**新增能力：**

```python
class CoderAgent(AgentExecutor):
    """增强版 Coder Agent - 集成错误分析能力"""
    
    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        # 检测任务类型
        if self._is_error_fix_task(task, context):
            return await self._handle_error_fix(task, context)
        return await self._handle_code_generation(task, context)
    
    def _is_error_fix_task(self, task: str, context: AgentContext) -> bool:
        """判断是否为错误修复任务"""
        error_indicators = ["Traceback", "Error", "Exception", "fix bug", "修复"]
        return any(ind in task for ind in error_indicators)
    
    async def _handle_error_fix(self, task: str, context: AgentContext) -> AgentResult:
        """处理错误修复任务（原 BugAnalyzerAgent 逻辑）"""
        # 1. 分析错误
        analysis = await self._analyze_error(task, context)
        # 2. 生成修复建议
        suggestions = await self._generate_fix_suggestions(analysis)
        # 3. 生成修复代码
        fix_code = await self._generate_fix_code(analysis, suggestions, context)
        # 4. 返回结果
        return AgentResult(
            success=True,
            output=fix_code,
            artifacts={
                "analysis": analysis,
                "suggestions": suggestions,
                "code": fix_code
            },
            agent_type=self.agent_type,
        )
    
    async def _handle_code_generation(self, task: str, context: AgentContext) -> AgentResult:
        """处理代码生成任务（原 CoderAgent 逻辑）"""
        # ... 原有逻辑保持不变
```

### 3.2 TesterAgent 增强（合并 RegressionTestAgent）

**文件：[tester/agent.py](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/tester/agent.py)**

**新增能力：**

```python
class TesterAgent(AgentExecutor):
    """增强版 Tester Agent - 集成回归测试能力"""
    
    def __init__(self, test_type: str = "unit"):
        super().__init__()
        self._test_type = test_type  # "unit" | "regression"
    
    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        if self._test_type == "regression":
            return await self._handle_regression_test(task, context)
        return await self._handle_unit_test(task, context)
    
    async def _handle_regression_test(self, task: str, context: AgentContext) -> AgentResult:
        """处理回归测试任务（原 RegressionTestAgent 逻辑）"""
        # 1. 获取基准结果
        baseline = self._get_baseline_results(context)
        # 2. 运行当前测试
        current = await self._handle_unit_test(task, context)
        # 3. 对比结果
        diff = self._compare_results(baseline, current)
        # 4. 生成报告
        report = self._generate_regression_report(diff)
        # ...
```

### 3.3 兼容性策略

**为被合并的 Agent 创建兼容别名：**

**文件：[analyzer/__init__.py](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/analyzer/__init__.py)**

```python
"""
BugAnalyzerAgent 已合并到 CoderAgent
此模块保留用于向后兼容
"""
import warnings
from ..coder.agent import CoderAgent

warnings.warn(
    "BugAnalyzerAgent has been merged into CoderAgent. "
    "Please use CoderAgent with error-fix tasks instead.",
    DeprecationWarning,
    stacklevel=2
)

# 兼容别名
class BugAnalyzerAgent(CoderAgent):
    """兼容：BugAnalyzerAgent 现在是 CoderAgent 的别名"""
    def __init__(self, config=None, llm_client=None):
        super().__init__(config)
        # 保持接口兼容
```

**文件：[regression_tester/__init__.py](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/regression_tester/__init__.py)**

```python
"""
RegressionTestAgent 已合并到 TesterAgent
此模块保留用于向后兼容
"""
import warnings
from ..tester.agent import TesterAgent

warnings.warn(
    "RegressionTestAgent has been merged into TesterAgent. "
    "Please use TesterAgent(test_type='regression') instead.",
    DeprecationWarning,
    stacklevel=2
)

# 兼容别名
class RegressionTestAgent(TesterAgent):
    """兼容：RegressionTestAgent 现在是 TesterAgent 的别名"""
    def __init__(self, config=None):
        super().__init__(test_type="regression")
        self._config = config
```

---

## 4. 实施步骤

### Phase 1：准备（1-2天）
1. 创建新的合并模块文件结构
2. 迁移 Analyzer 的辅助模块到 Coder 目录
3. 迁移 RegressionTester 的逻辑到 Tester
4. 创建兼容性包装器

### Phase 2：实现合并（2-3天）
1. 增强 CoderAgent，集成错误分析能力
2. 增强 TesterAgent，集成回归测试能力
3. 更新 [AgentType](file:///Users/liangzai/CursorProjects/sprintcycle/sprintcycle/domain/core/execution/agents/base/base.py#L30-L37) 枚举（保持兼容）
4. 编写单元测试

### Phase 3：验证（1天）
1. 运行现有测试套件
2. 验证向后兼容性
3. 性能基准测试

### Phase 4：清理（可选，主要版本更新时）
1. 移除 deprecated 警告
2. 删除旧的模块文件
3. 更新文档

---

## 5. 预期收益

| 指标 | 当前 | 目标 | 改善 |
|------|------|------|------|
| Agent 模块数 | 5 | 3 | ↓ 40% |
| 文件数 | 15 | 8 | ↓ 47% |
| 理解成本 | 高（需了解5个Agent的协作） | 中（3个核心Agent职责清晰） | ↓ |
| 维护成本 | 高（修改需同步多个模块） | 中（功能集中） | ↓ |
| 向后兼容 | - | ✅ 完全兼容 | - |

---

## 6. 相关参考

- [ARCHITECTURE_SIMPLIFICATION.md](file:///Users/liangzai/CursorProjects/sprintcycle/docs/ARCHITECTURE_SIMPLIFICATION.md)
- [CONFIG_GOVERNANCE_PLAN.md](file:///Users/liangzai/CursorProjects/sprintcycle/docs/CONFIG_GOVERNANCE_PLAN.md)
- [AGENTS.md](file:///Users/liangzai/CursorProjects/sprintcycle/AGENTS.md)
