"""GovernanceSprintHooks 在 Planning/Review 后发出 governance_gate 事件（含 compose 命中）。"""

from unittest.mock import MagicMock

import pytest

from sprintcycle.config import RuntimeConfig
from sprintcycle.execution.events import EventType, reset_event_bus
from sprintcycle.governance.report import GovernanceReport, GovernanceViolation
from sprintcycle.governance.sprint_hooks import GovernanceSprintHooks
from sprintcycle.release_plan.models import SprintBacklogItem, SprintDefinition


@pytest.mark.asyncio
async def test_governance_gate_event_includes_compose_hits():
    bus = reset_event_bus()
    seen = []

    async def cap(ev):
        seen.append(ev)

    bus.on(EventType.GOVERNANCE_GATE, cap)

    cfg = MagicMock(spec=RuntimeConfig)
    cfg.governance_enabled = True
    cfg.governance_report_dir = ".sprintcycle"
    cfg.governance_config_path = ""
    cfg.governance_spec_glob = ""
    cfg.governance_block_on = "none"
    cfg.effective_quality_level = MagicMock(return_value="L0")

    hooks = GovernanceSprintHooks("/tmp/nonexistent-sc-hooks", cfg, bus)
    report = GovernanceReport(
        gate="review",
        violations=[
            GovernanceViolation(
                rule_id="compose:restart_policy",
                severity="warning",
                message="svc1 缺 restart",
                location={"file": "docker-compose.yml", "service": "api"},
            ),
        ],
        metadata={"duration_sec": 0.1},
    )
    sprint = SprintDefinition(name="S1", tasks=[SprintBacklogItem(description="t", agent="coder")])
    await hooks._emit_gate_summary("review", sprint, report)

    assert len(seen) == 1
    assert seen[0].type == EventType.GOVERNANCE_GATE
    d = seen[0].data
    assert d["gate"] == "review"
    assert d["sprint_name"] == "S1"
    assert d["compose_rule_ids"] == ["compose:restart_policy"]
    assert len(d["compose_hits"]) == 1
    assert "compose:restart_policy" in d["violation_rule_ids_sample"]


@pytest.mark.asyncio
async def test_governance_planning_skips_emit_when_event_bus_none():
    cfg = MagicMock(spec=RuntimeConfig)
    cfg.governance_enabled = True
    cfg.governance_report_dir = ".sprintcycle"
    cfg.governance_config_path = ""
    cfg.governance_spec_glob = ""
    cfg.effective_quality_level = MagicMock(return_value="L0")

    hooks = GovernanceSprintHooks("/tmp/nonexistent-sc-hooks-none", cfg, None)
    report = GovernanceReport(gate="planning", violations=[], metadata={})
    sprint = SprintDefinition(name="S0", tasks=[])
    await hooks._emit_gate_summary("planning", sprint, report)
    # 无 bus 时不抛错即可
