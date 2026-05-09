# SprintCycle Governance / Observability 目录治理与入口规范

> 版本：与当前仓库代码对齐的工程规范稿
> 目的：统一治理域的目录归属、对外入口、导入边界与子模块职责

---

## 1. 背景

SprintCycle 的治理能力已从单一的 HITL 决策扩展为一个更完整的治理域，包含：

- 观测与事件上报
- 人工决策请求与提交
- 门禁触发与策略评估
- 架构 / 规则检查
- 运行编排
- 历史查询与回放

为避免入口分散、命名混乱与职责重叠，本仓库采用以下治理原则：

- `governance` 是治理域父包
- `GovernanceFacade` 是治理域统一总入口
- `observability` 是治理域下的子包，承载观测与请求能力
- `hitl` 是治理域内的人机协同内部实现
- `arch_guard` 是治理域内的规则 / 门禁检查实现
- `runner` 是治理域内的编排执行实现

---

## 2. 目录关系

推荐目录结构如下：

```text
sprintcycle/
  governance/
    __init__.py
    facade.py
    observability/
      __init__.py
      bootstrap.py
      facade.py
      models.py
    hitl/
      coordinator.py
      service.py
      types.py
      session.py
      store.py
      context.py
      decision_normalize.py
    arch_guard/
    runner.py
    model_compare.py
```

### 2.1 归属原则

- `governance` 表示治理域总范畴
- `observability` 属于 `governance`
- `hitl` 属于 `governance`
- `arch_guard` 属于 `governance`
- `runner` 属于 `governance`

### 2.2 使用原则

- 对外优先使用 `GovernanceFacade`
- 如需单独接入观测能力，可使用 `ObservabilityFacade`
- 业务模块不应直接依赖 `hitl` 的内部实现作为主入口

---

## 3. 入口治理

## 3.1 总入口：`GovernanceFacade`

`GovernanceFacade` 是治理域的统一门面，负责将外部调用路由到各个子能力：

- `observability`
- `runner`
- 后续可扩展到 `arch_guard`、`hitl` 等

推荐通过以下方式创建：

```python
from sprintcycle.governance import create_governance_facade

governance = create_governance_facade(project_path, config)
```

### 典型方法

- `observe(...)`
- `request_human_decision(...)`
- `summary(...)`
- `list_pending(...)`
- `list_history(...)`
- `get_request(...)`
- `apply_context_patch(...)`
- `submit_decision(...)`
- `governance_check(...)`
- `run_planning_gate(...)`
- `run_review_gate(...)`

---

## 4. 子模块职责

## 4.1 `governance/observability/`

职责：统一观测与决策接口。

承担能力：

- 事件上报
- 门禁触发
- 人工决策请求
- 决策提交
- 请求查询
- 历史查询
- 摘要查询
- 上下文修正

推荐导出：

- `ObservabilityFacade`
- `create_observability_facade`
- `ObservationEvent`
- `ObservationGateResult`
- `ObservationRequestResult`

---

## 4.2 `governance/hitl/`

职责：HITL 的内部实现层。

承担能力：

- request / decision 协调
- session / status 管理
- store 持久化
- context patch / replay
- decision normalize
- 底层事件派发

原则：

- 不作为外部主入口
- 由 `ObservabilityFacade` / `GovernanceFacade` 内部调用

---

## 4.3 `governance/arch_guard/`

职责：治理规则与门禁检查。

承担能力：

- planning gate
- review gate
- ADR 检查
- compose 检查
- 结构 / 依赖 / spec 检查
- 报告聚合

---

## 4.4 `governance/runner.py`

职责：治理编排执行层。

承担能力：

- 聚合规则检查
- 触发门禁
- 写入治理报告
- 向观测体系发事件

---

## 4.5 `governance/model_compare.py`

职责：治理相关的模型对比与回归辅助能力。

---

## 5. 导入与使用规范

## 5.1 推荐导入

### 推荐 1：治理总入口

```python
from sprintcycle.governance import create_governance_facade
```

### 推荐 2：单独观测能力

```python
from sprintcycle.governance import create_observability_facade
```

### 推荐 3：治理检查能力

```python
from sprintcycle.governance import GovernanceRunner
```

## 5.2 不推荐的导入方式

以下方式仅建议在治理内部实现中使用，不作为外部主入口：

```python
from sprintcycle.governance.hitl import HitlCoordinator
from sprintcycle.governance.hitl import HitlService
```

原因：这些对象属于内部实现，外部应通过 Facade 访问。

---

## 6. 顶层导出原则

`governance/__init__.py` 的导出顺序建议如下：

### 第一组：总入口

- `GovernanceFacade`
- `create_governance_facade`

### 第二组：观测子能力

- `ObservabilityFacade`
- `create_observability_facade`
- `ObservationEvent`
- `ObservationGateResult`
- `ObservationRequestResult`

### 第三组：治理能力

- `GovernanceReport`
- `GovernanceViolation`
- `GovernanceRunner`
- `run_planning_gate_sync`
- `run_review_gate_sync`
- `run_model_compare`

---

## 7. 设计约束

### 7.1 不要绕过总入口新增外部 API

新能力优先挂到 `GovernanceFacade`，再由其内部路由到子模块。

### 7.2 `observability` 是子能力，不是父域

`observability` 属于 `governance`，不应反过来理解。

### 7.3 `hitl` 保持内部实现定位

`hitl` 的主要价值是内部协作实现，不应作为新外部入口。

### 7.4 Facade 不应变成业务杂烩

`GovernanceFacade` 只做统一路由与薄编排，复杂逻辑仍然下沉到子模块。

---

## 8. 当前推荐的调用方式

### 8.1 常规治理接入

```python
governance = create_governance_facade(project_path, config)
report = governance.governance_check("review")
```

### 8.2 观测与人工决策接入

```python
result = await governance.request_human_decision(
    execution_id=execution_id,
    gate="before_sprint",
    title="Sprint 1: Alpha",
    summary="确认开始本 Sprint",
    context={"sprint_name": "Alpha"},
)
```

### 8.3 观测摘要

```python
summary = await governance.summary(execution_id)
```

---

## 9. 演进建议

- 若 `observability` 持续扩展，可保留子包结构并继续细分 `models` / `bootstrap` / `facade`
- 若未来需要更多治理能力（audit / trace / metrics），优先追加到 `governance` 下的新子包
- 外部接入文档始终以 `GovernanceFacade` 为第一入口

---

## 10. 一句话总结

**目录上，`governance` 是总域，`observability` 是其子能力；使用上，优先通过 `GovernanceFacade` 接入，内部再路由到各治理子模块。**
