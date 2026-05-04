"""Claude Code / Cursor Cookbook 引擎适配单元测试。"""

from pathlib import Path

import pytest

import sprintcycle.execution.engines.claude_code as claude_code_mod

from sprintcycle.execution.engines.claude_code import check_claude_code_cli
from sprintcycle.execution.engines.cursor_cookbook import (
    build_cookbook_body,
    write_cookbook_recipe,
)


def test_check_claude_code_cli_uses_custom_bin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPRINTCYCLE_CLAUDE_BIN", "my-claude")

    def _which(exe: str):
        return f"/fake/{exe}" if exe == "my-claude" else None

    monkeypatch.setattr(claude_code_mod.shutil, "which", _which)
    assert check_claude_code_cli() is True


def test_write_cookbook_recipe_creates_file(tmp_path: Path) -> None:
    p = write_cookbook_recipe(
        str(tmp_path),
        title="T",
        body="## body\nhello",
        slug="my-recipe",
    )
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "T" in text
    assert "hello" in text
    assert ".sprintcycle" in str(p.relative_to(tmp_path)) or "cursor-cookbook" in str(p)


def test_build_cookbook_body_includes_sections() -> None:
    b = build_cookbook_body(
        "do the thing",
        prd_overlay_hint="overlay",
        architecture_hint="arch",
    )
    assert "do the thing" in b
    assert "overlay" in b
    assert "arch" in b
    assert "Cursor" in b
