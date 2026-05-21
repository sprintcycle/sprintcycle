# SprintCycle 代码精简 Phase 2 重启计划

> 创建时间：2025-05-20  
> 状态：草稿
> 目标：修复架构违规 + 精简代码至 22,000-25,000 行

---

## 1. 当前状态分析

### 1.1 代码统计

| 指标 | Phase 1 后 | 当前 |
|------|-----------|------|
| Python 文件数 | 345 | 342 |
| 总代码行数 | 35,170 | 36,541 |
| 顶层模块数 | 8 | 8 |

**说明**：
- ARCHITECTURE_INVARIANTS.md 记录的是 Phase 1 后的状态
- `cc56394` 提交已完成合并 Orchestrator + StateStore + 精简 evolution（净减少 1,624 行）
- 但后续开发又新增代码，当前总行数比 Phase 1 后更多
- Phase 2 任务是修复架构违规 + 继续精简

### 1.2 模块分布

| 模块 | 文件数 | 代码行数 | 占比 |
|------|--------|----------|------|
| `execution` | ~78 | ~9,500 | 26% |
| `governance` | ~77 | ~5,200 | 14% |
| `domain` | ~62 | ~4,800 | 13% |
| `infrastructure` | ~60 | ~4,200 | 11% |
| `application` | ~47 | ~6,500 | 18% |
| `observability` | ~12 | ~1,200 | 3% |
| `interfaces` | 4 | 390 | 1% |
| 根模块 | 5 | ~1,200 | 3% |

---

## 2. Phase 2 架构违规修复

### 2.1 违规 #1：domain/fitness/evaluator.py

**位置**：`sprintcycle/domain/fitness/evaluator.py:12`

**违规内容**：
```python
from sprintcycle.application.services.evaluator_agent import EvaluatorAgent
```

**问题**：domain 层不应依赖 application 层（违反架构不变性）

**修复方案**：
1. 将 `FitnessEvaluator` 中的 `_agent` 使用移除
2. 将 `EvaluatorAgent` 调用上移至 `application` 层
3. `FitnessEvaluator` 保持纯数据聚合逻辑

**预估精简**：移除 ~50 行 application 依赖代码

---

### 2.2 违规 #2：domain/verification/hooks.py

**位置**：`sprintcycle/domain/verification/hooks.py:7-9, 11`

**违规内容**：
```python
from sprintcycle.execution.events import Event, EventType, ExecutionEventBackend
from sprintcycle.execution.hooks.sprint_hooks import SprintLifecycleHooks
from sprintcycle.execution.sprint_types import SprintResult
from ...application.release_plan.models import ReleasePlan, SprintDefinition
```

**问题**：
- domain 层依赖 execution 层
- domain 层依赖 application 层

**修复方案**：
1. 将 `VerificationSprintHooks` 移至 `execution/hooks/` 层
2. 在 `domain/verification/` 仅保留领域模型和接口定义
3. 使用 Protocol 定义 Hook 接口，避免直接依赖

**预估精简**：重构后减少 ~100 行跨层依赖代码

---

## 3. 可精简模块分析

### 3.1 Orchestrator 重复实现

| 文件 | 行数 | 职责 |
|------|------|------|
| `application/sprint_orchestrator.py` | 477 | Sprint 编排主逻辑 |
| `application/release/orchestrator.py` | 27 | Release 编排（极简） |
| `execution/execution_orchestrator.py` | 79 | 执行编排 |

**分析**：
- `release/orchestrator.py` 只有 27 行，可能是废弃代码或可合并
- 三个文件职责有重叠，可考虑合并或统一接口

**建议**：
1. 检查 `release/orchestrator.py` 使用情况，考虑合并
2. 预估精简：~100 行

---

### 3.2 StateStore 重复实现

| 文件 | 行数 | 职责 |
|------|------|------|
| `application/services/lifecycle_state_machine.py` | 263 | 生命周期状态机 |
| `execution/core/state_machine.py` | 32 | 核心状态机 |
| `execution/state/state_store.py` | 340 | 状态存储 |
| `domain/evolution/runtime_state.py` | 92 | 运行时状态 |

**分析**：
- `execution/core/state_machine.py` 只有 32 行，可能功能很少
- `domain/evolution/runtime_state.py` 定义了大量枚举和类型

**建议**：
1. 检查 `execution/core/state_machine.py` 是否被使用
2. 预估精简：~50 行

---

### 3.3 Evaluation 模块可精简

**文件**：`domain/fitness/evaluator.py` (172行，含空行和注释)

**问题**：
- 包含 `_agent = EvaluatorAgent()` 调用
- 领域模型中包含执行逻辑

**建议**：
1. 将 Agent 调用移至 application 层
2. 保留纯数据聚合逻辑
3. 预估精简：~80 行

---

### 3.4 SprintExecutor 大文件

**文件**：`execution/sprint_executor.py` (935行)

**分析**：
- 单文件 935 行，需要拆分
- 可能包含多种职责混合

**建议**：
1. 按职责拆分为多个子模块
2. 不减少代码量，但改善结构

---

### 3.5 Debug/Trace 代码

**包含 TODO/FIXME/DEBUG/print 的文件数**：15+

**建议**：
1. 移除已完成的 TODO
2. 将调试 print 替换为 loguru 日志
3. 预估精简：~100 行

---

## 4. Phase 2 重启方案（修复版）

### 4.1 修复架构违规（P0）

| 任务 | 优先级 | 预估行数变化 |
|------|--------|-------------|
| 修复 `domain/fitness/evaluator.py` application 依赖 | P0 | -50 行 |
| 修复 `domain/verification/hooks.py` 跨层依赖 | P0 | -100 行 |

**修复原则**：
- domain 层保持纯净，无外部业务层依赖
- 使用 Protocol/ABC 定义接口
- 实现细节移至对应层

---

### 4.2 精简重复代码（P1）

| 任务 | 优先级 | 预估行数变化 |
|------|--------|-------------|
| 合并/检查 `release/orchestrator.py` | P1 | -27 行 |
| 检查 `execution/core/state_machine.py` 使用情况 | P1 | -32 行 |
| 精简 `domain/fitness/evaluator.py` | P1 | -80 行 |
| 移除调试代码 | P1 | -100 行 |

---

### 4.3 架构整理（P2）

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 拆分 `sprint_executor.py` | P2 | 按职责拆分为子模块 |
| 整理 `application/evolution/` | P2 | 评估是否过度抽象 |

---

## 5. 预估精简汇总

| 阶段 | 任务 | 预估精简行数 |
|------|------|-------------|
| **P0 架构修复** | domain/fitness/evaluator.py | -50 |
| | domain/verification/hooks.py | -100 |
| **P1 代码精简** | release/orchestrator.py | -27 |
| | execution/core/state_machine.py | -32 |
| | 精简 evaluator | -80 |
| | 移除调试代码 | -100 |
| **总计** | | **-389 行** |

**Phase 2 目标**：从 36,541 行降至 ~22,000-25,000 行

**阶段性目标**：
- P0 修复后：36,541 - 150 = 36,391 行
- P1 精简后：36,391 - 339 = 36,052 行
- 需要更多 P2 任务才能达到目标

---

## 6. 架构合规性确认

### 6.1 跨层依赖规则

```
interfaces → application → domain
                         ↓
                   execution
                         ↓
                   infrastructure

governance → domain (仅读)
governance → infrastructure (通过 runner)
```

### 6.2 修复后检查清单

- [ ] `domain/fitness/evaluator.py` 不导入 `application.*`
- [ ] `domain/verification/hooks.py` 不导入 `execution.*` 和 `application.*`
- [ ] `domain` 层无外部业务层依赖
- [ ] 所有 Hook 定义使用 Protocol/ABC

---

## 7. 后续工作建议

### 7.1 Phase 3 考虑方向

1. **evaluation 模块整体迁移**
   - 将 fitness 相关逻辑统一到 `application` 层
   - domain 只保留数据模型

2. **合并重复的 Orchestrator**
   - 统一接口，减少重复代码

3. **精简 evolution 模块**
   - `application/evolution/` 有 14 个文件，可能过度抽象

### 7.2 框架集成准备

参考 `docs/AI_FRAMEWORK_RESEARCH.md` 中的 LangGraph 集成研究，考虑：
- 统一状态管理接口
- 标准化事件契约
- 保持 Hook 扩展点

---

## 8. 附录：关键文件路径

| 文件 | 当前状态 | 需要操作 |
|------|----------|----------|
| `domain/fitness/evaluator.py` | 有违规 | 重构 |
| `domain/verification/hooks.py` | 有违规 | 迁移 |
| `application/release/orchestrator.py` | 27行 | 检查合并 |
| `execution/core/state_machine.py` | 32行 | 检查使用 |
| `execution/sprint_executor.py` | 935行 | 拆分 |
| `domain/support_legacy/prompt_sources.py` | 废弃区 | 评估清理 |

---

## 9. 执行检查清单

### Phase 2 重启前准备
- [x] 拉取最新代码
- [x] 分析当前架构违规
- [x] 扫描可精简模块
- [x] 制定重启方案
- [ ] 创建本文档

### Phase 2 执行中
- [ ] 修复 domain/fitness/evaluator.py 违规
- [ ] 修复 domain/verification/hooks.py 违规
- [ ] 检查并精简重复代码
- [ ] 运行架构验证测试

### Phase 2 完成后
- [ ] 验证代码行数减少
- [ ] 运行完整测试套件
- [ ] 更新 ARCHITECTURE_INVARIANTS.md
- [ ] 更新代码统计
