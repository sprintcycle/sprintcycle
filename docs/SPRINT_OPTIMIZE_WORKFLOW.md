# SprintCycle Optimize Workflow (full reference / 完整参考)

> Canonical workflow for `/sprint optimize`.  
> 规范工作流，对应 `/sprint optimize`。  
> SDD methodology: `docs/SPRINT_SDD_GATES.md` · `docs/SPRINTCYCLE_CONSTITUTION.md` · `sprintcycle-workflow.mdc`

---

## §0 SDD gates (methodology layer / 方法论层)

Unified SDD path for all substantive work (speckit retired 2026-06-18).  
统一 SDD 路径（speckit 已于 2026-06-18 退役）。

### §0.1 Workflow entries

| Entry | Use for |
|-------|---------|
| **`/sprint sdd`** | Scope, L/F grade, principle review |
| **`/sprint optimize`** | This workflow — medium+ refactors |
| **`/sprint evolve`** | Detection → gates → optimize |
| `docs/sdd-designs/YYYY-MM-DD/` | PRD + plan (+ optional tasks) |

Historical speckit output: `docs/archive/specs/` (read-only).

### §0.2 Pre-Phase 1 (mandatory for this workflow)

1. **Grade** — confirm L2 or L3 (this workflow is not for L1 polish)
2. **Impact surface** — Dashboard, API, SDK, `LifecycleContract`, domain layers, tests, docs
3. **Change list `C1…`** — each item tagged with one principle (Rational / Experience / Long-term / Thorough)
4. **Initial vs suggested scope** — if suggested > initial, HITL before PRD
5. **Document sink** — `docs/sdd-designs/YYYY-MM-DD/` (template: `docs/templates/sdd-feature-template.md`)

### §0.3 Post-plan review (before Phase 3)

After PRD + technical plan (Phase 1–2), run **three-layer review** per `docs/SPRINT_SDD_GATES.md` §6:

- ① Complete (non-goals, rollback, T-xxx)
- ② Four-principle review + fix docs in place
- ③ Implementable (file map, tests, revert)

Output the **principle review table** in the agent reply; block Phase 3 until ②③ pass or only HITL items remain.

### §0.4 Closure (after Phase 6)

One-line principle conclusion required:

```text
Closure: Rational ✅ · Experience ✅ · Long-term ✅ · Thorough ✅ — <one sentence>
```

---

## 适用范围

本工作流适用于以下**中等以上优化需求**：

| 需求类型 | 复杂度 | 是否适用 |
|---------|--------|----------|
| 字段整合/删减 | 中 | ✅ |
| DDD 架构治理 | 中 | ✅ |
| 兼容逻辑删除 | 中 | ✅ |
| 前后端契约对齐 | 中 | ✅ |
| 核心模块重构 | 高 | ✅ |
| 架构演进 | 高 | ✅ |
| 性能优化 | 中 | ✅ |
| 安全加固 | 中 | ✅ |

**简单修复（如单文件bug fix）** 可直接处理，无需走此工作流。

## 工作流触发

### 触发方式

1. **Command trigger**（推荐）
   ```
   /sprint optimize
   ```

2. **触发词识别**
   - 「删减字段」
   - 「遵循 DDD 治理」
   - 「删除兼容逻辑」
   - 「优化架构」
   - 「精简代码」
   - 「前后端对齐」
   - 「重构」
   - 「性能优化」
   - 「安全加固」

## 工作流阶段

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SprintCycle 优化工作流                          │
├─────────────────────────────────────────────────────────────────────┤
│  Phase 1: 需求分析 → Phase 2: 方案设计 → Phase 3: 执行实施          │
│         ↓                    ↓                    ↓                 │
│  Phase 4: 测试验证 ←→ Phase 5: 文档同步 → Phase 6: 审批提交        │
│                       ↑                                             │
│              [可并行执行]                                           │
└─────────────────────────────────────────────────────────────────────┘
```

**阶段依赖说明：**
- **顺序执行**：Phase 1 → Phase 2 → Phase 3 → Phase 4/5 → Phase 6
- **并行执行**：Phase 4（测试验证）与 Phase 5（文档同步）可并行进行
- **回滚机制**：每个阶段都支持退出并回滚到上一阶段

---

## Phase 1: 需求分析（必须）

### 1.1 理解业务背景与用户确认

- [ ] 与需求提出者确认优化目标和预期收益
- [ ] 分析现有代码结构和业务逻辑
- [ ] 识别受影响的模块和调用链

#### 1.1.1 用户需求确认（必须）

> **要求：在需求分析阶段，如果有任何疑问，必须向用户提问确认！**

**确认清单：**
- [ ] 优化目标是否明确？
- [ ] 影响范围是否需要调整？
- [ ] 优先级和时间要求是否明确？
- [ ] 是否有其他隐含需求？

**使用工具：** 使用 `AskUserQuestion` 工具向用户提出结构化的问题确认清单。

### 1.2 影响范围评估

> **SDD gate**: Complete §0.2 impact surface + `C1…` change list before finishing Phase 1. (须完成 §0.2 影响面与变更点清单。)

| 评估维度 | 检查项 | 风险等级 |
|---------|--------|----------|
| **业务影响** | 是否影响核心业务流程？ | 高/中/低 |
| **代码范围** | 涉及多少文件/模块？ | 高/中/低 |
| **前后端关联** | 是否需要同步修改前端？ | 是/否 |
| **外部依赖** | 是否影响外部系统集成？ | 是/否 |
| **测试覆盖** | 现有测试是否覆盖变更点？ | 是/部分/否 |

### 1.3 生成 PRD 需求文档（必须）

基于需求分析，生成完整的 PRD（产品需求文档），包含：
- 问题描述
- 影响范围
- 风险评估
- 业务目标
- 用户价值
- 非功能性需求

#### 1.3.1 PRD HITL 确认（必须）

> **要求：PRD 生成后，必须经过人工（Human-in-the-loop）确认和修改后方可进入方案设计阶段！**

**确认流程：**
```
AI 生成 PRD
    ↓
用户审查
    ↓
┌────────────────────────────────┐
│ 用户反馈（三选一）              │
├─ 批准 → 进入 Phase 2 方案设计   │
├─ 修改 → AI 更新 PRD → 重新审查 │
└─ 拒绝 → 中止工作流，记录原因    │
└────────────────────────────────┘
```

**反馈处理规则：**
| 用户反馈 | 处理方式 |
|---------|---------|
| **批准** | 立即进入 Phase 2 方案设计阶段 |
| **修改** | 根据用户意见更新 PRD，重新提交审查 |
| **拒绝** | 中止工作流，记录拒绝原因，生成终止报告 |

**PRD 确认清单：**
- [ ] 需求描述是否准确完整？
- [ ] 业务逻辑是否完整保留？
- [ ] 预期收益是否明确？
- [ ] 风险评估是否充分？

**使用工具：** PRD 生成后，使用 `AskUserQuestion` 工具向用户呈现以下选项：
1. 批准并进入方案设计阶段
2. 需要修改，请说明修改意见
3. 拒绝此 PRD，中止工作流

---

## Phase 2: 方案设计（必须）

### 2.1 架构合规性检查

对照 [sprintcycle-architecture-orchestration.mdc](file:///Users/liangzai/CursorProjects/sprintcycle/.cursor/rules/sprintcycle-architecture-orchestration.mdc)：

- [ ] 符合 DDD 六边形架构原则
- [ ] 保持领域层纯粹性
- [ ] 遵循组合根模式
- [ ] 保持聚合根不可变性

### 2.2 方案设计原则（必须遵守）

> **核心要求：不要留兼容逻辑，直接推进到终态、长期方案；保证业务逻辑不丢！**

- ✅ 直接实现终态方案，不添加过渡或兼容代码
- ✅ 一次性更新所有调用点（前端 + 后端）
- ✅ 保留完整业务逻辑，不丢失功能
- ✅ 设计长期可维护的架构方案

根据优化类型选择方案模板：

#### 方案类型 A：字段整合

1. 识别语义相关的字段组
2. 设计统一的上下文结构（终态方案）
3. 一次性更新所有调用点（前端 + 后端），**不添加兼容代码**
4. 保证业务逻辑完整保留

#### 方案类型 B：DDD 治理

1. 识别架构违规模式
2. 设计合规的长期改进方案
3. 确保边界清晰
4. 一次性重构到位，**不留过渡兼容逻辑**

#### 方案类型 C：兼容逻辑清理

1. 定位所有兼容辅助方法
2. 识别所有调用点
3. 直接替换为终态调用方式
4. **彻底移除兼容代码**

#### 方案类型 D：前后端对齐

1. 确定后端 DTO 终态结构
2. 一次性同步更新前端 API/类型/Store
3. **不留任何兼容适配代码**
4. 保证数据流转的一致性

### 2.3 变更清单

| 模块 | 文件路径 | 变更类型 | 负责人 | 预计工时 |
|------|---------|----------|--------|----------|
| 后端领域层 | `sprintcycle/domain/core/` | 修改/新增/删除 | | |
| 后端应用层 | `sprintcycle/application/services/` | 修改/新增/删除 | | |
| 后端接口层 | `sprintcycle/interfaces/http/` | 修改/新增/删除 | | |
| 前端 API | `frontend/src/api/` | 修改/新增/删除 | | |
| 前端类型 | `frontend/src/types/` | 修改/新增/删除 | | |
| 前端 Store | `frontend/src/stores/` | 修改/新增/删除 | | |
| 前端视图 | `frontend/src/views/` | 修改/新增/删除 | | |

### 2.4 输出文档

- **优化方案设计文档**（包含：架构图、变更清单、迁移计划）

### 2.5 HITL 技术方案确认（必须）

> **要求：技术方案生成后，必须经过人工（Human-in-the-loop）确认和修改后方可执行！**

#### 2.5.1 确认流程

```
AI 生成技术方案
    ↓
用户审查
    ↓
┌────────────────────────────────┐
│ 用户反馈（三选一）              │
├─ 批准 → 进入 Phase 3 执行实施   │
├─ 修改 → AI 更新方案 → 重新审查  │
└─ 拒绝 → 中止工作流，记录原因    │
└────────────────────────────────┘
```

**反馈处理规则：**
| 用户反馈 | 处理方式 |
|---------|---------|
| **批准** | 立即进入 Phase 3 执行实施阶段 |
| **修改** | 根据用户意见更新技术方案，重新提交审查 |
| **拒绝** | 中止工作流，记录拒绝原因，生成终止报告 |

#### 2.5.2 确认要点

**技术方案确认清单：**
- [ ] 架构方案是否合理？
- [ ] 变更范围是否可接受？
- [ ] 风险评估是否充分？
- [ ] 是否有其他技术选型建议？
- [ ] 实施计划是否可行？

**使用工具：** 生成方案后，使用 `AskUserQuestion` 工具向用户呈现以下选项：
1. 批准并进入执行实施阶段
2. 需要修改，请说明修改意见
3. 拒绝此方案，中止工作流

#### 2.5.3 SDD principle review (must / 必须)

Before Phase 3, run `docs/SPRINT_SDD_GATES.md` §6 three-layer review on PRD + technical plan. Output the principle review table in the agent reply. (进入 Phase 3 前须完成原则审查表。)

---

## Phase 3: 执行实施（必须）

### 3.1 执行实施原则（必须遵守）

> **核心要求：不要留兼容逻辑，直接推进到终态、长期方案；保证业务逻辑不丢！**

- ✅ 一次性更新所有相关代码，**不添加过渡兼容代码**
- ✅ 前后端同步变更，**不留任何版本适配层**
- ✅ 彻底移除旧的代码结构和逻辑
- ✅ 确保业务逻辑 100% 完整保留
- ✅ 所有测试必须通过验证

### 3.2 后端变更流程

```
领域层（终态） → 应用层（终态） → DTO（终态） → HTTP路由（终态） → 测试
```

1. **领域层**：修改聚合根、值对象、领域服务（一次性到终态）
   - 确保 `@dataclass(frozen=True)` 不可变性
   - 更新 `domain/ports/` 端口定义
   - **彻底移除旧的结构和兼容代码**

2. **应用层**：更新服务实现和 DTO（一次性到终态）
   - 保持组合根纯净性
   - 确保 DTO 与前端类型对齐
   - **不添加兼容转换方法**

3. **接口层**：更新 HTTP 路由和 handlers（一次性到终态）
   - 使用一致的命名约定
   - **不保留旧的 API 版本或兼容路由**

### 3.3 前端变更流程

```
API定义（终态） → TypeScript类型（终态） → Store（终态） → 视图组件（终态） → 验证
```

1. **API 层**：更新 `frontend/src/api/` 接口定义（一次性到终态）
   - 与后端 DTO 保持一致
   - **彻底移除旧的接口定义**

2. **类型层**：更新 `frontend/src/types/` 类型定义（一次性到终态）
   - 镜像后端领域模型
   - **不保留旧类型或兼容定义**

3. **Store 层**：更新状态管理（一次性到终态）
   - 与后端聚合根对齐
   - **不添加迁移或兼容逻辑**

4. **视图层**：更新组件（一次性到终态）
   - 确保数据展示正确

### 3.4 变更检查清单

- [ ] 所有旧的兼容代码已彻底移除
- [ ] 业务逻辑 100% 保留
- [ ] 前后端完全同步，无版本差异
- [ ] 没有添加任何过渡代码
- [ ] 所有测试通过

---

## Phase 4: 测试验证（必须）

### 4.1 后端测试

- [ ] 运行相关 pytest 测试
- [ ] 确保所有测试通过
- [ ] 验证业务逻辑完整性

### 4.2 前端测试

- [ ] 运行 TypeScript 类型检查
- [ ] 运行 Playwright 端到端测试（如有）
- [ ] 手动验证关键功能

### 4.3 集成测试

- [ ] 验证前后端接口通信
- [ ] 验证数据流完整性
- [ ] 验证错误处理机制

### 4.4 性能测试（如适用）

- [ ] 基准性能测试
- [ ] 对比优化前后指标
- [ ] 确保性能达标

---

## Phase 5: 文档同步（必须）

⚠️ **代码变更后必须立即更新文档！**

### 5.1 文档更新清单

| 文档 | 路径 | 更新内容 |
|------|------|----------|
| README.md | `/README.md` | 产品定义、字段结构、架构描述 |
| README_EN.md | `/README_EN.md` | 镜像 README.md 变更 |
| ARCHITECTURE_INVARIANTS.md | `/docs/ARCHITECTURE_INVARIANTS.md` | 架构边界、DDD 模式、层职责 |
| sprintcycle-architecture-orchestration.mdc | `.cursor/rules/sprintcycle-architecture-orchestration.mdc` | DDD 子域、聚合根定义 |

### 5.2 文档更新检查

- [ ] README.md 字段描述与代码一致
- [ ] README_EN.md 与 README.md 对齐
- [ ] ARCHITECTURE_INVARIANTS.md 边界与代码一致
- [ ] sprintcycle-architecture-orchestration.mdc 与代码实现对齐

---

## Phase 6: 审批提交（必须）

### 6.1 代码审查

- [ ] 提交 Pull Request
- [ ] 指定至少 2 位 reviewer
- [ ] 确保代码符合架构规范
- [ ] 确保测试覆盖率达标

### 6.2 审批流程

| 审批环节 | 责任人 | 审批内容 |
|---------|--------|----------|
| 技术负责人 | 架构师 | 架构合规性 |
| 业务负责人 | 产品经理 | 业务逻辑正确性 |
| QA负责人 | 测试主管 | 测试覆盖完整性 |

### 6.3 提交规范

**提交信息格式：**
```
[优化类型] 简明描述变更内容

详细描述：
- 变更原因
- 主要修改
- 影响范围

验证结果：
- 后端测试：✅/❌
- 前端测试：✅/❌
- 文档更新：✅/❌
```

**示例：**
```
[字段整合] 整合 lifecycle 中 skill 相关字段

详细描述：
- 将 skill_refs、skill_matches、skill_review_checklists、skill_trace 整合为 skill_context
- 更新领域模型、DTO、HTTP 路由
- 同步更新前端 API、类型和 Store

验证结果：
- 后端测试：✅ 全部通过
- 前端测试：✅ 全部通过
- 文档更新：✅ README.md、ARCHITECTURE_INVARIANTS.md
```

---

## Phase 7: 退出与回滚机制（可选）

### 7.1 退出时机

用户可在以下阶段选择退出工作流：

| 阶段 | 退出后果 | 回滚操作 |
|------|---------|---------|
| Phase 1 | 无代码变更 | 无需回滚 |
| Phase 2 | 无代码变更 | 无需回滚 |
| Phase 3 | 代码已修改 | 执行 git 回滚 |
| Phase 4 | 测试中 | 执行 git 回滚 |
| Phase 5 | 文档已更新 | 回滚代码和文档 |
| Phase 6 | PR 已提交 | 关闭 PR，回滚代码 |

### 7.2 退出流程

```
用户请求退出
    ↓
确认退出意图
    ↓
┌────────────────────────────────┐
│ 是否有未提交的代码变更？        │
├─ 是 → 执行 git rollback        │
│       ↓                        │
├─ 否 → 生成终止报告              │
│       ↓                        │
└──→ 通知用户，工作流结束         │
└────────────────────────────────┘
```

### 7.3 回滚操作说明

**代码回滚：**
```bash
# 回滚所有未提交的更改
git checkout .

# 如果已提交但未推送
git reset --hard HEAD
```

**文档回滚：**
- 与代码回滚同步执行
- 确保文档恢复到优化前状态

### 7.4 终止报告内容

退出工作流时生成终止报告，包含：
- 终止阶段
- 终止原因
- 已完成的工作
- 已修改的文件列表
- 建议的后续操作

---

## 验证清单汇总

> **Unified source**: `sprintcycle-workflow.mdc` and `docs/CURSOR_OPTIMIZATION_RULES.md`

| 阶段 | 检查项 | 状态 |
|------|--------|------|
| **Phase 1: 需求分析** | SDD §0.2 影响面 + C1… + 初述 vs 建议范围 | [ ] |
| **Phase 1: 需求分析** | 用户需求已通过 AskUserQuestion 确认 | [ ] |
| **Phase 1: 需求分析** | 影响范围评估完成 | [ ] |
| **Phase 1: 需求分析** | 风险评估已记录 | [ ] |
| **Phase 2: 方案设计** | SDD §6 原则审查表已输出且 ②③ 通过 | [ ] |
| **Phase 2: 方案设计** | PRD 已通过 HITL 批准 | [ ] |
| **Phase 2: 方案设计** | 技术方案已通过 HITL 批准 | [ ] |
| **Phase 2: 方案设计** | 架构合规性检查通过 | [ ] |
| **Phase 3: 执行实施** | 代码编译无误（Python + TypeScript） | [ ] |
| **Phase 3: 执行实施** | 业务逻辑 100% 保留 | [ ] |
| **Phase 3: 执行实施** | 未添加任何兼容代码或过渡层 | [ ] |
| **Phase 4: 测试验证** | 相关测试通过（pytest + 前端测试） | [ ] |
| **Phase 4: 测试验证** | 测试覆盖率 ≥80% | [ ] |
| **Phase 5: 文档同步** | 4 个文档已更新并对齐 | [ ] |
| **Phase 6: 审批提交** | PR 创建完成，审核人已指定 | [ ] |
| **Phase 6: 审批提交** | CI/CD 流水线通过 | [ ] |
| **Closure** | §0.4 一行原则结论已输出 | [ ] |

---

## 核心原则

### 必须遵守

- ✅ 保持业务逻辑完整（100% 保留）
- ✅ 遵循 DDD + 六边形架构
- ✅ **不要留兼容逻辑，直接推进到终态、长期方案**
- ✅ **一次性更新所有调用点，不添加过渡代码**
- ✅ **彻底移除旧的代码结构和兼容代码**
- ✅ 测试全部通过
- ✅ 前后端同步变更
- ✅ 文档及时更新
- ✅ **需求分析阶段有疑问必须向用户确认**
- ✅ **PRD 必须经过 HITL 确认后才能进入方案设计**
- ✅ **技术方案必须经过 HITL 确认后方可执行**

### 禁止行为

- ❌ 不要破坏现有功能
- ❌ 不要引入架构违规
- ❌ 不要删除未验证的业务逻辑
- ❌ 不要忽略测试失败
- ❌ 不要前后端变更不同步
- ❌ 不要跳过审批流程
- ❌ **不要添加任何兼容逻辑或过渡代码**
- ❌ **不要保留旧的 API 版本或兼容路由**
- ❌ **不要在需求不明确时继续执行**
- ❌ **不要在 PRD 未经 HITL 确认时进入方案设计**
- ❌ **不要在技术方案未经 HITL 确认时执行**

---

## 工作流输出模板

```markdown
## 优化方案报告

### 一、需求分析

**问题描述：**
...

**影响范围：**
- 后端模块：...
- 前端模块：...
- 外部依赖：...

**风险评估：**
- 高风险点：...
- 缓解措施：...

**用户需求确认：** ✅ 已完成
- 确认清单项 1：✅
- 确认清单项 2：✅
- ...

### 二、PRD 生成与确认

**PRD 文档：**
- 业务目标：...
- 用户价值：...
- 非功能性需求：...

**PRD HITL 确认：** ✅ 已完成
- 用户反馈：...
- PRD 调整记录：...

### 三、方案设计

**架构合规性：**
- ✅/❌ 符合 DDD 六边形架构
- ✅/❌ 领域层纯粹性
- ✅/❌ 聚合根不可变性

**终态方案检查：**
- ✅/❌ 方案不包含任何兼容逻辑
- ✅/❌ 方案是长期可维护的终态设计
- ✅/❌ 业务逻辑 100% 保留

**变更清单：**
| 模块 | 文件路径 | 变更类型 |
|------|---------|----------|
| ... | ... | ... |

**HITL 技术方案确认：** ✅ 已完成
- 用户反馈：...
- 方案调整记录：...

### 四、执行记录

**实施原则：**
- 不添加任何兼容逻辑
- 直接推进到终态方案
- 前后端同步变更
- 业务逻辑 100% 保留

**实施顺序：**
1. ...
2. ...
3. ...

**兼容代码检查：**
- ✅/❌ 已彻底移除所有旧的兼容代码
- ✅/❌ 没有添加任何过渡代码
- ✅/❌ 前后端完全同步，无版本差异

### 五、验证结果

**后端测试：** ✅/❌
**前端测试：** ✅/❌
**集成测试：** ✅/❌
**性能测试：** ✅/❌（如适用）

### 六、文档更新

- [ ] README.md
- [ ] README_EN.md
- [ ] ARCHITECTURE_INVARIANTS.md
- [ ] sprintcycle-architecture-orchestration.mdc

### 七、审批状态

| 审批环节 | 状态 | 审批人 |
|---------|------|--------|
| 技术负责人 | ✅/❌ | ... |
| 业务负责人 | ✅/❌ | ... |
| QA负责人 | ✅/❌ | ... |
```
