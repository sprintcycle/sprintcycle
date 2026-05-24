"""run_workspace 辅助函数测试。"""

from pathlib import Path

import pytest

from sprintcycle.execution.planners.generator import IntentReleasePlanGenerator
from sprintcycle.domain.generic.models import ExecutionMode
from sprintcycle.execution.run_workspace import (
    effective_write_policy,
    normalize_reference_paths,
    normalize_write_policy,
)


def test_effective_write_policy_auto(tmp_path: Path) -> None:
    empty = tmp_path / "newdir"
    assert effective_write_policy("auto", empty) == "create"
    empty.mkdir()
    assert effective_write_policy("auto", empty) == "incremental"


def test_normalize_write_policy_invalid() -> None:
    with pytest.raises(ValueError, match="write_policy"):
        normalize_write_policy("nope")


def test_normalize_reference_paths_requires_dir(tmp_path: Path) -> None:
    d = tmp_path / "ref"
    d.mkdir()
    assert normalize_reference_paths([str(d)]) == [str(d.resolve())]
    nf = tmp_path / "missing"
    with pytest.raises(ValueError, match="须为已存在目录"):
        normalize_reference_paths([str(nf)])


def test_normal_build_uses_anchor_for_project_path(tmp_path: Path) -> None:
    from sprintcycle.domain.intent.parser import ActionType, ParsedIntent

    intent = ParsedIntent(
        action=ActionType.BUILD,
        description="hello",
    )
    plan = IntentReleasePlanGenerator.generate(
        intent,
        anchor_project_path=str(tmp_path / "proj"),
    )
    assert plan.mode == ExecutionMode.NORMAL
    assert Path(plan.project.path).resolve() == (tmp_path / "proj").resolve()
