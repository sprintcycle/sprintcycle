# SprintCycle Skill

通过 MCP 协议启动 SprintCycle，获取 Sprint 规划详情和执行详情。

## 架构

```
扣子 Skill (薄壳)
      │
      ▼ MCP 协议
┌─────────────────────────────────┐
│         MCP Server              │
│  ┌─────────────────────────────┐│
│  │ SprintChain (Sprint 管理)   ││
│  │         ↓                   ││
│  │ Chorus (Agent 协调)         ││
│  │         ↓                   ││
│  │ ChorusAdapter (工具路由)    ││
│  │    ┌────┼────┐             ││
│  │    ↓    ↓    ↓             ││
│  │ Cursor Claude Aider         ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
```

## MCP 工具

### sprintcycle_list_projects
列出所有 SprintCycle 项目。

### sprintcycle_list_tools
列出可用的执行工具 (cursor/claude/aider)。

### sprintcycle_status
检查环境和项目状态。
- project_path: 项目路径

### sprintcycle_get_sprint_plan
获取 Sprint 规划详情。
- project_path: 项目路径

### sprintcycle_get_execution_detail
获取执行详情。
- project_path: 项目路径

### sprintcycle_run_task
执行单个任务。
- project_path: 项目路径
- task: 任务描述
- files: 文件列表 (可选)
- agent: coder/reviewer/architect/tester (可选)
- tool: cursor/claude/aider (可选)

### sprintcycle_run_sprint
运行 Sprint。
- project_path: 项目路径
- sprint_name: Sprint 名称
- tasks: 任务列表
- tool: 指定工具 (可选)

### sprintcycle_create_sprint
创建新 Sprint。
- project_path: 项目路径
- sprint_name: Sprint 名称
- goals: 目标列表

## 使用示例

查看 Sprint 规划：
```
sprintcycle_get_sprint_plan({"project_path": "/root/xuewanpai"})
```

执行任务：
```
sprintcycle_run_task({
  "project_path": "/root/xuewanpai",
  "task": "优化首页加载",
  "files": ["frontend/src/views/Home.vue"],
  "agent": "coder",
  "tool": "aider"
})
```

## MCP Server 启动

```bash
python /root/sprintcycle/mcp/server.py
```
