#!/usr/bin/env python3
"""
SprintCycle MCP Server v2.0 - 优化版

优化点：
1. 任务调度器 - 支持超时重试、并发控制
2. 流式进度反馈
3. 知识库激活
4. 配置外部化
5. 模块化拆分 - chorus.py, sprint_chain.py
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# 重新导出 Chorus 模块的公共接口
from .chorus import (
    Config,
    ToolType,
    AgentType, 
    TaskStatus,
    ExecutionResult,
    TaskProgress,
    KnowledgeBase,
    ExecutionLayer,
    ChorusAdapter,
    Chorus
)

# 重新导出 SprintChain 模块
from .sprint_chain import SprintChain

# Loguru 日志系统
from loguru import logger
import sys as _sys

# 配置 Loguru
logger.remove()  # 移除默认 handler
_log_config = {
    "rotation": os.environ.get("SPRINT_LOG_ROTATION", "100 MB"),
    "retention": os.environ.get("SPRINT_LOG_RETENTION", "14 days"),
    "level": os.environ.get("SPRINT_LOG_LEVEL", "INFO"),
    "format_console": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
    "format_file": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
}

logger.add(
    _sys.stderr,
    format=_log_config["format_console"],
    level=_log_config["level"]
)

import os as _os
_log_dir = Path(_os.environ.get("SPRINT_ROOT", str(Path(__file__).parent.parent))) / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
logger.add(
    str(_log_dir / "sprintcycle_{time:YYYY-MM-DD}.log"),
    rotation=_log_config["rotation"],
    retention=_log_config["retention"],
    compression="zip",
    level="DEBUG",
    format=_log_config["format_file"]
)

# MCP Server
from .mcp.server_impl import Server, stdio_server as stdio_server_func, Tool, TextContent



app = Server("sprintcycle-mcp")


# ============================================================
# MCP 工具定义
# ============================================================

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(name="sprintcycle_list_projects", description="列出所有项目",
             inputSchema={"type": "object", "properties": {}}),
        
        Tool(name="sprintcycle_list_tools", description="列出可用工具",
             inputSchema={"type": "object", "properties": {}}),
        
        Tool(name="sprintcycle_status", description="检查状态",
             inputSchema={"type": "object", "properties": {"project_path": {"type": "string"}}, "required": ["project_path"]}),
        
        Tool(name="sprintcycle_get_sprint_plan", description="Sprint 规划",
             inputSchema={"type": "object", "properties": {"project_path": {"type": "string"}}, "required": ["project_path"]}),
        
        Tool(name="sprintcycle_get_execution_detail", description="执行详情",
             inputSchema={"type": "object", "properties": {"project_path": {"type": "string"}}, "required": ["project_path"]}),
        
        Tool(name="sprintcycle_get_kb_stats", description="知识库统计",
             inputSchema={"type": "object", "properties": {"project_path": {"type": "string"}}, "required": ["project_path"]}),
        
        Tool(name="sprintcycle_run_task", description="执行任务",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"}, "task": {"type": "string"},
                 "files": {"type": "array", "items": {"type": "string"}},
                 "agent": {"type": "string", "enum": ["coder", "reviewer", "architect", "tester", "ui_verify"]},
                 "tool": {"type": "string", "enum": ["cursor", "claude", "aider"]}
             }, "required": ["project_path", "task"]}),
        
        Tool(name="sprintcycle_run_sprint", description="运行 Sprint",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"}, "sprint_name": {"type": "string"},
                 "tasks": {"type": "array"}, "tool": {"type": "string", "enum": ["cursor", "claude", "aider"]}
             }, "required": ["project_path", "sprint_name", "tasks"]}),
        
        Tool(name="sprintcycle_create_sprint", description="创建 Sprint",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"}, "sprint_name": {"type": "string"},
                 "goals": {"type": "array", "items": {"type": "string"}}
             }, "required": ["project_path", "sprint_name", "goals"]}),
        
        Tool(name="sprintcycle_plan_from_prd", description="从 PRD 自动生成 Sprint 规划",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"}, "prd_path": {"type": "string"}
             }, "required": ["project_path", "prd_path"]}),
        
        Tool(name="sprintcycle_auto_run", description="自动执行所有待执行 Sprint",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"}
             }, "required": ["project_path"]}),
        
        Tool(name="sprintcycle_run_sprint_by_name", description="按名称执行 Sprint",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"}, "sprint_name": {"type": "string"},
                 "tool": {"type": "string", "enum": ["cursor", "claude", "aider"]}
             }, "required": ["project_path", "sprint_name"]}),
        
        Tool(name="sprintcycle_playwright_verify", description="使用 Playwright MCP 验证前端页面",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"},
                 "url": {"type": "string", "description": "要验证的页面 URL"},
                 "checks": {"type": "array", "items": {"type": "string"}, "description": "检查项: load, elements, accessibility"}
             }, "required": ["url"]}),
        
        Tool(name="sprintcycle_verify_frontend", description="验证前端页面",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"},
                 "url": {"type": "string"},
                 "method": {"type": "string", "enum": ["a11y", "console"]}
             }, "required": ["url"]}),
        
        Tool(name="sprintcycle_verify_visual", description="视觉验证",
             inputSchema={"type": "object", "properties": {
                 "project_path": {"type": "string"},
                 "url": {"type": "string"},
                 "baseline": {"type": "string"},
                 "method": {"type": "string", "enum": ["a11y", "screenshot"]}
             }, "required": ["url"]}),
        
        Tool(name="sprintcycle_scan_issues", description="扫描项目问题",
             inputSchema={"type": "object", "properties": {"project_path": {"type": "string"}}, "required": ["project_path"]}),
        
        Tool(name="sprintcycle_autofix", description="自动修复问题",
             inputSchema={"type": "object", "properties": {"project_path": {"type": "string"}, "auto": {"type": "boolean", "default": True}}, "required": ["project_path"]}),
        
        Tool(name="sprintcycle_rollback", description="回滚修复",
             inputSchema={"type": "object", "properties": {"project_path": {"type": "string"}}, "required": ["project_path"]})
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    
    if name == "sprintcycle_list_projects":
        projects = []
        for p in Path("/root").glob("*"):
            if (p / ".sprintcycle").exists() and p.is_dir():
                chain = SprintChain(str(p))
                stats = chain.get_kb_stats()
                projects.append(f"- **{p.name}** ({stats['total']} 任务, {stats['success_rate']}% 成功率)")
        return [TextContent(type="text", text="\n".join(projects) or "未找到项目")]
    
    elif name == "sprintcycle_list_tools":
        executor = ExecutionLayer()
        available = executor.list_available()
        return [TextContent(type="text", text="可用工具:\n" + "\n".join(f"- **{t}**: {'可用' if ok else '不可用'}" for t, ok in available.items()))]
    
    elif name == "sprintcycle_status":
        chain = SprintChain(arguments["project_path"])
        executor = ExecutionLayer()
        available = executor.list_available()
        stats = chain.get_kb_stats()
        text = f"""SprintCycle 状态
        
项目: {arguments['project_path']}
Sprints: {len(chain.get_sprints())}

知识库:
- 总任务: {stats['total']}
- 成功率: {stats['success_rate']}%
- 平均耗时: {stats['avg_duration']}s

工具:
""" + "\n".join(f"  {'可用' if ok else '不可用'} {t}" for t, ok in available.items())
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_get_sprint_plan":
        chain = SprintChain(arguments["project_path"])
        sprints = chain.get_sprints()
        name = chain.config.get("project", {}).get("name", "Project")
        completed = sum(1 for s in sprints if s.get("status") == "completed")
        
        text = f"**{name}** Sprint 规划\n\n"
        for i, s in enumerate(sprints, 1):
            st = s.get("status", "pending")
            icon = {"completed": "完成", "in_progress": "进行中", "pending": "待执行"}.get(st, "?")
            text += f"Sprint {i}: {s.get('name')}\n- 状态: {st}\n- 目标: {', '.join(s.get('goals', []))}\n\n"
        text += f"进度: {int(completed/len(sprints)*100) if sprints else 0}%"
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_get_execution_detail":
        chain = SprintChain(arguments["project_path"])
        results = chain.get_results()
        success = sum(1 for r in results if r.get("success"))
        duration = sum(r.get("duration", 0) for r in results)
        retries = sum(r.get("retries", 0) for r in results)
        
        text = f"执行详情\n\n任务: {len(results)} | 成功: {success} | 重试: {retries} | 耗时: {duration:.1f}s\n\n"
        for r in results[-10:]:
            status = "成功" if r.get("success") else "失败"
            retry = f" (重试{r['retries']}次)" if r.get("retries", 0) > 0 else ""
            text += f"{status} [{r.get('tool')}] {r.get('task', '')[:40]}{retry}\n"
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_get_kb_stats":
        chain = SprintChain(arguments["project_path"])
        stats = chain.get_kb_stats()
        return [TextContent(type="text", text=f"知识库统计\n\n- 总任务: {stats['total']}\n- 成功: {stats.get('success', 0)}\n- 成功率: {stats['success_rate']}%\n- 平均耗时: {stats['avg_duration']}s")]
    
    elif name == "sprintcycle_run_task":
        chain = SprintChain(arguments["project_path"])
        agent = AgentType(arguments["agent"]) if arguments.get("agent") else None
        tool = ToolType(arguments["tool"]) if arguments.get("tool") else None
        result = chain.run_task(arguments["task"], arguments.get("files"), agent, tool)
        
        retry_info = f" (重试 {result.retries} 次)" if result.retries > 0 else ""
        text = f"{'成功' if result.success else '失败'}{retry_info}\n\n{result.tool} | {result.duration:.1f}s\n{result.files_changed or '无修改'}\n"
        if result.error:
            text += f"错误: {result.error[:200]}"
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_run_sprint":
        chain = SprintChain(arguments["project_path"])
        tool = ToolType(arguments["tool"]) if arguments.get("tool") else None
        result = chain.run_sprint(arguments["sprint_name"], arguments["tasks"], tool)
        
        text = f"Sprint: {result['sprint_name']}\n\n"
        for i, r in enumerate(result["results"], 1):
            status = "成功" if r["success"] else "失败"
            retry = f" (重试)" if r.get("retries", 0) > 0 else ""
            text += f"{i}. {status} [{r['tool']}] {r['task'][:40]}{retry}\n"
        text += f"\n{result['success']}/{result['total']}"
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_create_sprint":
        chain = SprintChain(arguments["project_path"])
        sprint = chain.create_sprint(arguments["sprint_name"], arguments.get("goals", []))
        return [TextContent(type="text", text=f"Sprint 已创建: {sprint['name']}\n目标: {', '.join(sprint['goals'])}")]
    
    elif name == "sprintcycle_plan_from_prd":
        chain = SprintChain(arguments["project_path"])
        result = chain.auto_plan_from_prd(arguments["prd_path"])
        if result.get("error"):
            return [TextContent(type="text", text=f"错误: {result['error']}")]
        text = f"已从 PRD 生成 {len(result['sprints'])} 个 Sprint:\n"
        for s in result['sprints']:
            text += f"- {s['name']} ({len(s['tasks'])} 任务)\n"
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_auto_run":
        chain = SprintChain(arguments["project_path"])
        results = chain.run_all_sprints()
        text = f"已执行 {len(results)} 个 Sprint:\n"
        for r in results:
            text += f"- {r['sprint_name']}: {r['success']}/{r['total']}\n"
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_run_sprint_by_name":
        chain = SprintChain(arguments["project_path"])
        tool = ToolType(arguments["tool"]) if arguments.get("tool") else None
        result = chain.run_sprint_by_name(arguments["sprint_name"], tool)
        if result.get("error"):
            return [TextContent(type="text", text=f"错误: {result['error']}")]
        text = f"Sprint: {result['sprint_name']}\n\n"
        for i, r in enumerate(result["results"], 1):
            status = "成功" if r["success"] else "失败"
            retry = f" (重试)" if r.get("retries", 0) > 0 else ""
            text += f"{i}. {status} [{r['tool']}] {r['task'][:40]}{retry}\n"
        text += f"\n{result['success']}/{result['total']}"
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_playwright_verify":
        try:
            from .verifiers import PlaywrightVerifier
        except ImportError:
            return [TextContent(type="text", text="PlaywrightVerifier 未安装")]
        
        project_path = arguments.get("project_path", ".")
        url = arguments.get("url", "")
        checks = arguments.get("checks", ["load", "accessibility"])
        
        if not url:
            return [TextContent(type="text", text="请提供 url 参数")]
        
        verifier = PlaywrightVerifier(project_path)
        result = verifier.verify_all(url, checks=checks)
        
        passed = "通过" if result["passed"] else "失败"
        summary = result.get("summary", {})
        
        text = f"{passed} Playwright 验证完成\n\n"
        text += f"URL: {url}\n"
        text += f"检查项: {len(result.get('checks', {}))}\n"
        text += f"通过: {summary.get('passed_checks', 0)}/{summary.get('total_checks', 0)}\n\n"
        
        if "accessibility" in result.get("checks", {}):
            a11y = result["checks"]["accessibility"]
            text += f"Accessibility Tree:\n{a11y.get('text_preview', 'N/A')[:300]}...\n"
        
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_verify_frontend":
        project_path = arguments.get("project_path", ".")
        url = arguments.get("url", "")
        method = arguments.get("method", "a11y")
        
        if not url:
            return [TextContent(type="text", text="请提供 url 参数")]
        
        try:
            from .optimizations import FiveSourceVerifier
            if method == "a11y" and hasattr(FiveSourceVerifier, "verify_frontend_with_a11y"):
                result = FiveSourceVerifier.verify_frontend_with_a11y(project_path, url)
            else:
                result = FiveSourceVerifier.verify_frontend(project_path, url)
        except ImportError:
            return [TextContent(type="text", text="FiveSourceVerifier 未安装")]
        
        passed = "通过" if result["passed"] else "失败"
        text = f"{passed} Frontend 验证完成\n\n"
        text += f"URL: {url}\n"
        text += f"方法: {method}\n"
        
        if result.get("tree_summary"):
            text += "\n元素统计:\n"
            for role, count in result["tree_summary"].items():
                text += f"  - {role}: {count}\n"
        
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_verify_visual":
        project_path = arguments.get("project_path", ".")
        url = arguments.get("url", "")
        baseline = arguments.get("baseline")
        method = arguments.get("method", "a11y")
        
        if not url:
            return [TextContent(type="text", text="请提供 url 参数")]
        
        try:
            from .optimizations import FiveSourceVerifier
            if method == "a11y" and hasattr(FiveSourceVerifier, "verify_visual_with_a11y"):
                result = FiveSourceVerifier.verify_visual_with_a11y(project_path, url, baseline)
            else:
                result = FiveSourceVerifier.verify_visual(project_path, url, baseline)
        except ImportError:
            return [TextContent(type="text", text="FiveSourceVerifier 未安装")]
        
        passed = "通过" if result["passed"] else "失败"
        text = f"{passed} Visual 验证完成\n\n"
        text += f"URL: {url}\n"
        text += f"方法: {method}\n"
        
        if result.get("diff_from_baseline"):
            diff = result["diff_from_baseline"]
            text += f"\nBaseline 对比:\n"
            text += f"  - 新增: {diff['added_count']}\n"
            text += f"  - 移除: {diff['removed_count']}\n"
            text += f"  - 稳定: {diff['stable']}\n"
        
        return [TextContent(type="text", text=text)]
    
    elif name == "sprintcycle_scan_issues":
        project_path = arguments.get("project_path", ".")
        try:
            from .scanner import ProjectScanner
            scanner = ProjectScanner(project_path)
            result = scanner.scan()
            
            text = f"扫描完成: {result.scanned_files} 文件, 耗时 {result.scan_duration:.2f}s\n\n"
            text += f"问题统计: {result.critical_count} 严重, {result.warning_count} 警告, {result.info_count} 信息\n\n"
            
            for issue in result.issues[:20]:
                icon = {"critical": "严重", "warning": "警告", "info": "信息"}.get(issue.severity.value, "")
                loc = f" Line {issue.line}" if issue.line else ""
                text += f"{icon} [{issue.severity.value}] {issue.file_path}{loc}: {issue.message}\n"
            
            return [TextContent(type="text", text=text)]
        except ImportError:
            return [TextContent(type="text", text="ProjectScanner 未安装")]
    
    elif name == "sprintcycle_autofix":
        project_path = arguments.get("project_path", ".")
        auto = arguments.get("auto", True)
        
        try:
            from .autofix import AutoFixEngine
            fixer = AutoFixEngine(project_path)
            session = fixer.scan_and_fix(auto=auto)
            
            text = f"自动修复完成\n\n"
            text += f"处理: {len(session.fixes)} 问题\n"
            text += f"成功: {sum(1 for f in session.fixes if f.success)}\n"
            text += f"失败: {sum(1 for f in session.fixes if not f.success)}\n"
            text += f"备份: {len(session.rollbacks)} 文件\n\n"
            
            for f in session.fixes:
                icon = "成功" if f.success else "失败"
                text += f"{icon} {f.issue.file_path}: {f.issue.message[:50]}\n"
            
            return [TextContent(type="text", text=text)]
        except ImportError:
            return [TextContent(type="text", text="AutoFixEngine 未安装")]
    
    elif name == "sprintcycle_rollback":
        project_path = arguments.get("project_path", ".")
        
        try:
            from .autofix import AutoFixEngine
            fixer = AutoFixEngine(project_path)
            count = fixer.rollback()
            
            return [TextContent(type="text", text=f"已回滚 {count} 个修复")]
        except ImportError:
            return [TextContent(type="text", text="AutoFixEngine 未安装")]
    
    return [TextContent(type="text", text=f"未知工具: {name}")]


async def main():
    async with stdio_server_func() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
