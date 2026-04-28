SprintCycle - 自进化敏捷开发框架
===============================

一键执行入口：PRD解析 → 任务拆分 → 代码生成 → 多源验证 → 自进化

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/your-username/sprintcycle.git
cd sprintcycle

# 安装依赖
pip install -r requirements.txt

# 安装Playwright（用于前端验证）
playwright install
```

### 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，添加你的API密钥
vim .env
```

### 基本使用

```bash
# 自动修复项目问题
python run_cycle.py /path/to/your/project --autofix

# 执行PRD驱动的开发
python run_cycle.py /path/to/your/project /path/to/your/prd.md

# 只扫描不修复
python run_cycle.py /path/to/your/project --scan-only
```

## 示例：修复学玩派项目

```bash
# 自动修复学玩派的启动问题
python run_cycle.py /root/xuewanpai --autofix
```

执行成功后，会输出：
- 发现的问题
- 修复的问题
- 生成的文件

## 核心特性

- 🤖 **AI驱动全流程**：自动完成需求分析、任务拆分、代码生成、测试验证
- 🔄 **自进化机制**：通过执行结果持续优化自身能力
- 🎯 **多源验证**：Playwright MCP + CLI + 日志 + 测试用例 五源并行验证
- 🛠️ **灵活扩展**：支持多种AI编程工具（Aider、Cursor、Claude等）
- 📦 **开箱即用**：无需复杂部署，Python虚拟环境一键启动

## 架构设计

```
┌───────────────────────────────────────────────────┐
│                   SprintCycle                    │
├───────────┬───────────┬───────────┬─────────────┤
│  Scanner  │ Autofix   │ Verifier  │  Executor   │
├───────────┼───────────┼───────────┼─────────────┤
│  问题扫描 │ 自动修复  │ 多源验证  │ 任务执行    │
└───────────┴───────────┴───────────┴─────────────┘
         │           │           │           │
         ▼           ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│  Scanner  │ │ Autofix   │ │ Playwright│ │   Aider   │
│  Module   │ │  Engine   │ │   MCP     │ │  Cursor   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘
```

## 开发指南

### 添加新的工具支持

在`sprintcycle/config.py`中添加新的工具配置：

```python
@dataclass
class ToolConfig:
    """工具配置"""
    command: str
    timeout: int = 180
    # 添加新工具参数
    api_key: Optional[str] = None
```

然后在`config.yaml`中配置：

```yaml
tools:
  new_tool:
    command: new-tool-agent
    timeout: 180
    api_key: ${NEW_TOOL_API_KEY}
```

### 扩展问题扫描器

在`sprintcycle/scanner.py`中添加新的扫描方法：

```python
def scan_new_problem_type(self) -> List[str]:
    """扫描新类型的问题"""
    issues = []
    # 实现扫描逻辑
    return issues
```

然后在`scan_all()`方法中调用：

```python
def scan_all(self) -> List[str]:
    # ...
    issues.extend(self.scan_new_problem_type())
    # ...
```

## 贡献指南

欢迎提交Issue和Pull Request！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

MIT License - 详见LICENSE文件
