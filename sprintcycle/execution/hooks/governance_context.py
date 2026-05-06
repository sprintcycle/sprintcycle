"""任务执行 context 中与治理钩子约定的键（避免 execution ↔ governance 循环依赖）。"""

# G v3：``GovernanceTaskLifecycleHooks`` 在 ``task_after`` 阻断时写入；``SprintExecutor`` 成功后读取。
CTX_GOVERNANCE_TASK_AFTER_FAILED = "_sprintcycle_governance_task_after_failed"
CTX_GOVERNANCE_TASK_AFTER_DETAIL = "_sprintcycle_governance_task_after_detail"
