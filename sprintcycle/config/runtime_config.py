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
    "coding_engine": "cursor",
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
    "hitl_gates": "before_sprint,spec_confirm,execution_approval,release_approval,after_task,after_sprint",
    "hitl_after_task_on_failure": True,
    "hitl_after_sprint_always": False,
    "hitl_default_risk_level": "medium",
}
