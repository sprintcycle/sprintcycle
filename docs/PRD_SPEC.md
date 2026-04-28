# SprintCycle PRD 格式规范

本文档定义 SprintCycle PRD（产品需求文档）的 YAML 格式规范。

## 目录

- [基本结构](#基本结构)
- [执行模式](#执行模式)
- [项目配置](#项目配置)
- [Sprint 定义](#sprint-定义)
- [任务定义](#任务定义)
- [自进化配置](#自进化配置)
- [完整示例](#完整示例)

---

## 基本结构

```yaml
project:
  name: "项目名称"
  path: "/root/project-path"
  version: "v1.0.0"

mode: "normal"  # normal | evolution

sprints:
  - name: "Sprint 名称"
    goals:
      - "目标1"
    tasks:
      - task: |
          任务描述
        agent: "coder"
```

---

## 执行模式

### 普通模式 (normal)

适用于常规任务开发、代码优化等。

```yaml
mode: "normal"
```

### 自进化模式 (evolution)

适用于优化 SprintCycle 框架本身。

```yaml
mode: "evolution"
```

---

## 项目配置

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 项目名称 |
| path | string | 是 | 项目根目录路径（建议绝对路径） |
| version | string | 否 | 版本号，默认 "v1.0.0" |

---

## Sprint 定义

每个 Sprint 包含名称、目标和任务列表。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | Sprint 名称（建议使用英文冒号 `:`） |
| goals | list | 否 | Sprint 目标列表 |
| tasks | list | 是 | 任务列表 |

---

## 任务定义

每个任务定义一个具体的工作单元。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task | string | 是 | 任务描述（支持多行） |
| agent | string | 否 | Agent 类型，默认 "coder" |
| target | string | 否 | 目标文件/目录路径 |
| constraints | list | 否 | 任务约束条件 |
| timeout | int | 否 | 超时时间（秒），默认 600 |

### Agent 类型

| Agent | 说明 | 适用场景 |
|-------|------|----------|
| coder | 编码 agent | 功能开发、代码修改 |
| evolver | 进化 agent | 代码优化、性能提升 |
| tester | 测试 agent | 单元测试、集成测试 |

---

## 自进化配置

自进化模式（`mode: evolution`）需要配置 `evolution` 字段。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| targets | list | 是 | 进化目标文件列表 |
| goals | list | 否 | 进化目标描述 |
| constraints | list | 否 | 进化约束条件 |
| max_variations | int | 否 | 最大变异数量，默认 5 |
| iterations | int | 否 | 迭代次数，默认 3 |

---

## 完整示例

### 普通任务 PRD

```yaml
# prd.yaml - 普通任务 PRD
project:
  name: "xuewanpai"
  path: "/root/xuewanpai"
  version: "v2.5"

mode: "normal"

sprints:
  - name: "Sprint 1: 首页优化"
    goals:
      - "提升加载速度"
    tasks:
      - task: |
          优化首页图片加载
        agent: "coder"
        target: "src/pages/home/index.vue"
```

### 自进化 PRD

```yaml
# evolution_prd.yaml - 自进化 PRD
project:
  name: "sprintcycle"
  path: "/root/sprintcycle"
  version: "v0.6.0"

mode: "evolution"

evolution:
  targets:
    - "sprintcycle/evolution/engine.py"
    - "sprintcycle/evolution/client.py"
  goals:
    - "优化进化算法效率"
  constraints:
    - "保持 API 兼容"
```

---

## 常见问题

### 1. YAML 解析错误

**问题**：使用中文冒号 `：` 导致解析失败

**解决方案**：使用英文冒号 `:` 或引号包裹

```yaml
# ❌ 错误
name: "Sprint 1：首页优化"

# ✅ 正确
name: "Sprint 1: 首页优化"
```

---

## 相关文档

- [快速开始](QUICKSTART.md)
- [API 文档](API.md)
