# SprintCycle

<div align="center">

**AI-Powered Agile Development Framework**

**一句话解决开发痛点**：告别手动写代码、测不完的用例、改不完的 Bug —— 用自然语言描述需求，SprintCycle 自动完成开发、测试、部署全流程。

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-0.2.0-orange.svg)](CHANGELOG.md)

**[📹 观看演示视频](https://www.coze.cn/s/BkeOWwYYdO0/)** | English | [简体中文](README_CN.md)

</div>

---

## 🖼️ SprintCycle 演示

<div align="center">
<img src="docs/images/sprintcycle_demo.png" alt="SprintCycle Demo" width="800">

*一句话，一个项目 —— 从需求到部署全自动化*
</div>

---

## 😫 你是否遇到过这些痛点？

| 痛点 | SprintCycle 解决方案 |
|------|---------------------|
| 🔴 需求文档写完还要手写代码 | ✅ PRD 自动生成代码 |
| 🔴 测试用例写不完、跑不完 | ✅ 自动生成并执行测试 |
| 🔴 Bug 改了一个又来一个 | ✅ 智能诊断 + 自动修复 |
| 🔴 代码审查耗时耗力 | ✅ AI Agent 自动审查 |
| 🔴 文档永远落后于代码 | ✅ 知识库自动沉淀 |
| 🔴 项目越做越乱 | ✅ 自进化持续优化 |

---

## 🎯 两种使用方式

### Way 1: CLI（命令行）

```bash
# 一句话启动开发
sprintcycle run -p ./myproject --prd requirements.yaml
```

### Way 2: OpenClaw + MCP（推荐）

在 AI 助手中用自然语言描述需求：

```
"开发一个科技新闻网站，支持新闻列表、详情和分类筛选"
```

AI 自动完成：生成 PRD → 编写代码 → 测试验证 → 部署运行

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔄 **多轮迭代** | Sprint 式开发，自动任务拆解 |
| 🤖 **6 个 Agent** | CODER、REVIEWER、ARCHITECT、TESTER、DIAGNOSTIC、UI_VERIFY |
| ✅ **五源验证** | 测试、审查、运行时、UI、差异验证 |
| 📚 **知识库** | 自动沉淀经验，越用越强 |
| 🧬 **自进化** | 9 阶段闭环持续优化 |
| 🔌 **18 个 MCP 工具** | AI Agent 完美集成 |

---

## 🚀 快速开始

```bash
# 安装
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle && pip install -r requirements.txt

# 配置
cp config.yaml.example config.yaml
export LLM_API_KEY=your_key

# 一句话开发
sprintcycle run -p ./myproject -t "开发用户登录功能"
```

---

## 🤖 6 个专业 Agent

| Agent | 角色 | 能力 |
|-------|------|------|
| CODER | 代码编写 | 功能实现、重构、Bug修复 |
| REVIEWER | 代码审查 | PR review、代码质量 |
| ARCHITECT | 架构设计 | 技术方案、接口设计 |
| TESTER | 测试验证 | 单元测试、集成测试 |
| DIAGNOSTIC | 问题诊断 | 根因分析、调试 |
| UI_VERIFY | UI 验证 | 截图对比、无障碍检查 |

---

## 📄 许可证

[Apache License 2.0](LICENSE)

---

<div align="center">

**⭐ 如果觉得有用，请给个 Star ⭐**

**GitHub**: https://github.com/sprintcycle/sprintcycle

</div>
