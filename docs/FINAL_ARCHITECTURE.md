# SprintCycle 最终终态架构说明

本文档作为 SprintCycle 仓库内的技术方案定稿，描述当前已经收敛后的最终目标架构、分层边界、入口策略和阶段性落地原则。

---

## 1. 架构定稿结论

SprintCycle 的最终终态不是“多入口并行透出所有能力”，而是一个**分层清晰、入口收敛、能力隔离、可治理、可扩展**的生命周期编排平台。

最终只保留两类正式入口：

- **Dashboard**：面向人类使用的可视化控制台
- **REST API**：面向外部系统和自动化编排的标准集成入口
- **HTTP Interfaces**：`interfaces/http` 负责承载 public / internal 路由分层

同时，能力分层为：

- **Core Domain**：统一业务内核
- **Application**：Internal / Public API 服务编排层
- **Internal API**：Dashboard 专属控制面
- **Public API**：外部系统最小稳定集成面
- **Infrastructure Governance Modules**：鉴权、审计、限流的统一接入位

不再把 CLI 和 MCP 作为产品主路径。

---

## 2. 最终架构总览

```text
Dashboard ───────────────┐
                         │
                         ▼
                  Internal API
                         │
                         ▼
                     Core Domain
                         ▲
                         │
External Systems ────► Public API

Infrastructure 层提供：
- Auth
- Audit
- Rate Limit
```

### 2.1 设计原则

1. **Dashboard 使用全集能力**
   - Dashboard 面向人类操作与可视化控制
   - 可以调用内部治理、运行态、执行详情、观测、建议、修复等完整能力

2. **外部系统只使用 Public API**
   - 只暴露稳定、最小、可控的接口
   - 不直接暴露内部状态和治理细节

3. **Core Domain 不依赖入口类型**
   - 业务内核不感知 Dashboard / REST / future auth 入口差异
   - 入口只做适配，不承载业务裁决

4. **统一治理能力预留接入点**
   - 鉴权、审计、限流先作为正式命名模块保留
   - 当前实现可以是默认放行或占位实现，但接口边界要固定

5. **不推进模板系统和扩展生态**
   - 本终态架构不包含模板层、插件市场、MCP、CLI 主入口等扩展方向
   - 只保留当前闭环所需能力

---

## 3. 四层架构定义

### 3.1 Core Domain

Core Domain 是 SprintCycle 的真实业务内核，负责：

- 计划
- 执行
- 状态
- 停止
- 诊断
- 回滚
- 恢复
- 观测
- 修复
- 治理
- 版本晋升

核心要求：

- 不依赖 HTTP
- 不依赖 Dashboard
- 不依赖 CLI / MCP
- 不关心鉴权实现
- 不关心前端展示

### 3.2 Application

Application 层负责把 Core Domain 的能力编排成稳定的 Internal / Public API 服务。

### 3.3 Internal API

Internal API 是 Dashboard 的专属控制面，负责：

- 聚合内部状态
- 返回 Dashboard 友好的 payload
- 暴露 execution detail、trace、replay、governance、runtime、suggestion、platform overview 等全量能力
- 支持更复杂的查询与调试语义

### 3.4 Public API

Public API 是外部系统的标准集成入口，负责：

- 提供稳定最小契约
- 满足 CI/CD、外部系统、Agent 等调用场景
- 限制暴露面，减少内部结构泄漏

建议对外仅保留：

- `plan`
- `run`
- `status`
- `stop`
- `rollback`
- `diagnose`

### 3.5 Infrastructure Governance Modules

这一层先保留正式模块名，作为未来治理能力接入点：

- `auth`
- `audit`
- `rate_limit`

当前实现可以是默认上下文、默认放行或空记录，但接口和命名应稳定下来。

---

## 4. 入口终态

### 4.1 Dashboard

Dashboard 是 SprintCycle 的核心人机交互入口。

职责：

- 执行控制
- 进度可视化
- 运行态查看
- 观测与回放
- 修复和治理辅助
- 建议审查

Dashboard 通过 Internal API 获取完整能力。

### 4.2 REST API

REST API 是 SprintCycle 的标准自动化集成入口。

职责：

- 外部系统触发
- 自动化执行
- 状态查询
- 基础诊断
- 中断与回滚

REST API 只暴露 Public API 子集。

### 4.3 被移除的入口

以下入口不再作为产品主路径存在：

- CLI
- MCP

它们可能在历史上用于调试或兼容，但终态不再保留为正式产品能力。

---

## 5. 最终的能力边界

### 5.1 Dashboard 使用的能力

Dashboard 可以访问：

- `console_overview`
- `platform_overview`
- `management_overview`
- `fitness_view`
- `deploy_view`
- `deploy_lifecycle`
- `governance_view`
- `governance_lifecycle`
- `fix_view`
- `architecture_check`
- `execution_detail`
- `execution_events`
- `replay_execution`
- `runtime_latest`
- `runtime_update`
- `observability_trace`
- `observability_replay`
- `lifecycle_contract`
- `diagnose_repair_observe`
- `suggestion_overview`
- `review_suggestion`
- `approve_suggestion`
- `reject_suggestion`

### 5.2 Public API 使用的能力

外部系统建议仅使用：

- `plan`
- `run`
- `status`
- `stop`
- `rollback`
- `diagnose`

如果未来需要扩充，必须先明确稳定契约，再决定是否进入 Public API。

---

## 6. 当前代码层面的落地状态

### 6.1 `sprintcycle/api.py`

`SprintCycle` 仍是核心 Facade，承担：

- 生命周期协调
- 结果聚合
- 核心服务编排
- 业务方法暴露

它不应继续承担入口语义。

### 6.2 `sprintcycle/application/internal_api_service.py`

负责 Dashboard 的内部控制面编排。

### 6.3 `sprintcycle/application/public_api_service.py`

负责外部系统的最小 API 契约。

### 6.4 `sprintcycle/interfaces/http/public.py`
### 6.5 `sprintcycle/interfaces/http/internal.py`

负责 public / internal HTTP 路由与请求适配。

### 6.6 `sprintcycle/presentation/server.py`

负责 Dashboard 容器、SSE 事件连接与 router 挂载。

### 6.7 `sprintcycle/infrastructure/auth.py`
### 6.8 `sprintcycle/infrastructure/audit.py`
### 6.9 `sprintcycle/infrastructure/rate_limit.py`

这三个模块是未来统一治理能力的接入点。

---

## 7. 生命周期终态原则

SprintCycle 仍然围绕单一生命周期契约运作：

```text
new → normalized → planned → prepared → decomposed → executing → observing → diagnosed → repairing → verifying → delivering → runtime_linked → governing → promotion_ready → promoted
```

其中：

- `diagnosed → repairing → verifying → observing` 形成显式修复闭环
- `delivering → runtime_linked → governing → promotion_ready → promoted` 形成交付晋升闭环

终态仍然强调：

- 一个 contract
- 一条证据链
- 一个 final snapshot
- 一个可审计版本归档

---

## 8. Public / Internal 的行业实践划分

这套划分参考的是成熟控制面 / 集成面分离思路：

### Internal API

- 面向控制台
- 允许更细粒度内部数据
- 允许聚合展示
- 允许更丰富的运维语义

### Public API

- 面向外部系统
- 只暴露稳定能力
- 只保留最小集合
- 支持未来鉴权、审计、限流接入

这是 SprintCycle 当前最合适的边界方式。

---

## 9. 明确不做的事情

终态架构不推进以下内容：

- 模板系统
- MCP 主入口
- CLI 主入口
- 插件市场
- 额外扩展生态
- 独立 OpenAI API 入口
- 复杂的多租户治理落地

如果未来需要这些能力，应作为独立演进项，不进入当前定稿。

---

## 10. 三阶段完整推进方案（仅覆盖本次目标）

结合当前代码现状与产品评估结论，本次只覆盖以下四项落地，不扩展其他未要求能力：

- Dashboard 前端补齐
- 独立 Evaluator Agent
- 部署自动化
- 多维度评分 + Sprint Contract

为保证推进节奏清晰、风险可控，建议拆成三个阶段完成。每个阶段均给出里程碑、交付物与验收标准。

### 10.1 Phase 1：Dashboard 可用化 + 评分底座

目标：先把用户可见面做出来，同时把质量度量的基础骨架搭好。

#### 里程碑 1.1：Dashboard 基础框架可启动

交付物：

- Dashboard 前端工程骨架
- 基础布局与导航
- 核心路由占位
- 与后端 API 的基础联通

验收标准：

- 可通过本地命令启动前端
- 页面能正常渲染基础框架
- 能访问后端健康检查或基础 API
- 前端与现有 FastAPI Dashboard 后端保持联通

#### 里程碑 1.2：执行总览与详情可读

交付物：

- 总览面板
- 执行列表页
- 执行详情页
- 状态刷新机制（轮询或 SSE）

验收标准：

- 能看到当前执行项与历史执行项
- 能进入单次执行详情
- 执行状态变化能被前端正确显示
- 页面刷新后状态不会完全丢失

#### 里程碑 1.3：实时事件流可观测

交付物：

- SSE 事件流视图
- 关键事件类型展示
- 事件时间线或日志面板

验收标准：

- 事件可实时追加到页面
- 事件顺序与后端输出一致
- 至少可观察执行、诊断、修复、交付相关事件

#### 里程碑 1.4：评分与契约展示位预留

交付物：

- 评分结果只读展示位
- Sprint Contract 详情承载位
- 评分解释 / 证据摘要展示位

验收标准：

- 页面上存在评分和契约的固定入口
- 后续接入独立 Evaluator 时无需重做页面结构
- UI 不依赖未来未实现的数据源才能正常打开

不在本阶段内：复杂设计系统、插件化页面市场、完整交互式部署控制面。

### 10.2 Phase 2：独立 Evaluator Agent + Sprint Contract 正式化

目标：把原先隐式的校验 / FitnessFunction，升级为独立评审链路，并把合同写死。

#### 里程碑 2.1：Evaluator 职责边界确立

交付物：

- 独立 Evaluator Agent 的职责说明
- 与 Planner / Executor 的边界定义
- Evaluator 输入 / 输出契约草案

验收标准：

- 能明确说明 Evaluator 负责什么、不负责什么
- 不与执行器职责混淆
- 评审输入可从 contract / evidence / runtime 中读取

#### 里程碑 2.2：多维评分模型落地

交付物：

- 多维评分维度定义
- 每个维度的评分规则草案
- 评分聚合逻辑

验收标准：

- 评分不再是单一分值
- 至少覆盖：功能完成度、结构质量、验证证据、交付就绪度
- 每个维度都能给出可解释结果

#### 里程碑 2.3：Sprint Contract 正式化

交付物：

- Sprint Contract 数据结构
- Contract 必备字段定义
- Contract 与 execution / evidence / runtime 的关联字段

验收标准：

- 每次 Sprint 都有显式 contract
- contract 中能表达目标、门槛、证据、结论
- contract 可以被保存、读取、回放

#### 里程碑 2.4：评审结论可追溯

交付物：

- 通过 / 不通过 / 需修复 的判定模型
- 评分解释输出
- 失败原因与修复建议输出

验收标准：

- 任一评审结论都能解释原因
- 能追溯到对应证据或缺失项
- 结论可写回 contract 并被后续阶段消费

#### 里程碑 2.5：与现有生命周期衔接

交付物：

- Evaluator 接入生命周期的时点定义
- contract 进入对应 stage 的门禁规则
- 与现有最终快照 / promotion 逻辑的接口说明

验收标准：

- Evaluator 的结果能影响后续晋升判断
- contract 不破坏现有生命周期语义
- Planner / Executor / Evaluator 三段链路边界清晰

不在本阶段内：完整多 Agent 编排平台、复杂自治决策系统、插件化评审市场。

### 10.3 Phase 3：部署自动化闭环 + 质量晋升联动

目标：把“交付后怎么上运行态、怎么回查、怎么晋升”打通，形成闭环。

#### 里程碑 3.1：构建产物与运行态建立关联

交付物：

- 构建产物标识
- 部署目标与运行态引用
- 发布记录字段

验收标准：

- 任一构建产物能对应到运行态信息
- 发布记录可查询
- 构建与部署之间存在可追踪关联

#### 里程碑 3.2：部署状态可见可查

交付物：

- 发布状态视图
- 运行态回查入口
- 基础部署事件流

验收标准：

- 能看到部署是否成功、失败或进行中
- 能回查最近一次部署结果
- 部署状态能在 Dashboard 中正确展示

#### 里程碑 3.3：基础部署动作编排

交付物：

- 基础部署动作定义
- 部署触发与回调流程
- 与现有执行 / 交付链路的对接点

验收标准：

- 至少可以完成一次基础部署动作的编排
- 部署动作与执行产物之间关系明确
- 出错时能回到可诊断状态

#### 里程碑 3.4：质量门禁与晋升联动

交付物：

- 多维评分结果与部署门禁的联动规则
- Sprint Contract 中的部署 / 晋升证据字段
- 晋升判定入口

验收标准：

- 评分结果能影响是否允许晋升
- 晋升必须依赖 contract 和 evidence
- 可说明为什么通过、为什么拒绝晋升

#### 里程碑 3.5：证据链闭环

交付物：

- 从执行到部署到晋升的证据链整理
- 可回放的最终记录
- 面向版本化演化的归档结果

验收标准：

- 任一已完成 Sprint 可以回放关键证据
- 证据链能串起执行、评审、部署、晋升四类信息
- 能支持后续审计与版本沉淀

不在本阶段内：复杂 GitOps 平台、Kubernetes 多集群编排、蓝绿 / 金丝雀完整运营平台。

### 10.4 三阶段的最终约束

以上三阶段是本次设计方案的完整推进路径。除此之外：

- 不额外推进 CLI / MCP / 模板系统
- 不额外实现多租户产品化
- 不额外扩展插件生态
- 不额外改造核心 Domain 的既有生命周期语义

所有新增设计都应在“现有真实代码结构”上演进，而不是假设一个全新系统。

### 10.5 建议的推进顺序（从依赖关系出发）

为了避免返工，建议按以下顺序推进：

1. **先做 Phase 1**
   - 先补 Dashboard 基础框架，再接执行详情与事件流
   - 先预留评分与 Contract 展示位，再接真实数据源

2. **再做 Phase 2**
   - 先定义 Evaluator 职责和评分维度
   - 再正式化 Sprint Contract
   - 最后把评审结论接回生命周期门禁

3. **最后做 Phase 3**
   - 先打通构建产物与运行态关联
   - 再做部署状态可见化
   - 再把评分结果接到晋升门禁和证据链闭环

这个顺序的核心原则是：

- 先可见，再可评
- 先可评，再可部署
- 先可部署，再可晋升
- 先有 contract，再做最终门禁

### 10.6 可直接进入代码落地的详细实施方案

下面给出能直接用于实现的分阶段方案。每个阶段都明确：要改哪些模块、要新增什么能力、以及最小可交付结果。

#### Phase 1 代码落地方案：Dashboard 可用化 + 评分底座

**目标**：先让 Dashboard 从“后端壳子”变成“能看、能追、能定位”的控制台，同时把评分和 contract 的展示通道预埋好。

**建议修改模块**：

- `sprintcycle/presentation/server.py`
- `sprintcycle/application/internal_api_service.py`
- `sprintcycle/application/public_api_service.py`
- `sprintcycle/interfaces/http/internal.py`
- `sprintcycle/interfaces/http/public.py`
- `sprintcycle/dashboard/*`
- `README.md` / `README_EN.md`（仅文档同步）

**实施拆解**：

1. **Dashboard 页面骨架**
   - 建立首页布局、左侧导航、顶部状态栏
   - 预置页面：总览、执行、详情、事件流、评分、Contract
   - 页面先静态可渲染，数据用空态或 mock

2. **执行总览数据接入**
   - Dashboard 首页接入 `console_overview` / `platform_overview`
   - 列表页接入 `execution_detail` / `execution_events`
   - 详情页接入 `lifecycle_contract`

3. **实时事件流接入**
   - 直接复用现有 SSE 事件管道
   - 前端展示执行事件、诊断事件、修复事件、交付事件
   - 保持事件流为只读，不在本阶段做交互控制

4. **评分和 Contract 展示位**
   - 前端预留评分卡片、维度分解、证据摘要、Contract 摘要
   - 当前可先使用 `fitness_view()`、`lifecycle_contract()` 的已有 payload
   - 没有独立 Evaluator 之前，先显示“基础评分”或“待接入”状态

5. **前后端联通校验**
   - Dashboard 启动后能看到至少一个可用首页
   - SSE 连接不断开
   - 执行状态变化可被页面刷新后重新读取

**Phase 1 最小验收**：

- Dashboard 可启动
- 至少一个首页和一个详情页可用
- 能看到执行状态与事件流
- 评分/Contract 的 UI 容器已经具备

**Phase 1 不做**：部署编排、独立评审决策、晋升门禁改造。

---

#### Phase 2 代码落地方案：独立 Evaluator Agent + Sprint Contract

**目标**：把现有偏弱的 `FitnessEvaluator` 逻辑升级为独立评审链路，并让 contract 成为每次 Sprint 的显式事实载体。

**建议修改模块**：

- `sprintcycle/fitness.py` 或其对应评估模块
- `sprintcycle/api.py`
- `sprintcycle/results.py`
- `sprintcycle/services/lifecycle_contracts.py`（若存在/若需扩展）
- `sprintcycle/services/promotion_policy.py`
- `sprintcycle/services/lifecycle_evolution_service.py`
- `sprintcycle/dashboard/views/fitness_view.py`
- 新增 `sprintcycle/evaluator/*` 或 `sprintcycle/agents/evaluator/*`

**实施拆解**：

1. **Evaluator Agent 抽象**
   - 新建独立的评审服务类，职责只负责“打分、判定、解释”
   - 输入：contract、execution evidence、runtime、diagnostics、governance
   - 输出：分项评分、总分、结论、缺失证据、建议

2. **多维评分模型**
   - 定义至少四个维度：功能完成度、结构质量、验证证据、交付就绪度
   - 每个维度输出：分值、理由、证据引用
   - 总分不是简单平均，保留权重配置位

3. **Sprint Contract 正式化**
   - 明确 contract 的核心字段：目标、门槛、证据、评分、结论、修复建议
   - 将 contract 作为 evaluation 的输入和输出都保存下来
   - contract 必须能回放一次 Sprint 的完整判断过程

4. **评审结论回写生命周期**
   - 评审结果回到 `lifecycle_contract` / `final_snapshot`
   - `promotion_policy` 使用评审结果做门禁
   - `LifecycleEvolutionService` 读取评审结果决定是否允许晋升

5. **Dashboard 联动展示**
   - 评分页展示多维结果
   - Contract 详情展示结论与证据链
   - 不通过时展示失败原因与修复建议

**Phase 2 最小验收**：

- Evaluator 可独立产出评分和结论
- Contract 能承载目标、门槛、证据、评分、结论
- 晋升判断可消费评审结果
- Dashboard 能展示评分解释

**Phase 2 不做**：完整多 Agent 编排平台、复杂自治决策系统、插件化评审市场。

---

#### Phase 3 代码落地方案：部署自动化闭环 + 质量晋升联动

**目标**：把执行结果真正连到运行态和发布态，让“能交付、能回查、能晋升”形成闭环。

**建议修改模块**：

- `sprintcycle/deployment/*`
- `sprintcycle/deployment/runtime_registry.py`
- `sprintcycle/api.py`
- `sprintcycle/services/execution_lifecycle_service.py`
- `sprintcycle/services/lifecycle_evolution_service.py`
- `sprintcycle/services/promotion_policy.py`
- `sprintcycle/dashboard/views/deploy_view.py`
- `sprintcycle/dashboard/views/governance_view.py`

**实施拆解**：

1. **运行态关联**
   - 将构建产物、运行时 ID、发布记录绑定到同一条 contract / execution
   - 确保 `runtime_lifecycle()`、`deploy_lifecycle()` 可追溯同一来源

2. **部署状态模型**
   - 增加部署中、已成功、失败、待回滚等最小状态集
   - Dashboard 展示最近一次部署及其结果
   - 保留部署记录供回查

3. **基础部署动作编排**
   - 提供一个最小部署动作入口
   - 部署动作只做编排，不做复杂平台能力
   - 失败后要能回到诊断 / 修复链路

4. **晋升门禁联动**
   - 部署成功只是前置条件，最终晋升仍由 contract + evidence + evaluator 决定
   - 将部署证据纳入 final snapshot
   - 晋升入口读取部署与评审结果的联合状态

5. **证据链归档**
   - 归档 execution、evaluation、deployment、promotion 四类证据
   - 最终 snapshot 必须可回放
   - 面向版本注册表沉淀可审计信息

**Phase 3 最小验收**：

- 运行态与构建产物能关联
- 部署状态可见可查
- 部署失败能回到可诊断状态
- 晋升依赖 contract / evidence / evaluator / deployment 联合门禁

**Phase 3 不做**：复杂 GitOps 平台、Kubernetes 多集群编排、蓝绿 / 金丝雀完整运营平台。

### 10.7 从代码角度的推荐落地顺序

如果现在就开始写代码，建议按这个顺序切入：

1. **先改 `api.py` 的事实层能力**
   - 让 contract / evaluation / deployment 的数据结构先统一
   - 保证后续前端和服务层都能拿到一致字段

2. **再补 Dashboard 页面和路由**
   - 先做可见性，再做交互性
   - 用现有 payload 尽快把 UI 跑起来

3. **然后抽出 Evaluator Agent**
   - 先从 `fitness` 逻辑分层开始
   - 再形成独立评审服务

4. **最后接部署自动化**
   - 以最小部署状态模型切入
   - 再逐步补齐回查、联动、归档

---

## 11. 最终结论

SprintCycle 的最终终态架构可以概括为：

> **以 Core Domain 为唯一业务内核，以 Internal API 服务 Dashboard，以 Public API 服务外部系统，以 Auth / Audit / Rate Limit 作为统一治理接入位，最终收敛到 Dashboard + REST API 两类正式入口。**

这份边界定义保证：

- 逻辑不丢
- 入口收敛
- 能力可治理
- 内外隔离清晰
- 未来鉴权和审计可以自然接入

---

## 11. 文档状态

- 文档性质：技术方案定稿
- 适用范围：仓库内架构说明与后续实现依据
- 目标状态：当前终态
- 版本策略：随代码演进可做增量修订，但不再改变上述核心边界
