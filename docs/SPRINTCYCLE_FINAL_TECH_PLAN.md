# SprintCycle 最终技术方案

> SprintCycle + OpenHands + SpecKit 三工具组合  
> 目标：生产可用、可维护、观测驱动  
> 代码目标：46,000行 → 20,000行（-57%）  
> 遵循：ARCHITECTURE_INVARIANTS.md + sprintcycle-architecture-orchestration.mdc

---

## 一、最终架构设计

### 1.1 三工具定位

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户 Story 输入                               │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SpecKit (规范层) - 需求规范化                                        │
│  Story → spec.md → plan.md → tasks.md                               │
│  GitHub官方出品，MIT许可证                                           │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SprintCycle (编排层/大脑) - 敏捷框架核心                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Sprint规划 | Story拆分 | 任务调度 | 验收控制 | 自进化       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 架构不变性：15阶段状态机 | HITL | 架构守卫 | Hook系统      │    │
│  └─────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OpenHands (执行层/四肢) - 代码执行引擎                              │
│  代码生成 | 测试执行 | Bug修复 | Human-in-loop | PR提交              │
│  MIT许可证，SWE-bench 55-80.9%                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 SprintCycle 保留核心

| 核心能力 | 代码位置 | 保留理由 | 预估行数 |
|---------|---------|---------|---------|
| **生命周期状态机** | application/services/lifecycle_state_machine.py | 架构不变性 | 500 |
| **Sprint编排器** | application/services/sprint_orchestration.py | 核心编排 | 800 |
| **HITL系统** | governance/hitl/ | 架构不变性 | 1,200 |
| **架构守卫** | governance/arch_guard/ | 架构不变性 | 600 |
| **Hook系统** | execution/hooks/ | 架构不变性 | 400 |
| **事件总线** | execution/events.py | 解耦机制 | 350 |
| **验收控制** | domain/quality_spec/ | 质量保障 | 800 |
| **API Facade** | api.py | 入口层 | 500 |
| **LangGraph编排** | infrastructure/integrations/langgraph/ | 规划层 | 1,500 |

**保留核心总计**：约 6,650 行

---

## 二、精简方案

### 2.1 Phase 1：删除冗余模块（-1,500行）

| 删除模块 | 当前行数 | 理由 |
|---------|---------|------|
| execution/agents/ | 2,228 | OpenHands替代 |
| dashboard/ | 275 | 非核心 |
| presentation/ | 48 | 非核心 |
| evolution/ | 36 | 合并到rollback |
| execution/planners/ | 495 | 合并到executor |

**Phase 1 减少**：~3,000 行

### 2.2 Phase 2：合并重复实现（-800行）

| 合并操作 | 源 | 目标 | 减少 |
|---------|-----|------|------|
| observability → infrastructure | observability/ | infrastructure/observability/ | -200 |
| 合并hitl/store | hitl/store_sqlite.py | hitl/store/sqlite.py | -150 |
| 合并suggestion/store | suggestion/store.py | suggestion/sqlite_store.py | -100 |
| 合并state store | state/*_store.py | state/store.py | -200 |

**Phase 2 减少**：~650 行

### 2.3 Phase 3：新增适配器（+600行）

| 新增适配器 | 位置 | 功能 | 行数 |
|-----------|------|------|------|
| OpenHands Adapter | infrastructure/adapters/openhands_adapter.py | 代码生成/测试/Bug修复 | 300 |
| SpecKit Adapter | infrastructure/adapters/speckit_adapter.py | 规范生成 | 200 |
| mini-SWE Adapter | infrastructure/adapters/mini_swe_adapter.py | 轻量修复 | 100 |

**Phase 3 增加**：+600 行

### 2.4 Phase 4：简化大文件（-2,500行）

| 文件 | 当前行数 | 精简方案 | 目标行数 |
|------|---------|---------|---------|
| sprint_executor.py | 939 | 拆分职责 | 500 |
| runner.py | 628 | 简化逻辑 | 300 |
| feedback.py | 555 | 合并到executor | 200 |
| rollback.py | 496 | 合并到executor | 200 |
| api.py | 922 | 真正薄化 | 400 |
| engine_adapters.py | 424 | 合并到base | 200 |

**Phase 4 减少**：~2,500 行

### 2.5 Phase 5：清理死代码（-500行）

```bash
# 识别死代码
ruff check sprintcycle/ --select=F401,F841

# 识别未使用导入
ruff check sprintcycle/ --select=F401

# 识别未使用变量
ruff check sprintcycle/ --select=F841
```

**Phase 5 减少**：~500 行

### 2.6 Phase 6：精简测试代码（-1,500行）

| 操作 | 减少 |
|------|------|
| 删除冗余测试文件 | -500 |
| 简化测试用例 | -500 |
| 合并相似测试 | -500 |

---

## 三、精简汇总

| Phase | 操作 | 减少 | 增加 | 净变化 |
|------|------|------|------|--------|
| Phase 1 | 删除冗余模块 | -3,000 | 0 | **-3,000** |
| Phase 2 | 合并重复实现 | -650 | 0 | **-650** |
| Phase 3 | 新增适配器 | 0 | +600 | **+600** |
| Phase 4 | 简化大文件 | -2,500 | 0 | **-2,500** |
| Phase 5 | 清理死代码 | -500 | 0 | **-500** |
| Phase 6 | 精简测试 | -1,500 | 0 | **-1,500** |
| **总计** | | **-8,150** | **+600** | **-7,550** |

**目标达成**：46,000 - 7,550 = **38,450 行**

---

## 四、进一步精简（可选）

如果需要达到 20,000 行目标，需要更激进的措施：

### 4.1 删除 legacy 版本控制（-1,500行）

```
governance/versioning_legacy/ → 删除
```

### 4.2 简化 application 层（-3,000行）

| 文件 | 方案 | 减少 |
|------|------|------|
| internal_api_service.py | 删除，合并到api.py | -800 |
| public_api_service.py | 简化，合并到api.py | -500 |
| 其他服务 | 合并相似服务 | -1,700 |

### 4.3 合并 domain 层（-1,500行）

```
domain/quality_spec/ → domain/_quality_spec/
domain/models/ → domain/_models/
```

### 4.4 简化 infrastructure（-2,000行）

| 子模块 | 方案 | 减少 |
|-------|------|------|
| integrations/ | 精简LangGraph，只保留核心 | -1,000 |
| sandbox/ | 合并到deployment | -500 |
| 其他 | 清理冗余 | -500 |

### 4.5 删除接口层（-1,000行）

```
interfaces/ → 删除
```

---

## 五、20,000行目标分解

| 模块 | 目标行数 | 策略 |
|------|---------|------|
| api.py | 400 | 真正薄化 |
| application/ | 3,000 | 合并服务 |
| domain/ | 2,000 | 精简模型 |
| execution/ | 5,000 | 删除agents，合并planners |
| governance/ | 4,000 | 精简实现 |
| infrastructure/ | 3,500 | 合并observability+适配器 |
| interfaces/ | 0 | 删除 |
| dashboard/ | 0 | 删除 |
| presentation/ | 0 | 删除 |
| evolution/ | 0 | 删除 |
| tests/ | 2,100 | 精简测试 |
| **总计** | **20,000** | |

---

## 六、最终目录结构

```
sprintcycle/
├── api.py                          # 薄 facade (400行)
├── application/                    # 业务编排 (3,000行)
│   ├── services/
│   │   ├── lifecycle_state_machine.py  # 核心状态机
│   │   ├── sprint_orchestration.py     # Sprint编排
│   │   └── ...
│   └── __init__.py
├── domain/                         # 核心领域 (2,000行)
│   ├── models/
│   ├── quality_spec/
│   └── rules/
├── execution/                      # 执行引擎 (5,000行)
│   ├── sprint_executor.py         # 核心执行器
│   ├── state/                     # 状态管理
│   ├── events.py                  # 事件总线
│   ├── hooks/                     # Hook系统
│   ├── agents/                    # Agent基类（精简）
│   │   ├── base.py
│   │   ├── analyzer.py
│   │   └── traceback_parser.py
│   └── _internal/                 # 内部组件
├── governance/                     # 治理 (4,000行)
│   ├── runner.py                  # 治理运行器
│   ├── hitl/                      # HITL系统
│   ├── arch_guard/                # 架构守卫
│   ├── suggestion/                # 建议系统
│   └── task_hooks.py
├── infrastructure/                 # 基础设施 (3,500行)
│   ├── observability/             # 可观测性（合并）
│   ├── adapters/                  # 适配器（新增）
│   │   ├── openhands_adapter.py  # OpenHands
│   │   ├── speckit_adapter.py    # SpecKit
│   │   └── mini_swe_adapter.py   # mini-SWE
│   ├── integrations/
│   │   └── langgraph/            # LangGraph编排
│   └── persistence/
└── tests/                         # 测试 (2,100行)
```

---

## 七、实施顺序

| 阶段 | 任务 | 目标行数 | 验收 |
|------|------|---------|------|
| **Phase 0** | 当前状态 | 46,000 | - |
| **Phase 1** | 删除冗余模块 | 43,000 | ruff + pytest |
| **Phase 2** | 合并重复实现 | 42,350 | ruff + pytest |
| **Phase 3** | 新增适配器 | 42,950 | 适配器可用 |
| **Phase 4** | 简化大文件 | 40,450 | ruff + pytest |
| **Phase 5** | 清理死代码 | 39,950 | ruff 0 errors |
| **Phase 6** | 精简测试 | 38,450 | 测试覆盖80% |
| **Phase 7** | 激进精简 | 30,000 | 可选 |
| **Phase 8** | 极限精简 | 20,000 | 可选 |

---

## 八、验收标准

### 必须达标
- [ ] `ruff check sprintcycle/` 无错误
- [ ] `pytest tests/` 全部通过
- [ ] 15个生命周期阶段完整
- [ ] HITL系统正常工作
- [ ] 架构守卫检查通过
- [ ] API端点功能正常

### 质量指标
- [ ] 测试覆盖率 ≥ 80%
- [ ] 循环复杂度 ≤ 10
- [ ] 单一职责原则遵守
- [ ] 分层依赖规则遵守

---

## 九、架构约束清单

根据 ARCHITECTURE_INVARIANTS.md，以下**不可精简**：

```
✅ 必须保留：
   - 分层架构（8层目录）
   - 15个生命周期阶段 (REQUIRED_STAGE_SEQUENCE)
   - STAGE_TRANSITIONS 状态机
   - EventType 枚举
   - HITL 系统（coordinator, facade, policy, store）
   - 架构守卫（arch_guard/）
   - Hook 系统（HookDefinition, HookRegistry）
   - Rule Protocol（domain/quality_spec/rules/rule.py）

✅ 必须遵守：
   - interfaces → application → domain 依赖方向
   - governance 只读 domain
   - api.py 只做归一化、路由、委派、聚合
   - Hook 拦截关键操作点
   - Event 解耦组件间通信

❌ 禁止行为：
   - domain 层依赖其他业务层
   - api.py 承载工作流逻辑
   - 绕过 Hook 直接修改状态
   - 删除 STAGE_EVIDENCE_SCHEMA 必需字段
```

---

## 十、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 适配器实现复杂度 | 中 | 中 | 先实现最小可用版本 |
| 测试覆盖率下降 | 高 | 中 | 保留核心测试，逐步精简 |
| 架构违规 | 低 | 高 | 严格遵循ARCHITECTURE_INVARIANTS.md |
| 功能丢失 | 中 | 高 | 每阶段验证后提交 |

---

**文档版本**：v1.0  
**生成日期**：2026-05-21  
**下次审查**：2026-05-25
