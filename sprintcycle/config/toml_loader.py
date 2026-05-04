"""
加载项目根目录的 sprintcycle.toml，并映射为 RuntimeConfig 可 merge 的扁平字典。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def load_sprintcycle_toml(project_path: str | Path) -> Dict[str, Any]:
    """
    读取 ``<project_path>/sprintcycle.toml``。
    文件不存在时返回空 dict。
    """
    root = Path(project_path).resolve()
    path = root / "sprintcycle.toml"
    if not path.is_file():
        return {}
    try:
        import tomllib

        with path.open("rb") as f:
            data = tomllib.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning("无法解析 sprintcycle.toml: %s", e)
        return {}


def flatten_sprintcycle_toml(nested: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 sprintcycle.toml 的嵌套表转为 RuntimeConfig 字段名。
    仅输出调用方与 RuntimeConfig 交集内会消费的键。
    """
    out: Dict[str, Any] = {}

    project = _as_dict(nested.get("project"))
    if "path" in project:
        out["project_path"] = str(project["path"])
    for key in ("parallel_tasks", "max_sprints", "max_tasks_per_sprint", "continue_on_error"):
        if key in project:
            out[key] = project[key]

    quality = _as_dict(nested.get("quality"))
    if "level" in quality:
        out["quality_level"] = str(quality["level"]).strip()
    if "min_coverage_percent" in quality:
        out["min_coverage_percent"] = float(quality["min_coverage_percent"])

    execution = _as_dict(nested.get("execution"))
    if "max_verify_fix_rounds" in execution:
        out["max_verify_fix_rounds"] = int(execution["max_verify_fix_rounds"])

    engine = _as_dict(nested.get("engine"))
    if "name" in engine:
        out["coding_engine"] = str(engine["name"]).strip().lower()

    llm = _as_dict(nested.get("llm"))
    if "provider" in llm:
        out["llm_provider"] = str(llm["provider"])
    if "model" in llm:
        out["llm_model"] = str(llm["model"])
    if "temperature" in llm:
        out["llm_temperature"] = float(llm["temperature"])
    if "max_tokens" in llm:
        out["llm_max_tokens"] = int(llm["max_tokens"])

    storage = _as_dict(nested.get("storage"))
    if "state_dir" in storage:
        out["state_dir"] = str(storage["state_dir"])
    if "backend" in storage:
        out["storage_backend"] = str(storage["backend"]).strip().lower()
    if "sqlite_path" in storage:
        out["sqlite_path"] = str(storage["sqlite_path"])

    return out
