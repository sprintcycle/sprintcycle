"""
RuntimeConfig - 运行时核心配置

Dynaconf 负责多源合并与环境覆盖；Pydantic ``BaseModel`` 负责类型、默认值与校验。
"""

from __future__ import annotations

import os
from os import PathLike
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .dynaconf_app import build_dynaconf
from .quality import normalize_quality_level, normalize_quality_profile, resolve_effective_quality_level


class DashboardPortDefaults:
    """Dashboard 与 Vite 开发代理共用的默认端口（非 sprintcycle.toml 字段；与 frontend/vite 环境变量约定一致）。"""

    default_port: ClassVar[int] = 8080
    dev_port: ClassVar[int] = 5173


# ============================================================
# Default config values（供 to_dict_non_default）
# ============================================================

_DEFAULT_CONFIG: Dict[str, Any] = {
    "max_sprints": 10,
    "max_tasks_per_sprint": 5,
    "parallel_tasks": 3,
    "continue_on_error": False,
    "max_variations": 5,
    "evolution_iterations": 3,
    "evolution_enabled": True,
    "state_dir": ".sprintcycle/state",
    "log_level": "INFO",
    "log_dir": "./logs",
    "api_base": None,
    "api_key": None,
    "api_timeout": 60,
    "llm_provider": "deepseek",
    "llm_model": "deepseek-reasoner",
    "llm_temperature": 0.7,
    "llm_max_tokens": 2048,
    "convergence_threshold": 2,
    "min_improvement": 0.01,
    "quality_gate_enabled": True,
    "min_correctness": 0.5,
    "min_overall": 0.4,
    "auto_commit": True,
    "evolution_cache_dir": "./evolution_cache",
    "test_command": "python -m pytest tests/ -v --tb=short",
    "coverage_command": "python -m pytest --cov --cov-report=json",
    "complexity_threshold": 10,
    "diagnostic_timeout": 300,
    "dry_run": False,
    "verbose": False,
    "quiet": False,
    "quality_level": "L2",
    "quality_profile": "default",
    "max_verify_fix_rounds": 3,
    "coding_engine": "aider",
    "min_coverage_percent": 80.0,
    "project_path": ".",
    "storage_backend": "sqlite",
    "execution_event_backend": "sqlite",
    "knowledge_injection_enabled": True,
    "require_knowledge_injection_confirm": False,
    "persist_sprint_knowledge_cards": True,
    "product_code_root": ".",
    "products_subdir": "products",
    "governance_enabled": False,
    "governance_config_path": None,
    "governance_block_on": "none",
    "governance_spec_glob": None,
    "governance_review_static": True,
    "governance_review_import_linter": True,
    "governance_check_adr": False,
    "governance_adr_glob": None,
    "governance_check_compose": False,
    "governance_report_dir": ".sprintcycle",
    "governance_task_hooks_enabled": False,
    "governance_task_after_block_on_failure": False,
    "governance_downgrade_errors_to_warnings": True,
    "governance_pack_paths": [],
    "governance_spec_marker": None,
    "governance_acceptance_glob": None,
    "governance_planning_validate_release_plan": True,
    "governance_compose_supply_chain": False,
    "test_command_incremental": None,
    "governance_ci_matrix_tags": None,
    "governance_review_browser_e2e": False,
    "governance_review_visual": False,
    "governance_cli_emit_events": False,
    "governance_history_max_files": 50,
    "governance_argv_entry_points": True,
    "governance_pluggy_argv": False,
    "cache_enabled": True,
    "cache_backend": "diskcache",
    "cache_dir": ".sprintcycle/cache",
    "cache_redis_url": None,
    "cache_max_entries": 1000,
    "cache_default_ttl_hours": 24,
    "cache_llm_codegen": True,
    "hitl_enabled": False,
    "hitl_db_path": None,
    "hitl_default_timeout_seconds": 300,
    "hitl_timeout_behavior": "approve",
    "hitl_gates": "before_sprint",
    "hitl_after_task_on_failure": True,
    "hitl_after_sprint_always": False,
}

_TOML_SECTION_KEYS = frozenset(
    {
        "project",
        "quality",
        "execution",
        "engine",
        "llm",
        "storage",
        "cache",
        "behavior",
        "product_layout",
        "governance",
        "hitl",
    }
)

_DYNACONF_META_KEYS = frozenset({"load_dotenv"})


def _resolve_env_var(value: str) -> str:
    if value and isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        return os.getenv(var_name, value)
    return value


def _mask_sensitive(value: str) -> str:
    if not value:
        return value
    if len(value) <= 6:
        return "***"
    return "***"


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def flatten_sprintcycle_toml(nested: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 ``sprintcycle.toml`` 嵌套表转为 ``RuntimeConfig`` 扁平字段名。
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
    if "incremental_test_command" in execution:
        s = str(execution["incremental_test_command"]).strip()
        out["test_command_incremental"] = s or None

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
        out["require_knowledge_injection_confirm"] = bool(behavior["require_knowledge_injection_confirm"])
    if "persist_sprint_knowledge_cards" in behavior:
        out["persist_sprint_knowledge_cards"] = bool(behavior["persist_sprint_knowledge_cards"])

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
    if "packs" in gov:
        pv = gov["packs"]
        if isinstance(pv, list):
            out["governance_pack_paths"] = [str(x).strip() for x in pv if str(x).strip()]
        elif isinstance(pv, str) and pv.strip():
            out["governance_pack_paths"] = [pv.strip()]
    if "spec_marker" in gov:
        sm = str(gov["spec_marker"]).strip()
        out["governance_spec_marker"] = sm or None
    if "acceptance_glob" in gov:
        ag = str(gov["acceptance_glob"]).strip()
        out["governance_acceptance_glob"] = ag or None
    if "planning_validate_release_plan" in gov:
        out["governance_planning_validate_release_plan"] = bool(gov["planning_validate_release_plan"])
    if "compose_supply_chain" in gov:
        out["governance_compose_supply_chain"] = bool(gov["compose_supply_chain"])
    if "ci_matrix_tags" in gov:
        ct = str(gov["ci_matrix_tags"]).strip()
        out["governance_ci_matrix_tags"] = ct or None
    if "review_browser_e2e" in gov:
        out["governance_review_browser_e2e"] = bool(gov["review_browser_e2e"])
    if "review_visual" in gov:
        out["governance_review_visual"] = bool(gov["review_visual"])
    if "cli_emit_events" in gov:
        out["governance_cli_emit_events"] = bool(gov["cli_emit_events"])
    if "history_max_files" in gov:
        try:
            out["governance_history_max_files"] = int(gov["history_max_files"])
        except (TypeError, ValueError):
            pass
    if "argv_entry_points" in gov:
        out["governance_argv_entry_points"] = bool(gov["argv_entry_points"])
    if "pluggy_argv" in gov:
        out["governance_pluggy_argv"] = bool(gov["pluggy_argv"])

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


class RuntimeConfig(BaseModel):
    """
    运行时核心配置。

    无参构造 ``RuntimeConfig()`` 等价于 ``from_dynaconf(None)``：defaults + dotenv + ``SPRINTCYCLE_*``。
    ``from_project(path)`` 额外合并 ``<path>/sprintcycle.toml``（环境仍优先）。
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=False)

    max_sprints: int = 10
    max_tasks_per_sprint: int = 5
    parallel_tasks: int = 3
    continue_on_error: bool = False
    max_variations: int = 5
    evolution_iterations: int = 3
    evolution_enabled: bool = True
    state_dir: str = ".sprintcycle/state"
    log_level: str = "INFO"
    log_dir: str = "./logs"
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    api_timeout: int = 60
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-reasoner"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    convergence_threshold: int = 2
    min_improvement: float = 0.01
    quality_gate_enabled: bool = True
    min_correctness: float = 0.5
    min_overall: float = 0.4
    auto_commit: bool = True
    evolution_cache_dir: str = "./evolution_cache"
    test_command: str = "python -m pytest tests/ -v --tb=short"
    coverage_command: str = "python -m pytest --cov --cov-report=json"
    complexity_threshold: int = 10
    diagnostic_timeout: int = 300
    dry_run: bool = False
    verbose: bool = False
    quiet: bool = False
    project_path: str = "."
    quality_level: str = "L2"
    quality_profile: str = "default"
    max_verify_fix_rounds: int = 3
    coding_engine: str = "aider"
    min_coverage_percent: float = 80.0
    storage_backend: str = "sqlite"
    sqlite_path: Optional[str] = None
    execution_event_backend: str = "sqlite"
    knowledge_injection_enabled: bool = True
    require_knowledge_injection_confirm: bool = False
    persist_sprint_knowledge_cards: bool = True
    product_code_root: str = "."
    products_subdir: str = "products"
    governance_enabled: bool = False
    governance_config_path: Optional[str] = None
    governance_block_on: str = "none"
    governance_spec_glob: Optional[str] = None
    governance_review_static: bool = True
    governance_review_import_linter: bool = True
    governance_check_adr: bool = False
    governance_adr_glob: Optional[str] = None
    governance_check_compose: bool = False
    governance_report_dir: str = ".sprintcycle"
    governance_task_hooks_enabled: bool = False
    governance_task_after_block_on_failure: bool = False
    governance_downgrade_errors_to_warnings: bool = True
    governance_pack_paths: List[str] = Field(default_factory=list)
    governance_spec_marker: Optional[str] = None
    governance_acceptance_glob: Optional[str] = None
    governance_planning_validate_release_plan: bool = True
    governance_compose_supply_chain: bool = False
    test_command_incremental: Optional[str] = None
    governance_ci_matrix_tags: Optional[str] = None
    governance_review_browser_e2e: bool = False
    governance_review_visual: bool = False
    governance_cli_emit_events: bool = False
    governance_history_max_files: int = 50
    governance_argv_entry_points: bool = True
    governance_pluggy_argv: bool = False
    cache_enabled: bool = True
    cache_backend: str = "diskcache"
    cache_dir: str = ".sprintcycle/cache"
    cache_redis_url: Optional[str] = None
    cache_max_entries: int = 1000
    cache_default_ttl_hours: int = 24
    cache_llm_codegen: bool = True
    hitl_enabled: bool = False
    hitl_db_path: Optional[str] = None
    hitl_default_timeout_seconds: int = 300
    hitl_timeout_behavior: str = "approve"
    hitl_gates: str = "before_sprint"
    hitl_after_task_on_failure: bool = True
    hitl_after_sprint_always: bool = False

    def __init__(self, /, **data: Any) -> None:
        if not data:
            raw = build_dynaconf(None).as_dict()
            data = type(self)._coerce_from_dynaconf_raw(raw)
        super().__init__(**data)

    @staticmethod
    def _normalize_dynaconf_keys(raw: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in raw.items():
            if k in _DYNACONF_META_KEYS:
                continue
            out[str(k).lower()] = v
        return out

    @classmethod
    def _coerce_input_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """YAML/手写 dict：支持嵌套 sprintcycle 表或已扁平键。"""
        if not data:
            return {}
        lc = {str(k).lower(): v for k, v in data.items()}
        nested = {k: v for k, v in lc.items() if k in _TOML_SECTION_KEYS and isinstance(v, dict)}
        flat_only = {k: v for k, v in lc.items() if not (k in _TOML_SECTION_KEYS and isinstance(v, dict))}
        from_nested = flatten_sprintcycle_toml(nested) if nested else {}
        merged: Dict[str, Any] = {**from_nested, **flat_only}
        for sk in _TOML_SECTION_KEYS:
            merged.pop(sk, None)
        if merged.get("api_key") and isinstance(merged["api_key"], str):
            merged["api_key"] = _resolve_env_var(merged["api_key"])
        return merged

    @classmethod
    def _coerce_from_dynaconf_raw(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        return cls._coerce_input_dict(cls._normalize_dynaconf_keys(raw))

    @field_validator("quality_level")
    @classmethod
    def _normalize_quality_level(cls, v: str) -> str:
        return normalize_quality_level(v or "L2")

    @field_validator("quality_profile")
    @classmethod
    def _normalize_quality_profile(cls, v: str) -> str:
        return normalize_quality_profile(v or "default")

    @field_validator("governance_block_on")
    @classmethod
    def _normalize_governance_block_on(cls, v: str) -> str:
        allowed = frozenset({"none", "review_only", "planning_and_review"})
        s = (v or "none").strip().lower()
        return s if s in allowed else "none"

    @field_validator("governance_history_max_files")
    @classmethod
    def _clamp_governance_history_max_files(cls, v: int) -> int:
        if v < 0:
            return 0
        return min(int(v), 10_000)

    @field_validator("governance_pack_paths", mode="before")
    @classmethod
    def _coerce_governance_pack_paths(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip()]
        return []

    @field_validator("cache_backend")
    @classmethod
    def _normalize_cache_backend(cls, v: str) -> str:
        allowed = frozenset({"diskcache", "redis"})
        s = (v or "diskcache").strip().lower()
        return s if s in allowed else "diskcache"

    @field_validator("execution_event_backend")
    @classmethod
    def _normalize_execution_event_backend(cls, v: str) -> str:
        allowed = frozenset({"sqlite", "memory"})
        s = (v or "sqlite").strip().lower()
        return s if s in allowed else "sqlite"

    @field_validator("hitl_timeout_behavior")
    @classmethod
    def _normalize_hitl_timeout_behavior(cls, v: str) -> str:
        allowed = frozenset({"approve", "abort_execution", "skip_sprint"})
        s = (v or "approve").strip().lower()
        return s if s in allowed else "approve"

    @field_validator("hitl_default_timeout_seconds")
    @classmethod
    def _normalize_hitl_timeout_seconds(cls, v: int) -> int:
        n = int(v)
        return max(1, min(n, 86400))

    def effective_quality_level(self) -> str:
        return resolve_effective_quality_level(self.quality_profile, self.quality_level)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_dict_non_default(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in self.to_dict().items():
            default = _DEFAULT_CONFIG.get(key)
            if value is not None and value != default:
                result[key] = value
            elif key in ("continue_on_error", "dry_run", "verbose", "quiet"):
                if value is False and default is True:
                    result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeConfig":
        env_flat = cls._coerce_from_dynaconf_raw(build_dynaconf(None).as_dict())
        user_flat = cls._coerce_input_dict(data)
        merged = {**env_flat, **{k: v for k, v in user_flat.items() if v is not None}}
        return cls.model_validate(merged)

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls.from_dynaconf(None)

    @classmethod
    def from_dynaconf(
        cls,
        project_path: str | None = None,
        *,
        extra_files: Optional[Sequence[Union[str, PathLike[str]]]] = None,
    ) -> "RuntimeConfig":
        extras: list[Union[str, PathLike[str]]] | None = list(extra_files) if extra_files else None
        raw = build_dynaconf(project_path, extra_files=extras).as_dict()
        return cls.model_validate(cls._coerce_from_dynaconf_raw(raw))

    @classmethod
    def from_project(cls, project_path: str = ".") -> "RuntimeConfig":
        return cls.from_dynaconf(project_path)

    @classmethod
    def merge(cls, *configs: Union["RuntimeConfig", Dict[str, Any], None]) -> "RuntimeConfig":
        merged: Dict[str, Any] = {}
        for config in configs:
            if config is None:
                continue
            if isinstance(config, cls):
                config_dict = config.to_dict_non_default()
            elif isinstance(config, dict):
                config_dict = cls._coerce_input_dict(config)
            else:
                continue
            merged.update({k: v for k, v in config_dict.items() if v is not None})
        if not merged:
            return cls()
        env_flat = cls._coerce_from_dynaconf_raw(build_dynaconf(None).as_dict())
        return cls.model_validate({**env_flat, **merged})

    def update(self, **kwargs: Any) -> "RuntimeConfig":
        return self.merge(self, kwargs)
