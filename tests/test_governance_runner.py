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
from sprintcycle.governance.compose_hint import check_compose_hints, check_compose_supply_chain_hints
from sprintcycle.governance.model_compare import run_model_compare
from sprintcycle.governance.report import GovernanceReport, GovernanceViolation
from sprintcycle.governance.history import list_history_entries
from sprintcycle.governance.runner import (
    emit_governance_gate_cli_sync,
    persist_planning_report,
    persist_report,
    run_planning_gate_sync,
    run_review_gate_sync,
)
from sprintcycle.governance.task_hooks import GovernanceTaskLifecycleHooks
from sprintcycle.governance.yaml_checks import filter_argv_items_by_governance_sources, run_argv_checks, run_argv_item
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


def test_planning_argv_failure_downgraded_when_flag_on(tmp_path: Path) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
version: 1
planning:
  - id: bad-cmd
    argv: ["python", "-c", "import sys; sys.exit(1)"]
    expect_code: 0
    severity: error
""",
        encoding="utf-8",
    )
    base = dict(
        governance_config_path="gov.yaml",
        governance_review_static=False,
        governance_review_import_linter=False,
    )
    rep_on = run_planning_gate_sync(str(tmp_path), RuntimeConfig(governance_downgrade_errors_to_warnings=True, **base))
    v_on = [v for v in rep_on.violations if "bad-cmd" in v.rule_id]
    assert v_on
    assert v_on[0].severity == "warning"
    assert not rep_on.has_error_severity()

    rep_off = run_planning_gate_sync(str(tmp_path), RuntimeConfig(governance_downgrade_errors_to_warnings=False, **base))
    v_off = [v for v in rep_off.violations if "bad-cmd" in v.rule_id]
    assert v_off[0].severity == "error"
    assert rep_off.has_error_severity()


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


def test_run_argv_checks_skips_disabled(tmp_path: Path) -> None:
    items = [
        {
            "id": "off",
            "enabled": False,
            "argv": ["python", "-c", "import sys; sys.exit(1)"],
            "expect_code": 0,
        },
        {"id": "on", "argv": ["python", "-c", "import sys; sys.exit(0)"], "expect_code": 0},
    ]
    viol = run_argv_checks(items, tmp_path, "review")
    assert viol == []


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
async def test_task_after_skips_disabled_item(tmp_path: Path, caplog) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
task_after:
  - id: would-fail-if-ran
    enabled: false
    argv: ["python", "-c", "import sys; sys.exit(1)"]
    expect_code: 0
    run_when: success
  - id: ok-check
    argv: ["python", "-c", "import sys; sys.exit(0)"]
    expect_code: 0
    run_when: success
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(governance_config_path="gov.yaml")
    hook = GovernanceTaskLifecycleHooks(cfg, str(tmp_path))
    task = SprintBacklogItem(description="x", agent="coder")
    tr = TaskResult(work_item=task, sprint_name="S1", status=ExecutionStatus.SUCCESS, output="x")
    with caplog.at_level("ERROR"):
        await hook.on_after_task_complete(task, "S1", {}, tr)
    assert "would-fail-if-ran" not in caplog.text


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


def test_merged_governance_packs_sequence(tmp_path: Path) -> None:
    (tmp_path / "base.yaml").write_text(
        """
version: 1
planning:
  - id: first
    argv: ["python", "-c", "import sys; sys.exit(0)"]
    expect_code: 0
    severity: warning
""",
        encoding="utf-8",
    )
    (tmp_path / "pack.yaml").write_text(
        """
version: 1
planning:
  - id: second
    argv: ["python", "-c", "import sys; sys.exit(0)"]
    expect_code: 0
    severity: warning
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(
        governance_config_path="base.yaml",
        governance_pack_paths=["pack.yaml"],
        governance_review_static=False,
        governance_review_import_linter=False,
    )
    from sprintcycle.governance.yaml_merge import load_merged_governance_data

    merged = load_merged_governance_data(tmp_path, cfg)
    ids = [x.get("id") for x in merged.get("planning", [])]
    assert ids == ["first", "second"]


def test_compose_supply_chain_latest_image_warning(tmp_path: Path) -> None:
    cfile = tmp_path / "docker-compose.yml"
    viol = check_compose_supply_chain_hints(
        cfile,
        {"web": {"image": "nginx:latest"}, "ok": {"image": "nginx:1.25"}},
    )
    assert any(v.rule_id == "compose:image_latest" and "web" in v.message for v in viol)


def test_planning_gate_spec_ref_missing_with_release_plan(tmp_path: Path) -> None:
    from sprintcycle.release_plan.models import (
        ExecutionMode,
        ProductAnchor,
        ReleasePlan,
        SprintBacklogItem,
        SprintDefinition,
    )

    plan = ReleasePlan(
        project=ProductAnchor(name="x", path=str(tmp_path)),
        mode=ExecutionMode.NORMAL,
        sprints=[
            SprintDefinition(
                name="S",
                tasks=[SprintBacklogItem(description="t", agent="coder", spec_ref="missing-spec.md")],
            )
        ],
    )
    cfg = RuntimeConfig(
        governance_review_static=False,
        governance_review_import_linter=False,
    )
    rep = run_planning_gate_sync(str(tmp_path), cfg, extra_context={"release_plan": plan})
    assert any(v.rule_id == "planning:spec_ref_missing" for v in rep.violations)


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


def test_filter_argv_items_respects_browser_visual_toggles() -> None:
    items = [
        {"id": "b", "tags": ["browser"], "argv": ["python", "-c", "import sys; sys.exit(1)"], "expect_code": 0},
        {"id": "v", "tags": ["visual"], "argv": ["python", "-c", "import sys; sys.exit(1)"], "expect_code": 0},
        {"id": "plain", "argv": ["python", "-c", "import sys; sys.exit(0)"], "expect_code": 0},
    ]
    cfg = RuntimeConfig(governance_review_browser_e2e=False, governance_review_visual=False)
    out = filter_argv_items_by_governance_sources(items, cfg)
    assert [x["id"] for x in out] == ["plain"]

    cfg2 = RuntimeConfig(governance_review_browser_e2e=True, governance_review_visual=False)
    out2 = filter_argv_items_by_governance_sources(items, cfg2)
    assert {x["id"] for x in out2} == {"b", "plain"}


def test_review_skips_browser_tag_when_toml_off(tmp_path: Path) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
review:
  - id: pw-would-fail
    tags: [browser]
    argv: ["python", "-c", "import sys; sys.exit(1)"]
    expect_code: 0
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(
        governance_config_path="gov.yaml",
        governance_review_static=False,
        governance_review_import_linter=False,
        governance_review_browser_e2e=False,
    )
    rep = run_review_gate_sync(str(tmp_path), cfg)
    assert not any(v.rule_id == "review:pw-would-fail" for v in rep.violations)


def test_review_runs_browser_tag_when_toml_on(tmp_path: Path) -> None:
    gov = tmp_path / "gov.yaml"
    gov.write_text(
        """
review:
  - id: pw-fail
    tags: [browser]
    argv: ["python", "-c", "import sys; sys.exit(1)"]
    expect_code: 0
""",
        encoding="utf-8",
    )
    cfg = RuntimeConfig(
        governance_config_path="gov.yaml",
        governance_review_static=False,
        governance_review_import_linter=False,
        governance_review_browser_e2e=True,
    )
    rep = run_review_gate_sync(str(tmp_path), cfg)
    assert any(v.rule_id == "review:pw-fail" for v in rep.violations)


def test_persist_planning_report_writes_file(tmp_path: Path) -> None:
    rep = GovernanceReport(gate="planning", violations=[], metadata={"k": 1})
    cfg = RuntimeConfig(governance_report_dir=".sprintcycle")
    path = persist_planning_report(rep, str(tmp_path), cfg)
    assert path is not None and path.is_file()
    assert path.name == "governance_planning_last.json"


def test_persist_report_and_planning_append_history(tmp_path: Path) -> None:
    cfg = RuntimeConfig(
        governance_report_dir=".sprintcycle",
        governance_history_max_files=10,
        governance_review_import_linter=False,
    )
    (tmp_path / "README.md").write_text("ok", encoding="utf-8")
    r_rev = GovernanceReport(gate="review", violations=[], metadata={})
    r_pl = GovernanceReport(gate="planning", violations=[], metadata={})
    persist_report(r_rev, str(tmp_path), cfg)
    persist_planning_report(r_pl, str(tmp_path), cfg)
    ent = list_history_entries(str(tmp_path), cfg, limit=10)
    assert len(ent) >= 2
    gates = {e["gate"] for e in ent}
    assert "review" in gates and "planning" in gates


def test_emit_governance_gate_cli_sync_emits_when_enabled(tmp_path: Path) -> None:
    from sprintcycle.execution.events import EventType, reset_event_bus

    bus = reset_event_bus()
    seen: list = []

    async def cap(ev):
        seen.append(ev)

    bus.on(EventType.GOVERNANCE_GATE, cap)
    rep = GovernanceReport(
        gate="review",
        violations=[GovernanceViolation("compose:x", "warning", "m", {})],
        metadata={},
    )
    cfg = RuntimeConfig(governance_cli_emit_events=False)
    emit_governance_gate_cli_sync(str(tmp_path), cfg, "review", rep)
    assert seen == []

    cfg2 = RuntimeConfig(governance_cli_emit_events=True)
    emit_governance_gate_cli_sync(str(tmp_path), cfg2, "review", rep)
    assert len(seen) == 1
    assert seen[0].data["sprint_name"] == "__cli__"
    assert seen[0].data["gate"] == "review"


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
