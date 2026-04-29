# SprintCycle 技术架构 v0.3

## 1. 架构概览

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SprintCycle 架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          用户交互层 (CLI)                             │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │   │   cli.py    │  │ run_cycle.py│  │ server.py   │                 │   │
│  │   │  命令行工具  │  │   循环执行   │  │   MCP服务    │                 │   │
│  │   └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          核心业务层 (Core)                            │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │   │  chorus.py  │  │sprint_chain │  │   config    │                 │   │
│  │   │  Agent协调器 │  │   执行链     │  │   配置管理   │                 │   │
│  │   └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │   │exceptions.py│  │error_handlers│ │sprint_logger│                 │   │
│  │   │   异常体系   │  │   错误处理   │  │   日志系统   │                 │   │
│  │   └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          Agent 层                                    │   │
│  │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐│   │
│  │   │ CODER  │ │REVIEWER│ │ARCHITECT│ │ TESTER │ │DIAGNOSTIC│ │UI_VERIFY││   │
│  │   │ 编码   │ │ 审查   │ │ 架构   │ │ 测试   │ │ 诊断   │ │ UI验证 ││   │
│  │   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          工具层 (Tools)                              │   │
│  │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │   │
│  │   │ Aider  │ │ Claude │ │ Cursor │ │Playwright│ │ OpenClaw│          │   │
│  │   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          存储层 (Storage)                            │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │   │   Knowledge  │  │     Logs      │  │   Config     │            │   │
│  │   │     Base      │  │               │  │              │            │   │
│  │   │  (Markdown)   │  │   (JSON)      │  │   (YAML)     │            │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖

```
sprintcycle/
│
├── __init__.py                 # 包入口，版本号
│
├── core/                       # 核心模块
│   ├── chorus.py              # Agent 协调器
│   ├── sprint_chain.py        # Sprint 执行链
│   ├── config.py              # 配置管理 (v0.3)
│   ├── exceptions.py           # 异常体系
│   ├── sprint_logger.py       # Sprint 日志 (v0.3)
│   ├── error_handlers.py       # 错误处理 (v0.3)
│   ├── models.py              # 数据模型
│   └── ...
│
├── agents/                     # Agent 实现
│   ├── base.py                # Agent 基类
│   ├── executor.py            # 执行器
│   ├── types.py               # Agent 类型
│   ├── ui_verify_agent.py     # UI 验证 Agent
│   └── playwright_integration.py  # Playwright 集成
│
├── utils/                      # 工具模块
│   ├── logger.py              # 日志工具
│   └── ai.py                  # AI 提供者
│
├── adapters/                   # 适配器
│   ├── cursor_adapter.py
│   ├── claude_adapter.py
│   └── aider_adapter.py
│
└── skills/                     # Skill 定义
    └── self_evolution/
```

---

## 2. 核心模块详解

### 2.1 Chorus (Agent 协调器)

```python
class Chorus:
    """Agent 协调器 - 管理多 Agent 协作"""
    
    def __init__(self, config: SprintCycleConfig):
        self.config = config
        self.agents = self._init_agents()
        self.knowledge_base = KnowledgeBase()
    
    def execute_task(self, task: Task) -> ExecutionResult:
        """执行单个任务"""
        # 1. 选择合适的 Agent
        agent = self._select_agent(task)
        
        # 2. 调用 Agent 执行
        result = agent.execute(task)
        
        # 3. 沉淀知识
        self.knowledge_base.save(result)
        
        return result
```

**职责**:
- Agent 生命周期管理
- 任务分发与协调
- 知识库管理
- 错误处理与重试

### 2.2 SprintChain (执行链)

```python
class SprintChain:
    """Sprint 执行链"""
    
    def __init__(self, config: SprintCycleConfig):
        self.config = config
        self.chorus = Chorus(config)
        self.sprints = []
    
    def run(self, prd_path: str) -> SprintResults:
        """执行 Sprint 循环"""
        # 1. 加载 PRD
        prd = self._load_prd(prd_path)
        
        # 2. 创建 Sprint
        sprints = self._create_sprints(prd)
        
        # 3. 顺序执行 Sprint
        results = []
        for sprint in sprints:
            result = self._run_sprint(sprint)
            results.append(result)
        
        return SprintResults(results)
```

**职责**:
- PRD 解析与 Sprint 规划
- Sprint 顺序执行
- 结果汇总与报告

### 2.3 Config (配置管理 v0.3)

```python
@dataclass
class SprintCycleConfig:
    """SprintCycle 配置"""
    
    tools: Dict[str, ToolConfig]
    scheduler: SchedulerConfig
    review: ReviewConfig
    playwright: PlaywrightConfig
    
    # 知识库配置
    knowledge_base_path: str = "./knowledge"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # 执行配置
    execution_timeout: int = 600
    
    @classmethod
    def from_yaml(cls, path: Path) -> "SprintCycleConfig":
        """从 YAML 加载配置"""
        ...
    
    def validate(self) -> None:
        """验证配置"""
        ...
```

**特性**:
- 类型安全的 dataclass
- YAML 配置加载
- 环境变量覆盖
- 配置验证

### 2.4 Exceptions (异常体系 v0.3)

```python
# 异常层次结构
SprintCycleError (基类)
├── ConfigurationError
│   ├── ConfigFileNotFoundError
│   └── ConfigValidationError
├── TaskExecutionError
│   ├── TaskTimeoutError
│   └── TaskValidationError
├── KnowledgeBaseError
│   ├── KnowledgeNotFoundError
│   └── KnowledgeWriteError
├── ToolExecutionError
│   ├── ToolNotFoundError
│   └── ToolTimeoutError
├── ValidationError
├── RollbackError
└── FileOperationError
```

### 2.5 ErrorHandlers (错误处理 v0.3)

```python
class ErrorHandler:
    """统一错误处理器"""
    
    @classmethod
    def classify_error(cls, error: Exception) -> ErrorCategory:
        """自动分类错误"""
        ...
    
    @classmethod
    def get_recovery_suggestions(cls, category: ErrorCategory) -> List[str]:
        """获取恢复建议"""
        ...

@retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
def execute_with_retry():
    """带重试的执行"""
    ...

@handle_errors(default_return=None, reraise=True)
def safe_execute():
    """安全执行"""
    ...
```

### 2.6 SprintLogger (日志系统 v0.3)

```python
class SprintLogger:
    """Sprint 专用日志"""
    
    def start_sprint(self, sprint_id: str, name: str, tasks: int):
        """开始 Sprint"""
        ...
    
    def start_task(self, task_id: str, name: str, agent: str):
        """开始任务"""
        ...
    
    def complete_task(self, status: TaskStatus, files_changed: List[str]):
        """完成任务"""
        ...
    
    def complete_sprint(self, status: SprintStatus):
        """完成 Sprint"""
        ...
    
    def get_sprint_summary(self) -> Dict:
        """获取执行摘要"""
        ...
```

---

## 3. 数据流

### 3.1 Sprint 执行流程

```
用户输入 (PRD)
    │
    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PRD 解析                                                           │
│    └── SprintChain._load_prd() → 解析 YAML/JSON                      │
└────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Sprint 规划                                                        │
│    └── SprintChain._create_sprints() → 生成 Sprint 列表                │
└────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Sprint 执行 (循环)                                                  │
│    ┌────────────────────────────────────────────────────────────────┐ │
│    │ Sprint N 执行                                                    │ │
│    │    │                                                             │ │
│    │    ▼                                                             │ │
│    │ ┌────────────────────────────────────────────────────────────┐  │ │
│    │ │ 3.1 任务分发                                                   │  │ │
│    │ │     └── Chorus._select_agent() → 选择合适的 Agent           │  │ │
│    │ └────────────────────────────────────────────────────────────┘  │ │
│    │    │                                                             │ │
│    │    ▼                                                             │ │
│    │ ┌────────────────────────────────────────────────────────────┐  │ │
│    │ │ 3.2 Agent 执行                                               │  │ │
│    │ │     └── Agent.execute() → 调用工具执行任务                  │  │ │
│    │ └────────────────────────────────────────────────────────────┘  │ │
│    │    │                                                             │ │
│    │    ▼                                                             │ │
│    │ ┌────────────────────────────────────────────────────────────┐  │ │
│    │ │ 3.3 结果处理                                                 │  │ │
│    │ │     ├── Chorus._save_result() → 保存执行结果               │  │ │
│    │ │     ├── SprintLogger.log() → 记录执行日志                  │  │ │
│    │ │     └── KnowledgeBase.save() → 沉淀知识                     │  │ │
│    │ └────────────────────────────────────────────────────────────┘  │ │
│    │    │                                                             │ │
│    │    ▼                                                             │ │
│    │ 3.4 结果验证                                                     │ │
│    │     └── SprintChain._verify_result() → 验证是否成功             │ │
│    │                                                                     │ │
│    └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. 结果汇总                                                            │
│    └── SprintResults → JSON 格式报告                                   │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent 协作流程

```
Task 输入
    │
    ▼
┌─────────────────┐
│  CODER Agent    │ ───▶ 代码编写
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│REVIEWER Agent   │ ───▶ 代码审查
└────────┬────────┘
         │
         ▼ (发现问题时)
┌─────────────────┐
│  CODER Agent    │ ───▶ 修复问题
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TESTER Agent    │ ───▶ 编写测试
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│DIAGNOSTIC Agent │ ───▶ 问题诊断 (如有)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│UI_VERIFY Agent  │ ───▶ UI 验证 (如有)
└────────┬────────┘
         │
         ▼
    Task 完成
```

---

## 4. 扩展机制

### 4.1 Agent 扩展

```python
# 新增自定义 Agent
class CustomAgent(BaseAgent):
    """自定义 Agent"""
    
    @property
    def name(self) -> str:
        return "custom"
    
    @property
    def capabilities(self) -> List[str]:
        return ["custom_task"]
    
    async def execute(self, task: Task) -> ExecutionResult:
        """执行自定义任务"""
        ...

# 注册 Agent
Chorus.register_agent(CustomAgent)
```

### 4.2 工具扩展

```python
# 新增工具适配器
class CustomToolAdapter:
    """自定义工具适配器"""
    
    @property
    def name(self) -> str:
        return "custom_tool"
    
    async def execute(self, command: str, args: Dict) -> ExecutionResult:
        """执行工具命令"""
        ...

# 注册工具
Chorus.register_tool(CustomToolAdapter)
```

---

## 5. 部署架构

### 5.1 单机部署

```
┌─────────────────────────────────────────────┐
│              SprintCycle Server            │
│  ┌─────────────────────────────────────┐   │
│  │              Python Runtime          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────┐ │   │
│  │  │  CLI/Web │ │  Core   │ │ Tools │ │   │
│  │  └─────────┘ └─────────┘ └───────┘ │   │
│  └─────────────────────────────────────┘   │
│                    │                         │
│                    ▼                         │
│  ┌─────────────────────────────────────┐   │
│  │          本地存储 (Volume)           │   │
│  │   ├── knowledge/                    │   │
│  │   ├── logs/                         │   │
│  │   ├── config.yaml                   │   │
│  │   └── results/                      │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 5.2 容器部署

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "cli.py", "run"]
```

---

## 6. 安全性

### 6.1 权限控制

| 功能 | 权限 | 说明 |
|------|------|------|
| 项目访问 | 读 | 查看项目和任务 |
| 任务执行 | 写 | 执行代码修改 |
| 知识库写入 | 写 | 沉淀执行经验 |
| 配置修改 | 管理 | 更改系统配置 |

### 6.2 安全措施

| 措施 | 说明 |
|------|------|
| 沙箱执行 | 工具在隔离环境执行 |
| 权限最小化 | 仅请求必要权限 |
| 审计日志 | 记录所有操作 |
| 输入验证 | 防止注入攻击 |

---

## 7. 监控与运维

### 7.1 监控指标

| 指标 | 采集方式 | 告警阈值 |
|------|---------|---------|
| 执行成功率 | 日志统计 | < 95% |
| 平均执行时间 | 日志统计 | > 5min |
| 错误率 | 日志统计 | > 5% |
| 内存使用 | 系统监控 | > 500MB |

### 7.2 日志级别

| 级别 | 用途 | 触发条件 |
|------|------|---------|
| DEBUG | 开发调试 | 开发环境 |
| INFO | 一般信息 | 正常执行 |
| WARNING | 警告 | 可恢复错误 |
| ERROR | 错误 | 执行失败 |
| CRITICAL | 严重 | 系统故障 |

---

*最后更新: 2026-04-28*
*维护者: SprintCycle Team*
