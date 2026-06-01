# SprintCycle 优化工作流使用指南（前后端对齐版）

## 快速开始

### 触发优化

你可以通过以下方式触发优化工作流：

1. **使用命令**（推荐）
   ```
   /sprint-optimize
   ```

2. **使用触发词**
   - 「删减字段」
   - 「遵循 DDD 治理」
   - 「删除兼容逻辑」
   - 「优化架构」
   - 「精简代码」
   - 「前后端对齐」

### 工作流示例

#### 示例 1：删减字段

**用户输入：**
> 某些业务字段是不是太多、可以删减，降低复杂性

**Agent 响应：**
```
收到！将执行字段优化工作流。

## Step 1 - 分析

让我先查看相关的模型定义...
```

**执行步骤：**
1. 分析现有字段结构
2. 识别冗余字段组
3. 设计整合方案
4. 制定迁移计划（前端 + 后端）
5. 小步执行变更
6. 运行测试验证

#### 示例 2：DDD 治理

**用户输入：**
> 遵循 DDD + 六边形架构，治理一下这个

**Agent 响应：**
```
收到！将执行 DDD 架构治理工作流。

## Step 1 - 对标架构规范

参考 .cursor/rules/sprintcycle-architecture-orchestration.mdc...
```

**执行步骤：**
1. 对照架构规范
2. 识别违规模式
3. 设计改进方案
4. 确保领域层纯粹
5. 验证边界清晰
6. 测试通过

#### 示例 3：删除兼容逻辑

**用户输入：**
> 删除兼容逻辑

**Agent 响应：**
```
收到！将执行兼容逻辑清理工作流。

## Step 1 - 识别兼容代码

查找所有兼容性辅助方法...
```

**执行步骤：**
1. 定位兼容辅助方法
2. 识别所有调用点（前端 + 后端）
3. 验证测试覆盖
4. 更新调用点
5. 移除旧代码
6. 测试全部通过
7. **⚠️ 同步更新 4 个文档**
8. 提交代码

#### 示例 4：前后端对齐

**用户输入：**
> 让前端和后端的接口对齐

**Agent 响应：**
```
收到！将执行前后端对齐工作流。

## Step 1 - 检查契约一致性

对照后端 DTO 和前端类型定义...
```

**执行步骤：**
1. 检查后端 DTO 定义
2. 验证前端 API 和类型定义
3. 同步更新前端 Store 和组件
4. 验证编译和测试通过

## 内置规则

已创建的规则文件：

### 1. `.cursor/rules/sprintcycle-optimization.mdc`

**作用：** 全局优化约束
- **alwaysApply: true** - 所有对话自动生效
- 定义优化触发词（含「前后端对齐」）
- 制定核心原则（含前后端同步）
- 提供决策树
- 验证清单（含前后端检查）

### 2. `.cursor/commands/sprint-optimize.md`

**作用：** 优化工作流命令
- 详细的执行流程（前后端分离）
- 分步骤指导（后端 + 前端）
- 输出模板（含前后端变更清单）
- 核心原则

## 规则架构

```
用户输入
    ↓
触发词检测 / 命令调用
    ↓
┌─────────────────────────────────┐
│  Rule (alwaysApply)            │
│  sprintcycle-optimization.mdc  │
│  - 全局约束                     │
│  - 核心原则（含前后端对齐）      │
│  - 文档同步要求                 │
│  - 验证清单                     │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  Command (sprint-optimize)     │
│  - 工作流步骤（4步）            │
│  - 后端变更指导                 │
│  - 前端变更指导                 │
│  - 输出模板                     │
└─────────────────────────────────┘
    ↓
Agent 执行优化（前后端同步）
    ↓
┌─────────────────────────────────┐
│  Step 4: 文档同步（强制）       │
│  - README.md / README_EN.md    │
│  - ARCHITECTURE_INVARIANTS.md  │
│  - sprintcycle-architecture   │
└─────────────────────────────────┘
    ↓
测试验证 + 提交
```

## 验证清单

> **统一来源**: 完整验证清单定义在 `.cursor/rules/sprintcycle-optimization.mdc` 中，以下为摘要：

**🔹 Phase 1: 需求分析**
- [ ] 用户需求已通过 AskUserQuestion 确认
- [ ] 影响范围评估完成
- [ ] 风险评估已记录

**🔹 Phase 2: 设计阶段**
- [ ] PRD 已通过 HITL 批准
- [ ] 技术方案已通过 HITL 批准
- [ ] 架构合规性已检查

**🔹 Phase 3: 执行实施**
- [ ] 代码编译无误（Python + TypeScript）
- [ ] 业务逻辑 100% 保留
- [ ] 前后端契约对齐
- [ ] 未添加任何兼容代码或过渡层

**🔹 Phase 4: 测试验证**
- [ ] 相关测试通过（pytest + 前端测试）
- [ ] 测试覆盖率 ≥80%
- [ ] 集成测试通过

**🔹 Phase 5: 文档同步**
- [ ] README.md / README_EN.md 更新完成
- [ ] ARCHITECTURE_INVARIANTS.md 更新完成
- [ ] sprintcycle-architecture-orchestration.mdc 对齐完成

**🔹 Phase 6: 审批提交**
- [ ] PR 创建完成，描述清晰
- [ ] 至少 2 位审核人已指定
- [ ] CI/CD 流水线通过

## 前后端对齐检查清单

### 后端（Python）检查点
- [ ] 领域模型变更完成（`sprintcycle/domain/core/`）
- [ ] 端口定义更新完成（`sprintcycle/domain/ports/`）
- [ ] 服务层实现更新完成（`sprintcycle/application/services/`）
- [ ] DTO 定义更新完成（`sprintcycle/application/dto/`）
- [ ] HTTP 路由更新完成（`sprintcycle/interfaces/http/`）
- [ ] 测试覆盖验证完成

### 前端（Vue 3）检查点
- [ ] API 接口定义更新完成（`frontend/src/api/`）
- [ ] TypeScript 类型定义更新完成（`frontend/src/types/`）
- [ ] Store 状态结构更新完成（`frontend/src/stores/`）
- [ ] 视图组件更新完成（`frontend/src/views/`）
- [ ] TypeScript 编译通过
- [ ] 前端测试通过

## 文档同步（强制）

⚠️ **每次优化完成后必须更新以下 4 个文档：**

### 需要同步的文档

1. **README.md**（中文）
   - 更新产品定义和能力矩阵
   - 同步字段结构和架构描述
   - 反映新的 DDD 模式和生命周期阶段

2. **README_EN.md**（英文）
   - 镜像 README.md 的所有变更
   - 保持双语一致性

3. **docs/ARCHITECTURE_INVARIANTS.md**
   - 更新架构边界和不变性
   - 同步 DDD 模式（聚合根、值对象）
   - 反映 Port/Adapter 映射
   - 更新层职责

4. **.cursor/rules/sprintcycle-architecture-orchestration.mdc**
   - 与实际代码实现对齐
   - 更新 DDD 子域结构
   - 同步聚合根定义
   - 反映新模式和约定

### 同步原则

- ✅ **以代码实现为准**
- ✅ **保持双语一致性**
- ✅ **文档间无矛盾**
- ✅ **反映真实架构**
- ✅ **前后端契约同步**

### 同步检查点

- [ ] README.md 字段描述与代码一致
- [ ] README_EN.md 与 README.md 对齐
- [ ] ARCHITECTURE_INVARIANTS.md 边界与代码一致
- [ ] sprintcycle-architecture-orchestration.mdc 与代码实现对齐

### 工作流集成

```
代码变更（后端 + 前端）
    ↓
测试验证（后端测试 + 前端测试）
    ↓
⚠️ 文档同步（立即执行）
    ↓
提交代码 + 文档
```

## 最佳实践

### ✅ 推荐做法

1. **小步快跑**
   - 每次修改聚焦一个优化点
   - 及时测试验证
   - 可逆可回滚

2. **逻辑优先**
   - 先理解业务逻辑
   - 再优化代码结构
   - 最后清理兼容

3. **测试驱动**
   - 先写/运行测试
   - 再做修改
   - 确保测试通过

4. **架构合规**
   - 对照规范执行
   - 保持边界清晰
   - 遵循 DDD 原则

5. **前后端同步**
   - 后端变更后立即更新前端
   - 保持 API/类型/Store 一致性
   - 同步验证双方测试

### ❌ 避免做法

1. **不要暴力删改**
   - 不确定时先问用户
   - 不破坏现有功能

2. **不要跳过测试**
   - 测试是安全网
   - 失败必须修复

3. **不要引入违规**
   - 架构边界神圣
   - 违规必须纠正

4. **不要前后端不同步**
   - 后端变更必须同步到前端
   - 保持契约一致性

## 自定义扩展

### 添加新的触发词

编辑 `.cursor/rules/sprintcycle-optimization.mdc`:

```markdown
### Optimization Triggers / 优化触发词

当你遇到这些短语时，激活优化模式：
- **「你的新触发词」** / "new trigger"
```

### 添加新的工作流步骤

编辑 `.cursor/commands/sprint-optimize.md`:

```markdown
### Step N - 新步骤

1. ...
2. ...
```

### 创建专属 Skill

如果需要更复杂的工作流，可创建：

```
.cursor/skills/sprint-optimize/SKILL.md
```

参考 `.cursor/skills/speckit/SKILL.md` 格式。

## 故障排查

### 优化后测试失败

1. 查看测试输出
2. 定位失败原因
3. 修复代码或测试
4. 重新运行测试

### 业务逻辑丢失

1. 立即回滚代码
2. 检查变更点
3. 确保逻辑完整
4. 重新优化

### 架构违规

1. 对照架构规范
2. 识别违规模式
3. 设计合规方案
4. 重新执行

### 前后端契约不匹配

1. 检查后端 DTO 定义
2. 对比前端类型定义
3. 同步更新前端 API/Store/组件
4. 验证编译和测试

## 相关资源

- 架构规范：`.cursor/rules/sprintcycle-architecture-orchestration.mdc`
- 优化命令：`.cursor/commands/sprint-optimize.md`
- 优化规则：`.cursor/rules/sprintcycle-optimization.mdc`
- 前端代码：`frontend/src/`
- 后端代码：`sprintcycle/`
