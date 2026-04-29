# 贡献指南

感谢您对 SprintCycle 项目的兴趣！本指南将帮助您了解如何为项目做出贡献。

## 目录

- [快速开始](#快速开始)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [提交规范](#提交规范)
- [问题反馈](#问题反馈)

## 快速开始

1. Fork 本仓库
2. 克隆您的 Fork：`git clone https://github.com/YOUR_USERNAME/sprintcycle.git`
3. 安装依赖：`pip install -e .`
4. 创建分支：`git checkout -b feature/your-feature-name`

## 开发环境设置

### 前置要求

- Python 3.10+
- Git
- Node.js 18+ (用于 Playwright MCP)

### 安装开发依赖

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/sprintcycle.git
cd sprintcycle

# 安装项目依赖
pip install -e .

# 安装开发依赖
pip install pytest pytest-cov pytest-asyncio

# 运行测试
pytest
```

### 环境变量

复制 `.env.example` 到 `.env.local` 并配置：

```bash
cp .env.example .env.local
```

## 代码规范

### Python 代码规范

- 遵循 PEP 8
- 使用 type hints
- 编写 docstrings
- 最大行长：120 字符

### 代码格式

使用 `ruff` 格式化代码：

```bash
ruff format .
ruff check --fix .
```

### 命名规范

| 类型 | 命名规范 | 示例 |
|------|----------|------|
| 类 | PascalCase | `SprintChain` |
| 函数 | snake_case | `run_task` |
| 常量 | UPPER_SNAKE | `MAX_RETRIES` |
| 私有属性 | _prefix | `_internal_state` |

## 测试指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=sprintcycle --cov-report=term-missing

# 运行特定测试
pytest tests/test_chorus.py -v

# 运行测试并生成 HTML 报告
pytest --cov=sprintcycle --cov-report=html
```

### 编写测试

1. 测试文件命名：`test_<module_name>.py`
2. 测试类命名：`Test<ClassName>`
3. 测试方法命名：`test_<description>`

示例：

```python
class TestChorusAnalyze:
    """测试 Chorus 分析功能"""
    
    def test_analyze_coder_task(self, chorus):
        """测试 coder 任务分析"""
        result = chorus.analyze("Write a function")
        assert result.agent == "coder"
```

### 覆盖率要求

- 新代码覆盖率：≥ 80%
- 关键模块覆盖率：≥ 90%

## 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试更新
- `chore`: 构建/工具更新

### 示例

```
feat(chorus): 添加任务分析功能

- 支持自动识别 coder/reviewer/architect
- 集成知识库进行相似任务匹配

Closes #123
```

## 分支管理

- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支
- `release/*`: 发布分支

## 问题反馈

### 创建 Issue

1. 使用清晰的标题
2. 描述问题或功能
3. 提供复现步骤（针对 bug）
4. 添加相关标签

### Pull Request

1. 保持 PR 较小且专注
2. 描述更改内容
3. 添加测试
4. 更新文档（如有必要）

## 许可证

通过贡献代码，您同意您的代码将按照项目许可证发布。

## 联系方式

- GitHub Issues: [项目 Issues](https://github.com/your-repo/sprintcycle/issues)
- 讨论群: [加入讨论](https://github.com/your-repo/sprintcycle/discussions)

感谢您的贡献！
