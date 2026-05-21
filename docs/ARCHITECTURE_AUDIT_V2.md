# SprintCycle 架构审计报告 v2.0

> 版本: v2.0
> 日期: 2026-05-21
> 状态: 审计完成

---

## 一、架构总览

### 1.1 代码规模

| 指标 | 数值 |
|------|------|
| 源码总行数 | 38,097 行 |
| 测试总行数 | 8,802 行 |
| 总计 | 46,899 行 |
| Python 模块数 | ~250+ |
| 测试用例数 | 487+ |

### 1.2 架构分层

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          SprintCycle 架构分层 v2.0                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                                             ┃
┃  L7: 接口层 (Interface)                                    390 行          ┃
┃  ├── api.py (929行) - 统一API门面                                             ┃
┃  ├── cli.py (84行) - 命令行接口                                               ┃
┃  └── dashboard/ - Web UI                                                     ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  L6: 应用服务层 (Application)                              5,674 行        ┃
┃  ├── sprint_orchestrator.py (514行) - Sprint编排核心                            ┃
┃  ├── services/ - 业务服务 (lifecycle, suggestion, evolution等)                 ┃
┃  └── release_plan/ - 发布计划                                                 ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  L5: 领域层 (Domain)                                      5,982 行        ┃
┃  ├── domain/evolution/ - 版本演进 (1839行)                                     ┃
┃  ├── domain/errors/ - 错误处理 (551行)                                         ┃
┃  ├── domain/intent/ - 意图解析                                                 ┃
┃  ├── domain/fitness/ - 健康评估                                               ┃
┃  ├── domain/quality_spec/ - 质量规格                                           ┃
┃  └── domain/prompts/ - Prompt模板                                            ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  L4: 执行层 (Execution)                                   12,299 行       ┃
┃  ├── sprint_executor.py (939行) - Sprint执行核心                                ┃
┃  ├── feedback.py (555行) - 反馈循环                                            ┃
┃  ├── agents/ - AI Agent实现                                                   ┃
┃  ├── planners/ - 计划生成                                                     ┃
┃  └── hooks/ - 生命周期钩子                                                    ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  L3: 治理层 (Governance)                                  7,123 行        ┃
┃  ├── runner.py (628行) - 治理运行器                                           ┃
┃  ├── hitl/ - 人机回环                                                        ┃
┃  ├── versioning/ - 版本控制                                                   ┃
┃  └── suggestion/ - 建议管理                                                   ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  L2: 基础设施层 (Infrastructure)                        3,497 行          ┃
┃  ├── config/ - 配置管理                                                          ┃
┃  ├── persistence/ - 持久化                                                      ┃
┃  ├── mq/ - 消息队列                                                            ┃
┃  └── sandbox/ - 沙箱管理                                                       ┃
┃                                    │                                        ┃
┃                                    ▼                                        ┃
┃  L1: 观测层 (Observability)                             1,021 行          ┃
┃  ├── diagnostics/ - 诊断                                                         ┃
┃  └── runtime/ - 运行时观测                                                      ┃
┃                                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 二、架构改进 (Phase 1-5 完成)

### 2.1 已完成重构

| Phase | 提交 | 内容 | 代码变化 |
|-------|------|------|----------|
| Phase 1 | `5820b6a` | Legacy清理 | -272行 |
| Phase 2 | `68fa792` | 协议定义 + 统一导出 | +85行 |
| Phase 3 | `5e3f3c6` | Error下沉到领域层 | 0行 |
| Phase 4 | `cd05b2a` | Evolution三层归一 | 0行 |
| Phase 5 | `49d9daf` | 合并重复validator | -185行 |
| **总计** | | | **-372行** |

### 2.2 架构改进前后对比

**Before:**
```
L5: domain/evolution (三层分散)
L6: application/evolution (1839行冗余)
L4: execution/error_knowledge (领域逻辑在执行层)
```

**After:**
```
L5: domain/evolution (统一) ✅
L5: domain/errors (下沉) ✅
L6: application (纯编排) ✅
```

---

## 三、架构健康度评估

### 3.1 分层指标

| 指标 | 评分 | 说明 |
|------|------|------|
| 分层清晰度 | 8/10 | L5→L4→L3→L2→L1 单向依赖良好 |
| 模块内聚 | 7/10 | domain/evolution 已归一 |
| 可测试性 | 7/10 | 487+测试用例 |
| 可维护性 | 7/10 | 协议定义提升可维护性 |
| 可扩展性 | 8/10 | 模块化设计良好 |

**综合评分: 7.4/10**

### 3.2 架构违规清单

| 违规 | 位置 | 严重度 |
|------|------|--------|
| L5引用L6 | domain/evolution/default.py → application | 中 |
| L5引用L6 | domain/fitness/evaluator.py → application | 中 |
| L5引用L6 | domain/intent/base.py → application | 低 |

---

## 四、问题与建议

### 4.1 需要修复的架构违规

**问题1: domain/evolution 引用 application**
```python
# sprintcycle/domain/evolution/default.py
from sprintcycle.application.release_plan.validator import ReleasePlanValidator
from sprintcycle.execution.planners.generator import IntentReleasePlanGenerator
```

**建议修复方案:**
1. 将 `ReleasePlanValidator` 迁移到 `domain/quality_spec/`
2. 通过依赖注入解耦
3. 验证所有测试通过

### 4.2 大文件清单 (需重构)

| 文件 | 行数 | 建议 |
|------|------|------|
| sprint_executor.py | 939 | 拆分为执行策略 |
| api.py | 929 | 拆分为多个Facade |
| runner.py | 628 | 提取配置和常量 |
| feedback.py | 555 | 提取反馈策略 |

### 4.3 代码量目标

| 阶段 | 目标 | 当前 | 差距 |
|------|------|------|------|
| Phase 6 | 35,000 | 38,097 | -3,097 |
| Phase 7 | 30,000 | 38,097 | -8,097 |

---

## 五、测试验证

```
✅ test_evolution_rollback_manager: 34 passed
✅ test_lifecycle_end_to_end: 12 passed
✅ test_application_protocols: 4 passed
✅ test_prompt_sources: 3 passed
✅ test_error_handling: 8 passed
总计: 61+ passed
```

---

## 六、后续优化路径

### Phase 6: 修复架构违规 (1周)
- [ ] 将 ReleasePlanValidator 迁移到 domain
- [ ] 修复 domain → application 引用
- [ ] 验证所有测试通过

### Phase 7: 大文件重构 (2周)
- [ ] 拆分 sprint_executor.py (策略模式)
- [ ] 拆分 api.py (Facade分离)
- [ ] 提取硬编码常量到配置

### Phase 8: 代码精简 (持续)
- [ ] 移除死代码
- [ ] 合并相似模块
- [ ] 优化重复逻辑

---

## 七、Git 提交历史

```
49d9daf Phase 5: 合并重复的 validator.py
cd05b2a Phase 4: Evolution 三层归一到 domain/evolution
5e3f3c6 Phase 3: 执行层错误处理重构下沉到领域层
68fa792 Phase 2: Application Layer 协议定义 + 统一导出
5820b6a Phase 1: 架构清理 - 重命名legacy为prompts + 删除versioning_legacy
```
