"""
Dashboard 管理平台 — 进程内指标、审计轨迹、执行阶段摘要。

与 Prometheus 解耦：面向控制台 UI 的轻量计数与环形审计；SSE 事件类型分布自事件总线回调更新。
"""

from __future__ import annotations

import threading
import time
from collections import Counter, deque
from typing import Any, Deque, Dict, List, Optional


_lock = threading.RLock()
_started_at = time.time()
_http_by_route: Counter[str] = Counter()
_http_errors_by_route: Counter[str] = Counter()
_http_duration_ms_total: float = 0.0
_http_duration_ms_n: int = 0
_sse_event_types: Counter[str] = Counter()
_audit: Deque[Dict[str, Any]] = deque(maxlen=80)


def reset_platform_state_for_tests() -> None:
    """测试隔离：清空进程内指标与审计。"""
    global _started_at, _http_duration_ms_total, _http_duration_ms_n
    with _lock:
        _started_at = time.time()
        _http_by_route.clear()
        _http_errors_by_route.clear()
        _http_duration_ms_total = 0.0
        _http_duration_ms_n = 0
        _sse_event_types.clear()
        _audit.clear()


def record_http_request(*, route: str, method: str, status_code: int, duration_ms: float) -> None:
    global _http_duration_ms_total, _http_duration_ms_n
    key = f"{method} {route}"
    with _lock:
        _http_by_route[key] += 1
        if status_code >= 400:
            _http_errors_by_route[key] += 1
        _http_duration_ms_total += duration_ms
        _http_duration_ms_n += 1
        _audit.append(
            {
                "ts": time.time(),
                "kind": "http",
                "route": route,
                "method": method,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )


def record_sse_event_type(event_type: str) -> None:
    with _lock:
        _sse_event_types[event_type] += 1


def _derive_lane(ex: Dict[str, Any]) -> Dict[str, Any]:
    """将单条执行状态 dict 映射为控制台「阶段」轴（与任务级 status 字符串区分）。"""
    status = str(ex.get("status") or "").lower()
    cur = int(ex.get("current_sprint") or 0)
    total_s = int(ex.get("total_sprints") or 0)
    ct = int(ex.get("completed_tasks") or 0)
    tt = int(ex.get("total_tasks") or 0)

    lane_id = status or "unknown"
    label = status
    hint = ""

    if status == "running":
        lane_id = "running"
        done_sp = min(cur, total_s) if total_s else cur
        active_1based = min(done_sp + 1, total_s) if total_s else 1
        label = f"执行中 · Sprint {active_1based}/{total_s or '?'}" if total_s else "执行中"
        if tt > 0:
            hint = f"任务 {ct}/{tt}"
    elif status == "paused":
        lane_id = "paused"
        label = "已暂停（可 Resume）"
        if total_s:
            hint = f"进度约 Sprint {min(cur + 1, total_s)}/{total_s}"
    elif status in ("completed",):
        lane_id = "completed"
        label = "已完成"
        if total_s:
            hint = f"{total_s} 个 Sprint"
    elif status in ("failed",):
        lane_id = "failed"
        label = "失败"
        err = ex.get("error")
        if isinstance(err, str) and err:
            hint = err[:160]
    elif status in ("cancelled",):
        lane_id = "cancelled"
        label = "已取消"
    elif status in ("partial",):
        lane_id = "partial"
        label = "部分完成"
    else:
        label = status or "未知"

    progress = None
    if total_s and total_s > 0:
        progress = min(100.0, max(0.0, 100.0 * cur / total_s))
    elif tt and tt > 0:
        progress = min(100.0, max(0.0, 100.0 * ct / tt))

    return {
        "lane_id": lane_id,
        "lane_label_zh": label,
        "lane_hint": hint,
        "progress_percent": None if progress is None else round(progress, 1),
    }


def build_executions_overview(executions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """聚合执行列表：按会话 status 计数 + 每条附带 lane。"""
    by_status: Counter[str] = Counter()
    running: List[Dict[str, Any]] = []
    enriched: List[Dict[str, Any]] = []

    for ex in executions:
        if not isinstance(ex, dict):
            continue
        st = str(ex.get("status") or "")
        by_status[st] += 1
        lane = _derive_lane(ex)
        row = {**ex, **lane}
        enriched.append(row)
        if st == "running":
            running.append(row)

    primary = None
    if running:
        primary = max(running, key=lambda r: str(r.get("updated_at") or ""))
    elif enriched:
        primary = max(enriched, key=lambda r: str(r.get("updated_at") or r.get("created_at") or ""))

    primary_summary = None
    if primary:
        primary_summary = {
            "execution_id": primary.get("execution_id"),
            "release_plan_name": primary.get("release_plan_name"),
            "lane_id": primary.get("lane_id"),
            "lane_label_zh": primary.get("lane_label_zh"),
            "lane_hint": primary.get("lane_hint"),
            "progress_percent": primary.get("progress_percent"),
            "updated_at": primary.get("updated_at"),
        }

    return {
        "count": len(enriched),
        "by_status": dict(by_status),
        "running_count": len(running),
        "executions": enriched,
        "primary_execution": primary_summary,
    }


def get_platform_snapshot(
    *,
    project_path: str,
    sse_client_count: int,
    executions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """组装 GET /api/platform/summary 的 metrics + 执行总览。"""
    now = time.time()
    with _lock:
        http_total = sum(_http_by_route.values())
        http_err = sum(_http_errors_by_route.values())
        avg_ms = (
            (_http_duration_ms_total / _http_duration_ms_n) if _http_duration_ms_n else 0.0
        )
        sse_counts = dict(_sse_event_types.most_common(40))
        by_route = dict(_http_by_route.most_common(30))
        audit = list(_audit)[-40:]

    ex_list = executions if executions is not None else []
    overview = build_executions_overview(ex_list)

    return {
        "success": True,
        "project_path": project_path,
        "process": {
            "uptime_seconds": round(now - _started_at, 2),
            "started_at_unix": round(_started_at, 3),
        },
        "sse": {
            "connected_clients": sse_client_count,
        },
        "http": {
            "requests_total": http_total,
            "requests_4xx_5xx": http_err,
            "avg_duration_ms": round(avg_ms, 2),
            "by_route": by_route,
        },
        "execution_events_observed": sse_counts,
        "executions_overview": overview,
        "recent_activity": audit,
    }
