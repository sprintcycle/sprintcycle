# SprintCycle 技术架构

**版本**: v0.2  
**更新日期**: 2026-04-27

---

## 架构概述

SprintCycle 是一个基于敏捷开发理念的 AI 驱动迭代框架，核心特点：

- 🔄 **PRD 驱动** - 自动从产品需求文档生成 Sprint 规划
- 🤖 **Agent 编排** - 多类型 Agent 协同完成任务
- 📈 **自我进化** - 持续优化框架本身

---

## 核心模块

### 1. SprintChain (chorus.py)

核心执行引擎，负责 Sprint 编排和执行。

```python
from sprintcycle.chorus import SprintChain

chain = SprintChain("/path/to/project")
chain.auto_plan_from_prd("requirements.md")
chain.run_all_sprints()
```

### 2. Agent 模块

| Agent | 职责 | 典型任务 |
|-------|------|----------|
| CODER | 代码编写 | 功能实现、重构 |
| REVIEWER | 代码审查 | PR review、代码检查 |
| ARCHITECT | 架构设计 | 技术方案、接口设计 |
| TESTER | 测试验证 | 功能测试、集成测试 |
| DIAGNOSTIC | 问题诊断 | 根因分析、调试 |
| UI_VERIFY | UI 验证 | 界面检查、截图对比 |

### 3. 优化工具类

| 类 | 功能 |
|----|------|
| RollbackManager | 文件备份与回滚 |
| TimeoutHandler | 超时控制与重试 |
| ErrorHelper | 错误分类与修复建议 |
| ResponseCache | API 响应缓存 |

### 4. 验证器

五源验证系统：
- 测试结果验证
- 代码审查验证
- 运行时验证
- UI 验证
- 差异验证

---

## 数据流

```
PRD 文件
    ↓
PRD 解析器
    ↓
Sprint 规划
    ↓
Agent 调度
    ↓
任务执行
    ↓
结果验证
    ↓
知识库更新
```

---

## 配置管理

配置文件: `config.yaml`

```yaml
# 核心配置示例
scheduler:
  max_concurrent: 5
  
autofix:
  enabled: true
  api_key_env: LLM_API_KEY
```

---

## 扩展指南

### 添加新 Agent

1. 在 `AgentType` 枚举中添加新类型
2. 实现对应的执行逻辑
3. 添加验证器（如需要）

### 添加新验证器

1. 在 `verifiers/` 目录创建验证器类
2. 继承 `BaseVerifier`
3. 实现 `verify()` 方法

---

*SprintCycle v0.2 - Apache License 2.0*
