"""治理 Runner 与报告模型（不依赖完整 Sprint）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from sprintcycle.config.runtime_config import RuntimeConfig
from sprintcycle.execution.events import EventBus, EventType
from sprintcycle.execution.hooks.governance_context import (
    CTX_GOVERNANCE_TASK_AFTER_DETAIL,
    CTX_GOVERNANCE_TASK_AFTER_FAILED,
)
from sprintcycle.execution.sprint_types import ExecutionStatus, TaskResult
from sprintcycle.governance.adr_check import check_adr_readme_index, check_adr_readme_strict_glob
from sprintcycle.governance.compose_hint import check_compose_hints
from sprintcycle.governance.model_compare import run_model_compare
from sprintcycle.governance.report import GovernanceReport, GovernanceViolation
from sprintcycle.governance.runner import run_planning_gate_sync, run_review_gate_sync
from sprintcycle.governance.task_hooks import GovernanceTaskLifecycleHooks
from sprintcycle.governance.yaml_checks import run_argv_item
from sprintcycle.release_plan.models import SprintBacklogItem


def test_governance_report_to_dict_and_should_block_ci():
    r = GovernanceReport(
        gate="review",
        violations=[
            GovernanceViolation("x", "error", "bad", {}),
        ],
    )
    d = r.to_dict()
    assert d["gate"] == "review"
    assert len(d["violations"]) == 1
    assert r.should_block_ci("none") is False
    assert r.should_block_ci("review_only") is True
    assert r.should_block_ci("planning_and_review") is True


def test_planning_spec_glob_no_match_warning(tmp_path: Path) -> None:
    cfg = RuntimeConfig(
        governance_spec_glob="nonexistent_glob_xyz/*.md",
        governance_review_import_linter=False,
    )
    rep = run_planning_gate_sync(str(tmp_path), cfg)
    assert any(v.rule_id == "planning:spec_glob" for v in rep.violations)


def test_review_skips_static_when_quality_l0(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("ok", encoding="utf-8")
    cfg = RuntimeConfig(
        quality_level="L0",
        quality_profile="default",
        governance_review_static=True,
        governance_review_import_linter=False,
    )
    rep = run_review_gate_sync(str(tmp_path), cfg)
    assert "static_skipped" in rep.metadata.get("steps", [])


def test_review_yaml_argv(tmp_path: Path) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
version: 1
review:
  - id: ok-echo
    argv: ["python", "-c", "import sys; sys.exit(0)"]
    expect_code: 0
    severity: warning
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(
        governance_config_path="gov.yaml",
        governance_review_static=False,
        governance_review_import_linter=False,
    )
    rep = run_review_gate_sync(str(tmp_path), cfg)
    assert "yaml_review_checks" in rep.metadata.get("steps", [])
    assert not any("ok-echo" in v.rule_id for v in rep.violations)


def test_governance_block_on_validator_invalid_becomes_none():
    cfg = RuntimeConfig(governance_block_on="invalid_mode_xyz")
    assert cfg.governance_block_on == "none"


def test_adr_readme_detects_unindexed(tmp_path: Path) -> None:
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "README.md").write_text("See [first](0001-first.md)\n", encoding="utf-8")
    (adr / "0001-first.md").write_text("# a", encoding="utf-8")
    (adr / "0002-second.md").write_text("# b", encoding="utf-8")
    viol = check_adr_readme_index(tmp_path)
    assert any(v.rule_id == "adr:unindexed" and "0002-second.md" in v.message for v in viol)


def test_adr_strict_glob_matches_readme(tmp_path: Path) -> None:
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "README.md").write_text(
        "- [a](0001-a.md)\n- [b](0002-b.md)\n",
        encoding="utf-8",
    )
    (adr / "0001-a.md").write_text("# a", encoding="utf-8")
    (adr / "0002-b.md").write_text("# b", encoding="utf-8")
    viol = check_adr_readme_strict_glob(tmp_path, "docs/adr/*.md")
    assert viol == []


def test_adr_strict_glob_not_indexed_error(tmp_path: Path) -> None:
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "README.md").write_text("- [a](0001-a.md)\n", encoding="utf-8")
    (adr / "0001-a.md").write_text("# a", encoding="utf-8")
    (adr / "0002-b.md").write_text("# b", encoding="utf-8")
    viol = check_adr_readme_strict_glob(tmp_path, "docs/adr/*.md")
    assert any(v.rule_id == "adr:glob_not_indexed" and "0002-b.md" in v.message for v in viol)


def test_adr_strict_glob_readme_extra_error(tmp_path: Path) -> None:
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "README.md").write_text(
        "- [a](0001-a.md)\n- [phantom](9999-missing.md)\n",
        encoding="utf-8",
    )
    (adr / "0001-a.md").write_text("# a", encoding="utf-8")
    viol = check_adr_readme_strict_glob(tmp_path, "docs/adr/*.md")
    assert any(v.rule_id == "adr:readme_not_in_glob" for v in viol)


def test_adr_strict_glob_requires_readme(tmp_path: Path) -> None:
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "0001-a.md").write_text("# a", encoding="utf-8")
    viol = check_adr_readme_strict_glob(tmp_path, "docs/adr/*.md")
    assert any(v.rule_id == "adr:readme_required" for v in viol)


def test_review_gate_uses_strict_glob_when_configured(tmp_path: Path) -> None:
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "README.md").write_text("- [a](0001-a.md)\n", encoding="utf-8")
    (adr / "0001-a.md").write_text("# a", encoding="utf-8")
    (adr / "0002-b.md").write_text("# b", encoding="utf-8")
    cfg = RuntimeConfig(
        governance_check_adr=True,
        governance_adr_glob="docs/adr/*.md",
        governance_review_static=False,
        governance_review_import_linter=False,
    )
    rep = run_review_gate_sync(str(tmp_path), cfg)
    assert "adr_scan_strict_glob" in rep.metadata.get("steps", [])
    assert any(v.rule_id == "adr:glob_not_indexed" for v in rep.violations)


def test_model_compare_identical_runs(tmp_path: Path) -> None:
    (tmp_path / "test_mc_local.py").write_text("def test_ok():\n    assert 1\n", encoding="utf-8")
    rep = run_model_compare(tmp_path, [str(tmp_path / "test_mc_local.py"), "-q"], (), ())
    assert rep["failure_sets_equal"] is True
    assert rep["exit_code_run1"] == rep["exit_code_run2"]


@pytest.mark.asyncio
async def test_governance_task_lifecycle_hook_runs(tmp_path: Path) -> None:
    cfg = RuntimeConfig()
    hook = GovernanceTaskLifecycleHooks(cfg, str(tmp_path))
    task = SprintBacklogItem(description="hello", agent="coder")
    tr = TaskResult(work_item=task, sprint_name="S1", status=ExecutionStatus.SUCCESS, output="x")
    await hook.on_after_task_complete(task, "S1", {}, tr)


def test_run_argv_item_extra_env(tmp_path: Path) -> None:
    item = {
        "id": "env-print",
        "argv": [
            "python",
            "-c",
            "import os, sys; sys.exit(0 if os.environ.get('MY_HOOK_VAR')=='ok' else 1)",
        ],
        "expect_code": 0,
    }
    viol = run_argv_item(item, tmp_path, "x", extra_env={"MY_HOOK_VAR": "ok"})
    assert viol == []


@pytest.mark.asyncio
async def test_task_after_yaml_runs_with_task_env(tmp_path: Path, caplog) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
version: 1
task_after:
  - id: check-agent
    argv:
      - python
      - -c
      - |
        import os, sys
        assert os.environ.get("SPRINTCYCLE_TASK_AGENT") == "coder"
        assert "hi" in os.environ.get("SPRINTCYCLE_TASK_DESCRIPTION", "")
        sys.exit(0)
    expect_code: 0
    run_when: success
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(governance_config_path="gov.yaml")
    hook = GovernanceTaskLifecycleHooks(cfg, str(tmp_path))
    task = SprintBacklogItem(description="hi", agent="coder")
    tr = TaskResult(work_item=task, sprint_name="S1", status=ExecutionStatus.SUCCESS, output="x")
    with caplog.at_level("ERROR"):
        await hook.on_after_task_complete(task, "S1", {}, tr)
    assert "task_after[check-agent]" not in caplog.text


@pytest.mark.asyncio
async def test_task_after_emits_governance_event(tmp_path: Path) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
task_after:
  - id: ok-check
    argv: ["python", "-c", "import sys; sys.exit(0)"]
    expect_code: 0
    run_when: success
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(governance_config_path="gov.yaml")
    bus = EventBus()
    seen: list = []

    async def h(ev):
        seen.append(ev)

    bus.on(EventType.GOVERNANCE_TASK_CHECK, h)
    hook = GovernanceTaskLifecycleHooks(cfg, str(tmp_path), event_bus=bus)
    task = SprintBacklogItem(description="x", agent="coder")
    tr = TaskResult(work_item=task, sprint_name="S1", status=ExecutionStatus.SUCCESS, output="x")
    await hook.on_after_task_complete(task, "S1", {}, tr)
    assert len(seen) == 1
    assert seen[0].type == EventType.GOVERNANCE_TASK_CHECK
    assert seen[0].data.get("status") == "passed"
    assert seen[0].data.get("check_id") == "ok-check"


@pytest.mark.asyncio
async def test_task_after_skipped_on_failure_when_run_when_success(tmp_path: Path, caplog) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
task_after:
  - id: boom
    argv: ["python", "-c", "raise SystemExit(99)"]
    expect_code: 0
    run_when: success
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(governance_config_path="gov.yaml")
    hook = GovernanceTaskLifecycleHooks(cfg, str(tmp_path))
    task = SprintBacklogItem(description="x", agent="coder")
    tr = TaskResult(
        work_item=task,
        sprint_name="S1",
        status=ExecutionStatus.FAILED,
        error="nope",
    )
    with caplog.at_level("ERROR"):
        await hook.on_after_task_complete(task, "S1", {}, tr)
    assert "task_after[boom]" not in caplog.text


def test_compose_hints_clean_when_restart_and_healthcheck(tmp_path: Path) -> None:
    p = tmp_path / "compose.yaml"
    p.write_text(
        """
services:
  web:
    image: nginx:alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
""",
        encoding="utf-8",
    )
    text = p.read_text(encoding="utf-8")
    viol = check_compose_hints(p, text)
    assert not any(v.rule_id == "compose:restart_policy" for v in viol)
    assert not any(v.rule_id == "compose:service_healthcheck" for v in viol)


def test_compose_hints_per_service(tmp_path: Path) -> None:
    p = tmp_path / "docker-compose.yml"
    p.write_text(
        """
services:
  web:
    image: nginx:alpine
  api:
    image: python:3.12-slim
""",
        encoding="utf-8",
    )
    text = p.read_text(encoding="utf-8")
    viol = check_compose_hints(p, text)
    ids = {v.rule_id for v in viol}
    assert "compose:restart_policy" in ids
    assert "compose:service_healthcheck" in ids
    assert "compose:healthcheck" in ids


@pytest.mark.asyncio
async def test_task_after_block_on_failure_sets_context(tmp_path: Path) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
task_after:
  - id: must-pass
    argv: ["python", "-c", "raise SystemExit(1)"]
    expect_code: 0
    block_on_failure: true
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(governance_config_path="gov.yaml")
    hook = GovernanceTaskLifecycleHooks(cfg, str(tmp_path))
    task = SprintBacklogItem(description="x", agent="coder")
    tr = TaskResult(work_item=task, sprint_name="S1", status=ExecutionStatus.SUCCESS, output="ok")
    ctx: dict = {}
    await hook.on_after_task_complete(task, "S1", ctx, tr)
    assert ctx.get(CTX_GOVERNANCE_TASK_AFTER_FAILED) is True
    assert ctx.get(CTX_GOVERNANCE_TASK_AFTER_DETAIL)
