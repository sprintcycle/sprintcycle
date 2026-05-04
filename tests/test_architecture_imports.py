"""G4 / L3：import-linter 契约（CI 与本地 pytest 共用）。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_import_linter_contracts_pass() -> None:
    pytest.importorskip("importlinter")
    venv_bin = ROOT / ".venv" / "bin" / "lint-imports"
    exe = shutil.which("lint-imports") or (str(venv_bin) if venv_bin.is_file() else None)
    assert exe, "lint-imports 未找到（请 pip install -e '.[dev]'）"
    proc = subprocess.run(
        [exe],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
