# SprintCycle

🚀 **AI 驱动的敏捷开发迭代框架**

[English](README.md) | 简体中文

SprintCycle 是一个基于 AI 的敏捷开发框架，支持多轮代码迭代、自动测试、智能验证。

## ✨ 特性

- 🔄 **多轮迭代** - Sprint 式迭代开发，支持任务拆分、自动验证、迭代修复
- 🤖 **AI 驱动** - 集成 Aider、Claude、Cursor 等 AI 编程工具
- ✅ **自动验证** - 代码质量检查、测试覆盖率、UI 验证
- 📚 **知识库** - 迭代经验自动沉淀，支持知识复用
- 🔧 **可扩展** - 插件化架构，支持自定义 Agent 和验证器

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/sprintcycle.git
cd sprintcycle

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 设置 API Key 环境变量
export LLM_API_KEY=your_api_key_here
```

### 使用

```python
from sprintcycle.chorus import SprintChain

# 创建迭代链
chain = SprintChain("/path/to/your/project")

# 执行任务
result = chain.run_task("实现用户登录功能")
print(result)
```

### CLI 使用

```bash
# 查看状态
python cli.py status -p /path/to/project

# 执行任务
python cli.py run -p /path/to/project -t "修复登录bug"
```

## 📖 文档

- [架构设计](docs/ARCHITECTURE.md)
- [开发指南](docs/DEVELOPMENT.md)
- [变更日志](CHANGELOG.md)

## 🧪 测试

```bash
# 运行测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=sprintcycle
```

## 📦 项目结构

```
sprintcycle/
├── sprintcycle/          # 核心模块
│   ├── chorus.py         # Agent 协调器
│   ├── optimizations.py  # 优化工具类
│   ├── cache.py          # API 缓存
│   └── agents/           # Agent 模块
├── tests/                # 测试文件
├── docs/                 # 文档
├── cli.py                # 命令行工具
└── config.yaml.example   # 配置模板
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[Apache License 2.0](LICENSE)

## 🙏 致谢

- [Aider](https://github.com/paul-gauthier/aider) - AI 编程助手
- [Playwright](https://playwright.dev/) - 浏览器自动化
