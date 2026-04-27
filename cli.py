#!/usr/bin/env python3
"""
SprintCycle CLI v0.1.0

AI 驱动的敏捷开发迭代框架命令行工具
完整对齐 MCP Server 的 18 个工具
"""
import sys
import os
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.resolve()


def get_chain(project_path: str):
    """获取 SprintChain 实例"""
    try:
        from sprintcycle.sprint_chain import SprintChain
        return SprintChain(project_path)
    except ImportError:
        print("❌ SprintChain 模块导入失败")
        sys.exit(1)


# ============================================================
# 项目管理 (MCP: sprintcycle_list_projects, sprintcycle_list_tools)
# ============================================================

def cmd_projects_list(args):
    """列出所有 SprintCycle 项目"""
    print("📁 SprintCycle 项目列表\n")
    projects = []
    for p in Path("/root").glob("*"):
        if (p / ".sprintcycle").exists() and p.is_dir():
            chain = get_chain(str(p))
            stats = chain.get_kb_stats() if chain else {'total': 0, 'success_rate': 0}
            print(f"  • {p.name} ({stats.get('total', 0)} 任务, {stats.get('success_rate', 0)}% 成功率)")
            projects.append(p.name)
    if not projects:
        print("  未找到 SprintCycle 项目")


def cmd_tools_list(args):
    """列出可用工具"""
    print("🔧 可用工具列表\n")
    try:
        from sprintcycle.chorus import ExecutionLayer
        executor = ExecutionLayer()
        available = executor.list_available()
        for tool, ok in available.items():
            print(f"  {'✅' if ok else '❌'}  {tool}")
    except:
        for tool in ["aider", "cursor", "claude"]:
            print(f"  • {tool}")


# ============================================================
# 状态查询 (MCP: sprintcycle_status, sprintcycle_get_sprint_plan, 
#           sprintcycle_get_execution_detail, sprintcycle_get_kb_stats)
# ============================================================

def cmd_status(args):
    """查看项目状态"""
    project_path = Path(args.project).resolve()
    print(f"📊 SprintCycle 状态\n  项目: {project_path}\n  版本: v0.1.0\n")
    
    if not (project_path / ".sprintcycle").exists():
        print("⚠️  SprintCycle 未初始化")
        print(f"   运行: sprintcycle init -p {project_path}")
        return
    
    chain = get_chain(str(project_path))
    print("✅ SprintCycle 已初始化")
    
    sprints = chain.get_sprints()
    print(f"\n📋 Sprints: {len(sprints)}")
    for s in sprints[:5]:
        status = s.get("status", "pending")
        icon = "✅" if status == "completed" else "⏳" if status == "running" else "📋"
        print(f"   {icon} {s.get('name', 'Unknown')}")
    
    stats = chain.get_kb_stats()
    print(f"\n📚 知识库:")
    print(f"   总任务: {stats.get('total', 0)}")
    print(f"   成功率: {stats.get('success_rate', 0)}%")


def cmd_sprint_plan(args):
    """获取 Sprint 规划"""
    project_path = Path(args.project).resolve()
    print(f"📋 Sprint 规划\n")
    
    chain = get_chain(str(project_path))
    sprints = chain.get_sprints()
    
    if not sprints:
        print("暂无 Sprint 规划")
        return
    
    for i, s in enumerate(sprints, 1):
        status = s.get('status', 'pending')
        icon = "✅" if status == 'completed' else "⏳" if status == 'running' else "📋"
        print(f"{i}. {icon} {s.get('name', 'Unknown')}")
        print(f"   任务数: {len(s.get('tasks', []))}")


def cmd_execution_detail(args):
    """获取执行详情"""
    project_path = Path(args.project).resolve()
    print(f"📝 执行详情\n")
    
    chain = get_chain(str(project_path))
    for sprint in chain.get_sprints()[-3:]:
        print(f"\n📌 {sprint.get('name', 'Unknown')}")
        for task in sprint.get('tasks', [])[-5:]:
            status = task.get('status', 'pending')
            icon = "✅" if status == 'success' else "❌" if status == 'failed' else "⏳"
            desc = str(task.get('task', task.get('description', 'N/A')))[:40]
            print(f"     {icon} {desc}")


# ============================================================
# Sprint 管理 (MCP: sprintcycle_create_sprint, sprintcycle_run_sprint, 
#             sprintcycle_run_sprint_by_name, sprintcycle_auto_run)
# ============================================================

def cmd_sprint_create(args):
    """创建 Sprint"""
    project_path = Path(args.project).resolve()
    chain = get_chain(str(project_path))
    goals = args.goals.split(',') if args.goals else []
    sprint = chain.create_sprint(args.name, goals)
    print(f"✅ Sprint 已创建: {sprint['name']}")


def cmd_sprint_run(args):
    """运行 Sprint"""
    project_path = Path(args.project).resolve()
    print(f"🚀 运行 Sprint: {args.name}\n")
    
    chain = get_chain(str(project_path))
    result = chain.run_sprint_by_name(args.name)
    
    if result.get('error'):
        print(f"❌ 错误: {result['error']}")
        return
    
    print(f"✅ 执行完成: {result.get('success', 0)}/{result.get('total', 0)}")


def cmd_sprint_auto_run(args):
    """自动执行所有 Sprint"""
    project_path = Path(args.project).resolve()
    print(f"🔄 自动执行所有 Sprint\n")
    
    chain = get_chain(str(project_path))
    results = chain.run_all_sprints()
    
    print(f"✅ 已执行 {len(results)} 个 Sprint")
    for r in results:
        print(f"   {r.get('sprint_name', 'Unknown')}: {r.get('success', 0)}/{r.get('total', 0)}")


# ============================================================
# 任务执行 (MCP: sprintcycle_run_task, sprintcycle_plan_from_prd)
# ============================================================

def cmd_run(args):
    """执行任务或 PRD"""
    project_path = Path(args.project).resolve()
    
    if args.prd:
        prd_path = Path(args.prd)
        if not prd_path.exists():
            prd_path = project_path / args.prd
        
        print(f"🔄 执行 PRD: {prd_path}\n")
        chain = get_chain(str(project_path))
        result = chain.auto_plan_from_prd(str(prd_path))
        
        if result.get('error'):
            print(f"❌ 错误: {result['error']}")
            return
        
        print(f"✅ 已生成 {len(result.get('sprints', []))} 个 Sprint")
        
        if args.auto_run:
            print("\n开始自动执行...")
            results = chain.run_all_sprints()
            for r in results:
                print(f"   {r.get('sprint_name', 'Unknown')}: {r.get('success', 0)}/{r.get('total', 0)}")
    
    elif args.task:
        print(f"⚡ 执行任务: {args.task}\n")
        chain = get_chain(str(project_path))
        result = chain.run_task(args.task, agent=args.agent, tool=args.tool)
        print("✅ 成功" if result.get('success') else "❌ 失败")
    
    else:
        print("❌ 请指定 --prd 或 -t")


# ============================================================
# 验证 (MCP: sprintcycle_playwright_verify, sprintcycle_verify_frontend, 
#       sprintcycle_verify_visual)
# ============================================================

def cmd_verify_playwright(args):
    """Playwright 验证"""
    print(f"🎭 Playwright 验证\n  URL: {args.url}\n")
    try:
        from sprintcycle.verifiers import PlaywrightVerifier
        verifier = PlaywrightVerifier(args.project or ".")
        checks = args.checks.split(',') if args.checks else ['load', 'accessibility']
        result = verifier.verify_all(args.url, checks=checks)
        print("✅ 通过" if result['passed'] else "❌ 失败")
    except ImportError:
        print("❌ PlaywrightVerifier 未安装")


def cmd_verify_frontend(args):
    """前端验证"""
    print(f"🌐 前端验证\n  URL: {args.url}\n")
    try:
        from sprintcycle.optimizations import FiveSourceVerifier
        result = FiveSourceVerifier.verify_frontend(args.project or ".", args.url)
        print("✅ 通过" if result['passed'] else "❌ 失败")
    except ImportError:
        print("❌ FiveSourceVerifier 未安装")


def cmd_verify_visual(args):
    """视觉验证"""
    print(f"👁️ 视觉验证\n  URL: {args.url}\n")
    try:
        from sprintcycle.optimizations import FiveSourceVerifier
        result = FiveSourceVerifier.verify_visual(args.project or ".", args.url, args.baseline)
        print("✅ 通过" if result['passed'] else "❌ 失败")
    except ImportError:
        print("❌ FiveSourceVerifier 未安装")


# ============================================================
# 问题扫描与修复 (MCP: sprintcycle_scan_issues, sprintcycle_autofix, 
#                sprintcycle_rollback)
# ============================================================

def cmd_scan(args):
    """扫描项目问题"""
    project_path = Path(args.project).resolve()
    print(f"🔍 扫描项目问题\n  项目: {project_path}\n")
    try:
        from sprintcycle.scanner import ProjectScanner
        scanner = ProjectScanner(str(project_path))
        result = scanner.scan()
        print(f"✅ 扫描完成: {result.scanned_files} 文件\n")
        print(f"  严重: {result.critical_count}")
        print(f"  警告: {result.warning_count}")
        print(f"  信息: {result.info_count}")
    except ImportError:
        print("❌ ProjectScanner 未安装")


def cmd_autofix(args):
    """自动修复问题"""
    project_path = Path(args.project).resolve()
    print(f"🔧 自动修复问题\n")
    try:
        from sprintcycle.autofix import AutoFixEngine
        fixer = AutoFixEngine(str(project_path))
        session = fixer.scan_and_fix(auto=args.auto)
        print(f"✅ 修复完成: {len(session.fixes)} 问题")
    except ImportError:
        print("❌ AutoFixEngine 未安装")


def cmd_rollback(args):
    """回滚修复"""
    project_path = Path(args.project).resolve()
    print(f"⏪ 回滚修复\n")
    try:
        from sprintcycle.autofix import AutoFixEngine
        fixer = AutoFixEngine(str(project_path))
        count = fixer.rollback()
        print(f"✅ 已回滚 {count} 个修复")
    except ImportError:
        print("❌ AutoFixEngine 未安装")


# ============================================================
# 其他命令
# ============================================================

def cmd_init(args):
    """初始化项目"""
    project_path = Path(args.project).resolve()
    sprintcycle_dir = project_path / ".sprintcycle"
    sprintcycle_dir.mkdir(exist_ok=True)
    (sprintcycle_dir / "reports").mkdir(exist_ok=True)
    (sprintcycle_dir / "knowledge.json").write_text(json.dumps({
        "tasks": [], "created_at": datetime.now().isoformat()
    }, indent=2))
    (project_path / "prd").mkdir(exist_ok=True)
    print(f"✅ 初始化完成: {project_path}")


def cmd_knowledge(args):
    """知识库管理"""
    project_path = Path(args.project).resolve()
    knowledge_file = project_path / ".sprintcycle" / "knowledge.json"
    
    if args.knowledge_cmd == "show":
        if not knowledge_file.exists():
            print("❌ 知识库不存在")
            return
        knowledge = json.loads(knowledge_file.read_text())
        print(f"📚 知识库 ({len(knowledge.get('tasks', []))} 条)\n")
        for task in knowledge.get("tasks", [])[-10:]:
            status = task.get("status", "unknown")
            icon = "✅" if status == "success" else "❌" if status == "failed" else "⏳"
            desc = str(task.get("description", task.get("task", "N/A")))[:50]
            print(f"  {icon} {desc}")
    
    elif args.knowledge_cmd == "stats":
        chain = get_chain(str(project_path))
        stats = chain.get_kb_stats()
        print(f"📊 知识库统计\n  总任务: {stats.get('total', 0)}\n  成功率: {stats.get('success_rate', 0)}%")


def cmd_agents(args):
    """Agent 列表"""
    print("🤖 Agent 列表\n")
    for agent, role in [
        ("CODER", "代码编写"), ("REVIEWER", "代码审查"), ("ARCHITECT", "架构设计"),
        ("TESTER", "测试验证"), ("DIAGNOSTIC", "问题诊断"), ("UI_VERIFY", "UI 验证")
    ]:
        print(f"  {agent:12} - {role}")


def cmd_dashboard(args):
    """启动 Dashboard"""
    import subprocess
    print(f"🌐 启动 Dashboard...\n  地址: http://localhost:{args.port}\n")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "dashboard.server:app", 
        "--host", "0.0.0.0", 
        "--port", str(args.port),
        "--reload" if args.reload else ""
    ])


def main():
    parser = argparse.ArgumentParser(description="SprintCycle CLI v0.1.0")
    subparsers = parser.add_subparsers(dest="cmd", help="命令")
    
    # projects
    projects_p = subparsers.add_parser("projects", help="项目管理")
    projects_sp = projects_p.add_subparsers(dest="sub")
    projects_sp.add_parser("list", help="列出项目")
    
    # tools
    tools_p = subparsers.add_parser("tools", help="工具管理")
    tools_sp = tools_p.add_subparsers(dest="sub")
    tools_sp.add_parser("list", help="列出工具")
    
    # status
    status_p = subparsers.add_parser("status", help="项目状态")
    status_p.add_argument("-p", "--project", default=".")
    
    # sprint
    sprint_p = subparsers.add_parser("sprint", help="Sprint 管理")
    sprint_sp = sprint_p.add_subparsers(dest="sub")
    p1 = sprint_sp.add_parser("plan", help="Sprint 规划")
    p1.add_argument("-p", "--project", default=".")
    p2 = sprint_sp.add_parser("create", help="创建 Sprint")
    p2.add_argument("-p", "--project", default=".")
    p2.add_argument("--name", required=True)
    p2.add_argument("--goals")
    p3 = sprint_sp.add_parser("run", help="运行 Sprint")
    p3.add_argument("-p", "--project", default=".")
    p3.add_argument("--name", required=True)
    p4 = sprint_sp.add_parser("auto-run", help="自动执行")
    p4.add_argument("-p", "--project", default=".")
    
    # execution
    exec_p = subparsers.add_parser("execution", help="执行管理")
    exec_sp = exec_p.add_subparsers(dest="sub")
    p5 = exec_sp.add_parser("detail", help="执行详情")
    p5.add_argument("-p", "--project", default=".")
    
    # run
    run_p = subparsers.add_parser("run", help="执行任务")
    run_p.add_argument("-p", "--project", default=".")
    run_p.add_argument("-t", "--task")
    run_p.add_argument("--prd")
    run_p.add_argument("--agent")
    run_p.add_argument("--tool")
    run_p.add_argument("--auto-run", action="store_true")
    
    # verify
    verify_p = subparsers.add_parser("verify", help="验证")
    verify_sp = verify_p.add_subparsers(dest="sub")
    v1 = verify_sp.add_parser("playwright", help="Playwright 验证")
    v1.add_argument("--url", required=True)
    v1.add_argument("--checks", default="load,accessibility")
    v1.add_argument("--project", default=".")
    v2 = verify_sp.add_parser("frontend", help="前端验证")
    v2.add_argument("--url", required=True)
    v2.add_argument("--project", default=".")
    v3 = verify_sp.add_parser("visual", help="视觉验证")
    v3.add_argument("--url", required=True)
    v3.add_argument("--baseline")
    v3.add_argument("--project", default=".")
    
    # scan
    scan_p = subparsers.add_parser("scan", help="扫描问题")
    scan_p.add_argument("-p", "--project", default=".")
    
    # autofix
    autofix_p = subparsers.add_parser("autofix", help="自动修复")
    autofix_p.add_argument("-p", "--project", default=".")
    autofix_p.add_argument("--auto", action="store_true", default=True)
    
    # rollback
    rollback_p = subparsers.add_parser("rollback", help="回滚修复")
    rollback_p.add_argument("-p", "--project", default=".")
    
    # init
    init_p = subparsers.add_parser("init", help="初始化")
    init_p.add_argument("-p", "--project", default=".")
    
    # knowledge
    knowledge_p = subparsers.add_parser("knowledge", help="知识库")
    knowledge_sp = knowledge_p.add_subparsers(dest="sub")
    k1 = knowledge_sp.add_parser("show", help="查看知识库")
    k1.add_argument("-p", "--project", default=".")
    k2 = knowledge_sp.add_parser("stats", help="知识库统计")
    k2.add_argument("-p", "--project", default=".")
    
    # agents
    subparsers.add_parser("agents", help="Agent 列表")
    
    # dashboard
    dash_p = subparsers.add_parser("dashboard", help="启动 Dashboard")
    dash_p.add_argument("--port", type=int, default=8088)
    dash_p.add_argument("--reload", action="store_true")
    
    args = parser.parse_args()
    
    if not args.cmd:
        parser.print_help()
        return
    
    # 命令分发
    handlers = {
        ("projects", "list"): cmd_projects_list,
        ("tools", "list"): cmd_tools_list,
        ("status", None): cmd_status,
        ("sprint", "plan"): cmd_sprint_plan,
        ("sprint", "create"): cmd_sprint_create,
        ("sprint", "run"): cmd_sprint_run,
        ("sprint", "auto-run"): cmd_sprint_auto_run,
        ("execution", "detail"): cmd_execution_detail,
        ("run", None): cmd_run,
        ("verify", "playwright"): cmd_verify_playwright,
        ("verify", "frontend"): cmd_verify_frontend,
        ("verify", "visual"): cmd_verify_visual,
        ("scan", None): cmd_scan,
        ("autofix", None): cmd_autofix,
        ("rollback", None): cmd_rollback,
        ("init", None): cmd_init,
        ("knowledge", "show"): cmd_knowledge,
        ("knowledge", "stats"): cmd_knowledge,
        ("agents", None): cmd_agents,
        ("dashboard", None): cmd_dashboard,
    }
    
    key = (args.cmd, getattr(args, "sub", None))
    handler = handlers.get(key)
    
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
