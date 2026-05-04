"""P0: sprintcycle.toml、RuntimeConfig.from_project、质量档位"""

from pathlib import Path

import pytest

from sprintcycle.config import RuntimeConfig, flatten_sprintcycle_toml, load_sprintcycle_toml
from sprintcycle.evolution.measurement import MeasurementProvider, MeasurementResult


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


def test_load_sprintcycle_toml_missing(tmp_path: Path):
    assert load_sprintcycle_toml(tmp_path) == {}


def test_from_project_merges_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    for key in (
        "SPRINTCYCLE_QUALITY_LEVEL",
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
    from sprintcycle.prd.models import PRDSprint

    ex = SprintExecutor(max_verify_fix_rounds=3)
    sp = PRDSprint(name="s", goals=[], tasks=[])
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
