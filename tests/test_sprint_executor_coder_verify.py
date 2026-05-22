"""Coder 验证-修复轮次（max_verify_fix_rounds）。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sprintcycle.infrastructure.config import RuntimeConfig
from sprintcycle.execution.sprint_executor import SprintExecutor
from sprintcycle.domain.models import SprintBacklogItem


class _FakeCoder:
    calls = 0

    def __init__(self) -> None:
        pass

    async def execute(self, task: str, ctx: object) -> SimpleNamespace:
        _FakeCoder.calls += 1
        if _FakeCoder.calls < 2:
            return SimpleNamespace(success=False, error="first fail", output="")
        return SimpleNamespace(success=True, error=None, output="fixed")


@pytest.mark.asyncio
async def test_coder_retries_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeCoder.calls = 0
    monkeypatch.setattr(
        "sprintcycle.execution.agents.coder_base.CoderAgent",
        _FakeCoder,
    )
    cfg = RuntimeConfig(max_verify_fix_rounds=3, dry_run=False)
    ex = SprintExecutor(runtime_config=cfg, max_verify_fix_rounds=3)
    task = SprintBacklogItem(description="do thing", agent="coder")
    out = await ex._execute_coder_task(
        task,
        {"sprint_name": "S1", "coding_engine": "aider", "_sprint_coding_engine": "aider"},
    )
    assert out == "fixed"
    assert _FakeCoder.calls == 2


@pytest.mark.asyncio
async def test_coder_exhausts_rounds(monkeypatch: pytest.MonkeyPatch) -> None:
    class AlwaysFail:
        def __init__(self) -> None:
            pass

        async def execute(self, task: str, ctx: object) -> SimpleNamespace:
            return SimpleNamespace(success=False, error="nope", output="")

    monkeypatch.setattr(
        "sprintcycle.execution.agents.coder_base.CoderAgent",
        AlwaysFail,
    )
    cfg = RuntimeConfig(max_verify_fix_rounds=2, dry_run=False)
    ex = SprintExecutor(runtime_config=cfg, max_verify_fix_rounds=2)
    task = SprintBacklogItem(description="x", agent="coder")
    with pytest.raises(RuntimeError, match="nope"):
        await ex._execute_coder_task(
            task,
            {"sprint_name": "S1", "coding_engine": "aider"},
        )
