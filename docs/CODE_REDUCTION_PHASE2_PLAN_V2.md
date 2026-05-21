# SprintCycle 精简设计方案 V2

> 基于 ARCHITECTURE_INVARIANTS.md 和 sprintcycle-architecture-orchestration.mdc  
> 生成日期：2026-05-21  
> 当前代码量：46,745 行

---

## 一、架构约束确认

### 1.1 必须保留的架构元素（不可精简）

| 元素 | 位置 | 约束级别 |
|------|------|---------|
| 分层架构 | 8层目录结构 | **不可更改** |
| LifecycleStateMachine | application/services/lifecycle_state_machine.py | **不可更改** |
| STAGE_TRANSITIONS | 状态转移规则 | **不可更改** |
| REQUIRED_STAGE_SEQUENCE | 15个阶段定义 | **不可更改** |
| EventType 枚举 | execution/events.py | **不可更改** |
| Rule Protocol | domain/quality_spec/rules/rule.py | **不可更改** |
| HITL 系统 | governance/hitl/ | **不可精简** |
| 架构守卫 | governance/arch_guard/ | **不可精简** |
| Hook 系统 | execution/hooks/ | **不可精简** |

### 1.2 可精简区域

| 区域 | 当前代码量 | 精简理由 |
|------|-----------|---------|
| execution/agents/ | 2,228 行 | 可被 OpenHands/mini-SWE 替代 |
| observability/ | 1,022 行 | 可合并到 infrastructure/ |
| execution/planners/ | ~500 行 | 可合并到 execution/ |
| governance 中的角色 | ~1,500 行 | 编码者/实现者/测试者角色可删除 |

---

## 二、精简目标

| 阶段 | 当前 | 目标 | 减少 |
|------|------|------|------|
| Phase 2（本方案） | 46,745 | 38,000 | -8,745 (-19%) |
| Phase 3（后续） | 38,000 | 30,000 | -8,000 |
| **总计** | 46,745 | 30,000 | **-16,745 (-36%)** |

---

## 三、精简方案

### 3.1 Phase 2A：合并 observability → infrastructure

**理由**：observability 是基础设施能力，应属于 infrastructure 层

**操作**：
```
observability/  →  infrastructure/observability/
```

**文件映射**：
| 源 | 目标 |
|----|------|
| observability/facade.py | infrastructure/observability/facade.py |
| observability/diagnostics/ | infrastructure/observability/diagnostics/ |
| observability/trace.py | infrastructure/observability/trace.py |

**预估减少**：-150 行（简化导入路径）

---

### 3.2 Phase 2B：精简 execution/agents/（关键）

**理由**：agents 现有 2,228 行，与 OpenHands 功能重叠

#### 保留的 agent 能力（架构契约）

| 文件 | 保留理由 | 行数 |
|------|---------|------|
| agents/base.py | Agent 抽象基类 | 286 |
| agents/analyzer.py | 静态分析，非代码生成 | 486 |
| agents/traceback_parser.py | 错误解析，特异性强 | 123 |

#### 可删除的 agent 能力

| 文件 | 删除理由 | 行数 |
|------|---------|------|
| agents/coder_base.py | OpenHands 替代 | 265 |
| agents/tester.py | OpenHands 替代 | 276 |
| agents/architect.py | OpenHands 替代 | 154 |
| agents/regression_tester.py | OpenHands 替代 | 175 |
| agents/bug_models.py | mini-SWE 替代 | 226 |
| agents/patterns.py | 冗余辅助 | 96 |
| agents/coder_types.py | 可合并 | 55 |

#### 新增 OpenHands Adapter

在 `infrastructure/adapters/` 下新增：

```
infrastructure/adapters/
├── __init__.py
├── openhands_adapter.py      # ~300 行
├── speckit_adapter.py        # ~200 行
└── mini_swe_adapter.py       # ~100 行
```

**Phase 2B 净减少**：~1,247 - 600 = **~650 行**

---

### 3.3 Phase 2C：合并 execution/planners/ → execution/_planners/

**理由**：planners 功能简单，作为执行引擎内部组件

| 文件 | 操作 | 行数 |
|------|------|------|
| planners/generator.py | 合并到 engine | 260 |
| planners/parser.py | 合并到 engine | 235 |
| planners/__init__.py | 删除 | - |

**预估减少**：-100 行

---

### 3.4 Phase 2D：简化 governance/ 角色代码

**保留核心**：
- GovernanceRunner (622行)
- HITL 系统 (全部)
- 架构守卫 (全部)
- 建议系统 (全部)

**检查冗余**：通过 ruff check 识别死代码

---

## 四、精简后架构

### 4.1 新目录结构

```
sprintcycle/
├── api.py                          # 薄 facade (保持)
├── application/                    # 业务编排 (保持)
├── domain/                         # 核心领域 (保持)
├── execution/                      # 执行引擎 (精简后 ~10,500行)
│   ├── sprint_executor.py          # 核心执行器
│   ├── state/                     # 状态管理
│   ├── events.py                  # 事件总线
│   ├── _planners/                 # 内部规划器 (合并)
│   ├── agents/                     # Agent 基类 (精简)
│   │   ├── base.py               # 抽象基类
│   │   ├── analyzer.py           # 静态分析
│   │   └── traceback_parser.py   # 错误解析
│   └── hooks/                     # 执行 Hook
├── governance/                     # 治理 (~6,500行)
├── infrastructure/                 # 基础设施 (~4,500行)
│   ├── observability/             # 可观测性 (合并)
│   ├── adapters/                  # 适配器 (新增)
│   │   ├── openhands_adapter.py  # OpenHands
│   │   ├── speckit_adapter.py    # SpecKit
│   │   └── mini_swe_adapter.py   # mini-SWE
│   └── ...
└── interfaces/                    # 接口层
```

### 4.2 精简对比

| 模块 | 精简前 | 精简后 | 变化 |
|------|--------|--------|------|
| execution/ | 12,912 | 10,500 | -2,412 |
| governance/ | 7,140 | 6,500 | -640 |
| infrastructure/ | 3,466 | 4,566 | +1,100 |
| observability/ | 1,022 | 0 | -1,022 |
| **总计** | 24,540 | 21,566 | **-2,974** |

---

## 五、实施计划

| Day | Phase | 任务 |
|-----|-------|------|
| 1 | 2A | 合并 observability 到 infrastructure |
| 2-3 | 2B | 精简 agents + 新增 Adapter |
| 4 | 2C | 合并 planners |
| 5 | 2D | 清理冗余 + 验证 |

---

## 六、验收标准

- [ ] `ruff check sprintcycle/` 无错误
- [ ] `pytest tests/` 全部通过
- [ ] API 端点功能正常
- [ ] Dashboard 可正常访问
- [ ] 代码行数减少 ≥ 2,500 行

---

## 七、附录：架构边界检查

根据 sprintcycle-architecture-orchestration.mdc：

- [ ] `api.py` 保持薄 facade（归一化、路由、委派、聚合）
- [ ] `execution/agents/` 只保留架构契约相关
- [ ] 不绕过 Hook 系统
- [ ] 不绕过 Facade 系统
- [ ] LangGraph 只做编排，不做业务
- [ ] 保持 8 层目录结构

**文档版本**：v1.0  
**下次审查**：2026-05-25
