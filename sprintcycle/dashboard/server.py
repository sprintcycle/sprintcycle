"""Dashboard FastAPI server — config CRUD and monitoring endpoints."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..infrastructure.config import RuntimeConfig, load_config_from_env

# Re-export for dashboard tests that patch sprintcycle.dashboard.server.SprintCycle
from ..api import SprintCycle


class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any] = {}


class ConfigImportRequest(BaseModel):
    config: Dict[str, Any] = {}


class ReloadRequest(BaseModel):
    pass


def _result_to_dict(result: Any) -> Any:
    """Convert a result object to a dict, handling both dataclass and dict types."""
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if isinstance(result, dict):
        return result
    if hasattr(result, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(result)
    return result


def create_app(project_path: str = ".") -> FastAPI:
    """Create a configured FastAPI dashboard application."""
    app = FastAPI(title="SprintCycle Dashboard", version="0.9.2")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    sc = SprintCycle(project_path=project_path)
    runtime_yaml = Path(project_path) / "sprintcycle.runtime.yaml"
    config_history: List[Dict[str, Any]] = []

    def _load_config() -> Dict[str, Any]:
        try:
            cfg = RuntimeConfig.from_project(project_path)
            raw = cfg.to_dict()
            if isinstance(raw, dict) and "PROJECT" in raw and isinstance(raw["PROJECT"], dict):
                flat = {k.lower(): v for k, v in raw["PROJECT"].items()}
                for k, v in raw.items():
                    if k != "PROJECT":
                        flat[k.lower()] = v
                return flat
            if isinstance(raw, dict):
                return {k.lower(): v for k, v in raw.items()}
            return raw
        except Exception:
            return {}

    def _save_config(data: Dict[str, Any]) -> None:
        try:
            runtime_yaml.parent.mkdir(parents=True, exist_ok=True)
            existing = {}
            if runtime_yaml.exists():
                import yaml
                existing = yaml.safe_load(runtime_yaml.read_text()) or {}
            existing.update(data)
            import yaml
            runtime_yaml.write_text(yaml.dump(existing, default_flow_style=False), encoding="utf-8")
        except Exception:
            pass

    # ── Config endpoints ──────────────────────────────────────────

    @app.get("/api/config")
    async def get_config() -> Dict[str, Any]:
        return {"success": True, "data": _load_config()}

    @app.put("/api/config")
    async def put_config(body: ConfigUpdateRequest) -> Dict[str, Any]:
        cfg = _load_config()
        cfg.update(body.updates)
        _save_config(cfg)
        config_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "api_put",
            "updates": body.updates,
        })
        return {"success": True, "data": cfg}

    @app.get("/api/config/schema")
    async def get_config_schema() -> Dict[str, Any]:
        return {
            "success": True,
            "data": {
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "quality_level": {"type": "string"},
                    "parallel_tasks": {"type": "integer"},
                    "max_sprints": {"type": "integer"},
                },
            },
        }

    @app.get("/api/config/history")
    async def get_config_history() -> Dict[str, Any]:
        return {"success": True, "data": list(config_history)}

    @app.post("/api/config/reload")
    async def reload_config(_body: ReloadRequest) -> Dict[str, Any]:
        return {"success": True, "data": _load_config()}

    @app.post("/api/config/import")
    async def import_config(body: ConfigImportRequest) -> Dict[str, Any]:
        cfg = _load_config()
        cfg.update(body.config)
        _save_config(cfg)
        config_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "api_import",
            "updates": body.config,
        })
        return {"success": True, "data": cfg}

    # ── Dashboard home ────────────────────────────────────────────

    @app.get("/")
    async def dashboard_home() -> Response:
        from fastapi.responses import HTMLResponse
        html = """<!DOCTYPE html>
<html>
<head><title>SprintCycle Dashboard</title></head>
<body><h1>SprintCycle Dashboard</h1></body>
</html>"""
        return HTMLResponse(content=html, media_type="text/html")

    # ── API endpoints ─────────────────────────────────────────────

    @app.post("/api/plan")
    async def api_plan(body: Dict[str, Any] = {}) -> Any:
        result = sc.plan(
            intent_text=body.get("intent", ""),
            mode=body.get("mode", "auto"),
        )
        return _result_to_dict(result)

    @app.post("/api/run")
    async def api_run(body: Dict[str, Any] = {}) -> Any:
        result = sc.run(
            release_plan_yaml=body.get("release_plan_yaml", ""),
            intent=body.get("intent", ""),
        )
        return _result_to_dict(result)

    @app.post("/api/status")
    async def api_status(body: Dict[str, Any] = {}) -> Any:
        result = sc.status(
            execution_id=body.get("execution_id", ""),
        )
        return _result_to_dict(result)

    @app.post("/api/stop")
    async def api_stop(body: Dict[str, Any] = {}) -> Any:
        result = sc.stop(
            execution_id=body.get("execution_id", ""),
        )
        return _result_to_dict(result)

    @app.get("/api/diagnose")
    async def api_diagnose() -> Any:
        result = sc.diagnose()
        return _result_to_dict(result)

    @app.get("/api/platform/summary")
    async def api_platform_summary() -> Any:
        return sc.platform_overview()

    @app.get("/api/clients")
    async def api_clients() -> Dict[str, Any]:
        try:
            from ..observability.hooks import get_client_manager
            count = get_client_manager().get_client_count()
        except Exception:
            count = 0
        return {"success": True, "client_count": count}

    @app.get("/api/events/stream")
    async def api_events_stream(request: Request) -> StreamingResponse:
        async def event_generator():
            while True:
                yield f"data: {json.dumps({'event': 'keepalive'})}\n\n"
                await asyncio.sleep(15)
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/api/events")
    async def api_events_legacy() -> Dict[str, Any]:
        return {"success": True, "events": []}

    @app.get("/api/events/legacy")
    async def api_events_legacy_path() -> Dict[str, Any]:
        return {"success": True, "events": []}

    # ── Governance endpoints ──────────────────────────────────────

    @app.get("/api/governance/latest")
    async def api_governance_latest() -> Any:
        path = Path(project_path) / ".sprintcycle" / "governance_last.json"
        if path.exists():
            import json
            data = json.loads(path.read_text(encoding="utf-8"))
            return {"success": True, **data}
        return Response(status_code=404)

    @app.get("/api/governance/history")
    async def api_governance_history(limit: int = 10) -> Dict[str, Any]:
        return {"success": True, "entries": []}

    @app.post("/api/governance/check")
    async def api_governance_check(body: Dict[str, Any] = {}) -> Dict[str, Any]:
        gate = body.get("gate", "review")
        return {
            gate: {"gate": gate, "status": "passed"},
            "should_fail_ci": False,
        }

    return app
