# SprintCycle 开发指南

本指南涵盖两个场景：贡献 SprintCycle 框架本身代码，以及使用 SprintCycle 开发自己的产品。

---

## 场景 A: 贡献 SprintCycle 框架开发

### 环境准备

```bash
# 克隆代码
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 运行部署脚本
./scripts/start_develop/dev-setup.sh

# 激活开发环境
source scripts/start_develop/activate.sh
```

### 安装开发依赖

```bash
# 推荐：完整开发环境
pip install -e ".[full,dev,mcp-sse,mutation]"

# 基础开发
pip install -e ".[dev]"
```

### 运行测试

```bash
# P0 核心测试（快速验证）
pytest tests/test_p0_runtime.py -v

# 完整测试套件
pytest tests/ -v

# 单个测试文件
pytest tests/test_agents.py -v

# 带覆盖率
pytest --cov=sprintcycle tests/
```

### 代码质量检查

```bash
# Ruff lint
ruff check sprintcycle/

# MyPy 类型检查
mypy sprintcycle/ --ignore-missing-imports

# 架构分层检查
lint-imports

# 完整检查
./scripts/start_develop/run-lint.sh
```

### Dashboard 前端开发

```bash
# 安装 Node.js 依赖
cd sprintcycle/dashboard/frontend
npm install

# 开发模式（热重载）
npm run dev

# 构建生产版本
npm run build
```

### MCP Server 开发

```bash
# stdio 模式（本地 CLI）
sprintcycle serve

# SSE 模式（远程 Agent）
sprintcycle serve --transport sse --host 0.0.0.0 --port 8765
```

### 治理插件开发

1. 在 `sprintcycle/governance/plugins/` 创建插件
2. 实现 `GovernancePlugin` 接口
3. 注册到 `sprintcycle/governance/pluggy_host.py`

---

## 场景 B: 使用 SprintCycle 开发产品

### 安装

```bash
# pip 安装
pip install sprintcycle

# 完整功能
pip install sprintcycle[dashboard,mcp-sse]
```

### 快速开始

```bash
# 初始化
sprintcycle init

# 直接执行
sprintcycle run "为登录模块添加单元测试"

# 生成计划（不执行）
sprintcycle plan "实现用户注册功能" -m auto

# 启用治理
sprintcycle run "重构配置模块" --governance-level standard
```

### 配置 LLM API

创建 `.env` 文件：

```env
# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o

# 或 DeepSeek
DEEPSEEK_API_KEY=xxx
```

### Python API 使用

```python
from sprintcycle import SprintCycle

api = SprintCycle()
result = await api.run("实现用户认证模块", project_path="./my-app")
```

### Dashboard 监控

```bash
# 安装 Dashboard 依赖
pip install sprintcycle[dashboard]

# 启动
sprintcycle dashboard

# 开发模式
sprintcycle dashboard --dev
```

### MCP 集成

```bash
# 启动 MCP Server
sprintcycle serve

# SSE 模式（供远程 Agent 调用）
sprintcycle serve --transport sse
```

### 治理级别配置

| 级别 | 检查项 | 适用场景 |
|------|--------|---------|
| `minimal` | 基础语法检查 | 快速迭代 |
| `standard` | 静态分析 + 架构检查 | 日常开发 |
| `strict` | 全部检查 + 突变测试 | 发布前验证 |

```bash
sprintcycle run "功能开发" --governance-level standard
```

### HITL 人机回环

```bash
# 启用交互确认
sprintcycle run "重构模块" --yes

# 手动确认每个步骤
sprintcycle run "复杂任务"
```

### 缓存配置

```env
# 本地缓存（默认）
SPRINTCYCLE_CACHE_DIR=./cache

# Redis 缓存（需要 redis 包）
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
```

---

## 便捷脚本

所有脚本位于 `scripts/start_develop/` 目录：

| 脚本 | 功能 |
|------|------|
| `./activate.sh` | 激活开发环境 |
| `./run-dashboard.sh` | 启动 Web Dashboard |
| `./run-mcp.sh` | 启动 MCP Server |
| `./run-tests.sh` | 运行测试套件 |
| `./run-lint.sh` | 代码质量检查 |
| `./dev-setup.sh` | 一键环境部署 |

使用前需先激活环境：

```bash
source scripts/start_develop/activate.sh
```

---

## 常见问题

### Q: sprintcycle 命令找不到
```bash
# 确保在虚拟环境中
source .venv/bin/activate

# 重新安装
pip install -e .
```

### Q: ModuleNotFoundError
```bash
# 清除缓存
rm -rf __pycache__ .pytest_cache

# 重新安装依赖
pip install -e ".[full,dev,mcp-sse]"
```

### Q: 测试失败
```bash
# 确认测试依赖已安装
pip install -e ".[dev]"

# 单独运行
pytest tests/test_specific.py -v
```

---

**文档版本**: 2.0  
**最后更新**: 2024
