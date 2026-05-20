# SprintCycle Bug 修复清单
## 版本: 1.0.0
## 更新: 2026-05-19
## 总计: 29 个 F821 错误 + 5 个 F811 错误

---

## 🔴 优先级 P0（必须修复，阻塞运行）

### Bug #1: build_lifecycle_contract 缺失
- **位置**: `sprintcycle/api.py` 行 358, 372, 559
- **错误**: F821 Undefined name `build_lifecycle_contract`
- **修复**: 需要从 `sprintcycle.application.services.lifecycle_contracts` 导入或定义此函数
- **参考文件**: `sprintcycle/application/services/lifecycle_contracts.py`（存在但未被导入）

### Bug #2: build_platform_spec 缺失
- **位置**: `sprintcycle/api.py` 行 502
- **错误**: F821 Undefined name `build_platform_spec`
- **修复**: 需要从对应模块导入或定义此函数

### Bug #3: _OrchestratorSprintHooks 缺失
- **位置**: `sprintcycle/application/orchestration/sprint_orchestrator.py` 行 143
- **错误**: F821 Undefined name `_OrchestratorSprintHooks`
- **修复**: 需要定义此类或从未知模块导入

### Bug #4: _measurement_run_metadata 缺失
- **位置**: `sprintcycle/application/orchestration/sprint_orchestrator.py` 行 182
- **错误**: F821 Undefined name `_measurement_run_metadata`
- **修复**: 需要定义此变量或从其他模块导入

### Bug #5: SUGGESTION_ARCHIVE 缺失
- **位置**: `sprintcycle/application/services/suggestion_application_service.py` 行 215, 219 (3处)
- **错误**: F821 Undefined name `SUGGESTION_ARCHIVE`
- **修复**: 需要定义此常量（可能为路径常量）

### Bug #6: GovernanceViolation 缺失（12处）
- **位置**: 多文件，12个引用点
- **错误**: F821 Undefined name `GovernanceViolation`
- **修复**: 需要从 `sprintcycle.exceptions` 或其他模块导入/定义

### Bug #7: evaluate_hitl_policy 缺失
- **位置**: `sprintcycle/application/services/suggestion_application_service.py` 行 215
- **错误**: F821 Undefined name `evaluate_hitl_policy`
- **修复**: 需要定义此函数

---

## 🟡 优先级 P1（警告，不阻塞但需清理）

### Bug #8: Dict 导入缺失
- **位置**: `sprintcycle/domain/intent/parser.py` 行 47
- **错误**: F821 Undefined name `Dict`
- **修复**: 在文件顶部添加 `from typing import Dict`

### Bug #9: project_path 重定义（未使用）
- **位置**: `sprintcycle/application/internal_api_service.py` 行 27
- **错误**: F811 Redefinition of unused `project_path` from line 22
- **修复**: 删除重复定义或移除未使用的定义

### Bug #10: to_task_spec(s) 重定义（未使用）
- **位置**: 多处
- **错误**: F811 Redefinition of unused `to_task_spec` / `to_task_specs`
- **修复**: 删除重复定义

### Bug #11: update_evolution_link 重定义
- **位置**: 某文件
- **错误**: F811 Redefinition of unused `update_evolution_link` from line 165
- **修复**: 删除重复定义

### Bug #12: DashboardPanelViewModel 重定义
- **位置**: 某文件
- **错误**: F811 Redefinition of unused `DashboardPanelViewModel` from line 115
- **修复**: 删除重复定义

---

## 📋 修复顺序建议

```
Phase 1: 修复缺失的导入（P1）
  └─ Dict, typing.Any

Phase 2: 修复核心函数缺失（P0）
  ├─ build_lifecycle_contract
  ├─ build_platform_spec
  └─ evaluate_hitl_policy

Phase 3: 修复类/异常定义（P0）
  ├─ _OrchestratorSprintHooks
  ├─ GovernanceViolation
  └─ SUGGESTION_ARCHIVE

Phase 4: 修复变量定义（P0）
  ├─ _measurement_run_metadata
  └─ suggestion

Phase 5: 清理重定义（P1）
  └─ 删除所有未使用的重复定义
```

---

## 🎯 修复后预期

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| F821 错误 | 29 | 0 |
| F811 错误 | 5 | 0 |
| 代码可运行 | ❌ | ✅ |
| 生产就绪度 | 60% | 85%+ |
