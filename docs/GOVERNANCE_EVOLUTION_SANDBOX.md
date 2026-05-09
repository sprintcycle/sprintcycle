# SprintCycle 进化沙盒隔离、Git 备份与回滚设计

> 版本：SprintCycle 进化控制面设计稿
> 适用范围：多轮 sprint 下的 SprintCycle 自进化、用户需求进化
> 目标：在不侵入主体架构的前提下，实现沙盒隔离、Git 备份、可验证发布与可回滚部署

---

## 1. 背景与目标

SprintCycle 需要同时支持两类进化场景：

1. **场景一：通过多轮 sprint 自进化 SprintCycle**
   - 进化对象：代码、配置、治理规则、模块边界、执行策略
   - 目标：让 SprintCycle 自身持续变强，但不影响当前运行中的稳定实例

2. **场景二：通过多轮 sprint 进化用户需求**
   - 进化对象：intent、release plan、spec、acceptance criteria、backlog
   - 目标：让需求随着 sprint 反馈持续演化，并保持可审计、可回溯、可验证

两类场景必须遵守同一原则：

> **统一的是“循环”和“治理框架”，不同的是“被进化的对象”和“产物落点”。**

### 1.1 设计目标

- 对 SprintCycle 主体架构**低侵入**
- 模块**高内聚、低耦合**
- 尽量复用成熟开源方案，减少自建
- 进化过程必须**沙盒隔离**
- 候选版本必须**先验证、后发布**
- 所有产物必须可**Git 备份**、可**回滚**、可**审计**
- 自进化不得影响正在运行的 SprintCycle；只有部署新版本时才允许升级 / 重载生效

---

## 2. 总体设计原则

### 2.1 统一 sprint 生命周期

两类进化都通过同一条生命周期链路运转：

```text
Intake → Plan → Sandbox → Validate → Promote → Observe → Rollback
```

含义如下：

- **Intake**：接收反馈、缺陷、需求变化、治理信号、指标异常
- **Plan**：构造候选演化目标与验证计划
- **Sandbox**：在独立工作区 / 容器 / 依赖环境中执行
- **Validate**：跑测试、静态检查、治理门禁、契约校验
- **Promote**：通过后生成可发布版本并切换版本指针
- **Observe**：记录事件、报告、历史与审计信息
- **Rollback**：必要时回退到上一个稳定版本

### 2.2 控制面与执行面分离

- **进化控制面**：负责识别对象、创建沙盒、验证候选、决定发布 / 回滚
- **Sprint 执行面**：负责正常 sprint 执行，不感知进化内部细节

### 2.3 Active / Candidate 分离

系统至少维护三类版本语义：

- `active`：当前稳定运行版本
- `candidate`：沙盒中的候选版本
- `rollback_point`：最近一次稳定点

candidate 只能在沙盒中存在，不能直接影响 active。

### 2.4 版本化优先于原地修改

所有进化都应产出明确版本：

- Git commit
- Git tag
- worktree
- manifest
- 镜像 tag
- checkpoint / state snapshot

不要通过原地覆盖文件来实现“回滚”。

### 2.5 对象差异外置

统一生命周期中，只区分两种演化对象：

- **代码自进化对象**：实现、配置、规则、模块边界
- **需求进化对象**：intent、release plan、spec、backlog

这类差异不进入主执行链路，而是放到适配层处理。

---

## 3. 总体架构

### 3.1 架构图

```text
┌──────────────────────────────────────────────────────────────┐
│                        外部输入层                             │
│ 用户反馈 / Sprint 结果 / 缺陷 / 指标 / 业务变化 / 人工修正    │
└──────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│                     进化控制面 Evolution Control Plane       │
│ - 识别进化类型：Code / Requirement                          │
│ - 生成候选目标                                             │
│ - 创建沙盒                                                │
│ - 驱动验证                                                │
│ - 决定 promote / rollback                                 │
│ - 管理版本指针                                            │
└──────────────────────────────────────────────────────────────┘
                 ┌───────────────────────────┴───────────────────────────┐
                 ↓                                                       ↓
┌────────────────────────────────────┐       ┌────────────────────────────────────┐
│ 代码自进化适配层                   │       │ 用户需求进化适配层                 │
│ Code Evolution Adapter             │       │ Requirement Evolution Adapter      │
│ - 修改代码 / 配置                  │       │ - 演化 intent                      │
│ - 调整治理规则                     │       │ - 演化 release plan                │
│ - 重构模块边界                     │       │ - 演化 spec / acceptance           │
│ - 生成代码补丁                     │       │ - 演化 backlog                     │
└────────────────────────────────────┘       └────────────────────────────────────┘
                 ↓                                                       ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                         统一 Sprint 主循环                                   │
│ Intake → Plan → Sandbox → Validate → Promote → Observe → Rollback          │
│                                                                              │
│ 统一治理：governance                                                        │
│ 统一编排：orchestration / execution                                         │
│ 统一观测：events / reports / history                                        │
│ 统一回滚：git tag / commit / manifest / checkpoint                          │
└──────────────────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│                  Active SprintCycle 稳定运行实例             │
│ - 固定版本                                                │
│ - 不被 candidate 影响                                     │
│ - 只消费已发布稳定产物                                   │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 核心结论

- **统一 sprint 循环**：两类场景走同一套生命周期
- **统一治理框架**：用同一套治理、验证、观测、回滚机制
- **对象差异外置**：通过适配层区分代码与需求，不污染主链路

---

## 4. 两类进化场景

### 4.1 场景一：多轮 sprint 自进化 SprintCycle

#### 被进化对象

- `api`
- `governance`
- `orchestration`
- `execution`
- `release_plan`
- `config`
- 规则、策略、模块边界

#### 产物落点

- Git commit
- Git tag
- 可选 release branch
- 可选镜像 tag
- 新部署版本

#### 典型流程

1. 识别框架改进机会
2. 进入 candidate sandbox
3. 修改 SprintCycle 代码 / 配置 / 规则
4. 跑测试、静态分析、治理门禁
5. 生成 candidate 版本
6. 验证通过后 promote
7. 新版本仅对后续部署生效
8. 旧版本保留可回滚

### 4.2 场景二：多轮 sprint 进化用户需求

#### 被进化对象

- intent
- release plan
- spec
- acceptance criteria
- backlog

#### 产物落点

- 新需求版本
- 新计划版本
- 新规格版本
- 新任务版本

#### 典型流程

1. 收集 sprint 反馈与偏差
2. 识别为需求演化
3. 进入 candidate sandbox
4. 生成或修订需求版本
5. 做可测性、可切片性、依赖关系、治理检查
6. 形成需求候选版本
7. 通过后写回 backlog / release plan
8. 进入下一轮 sprint

---

## 5. 沙盒隔离设计

沙盒隔离的目标是：**candidate 在独立环境中生成和验证，绝不污染 active 实例。**

### 5.1 隔离层次

#### A. 代码空间隔离

推荐复用：

- `git worktree`
- 独立目录沙盒
- 独立分支 / commit

优点：

- 原生 Git 支持
- 适合多版本并行
- 方便 diff、审计、回滚

#### B. 进程隔离

candidate 的验证应在独立进程中运行，必要时放入容器中。

推荐复用：

- Docker
- Docker Compose

#### C. 依赖隔离

每个 candidate 使用独立依赖环境：

- Python `venv` 或 `uv`
- 锁定依赖版本
- 独立缓存目录

#### D. 文件系统隔离

候选版本仅可访问：

- 自己的 worktree
- 自己的报告目录
- 自己的缓存目录
- 只读共享依赖

禁止写入：

- 主仓库根目录
- active 运行状态库
- 其他版本工作区

### 5.2 推荐隔离组合

首期推荐：

```text
Git worktree + 独立进程 + Docker Compose（可选） + 独立 venv/uv
```

后续如需更强安全边界，可评估：

- gVisor
- Kata Containers
- Firecracker

但首期不建议直接引入这些复杂组件。

---

## 6. Git 备份与回滚设计

### 6.1 版本化策略

所有进化产物都必须形成 Git 可追踪版本。

#### 场景一：代码自进化

候选版本生成：

- commit
- tag
- 可选 release branch
- 可选镜像 tag

#### 场景二：需求进化

候选版本生成：

- release plan 版本
- spec 版本
- backlog 版本
- 变更记录

### 6.2 版本流转

```text
baseline → candidate → validated → promoted → active
                               ↓
                           rollback_point
```

### 6.3 回滚方式

回滚应基于版本指针，而不是文件级覆盖：

- 回滚到上一个 Git commit
- 回滚到上一个 Git tag
- 回滚到上一个 worktree 版本
- 回滚到上一个 manifest 指针

### 6.4 状态与代码分离回滚

需要区分两类回滚：

- **代码回滚**：恢复代码、配置、模块版本
- **状态回滚**：恢复运行状态、checkpoint、事件历史、观测记录

两者应解耦，但在回滚动作上协同。

### 6.5 推荐备份手段

- Git 原生 commit / tag / bundle
- `restic` 或 `borgbackup` 做目录级备份
- sqlite 记录版本索引与元数据

---

## 7. 统一 sprint 循环与架构整洁性

### 7.1 为什么仍然统一

两类进化如果拆成两套系统，会导致：

- 两套治理标准
- 两套报告格式
- 两套版本管理
- 两套回滚逻辑
- 两套事件模型

这会迅速破坏整洁性与一致性。

因此必须保持：

- 一套生命周期
- 一套治理体系
- 一套观测体系
- 一套版本与回滚体系

### 7.2 统一与差异的边界

#### 统一部分

- 生命周期
- 沙盒策略
- 验证门
- 版本流转
- 回滚方式
- 观测模型

#### 差异部分

- 代码自进化：改代码、配置、规则
- 需求进化：改 intent、plan、spec、backlog

### 7.3 整洁性结论

如果按“控制面 / 适配层 / 执行面”拆分，架构会比双系统方案更整洁、更一致，也更容易维护。

---

## 8. 模块拆分建议

建议新增以下模块，保持低侵入与高内聚：

```text
sprintcycle/
├── governance/
├── evolution/
├── sandbox/
├── versioning/
├── orchestration/
├── execution/
└── release_plan/
```

### 8.1 `governance`

职责：

- 统一门禁
- 统一检查包
- 统一报告与历史

要求：

- 不直接承担进化行为
- 继续作为治理域核心能力

### 8.2 `evolution`

职责：

- 识别进化目标
- 协调沙盒创建
- 组织验证和发布
- 决定 promote / rollback

要求：

- 只做控制面，不改执行器内部语义

### 8.3 `sandbox`

职责：

- worktree 管理
- 容器管理
- 环境隔离
- 缓存隔离

要求：

- 只负责隔离，不承担业务规则

### 8.4 `versioning`

职责：

- 版本索引
- `active` / `candidate` / `rollback_point` 管理
- 回滚接口

要求：

- 版本与部署指针清晰可追踪

---

## 9. 推荐复用的开源组件

### 9.1 代码与版本

- Git `worktree`
- Git `branch`
- Git `tag`
- Git `bundle`

### 9.2 沙盒与隔离

- Docker
- Docker Compose
- gVisor（可选）
- Kata Containers（可选）
- Firecracker（可选）

### 9.3 依赖管理

- `uv`
- `venv`
- `pip-tools`

### 9.4 备份与归档

- Git 原生能力
- `restic`
- `borgbackup`
- sqlite 版本索引

### 9.5 验证门

- pytest
- ruff
- mypy
- import-linter
- semgrep
- pip-audit

---

## 10. 发布与回滚机制

### 10.1 发布流程

1. candidate 生成
2. 通过验证
3. 打 commit / tag
4. 更新版本指针
5. 新部署读取新指针

### 10.2 回滚流程

1. 切回旧 commit / tag / manifest
2. 恢复对应状态快照
3. 重启或重载 active 版本

### 10.3 推荐策略

发布与回滚都应围绕“版本指针”展开，不建议用文件复制方式恢复。

---

## 11. 对 SprintCycle 主体架构的侵入性控制

### 11.1 保持不变

以下核心链路保持不变：

- `SprintCycle` 仍为唯一主入口
- `SprintOrchestrator` 继续负责调度
- `GovernanceRunner` 继续负责治理检查
- `RollbackManager` 继续负责回滚语义

### 11.2 外围新增

仅在外围增加控制面组件：

- `EvolutionControlPlane`
- `SandboxManager`
- `VersionRegistry`
- `PromotionManager`

### 11.3 避免事项

- 不把自进化逻辑散进执行器
- 不在运行中热改主链路
- 不让 candidate 污染 active
- 不把需求进化与代码进化混成一个大模块

---

## 12. 与现有仓库的映射建议

结合当前仓库，建议如下理解：

### 12.1 已有稳定核心

- `sprintcycle/api.py`
- `sprintcycle/governance/`
- `sprintcycle/orchestration/`
- `sprintcycle/execution/`
- `sprintcycle/release_plan/`

### 12.2 未来新增控制面

- `sprintcycle/evolution/`
- `sprintcycle/sandbox/`
- `sprintcycle/versioning/`

### 12.3 主链路保持不变

- `SprintCycle` 仍然是唯一主入口
- `SprintOrchestrator` 仍然负责调度
- `GovernanceRunner` 仍然负责门禁
- `RollbackManager` 仍然负责回滚语义

---

## 13. 落地路线建议

### Phase 1：最小可用隔离与回滚

目标：先让“自进化不会污染主线”。

实施内容：

- `git worktree`
- 独立 sandbox 目录
- candidate 产物落盘
- commit / tag 备份
- 简单 rollback

### Phase 2：版本注册与发布闸门

目标：让 candidate 有明确生命周期。

实施内容：

- version registry
- `active` / `candidate` 状态机
- promote / reject / rollback
- 版本报告归档

### Phase 3：需求进化闭环

目标：把用户反馈纳入需求演化链。

实施内容：

- feedback intake
- intent evolution
- release plan evolution
- spec / acceptance 版本化

---

## 14. 实施要点与建议

### 14.1 推荐技术栈

- 隔离：Git worktree + Docker Compose
- 版本：Git commit / tag + manifest
- 状态：现有 checkpoint / state store
- 备份：Git + restic/borgbackup
- 验证：pytest / ruff / mypy / import-linter / semgrep / pip-audit

### 14.2 需要避免的做法

- 不在运行中直接改主仓库代码
- 不把回滚做成手工复制文件
- 不把需求进化和代码进化合并成单一超大模块
- 不一开始就上重型编排平台（如 K8s / OPA）

### 14.3 推荐总原则

> **统一生命周期、统一治理、统一回滚；对象差异外置到适配层。**

---

## 15. 结论

SprintCycle 的进化能力应该采用以下模式：

> **统一 sprint 循环 + 统一治理框架 + 沙盒隔离 + Git 版本化 + 指针式发布 / 回滚**

其中：

- **代码自进化** 与 **需求进化** 共用同一条链路
- 差异只体现在适配层与产物落点
- 主体架构保持稳定，不被候选版本影响
- 通过开源成熟组件复用，减少自建成本

这是一种既能支持持续进化、又能保持系统整洁性的落地方案。
