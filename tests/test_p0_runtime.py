"""P0: sprintcycle.toml、RuntimeConfig.from_project、质量档位"""

from pathlib import Path

import pytest

from sprintcycle.infrastructure.config import (
    RuntimeConfig,
    flatten_sprintcycle_toml,
    resolve_effective_quality_level,
)
from sprintcycle.infrastructure.config.dynaconf_app import build_dynaconf
from sprintcycle.domain.evolution.measurement import MeasurementProvider, MeasurementResult


def test_resolve_effective_quality_level_profiles():
    assert resolve_effective_quality_level("default", "L2") == "L2"
    assert resolve_effective_quality_level("strict", "L0") == "L3"
    assert resolve_effective_quality_level("fast", "L3") == "L1"
    assert resolve_effective_quality_level("off", "L3") == "L0"


def test_flatten_sprintcycle_toml_roundtrip():
    nested = {
        "quality": {"level": "L2", "min_coverage_percent": 85.0},
        "execution": {"max_verify_fix_rounds": 2},
        "engine": {"name": "litellm"},
        "project": {"path": "./repo", "parallel_tasks": 1},
        "llm": {"provider": "openai", "model": "gpt-4o-mini"},
    }
    flat = flatten_sprintcycle_toml(nested)
    assert flat["project_path"] == "./repo"
    assert flat["quality_level"] == "L2"
    assert flat["min_coverage_percent"] == 85.0
    assert flat["max_verify_fix_rounds"] == 2
    assert flat["coding_engine"] == "litellm"
    assert flat["parallel_tasks"] == 1
    assert flat["llm_provider"] == "openai"


def test_flatten_quality_profile():
    nested = {"quality": {"level": "L0", "profile": "strict"}}
    flat = flatten_sprintcycle_toml(nested)
    assert flat["quality_level"] == "L0"
    assert flat["quality_profile"] == "strict"


def test_flatten_governance_downgrade_flag():
    nested = {"governance": {"downgrade_errors_to_warnings": False}}
    flat = flatten_sprintcycle_toml(nested)
    assert flat["governance_downgrade_errors_to_warnings"] is False


def test_flatten_governance_packs_and_execution_incremental():
    nested = {
        "governance": {"packs": ["a.yaml", "b.yaml"], "spec_marker": "SPEC>", "ci_matrix_tags": "x,y"},
        "execution": {"incremental_test_command": "pytest -q --lf"},
    }
    flat = flatten_sprintcycle_toml(nested)
    assert flat["governance_pack_paths"] == ["a.yaml", "b.yaml"]
    assert flat["governance_spec_marker"] == "SPEC>"
    assert flat["governance_ci_matrix_tags"] == "x,y"
    assert flat["test_command_incremental"] == "pytest -q --lf"


def test_flatten_cache_section_and_redis_url_alias():
    nested = {
        "cache": {
            "enabled": False,
            "backend": "redis",
            "dir": ".data/sc-cache",
            "url": "redis://localhost:6380/1",
            "max_entries": 500,
            "default_ttl_hours": 12,
            "llm_codegen": False,
        }
    }
    flat = flatten_sprintcycle_toml(nested)
    assert flat["cache_enabled"] is False
    assert flat["cache_backend"] == "redis"
    assert flat["cache_dir"] == ".data/sc-cache"
    assert flat["cache_redis_url"] == "redis://localhost:6380/1"
    assert flat["cache_max_entries"] == 500
    assert flat["cache_default_ttl_hours"] == 12
    assert flat["cache_llm_codegen"] is False


def test_flatten_governance_v4_browser_visual_cli_emit():
    nested = {
        "governance": {
            "review_browser_e2e": True,
            "review_visual": False,
            "cli_emit_events": True,
        }
    }
    flat = flatten_sprintcycle_toml(nested)
    assert flat["governance_review_browser_e2e"] is True
    assert flat["governance_review_visual"] is False
    assert flat["governance_cli_emit_events"] is True


def test_flatten_governance_history_argv_pluggy():
    nested = {
        "governance": {
            "history_max_files": 120,
            "argv_entry_points": False,
            "pluggy_argv": True,
        }
    }
    flat = flatten_sprintcycle_toml(nested)
    assert flat["governance_history_max_files"] == 120
    assert flat["governance_argv_entry_points"] is False
    assert flat["governance_pluggy_argv"] is True


def test_flatten_cache_redis_url_wins_over_url():
    nested = {
        "cache": {
            "redis_url": "redis://primary/0",
            "url": "redis://fallback/0",
        }
    }
    flat = flatten_sprintcycle_toml(nested)
    assert flat["cache_redis_url"] == "redis://primary/0"


def test_build_dynaconf_no_project_toml(tmp_path: Path) -> None:
    assert not (Path(tmp_path) / "sprintcycle.toml").exists()
    d = build_dynaconf(tmp_path)
    assert "QUALITY" not in d.as_dict()


def test_from_project_merges_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    for key in (
        "SPRINTCYCLE_QUALITY_LEVEL",
        "SPRINTCYCLE_QUALITY_PROFILE",
        "SPRINTCYCLE_MAX_VERIFY_FIX_ROUNDS",
        "SPRINTCYCLE_CODING_ENGINE",
    ):
        monkeypatch.delenv(key, raising=False)
    toml = tmp_path / "sprintcycle.toml"
    toml.write_text(
        """
[quality]
level = "L0"

[execution]
max_verify_fix_rounds = 2

[engine]
name = "llm"
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    cfg = RuntimeConfig.from_project(str(tmp_path))
    assert cfg.quality_level == "L0"
    assert cfg.max_verify_fix_rounds == 2
    assert cfg.coding_engine == "llm"


def test_from_project_quality_profile_overrides_effective_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in ("SPRINTCYCLE_QUALITY_LEVEL", "SPRINTCYCLE_QUALITY_PROFILE"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "sprintcycle.toml").write_text(
        '[quality]\nlevel = "L0"\nprofile = "strict"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    cfg = RuntimeConfig.from_project(str(tmp_path))
    assert cfg.quality_level == "L0"
    assert cfg.quality_profile == "strict"
    assert cfg.effective_quality_level() == "L3"


def test_measurement_strict_profile_runs_pytest_even_if_level_l0():
    rc = RuntimeConfig(quality_level="L0", quality_profile="strict")
    mock_calls: list[str] = []

    def runner(cmd: str, cwd: str, timeout: int):
        mock_calls.append(cmd)
        return 0, "1 passed", ""

    p = MeasurementProvider(repo_path=".", runtime_config=rc, runner=runner)
    p.measure_all()
    assert any("pytest" in c for c in mock_calls)


def test_measurement_l0_skips_pytest():
    rc = RuntimeConfig(quality_level="L0")
    mock_calls = []

    def runner(cmd, cwd, timeout):
        mock_calls.append(cmd)
        return 0, "", ""

    p = MeasurementProvider(runtime_config=rc, runner=runner)
    r = p.measure_all()
    assert r.overall == 1.0
    assert r.details.get("skipped") == "L0"
    assert mock_calls == []


def test_measurement_l1_skips_pytest_but_not_gate_defaults():
    rc = RuntimeConfig(quality_level="L1")
    mock_calls = []

    def runner(cmd, cwd, timeout):
        mock_calls.append(cmd)
        return 0, "", ""

    p = MeasurementProvider(runtime_config=rc, runner=runner)
    p._measure_correctness()
    assert not any("pytest" in str(c) for c in mock_calls)


def test_quality_gate_l2_coverage_fail():
    rc = RuntimeConfig(quality_level="L2", min_coverage_percent=80.0)
    p = MeasurementProvider(runtime_config=rc)
    result = MeasurementResult(
        correctness=0.9,
        performance=0.7,
        stability=0.7,
        code_quality=0.7,
        overall=0.9,
        details={"line_coverage_percent": 50.0},
    )
    assert p.check_quality_gate(result) is False


def test_sprint_executor_retry_budget():
    from sprintcycle.execution.sprint_executor import SprintExecutor
    from sprintcycle.application.release_plan.models import SprintDefinition

    ex = SprintExecutor(max_verify_fix_rounds=3)
    sp = SprintDefinition(name="s", goals=[], tasks=[])
    object.__setattr__(sp, "_retry_count", 2)
    assert ex._should_retry(sp) is True
    object.__setattr__(sp, "_retry_count", 3)
    assert ex._should_retry(sp) is False


def test_quality_gate_l2_coverage_pass():
    rc = RuntimeConfig(quality_level="L2", min_coverage_percent=80.0)
    p = MeasurementProvider(runtime_config=rc)
    result = MeasurementResult(
        correctness=0.9,
        performance=0.7,
        stability=0.7,
        code_quality=0.7,
        overall=0.9,
        details={"line_coverage_percent": 90.0},
    )
    assert p.check_quality_gate(result) is True
