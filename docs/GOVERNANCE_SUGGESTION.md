# SprintCycle `governance/suggestion` 设计说明

## 1. 模块定位

`suggestion` 是 `governance` 域下的一种治理能力模块，用于接收、分类、审批和转化来自系统运行过程中的改进建议。

这些建议可能来源于：

- 用户需求进化
- 观测与诊断
- 治理检查
- 回放分析
- 人工提交
- Dashboard 反馈

它的职责不是直接修改 SprintCycle，而是：

1. 收集建议
2. 归类建议
3. 进入人工审批
4. 审批通过后，转化为 `evolution` 的代码自进化请求

---

## 2. 核心原则

### 2.1 治理先行
建议属于治理对象，不是执行对象。

### 2.2 审批前不落执行链路
未经审批的 suggestion 不能直接进入 code evolution。

### 2.3 审批后才可进化
审批通过后，suggestion 才能被转换为 `EvolutionRequest(target="code")`。

### 2.4 主架构不侵入
`suggestion` 作为外围治理模块存在，不修改 SprintCycle 主执行链路。

### 2.5 统一生命周期
建议对象遵循统一状态流转：

```text
Capture → Classify → Review → Approve / Reject → Promote / Archive
```

---

## 3. 目录结构

```text
sprintcycle/
└── governance/
    └── suggestion/
        ├── __init__.py
        ├── models.py
        ├── store.py
        ├── classifier.py
        ├── reviewer.py
        ├── approval.py
        ├── service.py
        └── facade.py
```

---

## 4. 模块职责

### `models.py`
负责定义 suggestion 的核心数据结构。

### `store.py`
负责持久化与查询，首期建议用 sqlite。

### `classifier.py`
负责对 suggestion 分类、打标签、识别影响范围。

### `reviewer.py`
负责在人工审批前，生成建议上下文与风险摘要。

### `approval.py`
负责 approve / reject / archive。

### `service.py`
负责 suggestion 生命周期编排。

### `facade.py`
负责对外统一入口，给 CLI / Dashboard / SDK 使用。

---

## 5. 数据模型

建议的最小模型如下。

### `Suggestion`

```text
suggestion_id
source_type
source_id
title
summary
details
impact_scope
severity
status
created_at
updated_at
reviewed_at
approved_at
reviewer
review_notes
linked_evolution_id
linked_version_id
metadata
```

### `source_type`

```text
requirement_evolution
observability
governance_check
manual
replay_analysis
dashboard_feedback
```

### `impact_scope`

```text
code
governance
execution
release_plan
observability
rollback
documentation
```

### `severity`

```text
low
medium
high
critical
```

### `status`

```text
pending
under_review
approved
rejected
promoted
archived
```

---

## 6. 生命周期设计

建议 suggestion 遵循以下状态流转：

```text
pending
  → under_review
  → approved / rejected
  → promoted / archived
```

---

## 7. 与 `evolution` 的桥接

只有满足以下条件才能转化：

- suggestion 已审批
- suggestion 状态为 `approved`
- suggestion 尚未被 promoted
- `project_path` 有效

转化为：

```python
EvolutionRequest(
    request_id=f"evo_from_{suggestion.suggestion_id}",
    target="code",
    project_path=project_path,
    mode="multi_sprint",
    context={...},
)
```

---

## 8. 对外 API 建议

- `capture_suggestion(...)`
- `list_suggestions(...)`
- `get_suggestion(...)`
- `review_suggestion(...)`
- `approve_suggestion(...)`
- `reject_suggestion(...)`
- `archive_suggestion(...)`
- `promote_suggestion(...)`
- `suggestion_overview(...)`

---

## 9. Dashboard / CLI 视图

### Dashboard
建议显示：

- 待审批数量
- 审批中数量
- 已批准数量
- 已拒绝数量
- 已转化数量
- 已归档数量
- 来源分布
- 严重度分布
- 影响范围分布
- 最近建议列表

### CLI
建议支持：

```text
sprintcycle suggestion overview
sprintcycle suggestion list
sprintcycle suggestion show <id>
sprintcycle suggestion review <id>
sprintcycle suggestion approve <id> --approver <name>
sprintcycle suggestion reject <id> --approver <name>
sprintcycle suggestion promote <id>
```

---

## 10. 设计总结

`suggestion` 是 `governance` 域中的待审批建议池，用于承接用户需求进化、治理检查和观测分析中暴露出的 SprintCycle 改进信号。它先被治理管理，经过人工审批后，再被转换为 `EvolutionRequest(target="code")` 并进入统一自进化链路，从而实现对 SprintCycle 自身的受控演化。
