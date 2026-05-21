"""Dashboard FastAPI server — config CRUD and monitoring endpoints."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..infrastructure.config import RuntimeConfig, load_config_from_env


class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any] = {}


class ConfigImportRequest(BaseModel):
    config: Dict[str, Any] = {}


class ReloadRequest(BaseModel):
    pass


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

    runtime_yaml = Path(project_path) / "sprintcycle.runtime.yaml"
    config_history: List[Dict[str, Any]] = []

    def _load_config() -> Dict[str, Any]:
        try:
            cfg = RuntimeConfig.from_project(project_path)
            raw = cfg.to_dict()
            # Flatten dynaconf-nested structure and lowercase keys
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

    return app
