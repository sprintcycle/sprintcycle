from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from sprintcycle.domain.core.governance.common.model import Finding as GuardFinding


class ImportLinterAdapter:
    def run(self, project_root: str) -> List[GuardFinding]:
        root = Path(project_root).expanduser().resolve()
        pyproject = root / "pyproject.toml"
        if not pyproject.is_file():
            return []

        exe = self._resolve_exe()
        if not exe:
            return [
                GuardFinding(
                    rule_id="import_linter:missing",
                    severity="warning",
                    message="未找到 lint-imports/import-linter 可执行文件，跳过 import-linter 检查",
                    location={"project_root": str(root)},
                )
            ]

        try:
            proc = subprocess.run(
                [exe, "--config", str(pyproject)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
            )
        except Exception as e:
            return [
                GuardFinding(
                    rule_id="import_linter:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]

        if proc.returncode == 0:
            return []

        msg = ((proc.stderr or "").strip() + "\n" + (proc.stdout or "").strip()).strip()
        return [
            GuardFinding(
                rule_id="import_linter:contracts",
                severity="error",
                message=msg or "import-linter 未通过",
                location={"project_root": str(root), "exit_code": proc.returncode},
            )
        ]

    @staticmethod
    def _resolve_exe() -> str | None:
        p = shutil.which("lint-imports")
        if p:
            return p
        p = shutil.which("import-linter")
        if p:
            return p
        cand = Path(sys.executable).resolve().parent / "lint-imports"
        if cand.is_file():
            return str(cand)
        cand2 = Path(sys.executable).resolve().parent / "import-linter"
        if cand2.is_file():
            return str(cand2)
        return None
