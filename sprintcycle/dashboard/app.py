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
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }
.container { max-width: 960px; margin: 0 auto; padding: 24px; }
h1 { font-size: 24px; margin-bottom: 20px; color: #38bdf8; }
.status-bar { display: flex; gap: 16px; margin-bottom: 20px; font-size: 13px; color: #94a3b8; }
.status-bar .status { display: flex; align-items: center; gap: 6px; }
.status-bar .dot { width: 8px; height: 8px; border-radius: 50%; background: #64748b; }
.status-bar .dot.connected { background: #22c55e; }
.status-bar .dot.disconnected { background: #ef4444; }
.input-bar { display: flex; gap: 8px; margin-bottom: 24px; }
.input-bar input { flex: 1; padding: 12px 16px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #e2e8f0; font-size: 14px; }
.input-bar input:focus { outline: none; border-color: #38bdf8; }
.btn { padding: 12px 20px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; }
.btn-run { background: #22c55e; color: #fff; }
.btn-plan { background: #3b82f6; color: #fff; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.section { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.section h2 { font-size: 16px; color: #94a3b8; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.events-log { max-height: 300px; overflow-y: auto; font-family: 'Fira Code', monospace; font-size: 12px; line-height: 1.8; }
.events-log .event { padding: 4px 8px; border-radius: 4px; margin-bottom: 4px; }
.events-log .event.execution_start { background: rgba(59, 130, 246, 0.2); border-left: 3px solid #3b82f6; }
.events-log .event.sprint_start { background: rgba(168, 85, 247, 0.2); border-left: 3px solid #a855f7; }
.events-log .event.sprint_complete { background: rgba(34, 197, 94, 0.2); border-left: 3px solid #22c55e; }
.events-log .event.sprint_failed { background: rgba(239, 68, 68, 0.2); border-left: 3px solid #ef4444; }
.events-log .event.task_start { background: rgba(251, 191, 36, 0.2); border-left: 3px solid #fbbf24; }
.events-log .event.task_complete { background: rgba(34, 197, 94, 0.2); border-left: 3px solid #22c55e; }
.events-log .event.task_failed { background: rgba(239, 68, 68, 0.2); border-left: 3px solid #ef4444; }
.events-log .event.execution_complete { background: rgba(34, 197, 94, 0.3); border-left: 3px solid #22c55e; }
.events-log .event.execution_failed { background: rgba(239, 68, 68, 0.3); border-left: 3px solid #ef4444; }
.events-log .event.heartbeat { background: transparent; border-left: 3px solid #64748b; color: #64748b; }
.events-log .timestamp { color: #64748b; margin-right: 8px; }
.events-log .agent { color: #38bdf8; margin-right: 8px; }
.output { white-space: pre-wrap; font-family: 'Fira Code', monospace; font-size: 13px; line-height: 1.6; color: #cbd5e1; }
.output .ok { color: #22c55e; }
.output .err { color: #ef4444; }
.actions { display: flex; gap: 8px; margin-top: 12px; }
.btn-sm { padding: 6px 12px; font-size: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #94a3b8; cursor: pointer; }
.btn-sm:hover { border-color: #38bdf8; color: #38bdf8; }
</style>
</head>
<body>
<div class="container">
  <h1>🚀 SprintCycle Dashboard</h1>
  <div class="status-bar">
    <div class="status"><span class="dot" id="sseDot"></span> SSE <span id="sseStatus">disconnected</span></div>
    <div class="status">Clients: <span id="clientCount">0</span></div>
    <div class="status">Events: <span id="eventCount">0</span></div>
  </div>
  <div class="input-bar">
    <input id="intent" placeholder="描述你的意图..." autofocus />
    <button class="btn btn-plan" onclick="doPlan()">📋 Plan</button>
    <button class="btn btn-run" onclick="doRun()">▶ Run</button>
  </div>
  <div class="section">
    <h2>📊 实时事件流</h2>
    <div class="events-log" id="eventsLog"></div>
  </div>
  <div class="section">
    <h2>📋 输出</h2>
    <div class="output" id="output">等待输入...</div>
    <div class="actions">
      <button class="btn-sm" onclick="doDiagnose()">🏥 诊断</button>
      <button class="btn-sm" onclick="doStatus()">📜 历史</button>
      <button class="btn-sm" onclick="clearEvents()">🗑️ 清除事件</button>
    </div>
  </div>
</div>
<script>
const $ = id => document.getElementById(id);
let eventSource = null;
let eventCount = 0;

async function api(path, body) {
  const r = await fetch('/api/' + path, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  });
  return r.json();
}

function show(data) {
  $('output').textContent = JSON.stringify(data, null, 2);
}

function addEvent(event) {
  const log = $('eventsLog');
  const div = document.createElement('div');
  div.className = 'event ' + event.event_type;
  
  const ts = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '';
  const agent = event.agent_type ? `[${event.agent_type}]` : '';
  const msg = event.message || getEventMessage(event);
  
  div.innerHTML = `<span class="timestamp">${ts}</span><span class="agent">${agent}</span>${msg}`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  
  eventCount++;
  $('eventCount').textContent = eventCount;
}

function getEventMessage(event) {
  const type = event.event_type;
  const names = {
    'execution_start': '🚀 执行开始',
    'sprint_start': '📦 Sprint 开始',
    'sprint_complete': '✅ Sprint 完成',
    'sprint_failed': '❌ Sprint 失败',
    'task_start': '📋 任务开始',
    'task_complete': '✅ 任务完成',
    'task_failed': '❌ 任务失败',
    'execution_complete': '🎉 执行完成',
    'execution_failed': '💥 执行失败',
    'heartbeat': '💓 心跳',
  };
  return names[type] || type;
}

function connectSSE() {
  if (eventSource) {
    eventSource.close();
  }
  
  eventSource = new EventSource('/api/events/stream');
  
  eventSource.onopen = () => {
    $('sseDot').className = 'dot connected';
    $('sseStatus').textContent = 'connected';
    updateClientCount();
  };
  
  eventSource.onerror = () => {
    $('sseDot').className = 'dot disconnected';
    $('sseStatus').textContent = 'reconnecting...';
    setTimeout(connectSSE, 3000);
  };
  
  // 处理所有事件类型
  const eventTypes = [
    'execution_start', 'sprint_start', 'sprint_complete', 'sprint_failed',
    'task_start', 'task_complete', 'task_failed',
    'execution_complete', 'execution_failed', 'heartbeat', 'connected'
  ];
  
  eventTypes.forEach(type => {
    eventSource.addEventListener(type, (e) => {
      try {
        const data = JSON.parse(e.data);
        if (type === 'connected') {
          console.log('SSE connected:', data.client_id);
        } else {
          addEvent({ event_type: type, ...data });
        }
      } catch (err) {
        console.error('Failed to parse event:', err);
      }
    });
  });
}

async function updateClientCount() {
  try {
    const r = await fetch('/api/clients');
    const data = await r.json();
    $('clientCount').textContent = data.client_count;
  } catch (err) {
    console.error('Failed to get client count:', err);
  }
}

function clearEvents() {
  $('eventsLog').innerHTML = '';
  eventCount = 0;
  $('eventCount').textContent = '0';
}

async function doPlan() {
  const intent = $('intent').value; if (!intent) return;
  show({status: 'planning...'});
  const r = await api('plan', {intent});
  show(r);
}

async function doRun() {
  const intent = $('intent').value; if (!intent) return;
  show({status: 'running...'});
  const r = await api('run', {intent});
  show(r);
}

async function doDiagnose() {
  show({status: 'diagnosing...'});
  const r = await fetch('/api/diagnose').then(r => r.json());
  show(r);
}

async function doStatus() {
  show({status: 'loading...'});
  const r = await api('status', {});
  show(r);
}

$('intent').addEventListener('keydown', e => { if (e.key === 'Enter') doRun(); });

// 启动 SSE 连接
connectSSE();
setInterval(updateClientCount, 5000);
</script>
</body>
</html>"""


__all__ = ["create_app"]
