"""
监控仪表盘 - FastAPI Web 仪表盘

提供可视化的执行监控能力：
1. 实时执行状态
2. 成功率统计
3. 耗时分析
"""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .metrics import (
    ExecutionStatus,
    ExecutionRecord,
    MetricsCollector,
    get_metrics_collector,
)

def setup_dashboard_logging(
    log_file: str = ".sprintcycle/logs/dashboard.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    配置 Dashboard 日志系统，支持文件轮转
    
    Args:
        log_file: 日志文件路径
        level: 日志级别
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的备份文件数量
    """
    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 配置根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 添加文件轮转处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)


# ===== 数据模型 =====

class ExecutionResponse(BaseModel):
    """执行记录响应"""
    id: str
    name: str
    agent_type: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration: float
    error: Optional[str]


class StatsResponse(BaseModel):
    """统计响应"""
    timestamp: str
    executions: Dict[str, Any]
    duration: Dict[str, float]
    counters: Dict[str, float]
    agent_stats: Dict[str, Any]
    recent_executions: List[Dict[str, Any]]


# ===== FastAPI 应用 =====

def create_dashboard_app(
    metrics_collector: Optional[MetricsCollector] = None,
    title: str = "SprintCycle Monitor",
    port: int = 8080
) -> FastAPI:
    """
    创建监控仪表盘应用
    
    Args:
        metrics_collector: 指标收集器（默认使用全局实例）
        title: 应用标题
        port: 默认端口
        
    Returns:
        FastAPI: FastAPI 应用实例
    """
    app = FastAPI(
        title=title,
        description="SprintCycle 执行监控仪表盘",
        version="1.0.0",
    )
    
    # 使用指定的收集器或全局实例
    collector = metrics_collector or get_metrics_collector()
    
    # CORS 配置 - 通过环境变量控制允许的源
    # 环境变量格式: ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # ===== API 端点 =====
    
    @app.get("/api/stats", response_model=StatsResponse)
    async def get_stats():
        """获取统计数据"""
        return collector.get_stats()
    
    @app.get("/api/executions", response_model=List[ExecutionResponse])
    async def list_executions(
        status: Optional[str] = Query(None, description="按状态过滤"),
        agent_type: Optional[str] = Query(None, description="按 Agent 类型过滤"),
        limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    ):
        """获取执行记录列表"""
        status_enum = None
        if status:
            try:
                status_enum = ExecutionStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的状态值: {status}，可选值: {[s.value for s in ExecutionStatus]}"
                )
        
        return collector.get_executions(
            status=status_enum,
            agent_type=agent_type,
            limit=limit
        )
    
    @app.get("/api/executions/{execution_id}", response_model=ExecutionResponse)
    async def get_execution(execution_id: str):
        """获取单个执行记录详情"""
        executions = collector.get_executions(limit=1000)
        for exec_data in executions:
            if exec_data["id"] == execution_id:
                return exec_data
        
        raise HTTPException(status_code=404, detail=f"执行记录不存在: {execution_id}")
    
    @app.post("/api/record")
    async def record_execution(data: Dict[str, Any]):
        """记录执行结果"""
        collector.record_execution(data)
        return {"status": "ok", "recorded_at": datetime.now().isoformat()}
    
    @app.get("/api/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "collector": "active" if collector else "inactive",
        }
    
    # ===== Web UI =====
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home():
        """监控仪表盘首页"""
        return get_dashboard_html()
    
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard():
        """监控仪表盘页面"""
        return get_dashboard_html()
    
    return app


def get_dashboard_html() -> str:
    """获取仪表盘 HTML 内容"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SprintCycle Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 30px 0;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .header p { color: #888; }
        .container { max-width: 1400px; margin: 0 auto; }
        
        /* 统计卡片 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        }
        .stat-label { font-size: 0.9rem; color: #888; margin-bottom: 8px; }
        .stat-value { font-size: 2.5rem; font-weight: 700; }
        .stat-value.success { color: #00ff88; }
        .stat-value.failed { color: #ff6b6b; }
        .stat-value.running { color: #ffd93d; }
        .stat-value.total { color: #00d9ff; }
        .stat-sub { font-size: 0.85rem; color: #666; margin-top: 8px; }
        
        /* 执行记录表格 */
        .section {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .section-title { font-size: 1.2rem; margin-bottom: 16px; color: #fff; }
        
        .exec-table { width: 100%; border-collapse: collapse; }
        .exec-table th, .exec-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .exec-table th { color: #888; font-weight: 500; }
        .exec-table tr:hover { background: rgba(255,255,255,0.05); }
        
        /* 状态标签 */
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        .status-success { background: rgba(0,255,136,0.2); color: #00ff88; }
        .status-failed { background: rgba(255,107,107,0.2); color: #ff6b6b; }
        .status-running { background: rgba(255,217,61,0.2); color: #ffd93d; }
        
        .refresh-btn {
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            color: #1a1a2e;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .refresh-btn:hover { transform: scale(1.05); }
        
        .loading { text-align: center; padding: 40px; color: #666; }
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #00d9ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .error { color: #ff6b6b; text-align: center; padding: 20px; }
        
        .last-update {
            text-align: right;
            color: #666;
            font-size: 0.85rem;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SprintCycle Monitor</h1>
            <p>实时执行监控仪表盘</p>
        </div>
        
        <div class="stats-grid" id="stats-grid">
            <div class="loading"><div class="spinner"></div>加载中...</div>
        </div>
        
        <div class="section">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <h2 class="section-title" style="margin:0;">最近执行记录</h2>
                <button class="refresh-btn" onclick="loadData()">刷新</button>
            </div>
            <p class="last-update" id="last-update"></p>
            <div id="executions">
                <div class="loading"><div class="spinner"></div>加载中...</div>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '/api';
        
        async function loadData() {
            try {
                const [statsRes, execRes] = await Promise.all([
                    fetch(API_BASE + '/stats'),
                    fetch(API_BASE + '/executions?limit=20')
                ]);
                
                if (!statsRes.ok || !execRes.ok) throw new Error('API请求失败');
                
                const stats = await statsRes.json();
                const executions = await execRes.json();
                
                renderStats(stats);
                renderExecutions(executions);
                
                document.getElementById('last-update').textContent = 
                    '最后更新: ' + new Date().toLocaleTimeString();
            } catch (err) {
                document.getElementById('stats-grid').innerHTML = 
                    '<div class="error">加载失败: ' + err.message + '</div>';
                document.getElementById('executions').innerHTML = '';
            }
        }
        
        function renderStats(stats) {
            const grid = document.getElementById('stats-grid');
            const exec = stats.executions;
            
            grid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-label">总执行数</div>
                    <div class="stat-value total">${exec.total || 0}</div>
                    <div class="stat-sub">历史累计</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">成功率</div>
                    <div class="stat-value success">${exec.success_rate || 0}%</div>
                    <div class="stat-sub">${exec.success || 0} 成功 / ${exec.failed || 0} 失败</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">运行中</div>
                    <div class="stat-value running">${exec.running || 0}</div>
                    <div class="stat-sub">当前任务</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">平均耗时</div>
                    <div class="stat-value total">${(stats.duration?.avg || 0).toFixed(3)}s</div>
                    <div class="stat-sub">范围: ${(stats.duration?.min || 0).toFixed(3)}s - ${(stats.duration?.max || 0).toFixed(3)}s</div>
                </div>
            `;
        }
        
        function renderExecutions(executions) {
            const container = document.getElementById('executions');
            
            if (!executions || executions.length === 0) {
                container.innerHTML = '<p style="color:#666; text-align:center; padding:20px;">暂无执行记录</p>';
                return;
            }
            
            const rows = executions.map(e => {
                const statusClass = e.status === 'success' ? 'status-success' : 
                                   e.status === 'failed' ? 'status-failed' : 'status-running';
                const statusText = e.status === 'success' ? '成功' : 
                                  e.status === 'failed' ? '失败' : '运行中';
                const time = e.start_time ? new Date(e.start_time).toLocaleString() : '-';
                
                return `<tr>
                    <td>${e.name || e.id}</td>
                    <td>${e.agent_type || '-'}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td>${time}</td>
                    <td>${e.duration?.toFixed(3) || 0}s</td>
                    <td>${e.error || '-'}</td>
                </tr>`;
            }).join('');
            
            container.innerHTML = `
                <table class="exec-table">
                    <thead>
                        <tr>
                            <th>名称</th>
                            <th>Agent</th>
                            <th>状态</th>
                            <th>开始时间</th>
                            <th>耗时</th>
                            <th>错误</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        }
        
        // 初始加载
        loadData();
        
        // 自动刷新
        setInterval(loadData, 5000);
    </script>
</body>
</html>
"""


async def run_dashboard(
    host: str = "0.0.0.0",
    port: int = 8080,
    metrics_collector: Optional[MetricsCollector] = None
):
    """运行监控仪表盘服务器"""
    import uvicorn
    
    app = create_dashboard_app(metrics_collector, port=port)
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    logger.info(f"启动监控仪表盘: http://{host}:{port}")
    await server.serve()


__all__ = [
    "create_dashboard_app",
    "get_dashboard_html",
    "run_dashboard",
]
