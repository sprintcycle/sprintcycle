# SprintCycle Governance Overview

## 1. 目标

本页描述 SprintCycle 的治理总览能力：

- `evolution_overview()`
- `suggestion_overview()`
- `management_overview()`

它们分别用于：

- 查看演化版本与 active 状态
- 查看待审批建议池
- 一屏汇总治理与演化状态

---

## 2. API 清单

| API | 返回类型 | 用途 |
|---|---|---|
| `evolution_overview()` | `EvolutionOverviewResult` | 查看演化版本、active 指针、索引、sandbox 状态 |
| `evolution_overview_cli()` | `str` | CLI 友好的演化总览文本 |
| `evolution_overview_dashboard()` | `dict` | Dashboard 首屏 payload |
| `suggestion_overview()` | `dict` | 查看 suggestion 总览 |
| `suggestion_overview_cli()` | `str` | CLI 友好的 suggestion 总览文本 |
| `suggestion_overview_dashboard()` | `dict` | Dashboard 首屏 payload |
| `management_overview()` | `dict` | 汇总 evolution + suggestion 的治理总览 |
| `management_overview_cli()` | `str` | CLI 友好的治理总览文本 |
| `management_overview_dashboard()` | `dict` | Dashboard 首屏 payload |

---

## 3. 演化总览

### `evolution_overview()`
返回 `EvolutionOverviewResult`，包含：

- 当前 `code` / `requirement` 的 active 版本
- 最近 5 个版本
- 版本索引
- 版本总数统计
- sandbox 配置状态

### CLI

```python
print(cycle.evolution_overview_cli())
```

### Dashboard

```python
evo = cycle.evolution_overview_dashboard()
```

---

## 4. Suggestion 总览

### `suggestion_overview()`
返回 suggestion 总览对象，包含：

- pending / under_review / approved / rejected / promoted / archived 计数
- 最近建议列表
- 来源分布
- 严重度分布
- 影响范围分布

### CLI

```python
print(cycle.suggestion_overview_cli())
```

### Dashboard

```python
sug = cycle.suggestion_overview_dashboard()
```

---

## 5. 治理总览

### `management_overview()`
把 `evolution` 与 `suggestion` 汇总到同一 payload 中，适合 Dashboard 首屏。

返回结构：

```python
{
  "success": True,
  "data": {
    "evolution": {...},
    "suggestion": {...},
    "project_path": "..."
  }
}
```

### CLI

```python
print(cycle.management_overview_cli())
```

### Dashboard

```python
mgmt = cycle.management_overview_dashboard()
```

---

## 6. 关系说明

```text
Suggestion 池
   ↓ 审批通过
EvolutionRequest(target="code")
   ↓
Sandbox / Validate / Promote
   ↓
Versioning / Rollback
```

---

## 7. 设计原则

- 治理先行
- 审批后进化
- 主架构不侵入
- 模块化、高内聚
- 优先复用 sqlite / 现有 governance / evolution / versioning
