# Execution 层治理方案

## 问题描述

execution/ 模块占 11,985 行（32.9%），存在以下问题：
1. `state/` 模块属于基础设施职责，不应在执行层
2. 多个超大文件：`sprint_executor.py`(930行)、`feedback.py`(555行)、`rollback.py`(496行)、`analyzer.py`(486行)

## 治理策略

### 策略一：状态层迁移

将 `execution/state/` 迁移到 `infrastructure/persistence/state/`

**迁移文件：**
- cache.py → infrastructure/persistence/state/cache.py
- checkpoint.py → infrastructure/persistence/state/checkpoint.py
- context.py → infrastructure/persistence/state/context.py
- machine.py → infrastructure/persistence/state/machine.py
- rollback.py → infrastructure/persistence/state/rollback.py
- rollback_types.py → infrastructure/persistence/state/rollback_types.py
- sqlite_event_backend.py → infrastructure/persistence/state/sqlite_event_backend.py
- sqlite_state_store.py → infrastructure/persistence/state/sqlite_state_store.py
- state_store.py → infrastructure/persistence/state/state_store.py

### 策略二：策略模式拆分

在 `execution/orchestrator/policies/` 下创建策略模块：
- task_retry_policy.py
- sprint_retry_policy.py
- sprint_feedback_policy.py

### 策略三：向后兼容

在 `execution/state/` 保留兼容导入，逐步迁移调用方

## 执行步骤

1. 创建 infrastructure/persistence/state/ 目录结构
2. 迁移状态层文件
3. 更新 execution/state/ 作为兼容层
4. 拆分策略类
5. 更新所有调用点
6. 运行测试验证