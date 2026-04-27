# SprintCycle

<div align="center">

**AI 驱动的敏捷开发迭代框架**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-0.2.0-orange.svg)](CHANGELOG.md)

[English](README.md) | 简体中文

</div>

---

## 📖 产品介绍

SprintCycle 是一个 **AI 驱动的敏捷开发迭代框架**，自动化从需求到部署的整个迭代生命周期。它结合智能任务规划、多 Agent 协作和持续自进化，帮助开发者更快地构建更好的软件。

### 核心理念

```
需求文档(PRD) → Sprint规划 → Agent执行 → 验证测试 → 知识沉淀 → 自我进化
```

---

## 🎯 两种使用方式

SprintCycle 支持 **两种灵活的使用方式**：

### 方式一：CLI（命令行工具）

直接通过命令行使用，适合本地开发和自动化：

```bash
# 初始化项目
sprintcycle init -p /path/to/project

# 从 PRD 执行开发
sprintcycle run -p /path/to/project --prd requirements.yaml

# 运行自进化闭环
sprintcycle sprint auto-run -p /path/to/project
```

**适用场景**：本地开发、CI/CD 流水线、自动化脚本

### 方式二：OpenClaw 技能 + MCP（推荐 AI Agent 使用）

通过 OpenClaw 技能配合 MCP（模型上下文协议）触发，自然语言驱动开发：

```python
# 在 AI 助手中（如扣子/Claude/GPT）
# 只需用自然语言描述你想构建的产品

"用 SprintCycle 开发一个科技新闻网站：
- 前端：新闻列表和详情页
- 后端：FastAPI + SQLite
- 功能：查看历史、分类筛选"

# SprintCycle MCP 工具会自动被调用：
# - sprintcycle_init（初始化）
# - sprintcycle_plan_from_prd（生成 PRD）
# - sprintcycle_run_sprint（执行开发）
# - sprintcycle_playwright_verify（UI 验证）
# - 返回完成的项目
```

**适用场景**：AI 驱动开发、自然语言工作流、智能自动化

| 特性 | CLI | OpenClaw + MCP |
|------|-----|----------------|
| 本地开发 | ✅ | ✅ |
| 自然语言输入 | ❌ | ✅ |
| AI Agent 集成 | ❌ | ✅ |
| 自动规划 | 手动 | ✅ 自动 |
| 适用对象 | 开发者 | AI Agent |

---

## ✨ 核心特性

### 🔄 多轮迭代
- Sprint 式敏捷开发，自动任务拆解
- 支持迭代优化和 Bug 修复
- 事务性回滚机制

### 🤖 多 Agent 协作
| Agent | 角色 | 能力 |
|-------|------|------|
| CODER | 代码编写 | 功能实现、重构、Bug修复 |
| REVIEWER | 代码审查 | PR review、代码质量、最佳实践 |
| ARCHITECT | 架构设计 | 技术方案、接口设计、系统设计 |
| TESTER | 测试验证 | 单元测试、集成测试、覆盖率 |
| DIAGNOSTIC | 问题诊断 | 根因分析、调试、日志分析 |
| UI_VERIFY | UI 验证 | 截图对比、无障碍检查 |

### ✅ 智能验证
- **五源验证系统**：测试结果、代码审查、运行时、UI、差异验证
- **Playwright 集成**：自动化 UI 测试和视觉回归
- **代码质量检查**：Lint、类型检查、复杂度分析

### 📚 知识库
- 自动沉淀每次迭代的经验
- 任务成功/失败模式学习
- 可复用的解决方案和最佳实践

### 🧬 自进化能力
SprintCycle 通过 9 阶段闭环实现自我进化：

1. **主线抽取** - 分析历史，提取进化模式
2. **PRD 生成** - 自动生成下一阶段需求
3. **迭代执行** - 执行开发任务
4. **产品评估** - 度量产品改进
5. **框架评估** - 评估框架性能
6. **Bug 修复** - 发现并修复框架 Bug
7. **框架优化** - 增强能力
8. **集成测试** - 验证变更
9. **自我迭代** - 更新进化技能

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Git

### 安装

```bash
# 克隆仓库
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 设置 LLM API Key
export LLM_API_KEY=your_api_key_here
```

### 使用（CLI 方式）

```bash
# 初始化项目
python cli.py init -p /path/to/your/project

# 查看项目状态
python cli.py status -p /path/to/your/project

# 执行单个任务
python cli.py run -p /path/to/your/project -t "实现用户认证功能"

# 从 PRD 执行
python cli.py run -p /path/to/your/project --prd prd/requirements.yaml

# 运行自进化闭环
python cli.py sprint auto-run -p /path/to/your/project
```

### 使用（OpenClaw + MCP 方式）

在已安装 OpenClaw 技能的 AI 助手（扣子、Claude 等）中：

```
用户: "帮我开发一个博客系统，需要用户认证和文章管理"

AI 助手: 
  → 调用 sprintcycle_init
  → 调用 sprintcycle_plan_from_prd（自动生成 PRD）
  → 调用 sprintcycle_auto_run
  → 调用 sprintcycle_playwright_verify
  → 返回完成的项目
```

---

## 📚 文档

### 入门指南
- [快速入门](docs/QUICKSTART.md) - 分步教程
- [配置指南](docs/CONFIGURATION.md) - 详细配置选项

### 架构设计
- [架构概览](docs/ARCHITECTURE.md) - 系统设计和组件
- [开发指南](docs/DEVELOPMENT.md) - 如何扩展 SprintCycle

---

## 🛠️ CLI 命令参考

| 命令 | 说明 |
|------|------|
| `init` | 初始化 SprintCycle |
| `status` | 查看项目状态和统计 |
| `run` | 执行任务或 PRD 迭代 |
| `sprint plan` | 查看 Sprint 规划 |
| `sprint create` | 创建新 Sprint |
| `sprint run` | 执行指定 Sprint |
| `sprint auto-run` | 执行所有待执行 Sprint |
| `verify playwright` | 运行 Playwright UI 验证 |
| `verify frontend` | 运行前端无障碍检查 |
| `scan` | 扫描项目问题 |
| `autofix` | 自动修复检测到的问题 |
| `rollback` | 回滚最近的修改 |
| `knowledge show` | 查看知识库 |
| `dashboard` | 启动 Web Dashboard |

---

## 🔌 MCP 工具

SprintCycle 提供 **18 个 MCP 工具** 供 AI Agent 集成：

### 项目管理
| 工具 | 说明 |
|------|------|
| `sprintcycle_list_projects` | 列出所有项目 |
| `sprintcycle_list_tools` | 列出可用工具 |
| `sprintcycle_status` | 获取项目状态 |

### Sprint 管理
| 工具 | 说明 |
|------|------|
| `sprintcycle_get_sprint_plan` | 获取 Sprint 规划 |
| `sprintcycle_create_sprint` | 创建 Sprint |
| `sprintcycle_run_sprint` | 执行 Sprint |
| `sprintcycle_run_sprint_by_name` | 按名称执行 |
| `sprintcycle_auto_run` | 自动执行所有 |
| `sprintcycle_plan_from_prd` | 从 PRD 生成 |

### 任务执行
| 工具 | 说明 |
|------|------|
| `sprintcycle_run_task` | 执行单个任务 |

### 验证
| 工具 | 说明 |
|------|------|
| `sprintcycle_playwright_verify` | Playwright 验证 |
| `sprintcycle_verify_frontend` | 前端验证 |
| `sprintcycle_verify_visual` | 视觉验证 |

### 问题管理
| 工具 | 说明 |
|------|------|
| `sprintcycle_scan_issues` | 扫描问题 |
| `sprintcycle_autofix` | 自动修复 |
| `sprintcycle_rollback` | 回滚修改 |

### 知识库
| 工具 | 说明 |
|------|------|
| `sprintcycle_get_kb_stats` | 知识库统计 |
| `sprintcycle_get_execution_detail` | 执行详情 |

---

## 📦 项目结构

```
sprintcycle/
├── sprintcycle/           # 核心框架
│   ├── chorus.py          # Agent 协调器
│   ├── sprint_chain.py    # Sprint 执行链
│   └── agents/            # Agent 实现
├── dashboard/             # Web Dashboard
├── tests/                 # 测试套件
├── docs/                  # 文档
├── cli.py                 # 命令行工具
└── config.yaml.example    # 配置模板
```

---

## 🤝 贡献

欢迎参与贡献！

1. **Fork** 本仓库
2. **创建** 特性分支 (`git checkout -b feature/amazing-feature`)
3. **提交** 更改 (`git commit -m 'Add amazing feature'`)
4. **推送** 分支 (`git push origin feature/amazing-feature`)
5. **创建** Pull Request

---

## 📄 许可证

本项目采用 **Apache License 2.0** 许可证。

---

## 🙏 致谢

- [Aider](https://github.com/paul-gauthier/aider) - AI 结对编程
- [Playwright](https://playwright.dev/) - 浏览器自动化
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架

---

<div align="center">

**由 SprintCycle 团队用 ❤️ 构建**

[⬆ 返回顶部](#sprintcycle)

</div>
