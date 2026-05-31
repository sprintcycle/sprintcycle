# SprintCycle 架构精简记录

> 本文档记录 SprintCycle 架构精简的历史变更。

---

## v1.0 (2026-05-31)

### 精简背景

SprintCycle 项目采用 DDD 六边形架构，随着功能迭代，部分模块存在：
- 模块拆分过细
- 概念重叠
- 新人理解成本高

### 精简目标

1. 降低架构复杂度
2. 减少文件数量
3. 保持向后兼容
4. 不破坏现有功能

### 精简内容

#### 1. HITL 模块精简

**变更位置**: `sprintcycle/domain/core/governance/hitl/`

**精简前**:
```
hitl/
├── __init__.py
├── coordinator.py      # 协调器
├── context.py          # 上下文工具 (5 个函数)
├── config.py          # 配置工具 (4 个函数)
├── events.py          # 事件类型
├── facade.py          # Facade
├── hooks.py          # Hooks
├── policy.py         # 策略
├── service.py        # 服务
├── session.py        # 会话
├── types.py          # 类型定义
└── utils.py          # 工具函数 (1 个函数)
```

**精简后**:
```
hitl/
├── __init__.py
├── coordinator.py      # 合并 context.py 和 utils.py 的函数
├── events.py
├── facade.py
├── hooks.py
├── policy.py
├── service.py
├── session.py
├── types.py           # 合并 config.py 的函数
├── context.py         # 向后兼容：重新导出 coordinator 的函数
├── config.py          # 向后兼容：重新导出 types 的函数
└── utils.py           # 向后兼容：重新导出 coordinator 的函数
```

**合并详情**:
- `context.py` → 合并到 `coordinator.py`
  - `build_hitl_context()`
  - `build_replay_context()`
  - `merge_correction_into_context()`
  - `summarize_context_diff()`
  - `summarize_hitl_context()`
- `utils.py` → 合并到 `coordinator.py`
  - `compact_dict()`
- `config.py` → 合并到 `types.py`
  - `is_hitl_enabled()`
  - `get_hitl_timeout_seconds()`
  - `get_hitl_timeout_behavior()`
  - `get_hitl_gates()`

#### 2. arch_guard 模块精简

**变更位置**: `sprintcycle/domain/core/governance/arch_guard/`

**精简内容**:
- 创建 `checks.py` 统一检查逻辑
- `sdd_checks.py` 和 `yaml_checks.py` 合并到 `checks.py`
- 保持向后兼容

**合并详情**:
- `checks.py` (新文件)
  - 包含所有 SDD 检查函数
  - 包含所有 YAML 检查函数
- `sdd_checks.py` → 重新导出 `checks.py` 的函数
- `yaml_checks.py` → 重新导出 `checks.py` 的函数

#### 3. execution hooks 模块精简

**变更位置**: `sprintcycle/domain/core/execution/hooks/`

**精简前**:
```
hooks/
├── __init__.py
├── governance_context.py   # 常量定义
├── hook_context.py          # 上下文数据类
├── lifecycle_hooks.py       # (新文件)
├── quality_hooks.py         # 质量钩子
├── skill_hooks.py          # 技能钩子
├── sprint_hooks.py          # Sprint 钩子
└── task_hooks.py            # Task 钩子
```

**精简后**:
```
hooks/
├── __init__.py
├── governance_context.py   # 常量定义 (不变)
├── hook_context.py          # 上下文数据类 (不变)
├── lifecycle_hooks.py       # 合并 sprint_hooks 和 task_hooks
├── quality_hooks.py         # 质量钩子 (不变)
├── skill_hooks.py          # 技能钩子 (不变)
├── sprint_hooks.py          # 向后兼容：重新导出
└── task_hooks.py            # 向后兼容：重新导出
```

**合并详情**:
- `sprint_hooks.py` + `task_hooks.py` → 合并到 `lifecycle_hooks.py`
  - `SprintLifecycleHooks` 基类
  - `TaskLifecycleHooks` 基类
  - `create_noop_sprint_hooks()`
  - `create_chained_sprint_hooks()`
  - `create_noop_task_hooks()`
  - `create_chained_task_hooks()`

#### 4. governance hooks 模块精简

**变更位置**: `sprintcycle/domain/core/governance/hooks/`

**精简内容**:
- 创建 `governance_hooks.py` 统一治理钩子
- `sprint_hooks.py` 和 `task_hooks.py` 合并到 `governance_hooks.py`
- 保持向后兼容

### 向后兼容策略

所有被合并的模块都保留了以下内容：
1. 原始的 `__all__` 列表
2. 从新位置导入并重新导出函数/类
3. 更新文档字符串，标注"已精简"

### 测试验证

所有模块的导入测试均通过：
```bash
# HITL 模块
python -c "from sprintcycle.domain.core.governance.hitl.coordinator import *"
python -c "from sprintcycle.domain.core.governance.hitl.context import *"
python -c "from sprintcycle.domain.core.governance.hitl.config import *"
python -c "from sprintcycle.domain.core.governance.hitl.utils import *"

# arch_guard 模块
python -c "from sprintcycle.domain.core.governance.arch_guard.checks import *"
python -c "from sprintcycle.domain.core.governance.arch_guard.sdd_checks import *"
python -c "from sprintcycle.domain.core.governance.arch_guard.yaml_checks import *"

# execution hooks 模块
python -c "from sprintcycle.domain.core.execution.hooks.lifecycle_hooks import *"
python -c "from sprintcycle.domain.core.execution.hooks.sprint_hooks import *"
python -c "from sprintcycle.domain.core.execution.hooks.task_hooks import *"

# governance hooks 模块
python -c "from sprintcycle.domain.core.governance.hooks.governance_hooks import *"
python -c "from sprintcycle.domain.core.governance.hooks.sprint_hooks import *"
python -c "from sprintcycle.domain.core.governance.hooks.task_hooks import *"
```

### 精简效果

| 指标 | 精简前 | 精简后 | 改善 |
|------|--------|--------|------|
| hitl/ 文件数 | 12 | 12 | 逻辑更集中 |
| arch_guard/checks 相关文件 | 3 | 3 | 逻辑统一 |
| execution/hooks 文件数 | 7 | 7 | 逻辑统一 |
| governance/hooks 文件数 | 3 | 3 | 逻辑统一 |

### 后续优化方向

1. **execution 子域精简**
   - 将 analyzer agent 整合到 coder agent
   - 将 architect agent 作为可选插件
   - 将 regression_tester 整合到 tester agent

2. **lifecycle 服务精简**
   - 合并 `delivery_service.py` 和 `execution_lifecycle_service.py`
   - 重构 `lifecycle_service.py`

3. **Facade 层简化**
   - 扁平化 GovernanceFacade 调用链

---

> **维护者**: 架构团队
> **更新日期**: 2026-05-31
