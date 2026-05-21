"""G4 / L3：import-linter 契约（CI 与本地 pytest 共用）。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _resolve_lint_imports_exe() -> str | None:
    """Locate lint-imports binary (same logic as governance runner)."""
    p = shutil.which("lint-imports")
    if p:
        return p
    cand = Path(sys.executable).resolve().parent / "lint-imports"
    if cand.is_file():
        return str(cand)
    # Check common user-local bin paths
    for home_prefix in (Path.home() / ".local", Path.home()):
        cand2 = home_prefix / "bin" / "lint-imports"
        if cand2.is_file():
            return str(cand2)
    return None


def test_import_linter_contracts_pass() -> None:
    pytest.importorskip("importlinter")
    exe = _resolve_lint_imports_exe()
    assert exe, "lint-imports 未找到（请 pip install -e '.[dev]'）"
    proc = subprocess.run(
        [exe],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
