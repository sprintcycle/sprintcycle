"""
SprintCycle Dashboard Server v0.1.0

功能对齐 MCP Server，提供 Web UI 和 REST API
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import json
import sys

# 添加项目路径
sys.path.insert(0, "/root/sprintcycle")

app = FastAPI(
    title="SprintCycle Dashboard",
    description="AI 驱动的敏捷开发迭代框架 - Web Dashboard",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


def get_chain(project_path: str = "/root/xuewanpai"):
    """获取 SprintChain 实例"""
    try:
        from sprintcycle.sprint_chain import SprintChain
        return SprintChain(project_path)
    except ImportError:
        return None


# ============================================================
# Web UI Routes
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Dashboard 主页"""
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SprintCycle Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .header {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 { font-size: 28px; margin-bottom: 5px; }
        .header .version { color: #4ecdc4; font-size: 14px; }
        .nav {
            display: flex;
            justify-content: center;
            gap: 20px;
            padding: 15px;
            background: rgba(0,0,0,0.2);
        }
        .nav a {
            color: #4ecdc4;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 8px;
            transition: all 0.3s;
        }
        .nav a:hover { background: rgba(78, 205, 196, 0.2); }
        .container { max-width: 1400px; margin: 20px auto; padding: 0 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 { 
            font-size: 18px; 
            margin-bottom: 16px; 
            display: flex; 
            align-items: center; 
            gap: 10px;
        }
        .card h2 .icon { font-size: 24px; }
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .stat-row:last-child { border-bottom: none; }
        .stat-label { color: #888; }
        .stat-value { font-weight: 600; color: #4ecdc4; }
        .progress-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 8px;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-fill {
            background: linear-gradient(90deg, #4ecdc4, #44a08d);
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-running { background: #4ecdc4; color: #1a1a2e; }
        .status-pending { background: #ffd93d; color: #1a1a2e; }
        .status-completed { background: #6bcb77; color: #1a1a2e; }
        .status-failed { background: #ff6b6b; color: #fff; }
        .api-link {
            display: inline-block;
            margin-top: 10px;
            color: #4ecdc4;
            text-decoration: none;
            font-size: 14px;
        }
        .api-link:hover { text-decoration: underline; }
        .endpoint-list { margin-top: 10px; }
        .endpoint {
            background: rgba(0,0,0,0.2);
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-family: monospace;
            font-size: 13px;
        }
        .endpoint .method {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin-right: 10px;
        }
        .method-get { background: #4ecdc4; color: #1a1a2e; }
        .method-post { background: #6bcb77; color: #1a1a2e; }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 20px;
        }
        .full-width { grid-column: 1 / -1; }
        pre {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 SprintCycle Dashboard</h1>
        <div class="version">v0.1.0 - AI 驱动的敏捷开发迭代框架</div>
    </div>
    
    <div class="nav">
        <a href="/">Dashboard</a>
        <a href="/docs">API 文档</a>
        <a href="/api/projects">项目列表</a>
        <a href="/api/tools">工具列表</a>
    </div>
    
    <div class="container">
        <div class="grid">
            <!-- 快速开始 -->
            <div class="card">
                <h2><span class="icon">🚀</span> 快速开始</h2>
                <div class="stat-row">
                    <span class="stat-label">初始化项目</span>
                    <span class="stat-value" style="font-size:12px">sprintcycle init -p /path</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">执行任务</span>
                    <span class="stat-value" style="font-size:12px">sprintcycle run -t "任务"</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">执行 PRD</span>
                    <span class="stat-value" style="font-size:12px">sprintcycle run --prd x.yaml</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">自进化闭环</span>
                    <span class="stat-value" style="font-size:12px">sprintcycle evolve</span>
                </div>
            </div>
            
            <!-- MCP 工具对齐 -->
            <div class="card">
                <h2><span class="icon">🔧</span> MCP 工具 (18个)</h2>
                <div class="stat-row">
                    <span class="stat-label">项目管理</span>
                    <span class="stat-value">2</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Sprint 管理</span>
                    <span class="stat-value">6</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">验证功能</span>
                    <span class="stat-value">3</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">问题修复</span>
                    <span class="stat-value">3</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">其他功能</span>
                    <span class="stat-value">4</span>
                </div>
                <a href="/api/tools" class="api-link">查看所有工具 →</a>
            </div>
            
            <!-- Agent 列表 -->
            <div class="card">
                <h2><span class="icon">🤖</span> Agent 列表</h2>
                <div class="stat-row">
                    <span class="stat-label">CODER</span>
                    <span class="stat-value">代码编写</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">REVIEWER</span>
                    <span class="stat-value">代码审查</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">ARCHITECT</span>
                    <span class="stat-value">架构设计</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">TESTER</span>
                    <span class="stat-value">测试验证</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">DIAGNOSTIC</span>
                    <span class="stat-value">问题诊断</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">UI_VERIFY</span>
                    <span class="stat-value">UI 验证</span>
                </div>
            </div>
            
            <!-- CLI 命令 -->
            <div class="card">
                <h2><span class="icon">💻</span> CLI 命令对齐</h2>
                <div class="stat-row">
                    <span class="stat-label">status</span>
                    <span class="status-badge status-completed">✅ 已对齐</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">run</span>
                    <span class="status-badge status-completed">✅ 已对齐</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">sprint *</span>
                    <span class="status-badge status-completed">✅ 已对齐</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">verify *</span>
                    <span class="status-badge status-completed">✅ 已对齐</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">scan/autofix/rollback</span>
                    <span class="status-badge status-completed">✅ 已对齐</span>
                </div>
            </div>
        </div>
        
        <!-- API 端点列表 -->
        <div class="card full-width">
            <h2><span class="icon">📡</span> API 端点</h2>
            <div class="grid" style="margin-top: 15px;">
                <div>
                    <h3 style="margin-bottom: 10px; color: #4ecdc4;">项目管理</h3>
                    <div class="endpoint"><span class="method method-get">GET</span>/api/projects</div>
                    <div class="endpoint"><span class="method method-get">GET</span>/api/tools</div>
                    <div class="endpoint"><span class="method method-get">GET</span>/api/status?project_path=/path</div>
                </div>
                <div>
                    <h3 style="margin-bottom: 10px; color: #4ecdc4;">Sprint 管理</h3>
                    <div class="endpoint"><span class="method method-get">GET</span>/api/sprints?project_path=/path</div>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/sprints/create</div>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/sprints/run</div>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/sprints/auto-run</div>
                </div>
                <div>
                    <h3 style="margin-bottom: 10px; color: #4ecdc4;">任务执行</h3>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/tasks/run</div>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/tasks/run-prd</div>
                </div>
                <div>
                    <h3 style="margin-bottom: 10px; color: #4ecdc4;">验证</h3>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/verify/playwright</div>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/verify/frontend</div>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/verify/visual</div>
                </div>
                <div>
                    <h3 style="margin-bottom: 10px; color: #4ecdc4;">问题修复</h3>
                    <div class="endpoint"><span class="method method-get">GET</span>/api/scan?project_path=/path</div>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/autofix</div>
                    <div class="endpoint"><span class="method method-post">POST</span>/api/rollback</div>
                </div>
                <div>
                    <h3 style="margin-bottom: 10px; color: #4ecdc4;">知识库</h3>
                    <div class="endpoint"><span class="method method-get">GET</span>/api/knowledge?project_path=/path</div>
                    <div class="endpoint"><span class="method method-get">GET</span>/api/knowledge/stats</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        SprintCycle v0.1.0 | <a href="/docs" style="color:#4ecdc4">API 文档</a> | <a href="/health" style="color:#4ecdc4">健康检查</a> | Apache 2.0 License
    </div>
    
    <script>
        // 自动刷新
        setTimeout(() => location.reload(), 60000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


# ============================================================
# API Routes - 对齐 MCP 工具
# ============================================================

# ------------ 项目管理 ------------

@app.get("/api/projects")
async def list_projects():
    """列出所有 SprintCycle 项目"""
    projects = []
    for p in Path("/root").glob("*"):
        if (p / ".sprintcycle").exists() and p.is_dir():
            chain = get_chain(str(p))
            if chain:
                stats = chain.get_kb_stats()
                projects.append({
                    "name": p.name,
                    "path": str(p),
                    "total_tasks": stats.get('total', 0),
                    "success_rate": stats.get('success_rate', 0)
                })
            else:
                projects.append({
                    "name": p.name,
                    "path": str(p),
                    "total_tasks": 0,
                    "success_rate": 0
                })
    return {"projects": projects}


@app.get("/api/tools")
async def list_tools():
    """列出可用工具"""
    tools = [
        {"name": "aider", "description": "AI 编程助手", "available": True},
        {"name": "cursor", "description": "Cursor IDE", "available": True},
        {"name": "claude", "description": "Claude AI", "available": True},
    ]
    
    try:
        from sprintcycle.chorus import ExecutionLayer
        executor = ExecutionLayer()
        available = executor.list_available()
        tools = [{"name": k, "available": v} for k, v in available.items()]
    except:
        pass
    
    return {"tools": tools}


@app.get("/api/status")
async def get_status(project_path: str = Query(default="/root/xuewanpai")):
    """获取项目状态"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    stats = chain.get_kb_stats()
    sprints = chain.get_sprints()
    
    return {
        "project_path": project_path,
        "sprints_count": len(sprints),
        "knowledge": {
            "total": stats.get('total', 0),
            "success_rate": stats.get('success_rate', 0),
            "avg_duration": stats.get('avg_duration', 0)
        }
    }


# ------------ Sprint 管理 ------------

@app.get("/api/sprints")
async def get_sprints(project_path: str = Query(default="/root/xuewanpai")):
    """获取 Sprint 规划"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    sprints = chain.get_sprints()
    return {"sprints": sprints}


@app.post("/api/sprints/create")
async def create_sprint(
    project_path: str = Query(...),
    sprint_name: str = Query(...),
    goals: Optional[str] = Query(default=None)
):
    """创建 Sprint"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    goals_list = goals.split(',') if goals else []
    sprint = chain.create_sprint(sprint_name, goals_list)
    
    return {"success": True, "sprint": sprint}


@app.post("/api/sprints/run")
async def run_sprint(
    project_path: str = Query(...),
    sprint_name: str = Query(...),
    tool: Optional[str] = Query(default=None)
):
    """运行指定 Sprint"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    result = chain.run_sprint_by_name(sprint_name)
    return result


@app.post("/api/sprints/auto-run")
async def auto_run_sprints(project_path: str = Query(...)):
    """自动执行所有待执行 Sprint"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    results = chain.run_all_sprints()
    return {"results": results}


# ------------ 任务执行 ------------

@app.post("/api/tasks/run")
async def run_task(
    project_path: str = Query(...),
    task: str = Query(...),
    agent: Optional[str] = Query(default=None),
    tool: Optional[str] = Query(default=None)
):
    """执行单个任务"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    result = chain.run_task(task, agent=agent, tool=tool)
    return result


@app.post("/api/tasks/run-prd")
async def run_from_prd(
    project_path: str = Query(...),
    prd_path: str = Query(...),
    auto_run: bool = Query(default=False)
):
    """从 PRD 生成并执行 Sprint"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    result = chain.auto_plan_from_prd(prd_path)
    
    if auto_run and not result.get('error'):
        chain.run_all_sprints()
    
    return result


# ------------ 验证 ------------

@app.post("/api/verify/playwright")
async def verify_playwright(
    url: str = Query(...),
    checks: Optional[str] = Query(default="load,accessibility"),
    project_path: Optional[str] = Query(default=".")
):
    """Playwright 验证"""
    try:
        from sprintcycle.verifiers import PlaywrightVerifier
        verifier = PlaywrightVerifier(project_path)
        checks_list = checks.split(',') if checks else ['load', 'accessibility']
        result = verifier.verify_all(url, checks=checks_list)
        return result
    except ImportError:
        raise HTTPException(status_code=500, detail="PlaywrightVerifier 未安装")


@app.post("/api/verify/frontend")
async def verify_frontend(
    url: str = Query(...),
    method: Optional[str] = Query(default="a11y"),
    project_path: Optional[str] = Query(default=".")
):
    """前端验证"""
    try:
        from sprintcycle.optimizations import FiveSourceVerifier
        result = FiveSourceVerifier.verify_frontend(project_path, url)
        return result
    except ImportError:
        raise HTTPException(status_code=500, detail="FiveSourceVerifier 未安装")


@app.post("/api/verify/visual")
async def verify_visual(
    url: str = Query(...),
    baseline: Optional[str] = Query(default=None),
    method: Optional[str] = Query(default="a11y"),
    project_path: Optional[str] = Query(default=".")
):
    """视觉验证"""
    try:
        from sprintcycle.optimizations import FiveSourceVerifier
        result = FiveSourceVerifier.verify_visual(project_path, url, baseline)
        return result
    except ImportError:
        raise HTTPException(status_code=500, detail="FiveSourceVerifier 未安装")


# ------------ 问题扫描与修复 ------------

@app.get("/api/scan")
async def scan_issues(project_path: str = Query(...)):
    """扫描项目问题"""
    try:
        from sprintcycle.scanner import ProjectScanner
        scanner = ProjectScanner(project_path)
        result = scanner.scan()
        return {
            "scanned_files": result.scanned_files,
            "scan_duration": result.scan_duration,
            "critical_count": result.critical_count,
            "warning_count": result.warning_count,
            "info_count": result.info_count,
            "issues": [
                {
                    "file": i.file_path,
                    "line": i.line,
                    "severity": i.severity.value,
                    "message": i.message
                } for i in result.issues[:50]
            ]
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="ProjectScanner 未安装")


@app.post("/api/autofix")
async def autofix(
    project_path: str = Query(...),
    auto: bool = Query(default=True)
):
    """自动修复问题"""
    try:
        from sprintcycle.autofix import AutoFixEngine
        fixer = AutoFixEngine(project_path)
        session = fixer.scan_and_fix(auto=auto)
        return {
            "total": len(session.fixes),
            "success": sum(1 for f in session.fixes if f.success),
            "failed": sum(1 for f in session.fixes if not f.success),
            "rollbacks": len(session.rollbacks)
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="AutoFixEngine 未安装")


@app.post("/api/rollback")
async def rollback(project_path: str = Query(...)):
    """回滚修复"""
    try:
        from sprintcycle.autofix import AutoFixEngine
        fixer = AutoFixEngine(project_path)
        count = fixer.rollback()
        return {"rolled_back": count}
    except ImportError:
        raise HTTPException(status_code=500, detail="AutoFixEngine 未安装")


# ------------ 知识库 ------------

@app.get("/api/knowledge")
async def get_knowledge(project_path: str = Query(default="/root/xuewanpai")):
    """获取知识库"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    knowledge_file = Path(project_path) / ".sprintcycle" / "knowledge.json"
    if not knowledge_file.exists():
        return {"tasks": []}
    
    knowledge = json.loads(knowledge_file.read_text())
    return knowledge


@app.get("/api/knowledge/stats")
async def get_knowledge_stats(project_path: str = Query(default="/root/xuewanpai")):
    """获取知识库统计"""
    chain = get_chain(project_path)
    if not chain:
        raise HTTPException(status_code=500, detail="SprintChain 初始化失败")
    
    stats = chain.get_kb_stats()
    return stats


# ------------ 健康检查 ------------

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
