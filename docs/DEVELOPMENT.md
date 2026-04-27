# SprintCycle 开发指南

**版本**: v0.1  
**更新日期**: 2026-04-27

---

## 开发环境

### 环境要求

- Python >= 3.9
- pip

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/sprintcycle.git
cd sprintcycle

# 安装依赖
pip install -r requirements.txt

# 配置
cp config.yaml.example config.yaml
```

### 环境变量

```bash
# 设置 API Key
export LLM_API_KEY='your_api_key_here'
```

---

## 项目结构

```
sprintcycle/
├── sprintcycle/          # 核心模块
│   ├── chorus.py         # SprintChain 引擎
│   ├── optimizations.py  # 优化工具类
│   ├── cache.py          # API 缓存
│   ├── models.py         # 数据模型
│   └── agents/           # Agent 模块
├── tests/                # 测试文件
├── docs/                 # 文档
├── config/               # 配置文件
├── cli.py                # 命令行工具
└── run_cycle.py          # 执行入口
```

---

## 快速开始

### CLI 使用

```bash
# 查看状态
python cli.py status -p /path/to/project

# 执行任务
python cli.py run -p /path/to/project -t "实现用户登录"
```

### Python API

```python
from sprintcycle.chorus import SprintChain

# 初始化
chain = SprintChain("/path/to/project")

# 执行任务
result = chain.run_task("实现用户登录功能")
```

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_chorus.py -v

# 查看覆盖率
pytest tests/ --cov=sprintcycle
```

---

## 开发指南

### 添加新 Agent

```python
# 1. 在 AgentType 枚举中添加
class AgentType(str, Enum):
    coder = "coder"
    reviewer = "reviewer"
    new_agent = "new_agent"  # 新类型

# 2. 实现执行逻辑
async def execute_new_agent(task, context):
    # 实现具体逻辑
    pass
```

### 添加新验证器

```python
# 继承 BaseVerifier
class MyVerifier(BaseVerifier):
    def verify(self, result) -> bool:
        # 实现验证逻辑
        return True
```

---

## 常见问题

### Q: PRD 解析失败？

检查：
1. YAML 格式是否正确
2. 是否包含 `sprints:` 键
3. 每个 Sprint 是否有 `tasks:` 列表

### Q: 任务执行超时？

解决：
1. 调整配置中的 `timeout` 值
2. 优化任务粒度
3. 使用 PRD 拆分功能

### Q: files_changed 为空？

这是正常的，对于：
- 只读操作
- 验证任务
- 诊断任务

---

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

---

## 许可证

Apache License 2.0

---

*SprintCycle v0.1*
