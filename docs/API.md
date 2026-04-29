# SprintCycle API 文档

## 核心模块

### SprintChain

Sprint 链式执行器，主要负责管理 Sprint 生命周期。

#### 类定义

```python
from sprintcycle.sprint_chain import SprintChain

chain = SprintChain(project_path: str, review_enabled: bool = False)
```

#### 方法

##### `run_task(task, files=None, agent=None, tool=None) -> ExecutionResult`

执行单个任务。

**参数：**
- `task` (str): 任务描述
- `files` (List[str], optional): 相关文件列表
- `agent` (AgentType, optional): 指定代理类型
- `tool` (ToolType, optional): 指定工具

**返回：**
- `ExecutionResult`: 执行结果

##### `run_sprint(sprint_name, tasks, tool=None) -> Dict`

运行 Sprint。

**参数：**
- `sprint_name` (str): Sprint 名称
- `tasks` (List[Dict]): 任务列表
- `tool` (ToolType, optional): 工具类型

##### `create_sprint(name, goals) -> Dict`

创建新 Sprint。

##### `auto_plan_from_prd(prd_path) -> Dict`

从 PRD 文档自动生成 Sprint 规划。

##### `get_results() -> List[Dict]`

获取执行结果。

##### `get_kb_stats() -> Dict`

获取知识库统计信息。

---

### Chorus

任务编排和智能路由模块。

#### 类定义

```python
from sprintcycle.chorus import Chorus, KnowledgeBase

kb = KnowledgeBase(project_path: str)
chorus = Chorus(kb)
```

#### 方法

##### `analyze(task: str) -> AgentType`

分析任务并返回合适的代理类型。

**返回：**
- `AgentType`: CODERS / REVIEWER / ARCHITECT / TESTER / UI_VERIFY

##### `dispatch(project_path, task, files=None, agent=None, tool=None) -> ExecutionResult`

分发任务到合适的执行器。

##### `KnowledgeBase.record_task(task, result, files)`

记录任务到知识库。

##### `KnowledgeBase.find_similar(task) -> List[Dict]`

查找相似任务。

##### `KnowledgeBase.get_stats() -> Dict`

获取知识库统计。

---

### ExecutionLayer

底层执行层，支持多种工具。

#### 类定义

```python
from sprintcycle.chorus import ExecutionLayer

layer = ExecutionLayer()
```

#### 方法

##### `check_available(tool: ToolType) -> bool`

检查工具是否可用。

##### `list_available() -> Dict[str, bool]`

列出所有可用工具。

##### `execute(project_path, task, files, tool=None, agent=None) -> ExecutionResult`

执行任务。

---

## 枚举类型

### ToolType

```python
from sprintcycle.chorus import ToolType

# 值: CURSOR, CLAUDE, AIDER
```

### AgentType

```python
from sprintcycle.chorus import AgentType

# 值: CODER, REVIEWER, ARCHITECT, TESTER, UI_VERIFY

# 从字符串创建
agent = AgentType.from_string("coder")
```

### TaskStatus

```python
from sprintcycle.chorus import TaskStatus

# 值: PENDING, RUNNING, SUCCESS, FAILED, RETRYING
```

---

## 数据类

### ExecutionResult

```python
from sprintcycle.chorus import ExecutionResult

result = ExecutionResult(
    success: bool,
    output: str,
    duration: float,
    tool: str,
    files_changed: Dict = {...},
    retries: int = 0,
    error: Optional[str] = None
)
```

**属性：**
- `success`: 是否成功
- `output`: 执行输出
- `duration`: 执行时长（秒）
- `tool`: 使用的工具
- `files_changed`: 文件变更
- `retries`: 重试次数
- `error`: 错误信息
- `files_list`: 所有变更文件的列表
- `has_changes`: 是否有变更

---

## MCP Server

### 工具列表

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `sprintcycle_list_projects` | 列出所有项目 | - |
| `sprintcycle_list_tools` | 列出可用工具 | - |
| `sprintcycle_status` | 检查状态 | `project_path` |
| `sprintcycle_get_sprint_plan` | 获取 Sprint 规划 | `project_path` |
| `sprintcycle_run_task` | 执行任务 | `project_path`, `task` |
| `sprintcycle_run_sprint` | 运行 Sprint | `project_path`, `sprint_name`, `tasks` |
| `sprintcycle_create_sprint` | 创建 Sprint | `project_path`, `sprint_name`, `goals` |
| `sprintcycle_plan_from_prd` | 从 PRD 规划 | `project_path`, `prd_path` |
| `sprintcycle_auto_run` | 自动运行 | `project_path` |
| `sprintcycle_playwright_verify` | Playwright 验证 | `url`, `checks` |

---

## 验证模块

### PlaywrightVerifier

```python
from sprintcycle.verifiers import PlaywrightVerifier

verifier = PlaywrightVerifier(
    project_path: str = None,
    mcp_command: str = "npx @playwright/mcp@latest",
    timeout: int = 30000
)
```

#### 方法

##### `verify_page_load(url) -> Dict`

验证页面加载。

##### `get_accessibility_tree(url=None) -> Dict`

获取可访问性树。

##### `verify_element_exists(url, selector) -> Dict`

验证元素存在。

##### `verify_interaction(url, action, selector, value=None) -> Dict`

验证交互操作。

##### `verify_form(url, form_config) -> Dict`

验证表单功能。

##### `verify_navigation_flow(url, steps) -> Dict`

验证导航流程。

---

## 异常处理

### SprintCycleError

基础异常类。

```python
from sprintcycle.exceptions import SprintCycleError

raise SprintCycleError("错误信息")
```

### 其他异常

- `ConfigurationError`: 配置错误
- `ExecutionError`: 执行错误
- `ValidationError`: 验证错误
- `TimeoutError`: 超时错误
