# Chorus.py 拆分分析报告

## 当前状态
- **文件大小**: 988 行
- **当前覆盖率**: 65%
- **模块数**: 多个功能模块混杂

## 建议拆分方案

### 方案 1: 按功能拆分 (推荐)

```
sprintcycle/
├── chorus/
│   ├── __init__.py          # 导出公共接口
│   ├── types.py             # ToolType, AgentType, TaskStatus, ExecutionResult 等
│   ├── config.py            # Config 配置管理
│   ├── knowledge.py          # KnowledgeBase 知识库
│   ├── execution.py          # ExecutionLayer 统一执行层
│   ├── adapter.py            # ChorusAdapter 工具路由层
│   ├── dispatcher.py         # Chorus Agent 协调层
│   └── helpers.py           # normalize_files_changed 等工具函数
```

### 方案 2: 按关注点拆分

```
sprintcycle/
├── chorus/
│   ├── core/                # 核心类型和接口
│   │   ├── __init__.py
│   │   ├── types.py
│   │   └── config.py
│   ├── agents/              # Agent 相关
│   │   ├── __init__.py
│   │   ├── chorus.py        # Chorus 协调层
│   │   └── adapter.py       # ChorusAdapter 路由
│   ├── execution/           # 执行相关
│   │   ├── __init__.py
│   │   ├── layer.py         # ExecutionLayer
│   │   └── knowledge.py     # KnowledgeBase
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── files.py         # 文件变更处理
```

## 各模块详细分析

### 1. 调度器模块 (Scheduler) - 建议提取
**当前行号**: 540-560
**职责**:
- 任务队列管理
- 并发控制
- 优先级调度

### 2. 执行器模块 (Executor)
**当前行号**: 530-720
**职责**:
- ExecutionLayer: 统一执行层
- 工具调用 (AIDER, Claude, Cursor)
- 重试机制

### 3. 监控器模块 (Monitor)
**当前行号**: 现有模块分散
**职责**:
- 进度跟踪 (TaskProgress)
- 状态管理
- 健康检查

## 拆分风险评估

| 拆分项 | 风险等级 | 影响范围 | 建议 |
|--------|---------|---------|------|
| 类型定义拆分 | 🟢 低 | 无外部依赖 | 可立即执行 |
| Config 拆分 | 🟢 低 | 内部使用 | 可执行 |
| KnowledgeBase 拆分 | 🟡 中 | Chorus 使用 | 需测试验证 |
| ExecutionLayer 拆分 | 🟡 中 | ChorusAdapter 依赖 | 需接口抽象 |
| Chorus 协调层拆分 | 🔴 高 | 全局影响 | 暂缓 |

## 实施建议

### Phase 1: 准备阶段 (低风险)
1. 创建 `chorus/types.py` - 提取类型定义
2. 创建 `chorus/config.py` - 提取 Config
3. 创建 `chorus/helpers.py` - 提取工具函数
4. **不改变现有接口**

### Phase 2: 重构阶段 (中风险)
1. 提取 KnowledgeBase 到独立模块
2. 提取 ExecutionLayer 到独立模块
3. 使用抽象接口解耦

### Phase 3: 高级重构 (高风险)
1. 拆分 Chorus 主类
2. 实现策略模式
3. 添加事件驱动架构

## 验证清单

拆分完成后需要验证:
- [ ] 所有现有测试通过
- [ ] 覆盖率不下降
- [ ] 外部导入未破坏 (向后兼容)
- [ ] 性能无明显下降

---
注意: 本分析仅供决策参考，实际拆分需谨慎评估风险。
