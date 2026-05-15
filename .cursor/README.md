# Cursor 使用说明 / Cursor Guide

本目录用于存放 SprintCycle 项目的 Cursor 专用配置，包括：

- `agents/`：子代理（subagent）配置
- `commands/`：命令入口配置
- `rules/`：项目规则与约束

这些配置都是**项目级**的，适用于当前仓库 `sprintcycle`。

如果你想快速了解这套协作团队，请先看 `docs/CURSOR_TEAM_PLAYBOOK.md`。

## 目录结构

```text
.cursor/
  README.md
  agents/
  commands/
  rules/
```

---

## 1. subagent 怎么用

subagent 适合做“专岗助手”，把复杂任务拆成多个固定职责。

### 当前可用的 subagent

- `team-commander`
  - 需求分类与任务路由
  - 拆解多步骤工作流
  - 选择最合适的专岗路径

- `arch-guardian`
  - 架构边界审查
  - 检查分层、职责归属、跨层耦合、重复业务逻辑

- `graph-orchestrator`
  - LangGraph 编排审查
  - 检查节点职责、状态流转、plan / sprint 拆分、dispatch 流程

- `lifecycle-auditor`
  - 生命周期审查
  - 检查 execution、runtime registry、observability、promotion / evolution 链路

- `test-risk-reviewer`
  - 测试与风险审查
  - 检查缺失测试、边界条件、回归风险、兼容性问题

- `review-commander`
  - 汇总审查
  - 综合多个 subagent 的结论，输出最终 verdict

### 使用方式

当你想让 Cursor 用某个 subagent 时，可以直接在对话里说：

- `Use the team-commander subagent to classify this work`
- `Use the arch-guardian subagent to review this change`
- `Use the graph-orchestrator subagent to inspect the LangGraph flow`
- `Use the lifecycle-auditor subagent to check runtime and promotion consistency`
- `Use the test-risk-reviewer subagent to find regression gaps`
- `Use the review-commander subagent to consolidate the final review`

也可以直接描述任务，让 Cursor 自动选择合适的 subagent。

---

## 2. commands 怎么用

commands 是“固定入口”，适合把常用任务包装成统一调用方式。

### 当前可用的 commands

- `/team-command`
- `/review-arch`
- `/review-graph`
- `/review-lifecycle`
- `/review-tests`
- `/review-final`

### 调用方式

在 Cursor 聊天输入框里输入命令名，例如：

- `/team-command`
- `/review-tests`

Cursor 会按照对应命令定义，调用匹配的 subagent 完成任务。

### 每个命令对应什么

- `/team-command` → `team-commander`
- `/review-arch` → `arch-guardian`
- `/review-graph` → `graph-orchestrator`
- `/review-lifecycle` → `lifecycle-auditor`
- `/review-tests` → `test-risk-reviewer`
- `/review-final` → `review-commander`

---

## 3. rules 怎么用

rules 适合放“长期有效的项目约束”。

本项目当前重点规则包括：

- 分层架构边界
- LangGraph 只负责 orchestration
- 生命周期、观测、演化链路必须保持闭环
- 公共 API、service、facade、hook、registry 的职责边界
- 团队路由和角色选择

### 使用建议

- 需要所有改动都遵守的约束 → 放 `rules`
- 需要特定任务时才启用的能力 → 放 `agents`
- 需要统一入口调用的任务 → 放 `commands`

---

## 4. 推荐工作流

### 场景 A：代码改动后做审查

1. 完成代码修改
2. 调用 `/review-arch` 或 `/review-graph`
3. 如果是生命周期相关，再调用 `/review-lifecycle`
4. 最后用 `/review-final` 汇总

### 场景 B：补测试

1. 先调用 `/review-tests`
2. 根据输出补测试
3. 再重新审查一次

### 场景 C：大改动 / 多文件迁移

1. 先审架构 `/review-arch`
2. 再审流程 `/review-graph`
3. 再审生命周期 `/review-lifecycle`
4. 再审测试 `/review-tests`
5. 用 `/review-final` 生成最终结论

### 场景 D：做需求拆解和协作分工

1. 调用 `/team-command`
2. 让 `team-commander` 判断所属子系统和执行顺序
3. 需要时再进入对应专项审查命令

---

## 5. 这个项目里怎么分工最合理

SprintCycle 是一个强约束的分层系统，建议按下面方式分工：

- 需求拆解与路由 → `team-commander`
- 架构边界问题 → `arch-guardian`
- 编排和流程问题 → `graph-orchestrator`
- 执行链路和 runtime 问题 → `lifecycle-auditor`
- 测试缺口和风险 → `test-risk-reviewer`
- 最终结论 → `review-commander`

---

## 6. 使用建议

- 一个任务尽量只调用一个主要 subagent
- 大改动时再按顺序组合多个 subagent
- 如果输出不够明确，优先补充上下文，而不是让 agent 猜
- 审查类命令尽量返回固定格式，方便团队快速扫读
- 需求拆解优先于直接开改，尤其是跨层任务

---

## 7. 适合的提问方式

推荐这样问：

- “用 `/team-command` 帮我拆一下这次改动的协作路径”
- “用 `/review-arch` 看一下这次 service 迁移有没有越界”
- “用 `/review-graph` 检查 LangGraph 节点职责是否过重”
- “用 `/review-lifecycle` 看 runtime registry 和 observability 是否一致”
- “用 `/review-tests` 找出这次改动缺哪些测试”
- “用 `/review-final` 汇总前面的审查结论”

---

## 8. 维护建议

如果以后你新增了新的 subagent 或 command，建议同步更新这里：

- 新增用途
- 对应命令入口
- 使用场景
- 输出格式

这样团队成员不需要记配置细节，只看这一份说明就能上手。
