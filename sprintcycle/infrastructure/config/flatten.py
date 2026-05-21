"""Utility to flatten nested sprintcycle.toml dicts into flat key-value mapping."""

from __future__ import annotations

from typing import Any, Dict

# Mapping from (section, key) → flat key
_FLATTEN_MAP: Dict[str, str] = {
    # quality
    "quality.level": "quality_level",
    "quality.min_coverage_percent": "min_coverage_percent",
    "quality.profile": "quality_profile",
    # execution
    "execution.max_verify_fix_rounds": "max_verify_fix_rounds",
    "execution.incremental_test_command": "test_command_incremental",
    # engine
    "engine.name": "coding_engine",
    # project
    "project.path": "project_path",
    "project.parallel_tasks": "parallel_tasks",
    # llm
    "llm.provider": "llm_provider",
    "llm.model": "llm_model",
    # governance
    "governance.downgrade_errors_to_warnings": "governance_downgrade_errors_to_warnings",
    "governance.packs": "governance_pack_paths",
    "governance.spec_marker": "governance_spec_marker",
    "governance.ci_matrix_tags": "governance_ci_matrix_tags",
    "governance.review_browser_e2e": "governance_review_browser_e2e",
    "governance.review_visual": "governance_review_visual",
    "governance.cli_emit_events": "governance_cli_emit_events",
    "governance.history_max_files": "governance_history_max_files",
    "governance.argv_entry_points": "governance_argv_entry_points",
    "governance.pluggy_argv": "governance_pluggy_argv",
    # cache
    "cache.enabled": "cache_enabled",
    "cache.backend": "cache_backend",
    "cache.dir": "cache_dir",
    "cache.url": "cache_redis_url",
    "cache.redis_url": "cache_redis_url",
    "cache.max_entries": "cache_max_entries",
    "cache.default_ttl_hours": "cache_default_ttl_hours",
    "cache.llm_codegen": "cache_llm_codegen",
}


def flatten_sprintcycle_toml(nested: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a nested sprintcycle.toml dict into a flat key-value mapping.

    Example:
        {"quality": {"level": "L2"}} → {"quality_level": "L2"}

    When multiple keys map to the same flat key (e.g. cache.url / cache.redis_url
    both map to ``cache_redis_url``), the more specific key wins via sorting.
    """
    flat: Dict[str, Any] = {}
    for section, values in nested.items():
        if not isinstance(values, dict):
            flat[section] = values
            continue
        # Process keys in reverse-sorted order so more-specific keys (e.g. redis_url)
        # overwrite less-specific ones (e.g. url) when they share a flat name.
        for key in sorted(values.keys(), reverse=True):
            val = values[key]
            mapped = _FLATTEN_MAP.get(f"{section}.{key}")
            if mapped is not None:
                flat[mapped] = val
            else:
                flat[f"{section}_{key}"] = val
    return flat
