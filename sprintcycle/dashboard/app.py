"""
SprintCycle Dashboard — FastAPI 应用

REST API + SSE 实时事件流，调用 SprintCycle API。
支持 EventBus→SSE 实时推送执行进度。
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel

from sprintcycle.api import SprintCycle
from sprintcycle.execution.events import EventBus, EventType, Event, get_event_bus

logger = logging.getLogger(__name__)


# ─── SSE 客户端管理 ───

class SSEClient:
    """SSE 客户端"""
    def __init__(self, client_id: str, queue: asyncio.Queue):
        self.client_id = client_id
        self.queue = queue
    
    async def send(self, event: Event) -> None:
        """发送事件到客户端"""
        message = event.to_sse_message()
        await self.queue.put(message)
    
    async def send_raw(self, message: str) -> None:
        """发送原始消息到客户端"""
        await self.queue.put(message)


class SSEClientManager:
    """SSE 客户端管理器"""
    def __init__(self):
        self._clients: Dict[str, SSEClient] = {}
        self._lock = asyncio.Lock()
    
    async def create_client(self) -> SSEClient:
        """创建新的客户端"""
        client_id = str(uuid.uuid4())
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        client = SSEClient(client_id, queue)
        async with self._lock:
            self._clients[client_id] = client
        logger.info(f"SSE client connected: {client_id}")
        return client
    
    async def remove_client(self, client_id: str) -> None:
        """移除客户端"""
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                logger.info(f"SSE client disconnected: {client_id}")
    
    async def broadcast(self, event: Event) -> None:
        """广播事件到所有客户端"""
        async with self._lock:
            clients = list(self._clients.values())
        
        if not clients:
            return
        
        message = event.to_sse_message()
        disconnected = []
        
        for client in clients:
            try:
                client.queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning(f"SSE client queue full: {client.client_id}")
                disconnected.append(client.client_id)
        
        # 清理断开的客户端
        for client_id in disconnected:
            await self.remove_client(client_id)
    
    def get_client_count(self) -> int:
        """获取当前客户端数量"""
        return len(self._clients)


# 全局客户端管理器
_client_manager: Optional[SSEClientManager] = None


def get_client_manager() -> SSEClientManager:
    """获取客户端管理器"""
    global _client_manager
    if _client_manager is None:
        _client_manager = SSEClientManager()
    return _client_manager


# ─── 全局事件处理器 ───

class SSEEventHandler:
    """SSE 事件处理器 - 将 EventBus 事件转发到 SSE 客户端"""
    
    def __init__(self, client_manager: SSEClientManager):
        self._client_manager = client_manager
        self._is_running = False
    
    async def handle_event(self, event: Event) -> None:
        """处理事件并广播到所有 SSE 客户端"""
        if self._is_running:
            await self._client_manager.broadcast(event)
    
    def start(self) -> None:
        """启动处理器"""
        self._is_running = True
    
    def stop(self) -> None:
        """停止处理器"""
        self._is_running = False


# ─── 请求模型 ───


class PlanRequest(BaseModel):
    intent: str
    mode: str = "auto"
    target: Optional[str] = None
    prd_path: Optional[str] = None


class RunRequest(BaseModel):
    intent: Optional[str] = None
    mode: str = "auto"
    target: Optional[str] = None
    prd_yaml: Optional[str] = None
    prd_path: Optional[str] = None
    execution_id: Optional[str] = None
    resume: bool = False


class StopRequest(BaseModel):
    execution_id: str


class RollbackRequest(BaseModel):
    execution_id: str


class StatusRequest(BaseModel):
    execution_id: Optional[str] = None


# ─── 全局状态 ───

_event_handler: Optional[SSEEventHandler] = None


async def _on_event(event: Any) -> None:
    """EventBus 事件回调"""
    global _event_handler
    if _event_handler:
        await _event_handler.handle_event(event)


# ─── App 工厂 ───


def create_app(project_path: str = ".") -> FastAPI:
    """创建 FastAPI 应用"""
    sc = SprintCycle(project_path=project_path)
    event_bus = get_event_bus()

    app = FastAPI(title="SprintCycle Dashboard", version="0.9.1")

    # 初始化 SSE 客户端管理器
    client_manager = get_client_manager()
    
    # 初始化并启动 SSE 事件处理器
    global _event_handler
    _event_handler = SSEEventHandler(client_manager)
    _event_handler.start()
    
    # 注册全局事件处理器到 EventBus
    # 监听所有事件类型
    for event_type in EventType:
        event_bus.on(event_type, _on_event)

    # ─── API 路由 ───

    @app.post("/api/plan")
    async def api_plan(req: PlanRequest) -> Dict[str, Any]:
        result = sc.plan(intent=req.intent, mode=req.mode, target=req.target, prd_path=req.prd_path)
        return result.to_dict()

    @app.post("/api/run")
    async def api_run(req: RunRequest) -> Dict[str, Any]:
        result = sc.run(
            intent=req.intent, mode=req.mode, target=req.target,
            prd_yaml=req.prd_yaml, prd_path=req.prd_path,
            execution_id=req.execution_id, resume=req.resume,
        )
        return result.to_dict()

    @app.get("/api/diagnose")
    async def api_diagnose() -> Dict[str, Any]:
        result = sc.diagnose()
        return result.to_dict()

    @app.post("/api/status")
    async def api_status(req: StatusRequest) -> Dict[str, Any]:
        result = sc.status(execution_id=req.execution_id)
        return result.to_dict()

    @app.post("/api/rollback")
    async def api_rollback(req: RollbackRequest) -> Dict[str, Any]:
        result = sc.rollback(execution_id=req.execution_id)
        return result.to_dict()

    @app.post("/api/stop")
    async def api_stop(req: StopRequest) -> Dict[str, Any]:
        result = sc.stop(execution_id=req.execution_id)
        return result.to_dict()

    # ─── SSE 事件流 ───

    @app.get("/api/events/stream")
    async def api_events_stream(request: Request) -> StreamingResponse:
        """
        SSE 实时事件流端点
        
        推送 Sprint 执行相关的实时事件：
        - execution_start: 执行开始
        - sprint_start: Sprint 开始
        - sprint_complete: Sprint 完成
        - sprint_failed: Sprint 失败
        - task_start: 任务开始
        - task_complete: 任务完成
        - task_failed: 任务失败
        - execution_complete: 执行完成
        - execution_failed: 执行失败
        """
        client = await client_manager.create_client()
        client_id = client.client_id
        
        async def event_stream() -> AsyncGenerator[str, None]:
            try:
                # 发送连接成功消息
                yield f"event: connected\ndata: {json.dumps({'client_id': client_id, 'message': 'SSE connected'})}\n\n"
                
                # 持续发送事件直到客户端断开
                while True:
                    try:
                        # 等待消息，15秒超时以发送心跳
                        message = await asyncio.wait_for(
                            client.queue.get(),
                            timeout=15.0
                        )
                        yield message
                    except asyncio.TimeoutError:
                        # 发送心跳保活
                        yield f"event: heartbeat\ndata: {json.dumps({'type': 'heartbeat', 'client_id': client_id})}\n\n"
                    except asyncio.CancelledError:
                        break
            finally:
                await client_manager.remove_client(client_id)
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    @app.get("/api/events")
    @app.get("/api/events/legacy")
    async def api_events_legacy() -> StreamingResponse:
        """向后兼容的 SSE 端点 - 重定向到 /api/events/stream"""
        return StreamingResponse(
            _legacy_heartbeat_stream(),
            media_type="text/event-stream"
        )

    async def _legacy_heartbeat_stream() -> AsyncGenerator[str, None]:
        """传统的心跳流（保持向后兼容）"""
        while True:
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            await asyncio.sleep(15)

    @app.get("/api/clients")
    async def api_clients() -> Dict[str, Any]:
        """获取当前 SSE 客户端数量"""
        return {
            "client_count": client_manager.get_client_count(),
        }

    # ─── Dashboard 首页 ───

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return _render_dashboard_html()

    return app


def _render_dashboard_html() -> str:
    """渲染 Dashboard 首页 HTML"""
    return """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SprintCycle Dashboard</title>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0f172a;--surface:#1e293b;--surface2:#26334a;--border:#334155;--text:#e2e8f0;--text-dim:#94a3b8;--text-muted:#64748b;--accent:#38bdf8;--accent2:#818cf8;--green:#22c55e;--red:#ef4444;--yellow:#f59e0b;--purple:#a855f7;--pink:#ec4899;--code-bg:#0b1120}
html,body{height:100%}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.5}
.app{display:flex;flex-direction:column;height:100vh;overflow:hidden}
.header{background:var(--surface);border-bottom:1px solid var(--border);padding:0 24px;display:flex;align-items:center;gap:16px;height:56px;flex-shrink:0}
.header .logo{font-size:18px;font-weight:700;color:var(--accent);display:flex;align-items:center;gap:8px}
.header .logo span{color:var(--text-dim);font-weight:400;font-size:13px}
.header-right{margin-left:auto;display:flex;align-items:center;gap:16px}
.status-pill{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--text-dim);padding:4px 10px;background:var(--bg);border:1px solid var(--border);border-radius:20px}
.dot{width:7px;height:7px;border-radius:50%;background:var(--text-muted)}
.dot.green{background:var(--green);box-shadow:0 0 6px var(--green)}
.dot.red{background:var(--red)}
.dot.yellow{background:var(--yellow)}
.tab-bar{background:var(--surface);border-bottom:1px solid var(--border);display:flex;padding:0 24px;flex-shrink:0;gap:4px}
.tab{padding:12px 20px;font-size:13px;font-weight:500;color:var(--text-dim);cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;display:flex;align-items:center;gap:6px;user-select:none}
.tab:hover{color:var(--text)}
.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.tab .badge{background:var(--accent);color:var(--bg);font-size:10px;font-weight:700;padding:1px 6px;border-radius:10px;min-width:18px;text-align:center}
.main{flex:1;overflow:hidden;display:flex;flex-direction:column}
.panel{display:none;flex-direction:column;height:100%;overflow:hidden}
.panel.active{display:flex}
.prd-panel{padding:20px;gap:16px;overflow-y:auto}
.prd-top{display:grid;grid-template-columns:1fr 1fr;gap:16px;min-height:0}
.prd-top>*{min-height:0}
.panel-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;display:flex;flex-direction:column;overflow:hidden}
.panel-card .card-header{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:var(--text-dim);flex-shrink:0}
.panel-card .card-body{flex:1;overflow:auto}
textarea.prd-input{width:100%;height:100%;background:var(--code-bg);color:var(--text);border:none;padding:14px;font-family:'Fira Code','Cascadia Code','Consolas',monospace;font-size:12px;line-height:1.7;resize:none;outline:none}
textarea.prd-input::placeholder{color:var(--text-muted)}
.prd-controls{padding:12px 16px;border-top:1px solid var(--border);display:flex;gap:8px;flex-shrink:0}
.btn{padding:8px 18px;border-radius:7px;border:none;cursor:pointer;font-size:13px;font-weight:600;transition:all .15s;display:inline-flex;align-items:center;gap:6px}
.btn:disabled{opacity:.45;cursor:not-allowed}
.btn-primary{background:var(--green);color:#fff}
.btn-primary:hover:not(:disabled){background:#16a34a}
.btn-secondary{background:var(--surface2);color:var(--text);border:1px solid var(--border)}
.btn-secondary:hover:not(:disabled){border-color:var(--accent);color:var(--accent)}
.btn-danger{background:var(--red);color:#fff}
.btn-danger:hover:not(:disabled){background:#dc2626}
.btn-sm{padding:5px 12px;font-size:12px}
.plan-result{padding:14px;font-size:13px;overflow:auto;height:100%}
.plan-result .plan-header{font-size:15px;font-weight:700;color:var(--accent);margin-bottom:12px;display:flex;align-items:center;gap:8px}
.plan-result .sprint-item{background:var(--bg);border:1px solid var(--border);border-radius:8px;margin-bottom:8px;overflow:hidden}
.plan-result .sprint-name{padding:8px 12px;font-weight:600;color:var(--text);font-size:12px;background:var(--surface2);border-bottom:1px solid var(--border)}
.plan-result .task-list{padding:8px 12px}
.plan-result .task-item{padding:4px 0;color:var(--text-dim);font-size:12px;display:flex;align-items:flex-start;gap:6px}
.plan-result .task-item::before{content:'→';color:var(--accent);flex-shrink:0}
.plan-result .prd-meta{display:flex;gap:16px;margin-bottom:12px;font-size:12px;color:var(--text-dim)}
.plan-result .error-text{color:var(--red);font-size:13px}
.history-panel{flex:1;overflow-y:auto;padding:20px}
.executions-list{display:flex;flex-direction:column;gap:10px}
.exec-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;transition:border-color .15s}
.exec-card:hover{border-color:var(--accent)}
.exec-card-header{padding:14px 16px;display:flex;align-items:center;gap:12px;cursor:pointer;user-select:none}
.exec-card-header:hover{background:rgba(56,189,248,.04)}
.exec-id{font-family:'Fira Code',monospace;font-size:11px;color:var(--accent2);background:var(--bg);padding:3px 8px;border-radius:4px;flex-shrink:0}
.exec-status{font-size:12px;font-weight:600;padding:3px 10px;border-radius:20px;flex-shrink:0}
.exec-status.running{background:rgba(59,130,246,.2);color:#60a5fa}
.exec-status.completed{background:rgba(34,197,94,.2);color:var(--green)}
.exec-status.failed{background:rgba(239,68,68,.2);color:var(--red)}
.exec-status.cancelled{background:rgba(245,158,11,.2);color:var(--yellow)}
.exec-status.pending{background:rgba(148,163,184,.15);color:var(--text-dim)}
.exec-status.paused{background:rgba(168,85,247,.15);color:var(--purple)}
.exec-info{flex:1;font-size:12px;color:var(--text-dim);display:flex;gap:16px;flex-wrap:wrap}
.exec-actions{display:flex;gap:6px;margin-left:8px}
.exec-detail{display:none;padding:0 16px 16px;border-top:1px solid var(--border)}
.exec-detail.open{display:block}
.sprint-section{margin-top:14px}
.sprint-card{background:var(--bg);border:1px solid var(--border);border-radius:8px;margin-bottom:8px;overflow:hidden}
.sprint-card-header{padding:8px 12px;display:flex;align-items:center;gap:10px;background:var(--surface2);border-bottom:1px solid var(--border);font-size:12px}
.sprint-status-dot{width:6px;height:6px;border-radius:50%}
.sprint-status-dot.success{background:var(--green)}
.sprint-status-dot.failed{background:var(--red)}
.sprint-status-dot.running{background:#60a5fa}
.sprint-status-dot.skipped{background:var(--yellow)}
.sprint-name-label{font-weight:600;color:var(--text);flex:1}
.sprint-meta{color:var(--text-dim)}
.task-result-list{padding:8px 12px}
.task-result-item{display:flex;align-items:flex-start;gap:8px;padding:5px 0;font-size:12px;color:var(--text-dim);border-bottom:1px solid rgba(51,65,85,.5)}
.task-result-item:last-child{border-bottom:none}
.task-result-item .task-status-icon{flex-shrink:0;font-size:11px}
.exec-empty{text-align:center;padding:60px 20px;color:var(--text-muted);font-size:14px}
.diag-panel{padding:20px;overflow-y:auto}
.diag-header{display:flex;align-items:center;gap:24px;margin-bottom:20px}
.diag-score{position:relative;width:100px;height:100px;flex-shrink:0}
.diag-score svg{transform:rotate(-90deg)}
.diag-score-bg{stroke:var(--border);fill:none}
.diag-score-fg{fill:none;stroke-linecap:round;transition:stroke-dashoffset .6s}
.diag-score-text{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.diag-score-num{font-size:24px;font-weight:700;line-height:1}
.diag-score-label{font-size:10px;color:var(--text-dim)}
.diag-summary{flex:1}
.diag-summary h2{font-size:18px;margin-bottom:6px}
.diag-summary p{font-size:13px;color:var(--text-dim)}
.diag-summary .diag-stats{display:flex;gap:24px;margin-top:10px}
.diag-stat{text-align:center}
.diag-stat .num{font-size:20px;font-weight:700}
.diag-stat .lbl{font-size:11px;color:var(--text-muted)}
.diag-stat .num.green{color:var(--green)}
.diag-stat .num.red{color:var(--red)}
.diag-stat .num.yellow{color:var(--yellow)}
.diag-section-title{font-size:14px;font-weight:600;color:var(--text-dim);margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px}
.diag-items{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.diag-item{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px;display:flex;align-items:flex-start;gap:10px}
.diag-item .item-icon{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.diag-item .item-icon.pass{background:rgba(34,197,94,.15)}
.diag-item .item-icon.warn{background:rgba(245,158,11,.15)}
.diag-item .item-icon.fail{background:rgba(239,68,68,.15)}
.diag-item .item-icon.info{background:rgba(56,189,248,.15)}
.diag-item .item-title{font-size:13px;font-weight:600;margin-bottom:2px}
.diag-item .item-msg{font-size:12px;color:var(--text-dim)}
.events-panel{flex:1;display:flex;flex-direction:column;overflow:hidden;padding:16px 20px;gap:12px}
.events-toolbar{display:flex;align-items:center;gap:10px;flex-shrink:0}
.events-toolbar .toolbar-label{font-size:12px;color:var(--text-dim);margin-right:auto}
.events-log{flex:1;background:var(--code-bg);border:1px solid var(--border);border-radius:10px;overflow-y:auto;font-family:'Fira Code','Cascadia Code','Consolas',monospace;font-size:12px;line-height:1.8;padding:8px}
.event-row{padding:3px 8px;border-radius:4px;margin-bottom:2px;display:flex;align-items:flex-start;gap:8px;animation:fadeIn .15s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(-2px)}to{opacity:1}}
.event-row.execution_start{background:rgba(59,130,246,.12);border-left:2px solid #3b82f6}
.event-row.sprint_start{background:rgba(168,85,247,.12);border-left:2px solid #a855f7}
.event-row.sprint_complete{background:rgba(34,197,94,.10);border-left:2px solid #22c55e}
.event-row.sprint_failed{background:rgba(239,68,68,.12);border-left:2px solid #ef4444}
.event-row.task_start{background:rgba(251,191,36,.10);border-left:2px solid #fbbf24}
.event-row.task_complete{background:rgba(34,197,94,.10);border-left:2px solid #22c55e}
.event-row.task_failed{background:rgba(239,68,68,.12);border-left:2px solid #ef4444}
.event-row.execution_complete{background:rgba(34,197,94,.18);border-left:2px solid #22c55e}
.event-row.execution_failed{background:rgba(239,68,68,.18);border-left:2px solid #ef4444}
.event-row.evolution_candidate{background:rgba(236,72,153,.12);border-left:2px solid #ec4899}
.event-row.heartbeat,.event-row.ping{background:transparent;border-left:2px solid var(--border);color:var(--text-muted)}
.ev-ts{color:var(--text-muted);flex-shrink:0;font-size:11px}
.ev-type{font-weight:600;flex-shrink:0;min-width:130px;font-size:11px}
.ev-type.execution_start{color:#60a5fa}
.ev-type.sprint_start{color:#c084fc}
.ev-type.sprint_complete{color:#4ade80}
.ev-type.sprint_failed{color:#f87171}
.ev-type.task_start{color:#fcd34d}
.ev-type.task_complete{color:#4ade80}
.ev-type.task_failed{color:#f87171}
.ev-type.execution_complete{color:#4ade80}
.ev-type.execution_failed{color:#f87171}
.ev-type.evolution_candidate{color:#f472b6}
.ev-content{flex:1;color:var(--text-dim);word-break:break-all}
.ev-badge{font-size:10px;padding:1px 5px;border-radius:3px;font-weight:700;flex-shrink:0}
.ev-badge.agent{background:rgba(129,140,248,.2);color:#818cf8}
.loading{color:var(--text-dim);font-style:italic}
.error-text{color:var(--red)}
.ok-text{color:var(--green)}
.blue-text{color:var(--accent)}
.chevron{transition:transform .2s;font-size:12px;color:var(--text-muted)}
.chevron.open{transform:rotate(90deg)}
@media(max-width:768px){.prd-top{grid-template-columns:1fr}.diag-items{grid-template-columns:1fr}.exec-info{font-size:11px;gap:8px}.header{padding:0 12px}.tab-bar{padding:0 12px}.tab{padding:10px 12px;font-size:12px}}
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <div class="logo">🚀 SprintCycle <span>Dashboard</span></div>
    <div class="header-right">
      <div class="status-pill"><span class="dot" id="sseDot"></span><span id="sseStatus">disconnected</span></div>
      <div class="status-pill">Clients: <b id="clientCount">0</b></div>
      <div class="status-pill">Events: <b id="eventCount">0</b></div>
    </div>
  </div>
  <div class="tab-bar">
    <div class="tab active" data-tab="prd">📝 PRD编辑器</div>
    <div class="tab" data-tab="history">📜 执行历史 <span class="badge" id="historyBadge" style="display:none">0</span></div>
    <div class="tab" data-tab="diag">🏥 诊断</div>
    <div class="tab" data-tab="events">📡 实时事件 <span class="badge" id="liveBadge">0</span></div>
  </div>
  <div class="main">
    <div class="panel prd-panel active" id="panel-prd">
      <div class="prd-top">
        <div class="panel-card">
          <div class="card-header">📝 PRD YAML 编辑器 <span style="margin-left:auto;font-size:11px;color:var(--text-muted);font-weight:400">支持自然语言或直接输入 YAML</span></div>
          <div class="card-body">
            <textarea class="prd-input" id="prdEditor" placeholder="输入 PRD YAML 或直接描述你的意图...

示例（YAML）:
project:
  name: MyApp
  path: ./demo
sprints:
  - name: Sprint 1
    tasks:
      - task: 添加用户认证
        agent: coder

示例（自然语言）:
帮我给 demo 项目添加单元测试"></textarea>
          </div>
          <div class="prd-controls">
            <button class="btn btn-secondary" id="btnClear">🗑️ 清空</button>
            <div style="flex:1"></div>
            <button class="btn btn-secondary" id="btnPlan" onclick="doPlan()">📋 Plan</button>
            <button class="btn btn-primary" id="btnRun" onclick="doRun()">▶ Run</button>
          </div>
        </div>
        <div class="panel-card">
          <div class="card-header">📊 计划预览 <span style="margin-left:auto;font-size:11px;color:var(--text-muted);font-weight:400" id="planMeta"></span></div>
          <div class="card-body">
            <div class="plan-result" id="planResult"><div style="color:var(--text-muted);text-align:center;padding:40px 0;font-size:13px">点击 <b>Plan</b> 预览执行计划，或直接 <b>Run</b> 开始执行</div></div>
          </div>
        </div>
      </div>
    </div>
    <div class="panel history-panel" id="panel-history">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
        <h2 style="font-size:16px;color:var(--text-dim)">执行历史</h2>
        <div style="flex:1"></div>
        <button class="btn btn-secondary btn-sm" onclick="loadHistory()">🔄 刷新</button>
      </div>
      <div class="executions-list" id="executionsList"><div class="exec-empty">加载中...</div></div>
    </div>
    <div class="panel diag-panel" id="panel-diag">
      <div class="diag-header">
        <div class="diag-score">
          <svg width="100" height="100" viewBox="0 0 100 100">
            <circle class="diag-score-bg" cx="50" cy="50" r="42" stroke-width="8"/>
            <circle class="diag-score-fg" id="scoreCircle" cx="50" cy="50" r="42" stroke-width="8" stroke-dasharray="264" stroke-dashoffset="264"/>
          </svg>
          <div class="diag-score-text"><span class="diag-score-num" id="diagScoreNum">—</span><span class="diag-score-label">健康分</span></div>
        </div>
        <div class="diag-summary">
          <h2 id="diagTitle">项目诊断</h2>
          <p id="diagDesc">点击"开始诊断"检查项目健康状态</p>
          <div class="diag-stats" id="diagStats" style="display:none">
            <div class="diag-stat"><div class="num green" id="statPass">0</div><div class="lbl">通过</div></div>
            <div class="diag-stat"><div class="num yellow" id="statWarn">0</div><div class="lbl">警告</div></div>
            <div class="diag-stat"><div class="num red" id="statFail">0</div><div class="lbl">失败</div></div>
          </div>
        </div>
        <button class="btn btn-secondary" onclick="doDiagnose()" id="diagRunBtn">🏥 开始诊断</button>
      </div>
      <div class="diag-section-title">检查项</div>
      <div class="diag-items" id="diagItems"><div style="color:var(--text-muted);font-size:13px;padding:20px 0">暂无诊断数据，点击上方"开始诊断"按钮</div></div>
    </div>
    <div class="panel events-panel" id="panel-events">
      <div class="events-toolbar">
        <span class="toolbar-label">实时事件流 (SSE)</span>
        <button class="btn btn-secondary btn-sm" onclick="clearEvents()">🗑️ 清除</button>
        <label style="display:flex;align-items:center;gap:5px;font-size:12px;color:var(--text-dim);cursor:pointer"><input type="checkbox" id="autoScroll" checked style="accent-color:var(--accent)"> 自动滚动</label>
      </div>
      <div class="events-log" id="eventsLog"></div>
    </div>
  </div>
</div>
<script>
var $=function(id){return document.getElementById(id)};
var $$=function(sel){return document.querySelectorAll(sel)};
var eventSource=null;
var eventCount=0;
var executionsCache=[];
async function apiPost(path,body){var r=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return r.json()}
async function apiGet(path){var r=await fetch('/api/'+path);return r.json()}
$$('.tab').forEach(function(tab){tab.addEventListener('click',function(){$$('.tab').forEach(function(t){t.classList.remove('active')});tab.classList.add('active');$$('.panel').forEach(function(p){p.classList.remove('active')});$('panel-'+tab.dataset.tab).classList.add('active');if(tab.dataset.tab==='history')loadHistory()})});
function connectSSE(){if(eventSource)eventSource.close();eventSource=new EventSource('/api/events/stream');eventSource.onopen=function(){setDot('sseDot','green');$('sseStatus').textContent='connected';updateClientCount()};eventSource.onerror=function(){setDot('sseDot','red');$('sseStatus').textContent='reconnecting...';setTimeout(connectSSE,3000)};var types=['execution_start','sprint_start','sprint_complete','sprint_failed','task_start','task_complete','task_failed','execution_complete','execution_failed','evolution_candidate','heartbeat','ping','connected'];types.forEach(function(type){eventSource.addEventListener(type,function(e){try{var data=JSON.parse(e.data);if(type!=='connected')appendEvent({event_type:type},data)}catch(err){console.error('Parse error:',err)}})})}
function setDot(id,cls){var dot=$(id);if(cls)dot.className='dot '+cls;else dot.className='dot'}
async function updateClientCount(){try{var d=await apiGet('clients');$('clientCount').textContent=d.client_count||0}catch(_){}}
var EVENT_META={execution_start:{icon:'🚀',label:'EXEC START'},sprint_start:{icon:'📦',label:'SPRINT START'},sprint_complete:{icon:'✅',label:'SPRINT DONE'},sprint_failed:{icon:'❌',label:'SPRINT FAIL'},task_start:{icon:'📋',label:'TASK START'},task_complete:{icon:'✅',label:'TASK DONE'},task_failed:{icon:'❌',label:'TASK FAIL'},execution_complete:{icon:'🎉',label:'EXEC DONE'},execution_failed:{icon:'💥',label:'EXEC FAIL'},evolution_candidate:{icon:'🧬',label:'EVOLUTION'},heartbeat:{icon:'💓',label:'HEARTBEAT'},ping:{icon:'📶',label:'PING'}};
function buildEventContent(data){var parts=[];if(data.execution_id)parts.push('['+data.execution_id.substring(0,8)+']');if(data.sprint_name)parts.push(data.sprint_name);if(data.task)parts.push(data.task);if(data.agent_type)parts.push('@'+data.agent_type);if(data.error)parts.push('⚠ '+data.error);if(data.duration!==undefined&&data.duration!==null)parts.push(data.duration.toFixed(1)+'s');return parts.join(' · ')||data.message||''}
function appendEvent(base,data){var log=$('eventsLog');var type=base.event_type;var meta=EVENT_META[type]||{icon:'?',label:type.toUpperCase()};var ts=data.timestamp?new Date(data.timestamp).toLocaleTimeString('zh-CN',{hour12:false}):'';var content=buildEventContent(data);var agentBadge=data.agent_type?'<span class="ev-badge agent">'+data.agent_type+'</span>':'';var row=document.createElement('div');row.className='event-row '+type;row.innerHTML='<span class="ev-ts">'+ts+'</span><span class="ev-type '+type+'">'+meta.icon+' '+meta.label+'</span><span class="ev-content">'+escHtml(content)+agentBadge+'</span>';log.appendChild(row);eventCount++;$('eventCount').textContent=eventCount;$('liveBadge').textContent=eventCount;if($('autoScroll').checked)log.scrollTop=log.scrollHeight}
function clearEvents(){$('eventsLog').innerHTML='';eventCount=0;$('eventCount').textContent='0';$('liveBadge').textContent='0'}
function escHtml(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
$('btnClear').addEventListener('click',function(){$('prdEditor').value='';$('planResult').innerHTML='<div style="color:var(--text-muted);text-align:center;padding:40px 0;font-size:13px">已清空，点击 <b>Plan</b> 预览执行计划</div>';$('planMeta').textContent=''});
$('prdEditor').addEventListener('keydown',function(e){if(e.key==='Enter'&&(e.ctrlKey||e.metaKey))doRun()});
function setButtonsDisabled(disabled){$('btnPlan').disabled=disabled;$('btnRun').disabled=disabled}
function renderPlanResult(data){if(!data.success&&data.error)return'<div class="error-text">❌ '+escHtml(data.error)+'</div>';if(!data.sprints||data.sprints.length===0)return'<div class="ok-text">✅ 计划为空</div>';var meta=[];if(data.prd_name)meta.push('📦 '+escHtml(data.prd_name));if(data.mode)meta.push('⚙ '+escHtml(data.mode));if(data.sprints)meta.push('📦 '+data.sprints.length+' Sprint');if(data.duration!==undefined)meta.push('⏱ '+data.duration.toFixed(2)+'s');if(meta.length)$('planMeta').textContent=meta.join(' · ');var html='<div class="plan-header">📋 执行计划预览</div>';if(meta.length)html+='<div class="prd-meta">'+meta.map(function(m){return'<span>'+m+'</span>'}).join('')+'</div>';data.sprints.forEach(function(sp,i){var tasks=Array.isArray(sp.tasks)?sp.tasks:[];html+='<div class="sprint-item"><div class="sprint-name">Sprint '+(i+1)+': '+escHtml(sp.name||'Unnamed')+'</div><div class="task-list">'+tasks.map(function(t){return'<div class="task-item">'+escHtml(t)+'</div>'}).join('')+'</div></div>'});return html}
async function doPlan(){var input=$('prdEditor').value.trim();if(!input){alert('请输入 PRD YAML 或意图描述');return}setButtonsDisabled(true);$('planResult').innerHTML='<div class="loading">⏳ 正在规划...</div>';try{var body=input.match(/^(project|sprints|mode|name|version)\s*:/im)?{prd_yaml:input}:{intent:input};var data=await apiPost('plan',body);$('planResult').innerHTML=renderPlanResult(data)}catch(e){$('planResult').innerHTML='<div class="error-text">请求失败: '+escHtml(e.message)+'</div>'}finally{setButtonsDisabled(false)}}
async function doRun(){var input=$('prdEditor').value.trim();if(!input){alert('请输入 PRD YAML 或意图描述');return}setButtonsDisabled(true);$('planResult').innerHTML='<div class="loading">🚀 正在执行... 请关注「实时事件」面板</div>';try{var body=input.match(/^(project|sprints|mode|name|version)\s*:/im)?{prd_yaml:input}:{intent:input};var data=await apiPost('run',body);$('planResult').innerHTML=renderPlanResult(data);loadHistory()}catch(e){$('planResult').innerHTML='<div class="error-text">请求失败: '+escHtml(e.message)+'</div>'}finally{setButtonsDisabled(false)}}
async function loadHistory(){var list=$('executionsList');list.innerHTML='<div style="color:var(--text-muted);padding:20px 0;text-align:center">⏳ 加载中...</div>';try{var data=await apiPost('status',{});if(!data.success){list.innerHTML='<div class="error-text">加载失败: '+escHtml(data.error||'unknown')+'</div>';return}executionsCache=data.executions||[];renderExecutions(executionsCache)}catch(e){list.innerHTML='<div class="error-text">请求失败: '+escHtml(e.message)+'</div>'}}
function renderExecutions(execs){var list=$('executionsList');if(!execs||execs.length===0){list.innerHTML='<div class="exec-empty">📭 暂无执行历史<br><br><button class="btn btn-secondary btn-sm" onclick="loadHistory()">🔄 刷新</button></div>';$('historyBadge').style.display='none';return}$('historyBadge').textContent=execs.length;$('historyBadge').style.display='';var html='';execs.forEach(function(ex){var status=ex.status||'unknown';var progress=ex.total_sprints>0?'Sprint '+(ex.current_sprint||0)+'/'+ex.total_sprints:'';var tasks=ex.completed_tasks!==undefined?ex.completed_tasks+'/'+(ex.total_tasks||'?')+' 任务':'';var created=ex.created_at?new Date(ex.created_at).toLocaleString('zh-CN',{hour12:false}):'';var canResume=['cancelled','failed','paused'].indexOf(status)!==-1&&ex.checkpoint;var execId=ex.execution_id||'';var shortId=execId.length>8?execId.substring(0,8):execId;html+='<div class="exec-card"><div class="exec-card-header" onclick="toggleExec(''+execId+'')"><span class="exec-id">'+escHtml(shortId)+'</span><span class="exec-status '+status+'">'+status+'</span><div class="exec-info">'+(ex.prd_name?'<span>📦 '+escHtml(ex.prd_name)+'</span>':'')+(ex.mode?'<span>⚙ '+escHtml(ex.mode)+'</span>':'')+(progress?'<span>📦 '+progress+'</span>':'')+(tasks?'<span>📋 '+tasks+'</span>':'')+(created?'<span>🕐 '+created+'</span>':'')+(ex.error?'<span style="color:var(--red)">❌ '+escHtml(ex.error.substring(0,50))+'</span>':'')+'</div><div class="exec-actions">'+(canResume?'<button class="btn btn-sm btn-primary" onclick="event.stopPropagation();resumeExec(''+execId+'')">▶ Resume</button>':'')+'<button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();stopExec(''+execId+'')" title="停止">⏹</button></div><span class="chevron" id="chev-'+execId+'">▶</span></div><div class="exec-detail" id="detail-'+execId+'">'+renderExecDetail(ex)+'</div></div>'});list.innerHTML=html}
function renderExecDetail(ex){var sprints=(ex.metadata&&ex.metadata.sprint_history)||(ex.checkpoint&&ex.checkpoint.sprint_history)||[];if(!sprints.length)return'<div style="padding:14px 0;color:var(--text-muted);font-size:12px">暂无详细信息</div>';var html='<div class="sprint-section">';sprints.forEach(function(sp,i){var tasks=Array.isArray(sp.tasks)?sp.tasks:[];var spStatus=sp.status||'unknown';var dotClass={success:'success',failed:'failed',running:'running',skipped:'skipped'}[spStatus]||'success';html+='<div class="sprint-card"><div class="sprint-card-header"><span class="sprint-status-dot '+dotClass+'"></span><span class="sprint-name-label">'+escHtml(sp.name||('Sprint '+(i+1)))+'</span><span class="sprint-meta">'+spStatus+'</span>'+(sp.duration!==undefined?'<span class="sprint-meta">⏱ '+sp.duration.toFixed(1)+'s</span>':'')+'</div><div class="task-result-list">';tasks.forEach(function(t){var icon=t.status==='success'?'✅':t.status==='failed'?'❌':'⏳';var color=t.status==='failed'?'var(--red)':t.status==='success'?'var(--green)':'var(--text-dim)';html+='<div class="task-result-item"><span class="task-status-icon" style="color:'+color+'">'+icon+'</span><span>'+escHtml(t.task||t.task_name||'unnamed')+'</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px">'+escHtml(t.agent||'')+'</span>'+(t.error?'<span style="color:var(--red);font-size:11px;margin-left:6px">⚠</span>':'')+'</div>'});html+='</div></div>'});html+='</div>';return html}
function toggleExec(execId){var detail=$('detail-'+execId);var chev=$('chev-'+execId);if(!detail)return;if(detail.classList.contains('open')){detail.classList.remove('open');chev.classList.remove('open')}else {detail.classList.add('open');chev.classList.add('open')}}
async function resumeExec(execId){if(!confirm('确认恢复执行 '+execId.substring(0,8)+' ?'))return;try{var data=await apiPost('run',{execution_id:execId,resume:true});if(data.success){loadHistory();switchTab('events')}else{alert('Resume 失败: '+(data.error||'unknown'))}}catch(e){alert('请求失败: '+e.message)}}
async function stopExec(execId){if(!confirm('确认停止执行 '+execId.substring(0,8)+' ?'))return;try{await apiPost('stop',{execution_id:execId});loadHistory()}catch(e){alert('请求失败: '+e.message)}}
function scoreColor(score){if(score>=80)return'#22c55e';if(score>=50)return'#f59e0b';return'#ef4444'}
function renderDiagResult(data){if(!data.success&&data.error){$('diagDesc').textContent='诊断失败: '+data.error;return}var score=data.health_score||0;var circ=$('scoreCircle');var circLen=264;var offset=circLen*(1-score/100);circ.style.stroke=scoreColor(score);circ.style.strokeDashoffset=offset;$('diagScoreNum').textContent=Math.round(score);$('diagScoreNum').style.color=scoreColor(score);var issues=data.issues||[];var pass=issues.filter(function(i){return['pass','ok','info'].indexOf((i.severity||'').toLowerCase())!==-1}).length;var warn=issues.filter(function(i){return['warn','warning'].indexOf((i.severity||'').toLowerCase())!==-1}).length;var fail=issues.filter(function(i){return['fail','error','critical'].indexOf((i.severity||'').toLowerCase())!==-1}).length;var total=issues.length;$('statPass').textContent=pass;$('statWarn').textContent=warn;$('statFail').textContent=fail;$('diagStats').style.display='flex';if(score>=80){$('diagTitle').textContent='✅ 项目健康';$('diagDesc').textContent='健康分 '+Math.round(score)+'/100，共 '+total+' 项检查，全部通过'}else if(score>=50){$('diagTitle').textContent='⚠ 项目需要注意';$('diagDesc').textContent='健康分 '+Math.round(score)+'/100，发现 '+fail+' 个问题，'+warn+' 个警告'}else{$('diagTitle').textContent='🚨 项目需要修复';$('diagDesc').textContent='健康分 '+Math.round(score)+'/100，存在 '+fail+' 个关键问题'}var items=$('diagItems');if(!total){items.innerHTML='<div style="color:var(--text-muted);font-size:13px;padding:10px 0">暂无详细检查项</div>';return}var itemsHtml='';issues.forEach(function(issue){var sev=(issue.severity||'info').toLowerCase();var icon=sev==='pass'||sev==='ok'?'✅':sev==='warn'||sev==='warning'?'⚠️':sev==='fail'||sev==='error'||sev==='critical'?'❌':'ℹ️';var cls=sev==='pass'||sev==='ok'?'pass':sev==='warn'||sev==='warning'?'warn':sev==='fail'||sev==='error'||sev==='critical'?'fail':'info';var msg=issue.message||issue.msg||JSON.stringify(issue);itemsHtml+='<div class="diag-item"><div class="item-icon '+cls+'">'+icon+'</div><div><div class="item-title">'+escHtml(sev.toUpperCase())+'</div><div class="item-msg">'+escHtml(msg)+'</div></div></div>'});items.innerHTML=itemsHtml}
async function doDiagnose(){var btn=$('diagRunBtn');btn.disabled=true;btn.textContent='⏳ 诊断中...';try{var data=await apiGet('diagnose');renderDiagResult(data)}catch(e){$('diagDesc').textContent='诊断请求失败: '+e.message}finally{btn.disabled=false;btn.textContent='🏥 开始诊断'}}
function switchTab(name){$$('.tab').forEach(function(t){t.classList.toggle('active',t.dataset.tab===name)});$$('.panel').forEach(function(p){p.classList.toggle('active',p.id==='panel-'+name)})}
connectSSE();setInterval(updateClientCount,5000);loadHistory()
</script>
</body>
</html>"""


__all__ = ["create_app"]
