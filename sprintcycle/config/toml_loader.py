"""
加载项目根目录的 sprintcycle.toml，并映射为 RuntimeConfig 可 merge 的扁平字典。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from loguru import logger


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
        logger.warning("无法解析 sprintcycle.toml: {}", e)
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
    if "profile" in quality:
        out["quality_profile"] = str(quality["profile"]).strip().lower()
    if "min_coverage_percent" in quality:
        out["min_coverage_percent"] = float(quality["min_coverage_percent"])

    execution = _as_dict(nested.get("execution"))
    if "max_verify_fix_rounds" in execution:
        out["max_verify_fix_rounds"] = int(execution["max_verify_fix_rounds"])
    if "event_backend" in execution:
        out["execution_event_backend"] = str(execution["event_backend"]).strip().lower()

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

    cache = _as_dict(nested.get("cache"))
    if "enabled" in cache:
        out["cache_enabled"] = bool(cache["enabled"])
    if "backend" in cache:
        out["cache_backend"] = str(cache["backend"]).strip().lower()
    if "dir" in cache:
        out["cache_dir"] = str(cache["dir"]).strip()
    if "redis_url" in cache:
        v = cache["redis_url"]
        out["cache_redis_url"] = str(v).strip() if v is not None else None
    elif "url" in cache:
        v = cache["url"]
        out["cache_redis_url"] = str(v).strip() if v is not None else None
    if "max_entries" in cache:
        out["cache_max_entries"] = int(cache["max_entries"])
    if "default_ttl_hours" in cache:
        out["cache_default_ttl_hours"] = int(cache["default_ttl_hours"])
    if "llm_codegen" in cache:
        out["cache_llm_codegen"] = bool(cache["llm_codegen"])

    behavior = _as_dict(nested.get("behavior"))
    if "require_knowledge_injection_confirm" in behavior:
        out["require_knowledge_injection_confirm"] = bool(
            behavior["require_knowledge_injection_confirm"]
        )
    if "persist_sprint_knowledge_cards" in behavior:
        out["persist_sprint_knowledge_cards"] = bool(
            behavior["persist_sprint_knowledge_cards"]
        )

    product_layout = _as_dict(nested.get("product_layout"))
    if "code_root" in product_layout:
        out["product_code_root"] = str(product_layout["code_root"]).strip()
    if "subdir" in product_layout:
        out["products_subdir"] = str(product_layout["subdir"]).strip()

    gov = _as_dict(nested.get("governance"))
    if "enabled" in gov:
        out["governance_enabled"] = bool(gov["enabled"])
    if "config_path" in gov:
        out["governance_config_path"] = str(gov["config_path"]).strip()
    if "block_on" in gov:
        out["governance_block_on"] = str(gov["block_on"]).strip().lower()
    if "spec_glob" in gov:
        out["governance_spec_glob"] = str(gov["spec_glob"]).strip()
    if "run_static" in gov:
        out["governance_review_static"] = bool(gov["run_static"])
    if "run_import_linter" in gov:
        out["governance_review_import_linter"] = bool(gov["run_import_linter"])
    if "check_adr" in gov:
        out["governance_check_adr"] = bool(gov["check_adr"])
    if "adr_glob" in gov:
        out["governance_adr_glob"] = str(gov["adr_glob"]).strip()
    if "check_compose" in gov:
        out["governance_check_compose"] = bool(gov["check_compose"])
    if "report_dir" in gov:
        out["governance_report_dir"] = str(gov["report_dir"]).strip()
    if "task_hooks" in gov:
        out["governance_task_hooks_enabled"] = bool(gov["task_hooks"])
    if "task_after_block_on_failure" in gov:
        out["governance_task_after_block_on_failure"] = bool(gov["task_after_block_on_failure"])
    if "downgrade_errors_to_warnings" in gov:
        out["governance_downgrade_errors_to_warnings"] = bool(gov["downgrade_errors_to_warnings"])

    hitl = _as_dict(nested.get("hitl"))
    if "enabled" in hitl:
        out["hitl_enabled"] = bool(hitl["enabled"])
    if "db_path" in hitl:
        v = hitl["db_path"]
        out["hitl_db_path"] = str(v).strip() if v is not None else None
    if "default_timeout_seconds" in hitl:
        out["hitl_default_timeout_seconds"] = int(hitl["default_timeout_seconds"])
    if "timeout_behavior" in hitl:
        out["hitl_timeout_behavior"] = str(hitl["timeout_behavior"]).strip().lower()
    if "gates" in hitl:
        g = hitl["gates"]
        if isinstance(g, str):
            out["hitl_gates"] = g.strip()
        elif isinstance(g, list):
            out["hitl_gates"] = ",".join(str(x).strip() for x in g if str(x).strip())
    if "after_task_on_failure" in hitl:
        out["hitl_after_task_on_failure"] = bool(hitl["after_task_on_failure"])
    if "after_sprint_always" in hitl:
        out["hitl_after_sprint_always"] = bool(hitl["after_sprint_always"])

    return out
