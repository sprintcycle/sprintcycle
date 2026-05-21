# SprintCycle 渐进式质量提升方案
## SDD-Driven Quality Improvement Plan

> 版本: v1.0
> 日期: 2026-05-21
> 状态: 设计中

---

## 一、现状与目标

### 1.1 当前代码健康度

| 指标 | 现状 | 目标 |
|------|------|------|
| 源码行数 | 38,080 | 25,000（-34%） |
| 测试行数 | 8,694 | 15,000（+70%） |
| 测试覆盖率 | ~23% | 80%+ |
| Ruff 错误 | 0（F821/F841） | 0 |
| 测试通过率 | 471/488（96.5%） | 100% |
| Import-Linter | 4/4 通过 | 保持 |

### 1.2 质量目标

```
当前状态 ──────────────────────────────────────────► 目标状态
  │                                              │
  │  38k行代码，23%覆盖率                       │  25k行代码，80%覆盖率
  │  17个测试失败                               │  0个测试失败
  │  散乱的质量规则                             │  SDD驱动的质量治理
  │  手动质量检查                               │  自动化门禁
  │                                              │
  └──────────────────────────────────────────────┘
                     │
                     ▼
              渐进式提升（6个月）
```

---

## 二、核心架构：SDD + SprintCycle 集成

### 2.1 架构分层

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SDD 约束层 (Spec-Driven)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │ CONSTITUTION│  │  SPEC.md   │  │  plan.md   │               │
│  │   架构宪法   │  │   规格文档  │  │   实施计划  │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│                                                                     │
│  约束：架构边界 │ 规格：做什么 │ 方案：怎么做 │ 任务：分步执行      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼ 约束验证
┌─────────────────────────────────────────────────────────────────────┐
│                       sdd-framework 治理层                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Spec Lint│  │ 依赖追踪 │  │ 孤儿检测 │  │ 漂移告警 │          │
│  │ 15条规则 │  │ Deps Map │  │ Orphan   │  │ Drift    │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
│                                                                     │
│  L0: 代码质量（Lint/Ruff）                                        │
│  L1: 架构合规（Import-Linter）                                     │
│  L2: Spec漂移（sdd-framework）                                    │
│  L3: 业务验收（FitnessEvaluator）                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼ 执行验证
┌─────────────────────────────────────────────────────────────────────┐
│                      SprintCycle 执行层                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  IntentGraphRuntime  ←  意图理解与规划                             │
│       │                                                        │
│       ▼                                                        │
│  SprintGraphRuntime  ←  Sprint编排与执行                           │
│       │                                                        │
│       ▼                                                        │
│  FitnessEvaluator    ←  质量验证与评估                             │
│       │                                                        │
│       ▼                                                        │
│  arch_guard         ←  架构守护                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 SDD 工作流

```
用户意图输入
     │
     ├─► 需求模糊 / 从零设计 ──────► Speckit 完整流程
     │                                /speckit.constitution
     │                                      ↓
     │                                /speckit.specify
     │                                      ↓
     │                                /speckit.plan
     │                                      ↓
     │                                /speckit.tasks
     │                                      ↓
     │                              [CHECKPOINT 审查]
     │                                      ↓
     │                                /speckit.implement
     │
     └─► 需求明确 / 增量开发 ──────► OpenSpec 轻量流程
                                      /openspec:propose
                                            ↓
                                      /openspec:apply
                                            ↓
                                      /openspec:archive
```

---

## 三、渐进式提升路线图

### 3.1 总体时间线

```
┌──────────────────────────────────────────────────────────────────────┐
│                    SprintCycle 渐进式质量提升                        │
│                         24 周 / 6 个月                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Phase 0      Phase 1      Phase 2      Phase 3      Phase 4         │
│  基础修复     代码质量     测试覆盖     架构重构     生产就绪         │
│  (1-2周)     (3-4周)     (5-8周)     (9-16周)    (17-24周)        │
│                                                                      │
│  ████████    ████████████████████████████    ████████████████████    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Phase 0: 基础修复 ✅ (已完成)

**目标**: 修复阻塞性问题，建立基线

| 任务 | 状态 | 说明 |
|------|------|------|
| F821 未定义名称修复 | ✅ | 7个 → 0个 |
| F841 未使用变量修复 | ✅ | 5个 → 0个 |
| reports 模块创建 | ✅ | Finding/Report/Summary |
| 导入清理 | ✅ | -31行净减少 |
| Git 提交 | ✅ | cce1ce2 |

**本周继续**:
- [ ] 修复 LangGraph 兼容性问题
- [ ] 修复剩余 15 个测试失败
- [ ] 验证 Import-Linter 合约

### 3.3 Phase 1: 代码质量基线 (Week 3-4)

**目标**: 消除所有代码质量警告

```
Week 3: E402 问题处理
├── 审查 E402 位置（故意的 vs 非故意的）
├── 调整导入顺序
└── 验证 ruff check 0 errors

Week 4: 格式化与规范化
├── ruff format sprintcycle/
├── ruff check sprintcycle/ --fix
└── pre-commit 钩子配置
```

**验收标准**:
```bash
ruff check sprintcycle/ --select=E,F,W,I  # 0 errors
import-linter lint                          # 4/4 contracts kept
```

### 3.4 Phase 2: 测试覆盖率提升 (Week 5-8)

**目标**: 覆盖率从 23% 提升到 60%+

#### 2.1 模块优先级

| 优先级 | 模块 | 当前覆盖 | 目标覆盖 | 工作量 |
|--------|------|---------|---------|--------|
| P0 | domain/ (核心域) | ~15% | 90% | 高 |
| P0 | execution/core/ (执行核心) | ~20% | 90% | 高 |
| P1 | governance/ (治理) | ~10% | 80% | 中 |
| P1 | api.py (接口) | ~30% | 90% | 中 |
| P2 | infrastructure/ (基础设施) | ~5% | 60% | 低 |
| P2 | observability/ (观测) | ~5% | 60% | 低 |

#### 2.2 测试策略

```
┌─────────────────────────────────────────────────────────┐
│                  测试金字塔                              │
│                                                          │
│                    ┌───────┐                            │
│                   │  E2E  │   端到端测试 (10%)         │
│                   │ Tests │   覆盖关键用户路径           │
│                  ┌┴───────┴┐                           │
│                 │ Integration│ 集成测试 (30%)            │
│                 │   Tests   │ 模块间交互                │
│                ┌┴──────────┴┐                          │
│               │   Unit Tests │ 单元测试 (60%)           │
│               │  (核心层)    │ 每个函数/类               │
│              ┌┴─────────────┴┐                         │
│             │   Fixture Lib  │ 共享 Fixture            │
│             │ (测试基础设施) │ Mock/Stub               │
└─────────────────────────────────────────────────────────┘
```

#### 2.3 增量覆盖计划

```python
# 每周目标
week_5:  +5%  # domain/intent, domain/fitness
week_6:  +5%  # execution/core, execution/state
week_7:  +5%  # governance/runner, governance/arch_guard
week_8:  +5%  # api.py, sprint_orchestrator
```

### 3.5 Phase 3: 架构重构 (Week 9-16)

**目标**: 代码量从 38k 减至 30k

#### 3.1 重构原则

| 原则 | 说明 |
|------|------|
| **Spec 驱动** | 每个重构必须有对应的 SPEC.md |
| **小步快跑** | 每次重构不超过 500 行变更 |
| **对比验证** | 重构前后功能对比 |
| **可回滚** | 每个重构独立提交 |

#### 3.2 重构候选

| 模块 | 当前行数 | 目标行数 | 策略 |
|------|---------|---------|------|
| execution/planners/ | ~3,000 | 2,000 | 合并冗余模型 |
| governance/hitl/ | ~2,500 | 1,800 | 简化状态机 |
| domain/quality_spec/ | ~2,000 | 1,500 | 合并 adapters |
| application/services/ | ~5,000 | 4,000 | 拆分大服务 |

#### 3.3 SPEC 模板

```markdown
# SPEC: [模块名] 重构

## 1. 背景
- 为什么要重构
- 当前问题

## 2. 目标
- 代码量减少目标
- 质量提升目标

## 3. 范围
- 包含哪些模块
- 不包含哪些模块

## 4. 实现方案
### 4.1 架构变更
### 4.2 接口变更
### 4.3 数据迁移

## 5. 验收标准
- [ ] 代码量减少 N 行
- [ ] 测试覆盖率 >= X%
- [ ] 所有测试通过
- [ ] Import-Linter 通过

## 6. 风险与缓解
- 风险1: xxx
- 缓解: xxx

## 7. 回滚方案
- 如何回滚
```

### 3.6 Phase 4: 生产就绪 (Week 17-24)

**目标**: 达到生产级别质量

| 维度 | 目标 | 工具 |
|------|------|------|
| 性能 | P99 < 200ms | pytest-benchmark |
| 安全 | 0 高危漏洞 | Bandit + Safety |
| 文档 | API 100% 覆盖 | Sphinx + autodoc |
| 监控 | 关键指标就绪 | Phoenix + Grafana |

---

## 四、SDD 驱动实现

### 4.1 CONSTITUTION.md 模板

```markdown
# SprintCycle 架构宪法

## 一、核心原则

1. **分层清晰**: API → Service → Domain → Infrastructure
2. **单向依赖**: 上层依赖下层，下层不依赖上层
3. **事件驱动**: 模块间通过事件总线通信
4. **可测试**: 所有业务逻辑可单元测试

## 二、架构边界

### 允许的依赖
- `api.py` → `application/services/`
- `application/services/` → `domain/`
- `domain/` → `infrastructure/adapters/`
- `governance/` → `domain/`

### 禁止的依赖
- `domain/` ↛ `application/services/`
- `infrastructure/` ↛ `domain/`
- `execution/` ↛ `dashboard/`
- `api.py` ↛ `dashboard/`

## 三、代码规范

1. 函数长度 ≤ 50 行
2. 类方法数 ≤ 20
3. 模块行数 ≤ 500 行
4. 圈复杂度 ≤ 10

## 四、测试要求

1. 新增代码覆盖率 ≥ 80%
2. 核心模块覆盖率 ≥ 90%
3. 所有 PR 必须有测试

## 五、门禁规则

| 门禁 | 工具 | 阈值 |
|------|------|------|
| L0 代码质量 | Ruff | 0 errors |
| L1 架构合规 | Import-Linter | 4/4 contracts |
| L2 Spec漂移 | sdd-framework | 0 drift |
| L3 业务验收 | FitnessEvaluator | 100% |
```

### 4.2 SDD 门禁集成

```yaml
# .github/workflows/sdd-gate.yml

name: SDD Quality Gate

on:
  pull_request:
    branches: [master]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: L0 Code Quality
        run: |
          pip install ruff
          ruff check sprintcycle/ --select=E,F,W,I
          
      - name: L1 Architecture Compliance
        run: |
          pip install import-linter
          import-linter lint
          
      - name: L2 Spec Drift Detection
        run: |
          pip install sdd-framework
          sdd-framework check --spec specs/
          
      - name: L3 Business Acceptance
        run: |
          pytest tests/ -q --cov=sprintcycle --cov-fail-under=80

      - name: Coverage Report
        uses: codecov/codecov-action@v3
```

### 4.3 Cursor Rules 集成

```markdown
# .cursorrules (SDD 约束)

## SDD 开发流程

1. **Spec First**: 任何变更先写/更新 SPEC.md
2. **Constitution Check**: 变更前检查架构宪法
3. **Incremental**: 小步提交，不要大爆炸
4. **Test Coverage**: 新增代码必须有测试

## 架构约束

- 禁止跨层直接调用
- 禁止循环依赖
- 禁止 dashboard 依赖 execution

## 代码规范

- 保存时: ruff check --fix
- 提交前: ruff format && ruff check
- 测试: pytest tests/ -q

## 重构规则

- 重构必须有 SPEC.md
- 重构前后对比测试
- 单次重构 ≤ 500 行变更
```

---

## 五、工具链配置

### 5.1 Ruff 配置

```toml
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]
ignore = [
    "E501",  # line too long (handled by formatter)
    "E402",  # module level import (sometimes intentional)
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # imports ok in __init__
"tests/*" = ["E402", "F401"]
```

### 5.2 Import-Linter 配置

```toml
# pyproject.toml
[tool.importlinter]
root_package = "sprintcycle"

[[tool.importlinter.contracts]]
name = "API 层不得依赖 dashboard"
type = "forbidden"
source_modules = ["sprintcycle.api"]
forbidden_modules = ["sprintcycle.dashboard"]

[[tool.importlinter.contracts]]
name = "Domain 层不得依赖 Application"
type = "layers"
layers = ["sprintcycle.domain", "sprintcycle.application"]

[[tool.importlinter.contracts]]
name = "Execution 层不得依赖 Dashboard"
type = "forbidden"
source_modules = ["sprintcycle.execution"]
forbidden_modules = ["sprintcycle.dashboard"]
```

### 5.3 Pre-commit 配置

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff format
        entry: ruff format sprintcycle/
        language: system
        pass_filenames: true
        
      - id: ruff-check
        name: ruff check
        entry: ruff check sprintcycle/ --fix
        language: system
        pass_filenames: true
        
      - id: import-linter
        name: import-linter
        entry: import-linter lint
        language: system
        pass_filenames: false
        
      - id: tests
        name: pytest
        entry: pytest tests/ -q
        language: system
        pass_filenames: false
```

---

## 六、Milestone 与验收

### 6.1 Milestone 规划

| Milestone | 日期 | 目标 |
|-----------|------|------|
| M0 | 2026-05-21 | ✅ 基础修复完成 |
| M1 | 2026-06-04 | Phase 1 完成，代码质量基线 |
| M2 | 2026-06-25 | Phase 2 完成，测试覆盖 60% |
| M3 | 2026-08-20 | Phase 3 完成，代码量 30k |
| M4 | 2026-09-30 | Phase 4 完成，生产就绪 |

### 6.2 验收清单

```markdown
## M1 验收清单

- [ ] ruff check sprintcycle/ --select=E,F,W,I → 0 errors
- [ ] import-linter lint → 4/4 contracts kept
- [ ] pytest tests/ → 100% passed
- [ ] pre-commit 钩子配置完成
- [ ] .cursorrules 更新完成

## M2 验收清单

- [ ] 测试覆盖率 ≥ 60%
- [ ] 核心模块覆盖率 ≥ 90%
- [ ] 新增测试 ≥ 500 行
- [ ] E2E 测试覆盖关键路径

## M3 验收清单

- [ ] 代码量 ≤ 30,000 行
- [ ] 每个重构有 SPEC.md
- [ ] 重构后功能对比通过
- [ ] 无回归测试失败

## M4 验收清单

- [ ] 性能测试 P99 < 200ms
- [ ] 安全扫描 0 高危漏洞
- [ ] API 文档 100% 覆盖
- [ ] 监控指标就绪
```

---

## 七、风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| LangGraph 依赖冲突 | 高 | 中 | 锁定版本，必要时降级 |
| 重构引入回归 | 中 | 高 | 充分测试，灰度发布 |
| 测试覆盖目标过高 | 中 | 低 | 动态调整目标 |
| 团队时间不足 | 高 | 高 | 自动化工具，减少人工 |

---

## 八、附录

### A. 相关文档

- [SprintCycle SDD 评估报告](./docs/sdd-evaluation-report.md)
- [Speckit Skill Guide](./docs/SPECKIT_SKILL_GUIDE.md)
- [架构不变量文档](./sprintcycle/docs/ARCHITECTURE_INVARIANTS.md)

### B. 工具清单

| 工具 | 用途 | 状态 |
|------|------|------|
| Ruff | 代码质量 | ✅ 已集成 |
| Import-Linter | 架构合规 | ✅ 已集成 |
| sdd-framework | Spec 漂移 | ⏳ 待集成 |
| pytest-cov | 覆盖率 | ✅ 已集成 |
| pre-commit | 钩子 | ⏳ 待配置 |
| Bandit | 安全扫描 | ⏳ 待集成 |
| Sphinx | 文档 | ⏳ 待集成 |

### C. 参考资料

- [Spec-Kit](https://github.com/github/spec-kit)
- [sdd-framework](https://github.com/...)
- [Import Linter](https://import-linter.readthedocs.io/)
