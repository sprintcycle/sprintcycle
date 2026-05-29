from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from sprintcycle.domain.core.governance.common.model import Finding as VerificationFinding


class SecurityProvider:
    name = "security"

    def run(self, project_root: str, context: Dict[str, Any]) -> List[VerificationFinding]:
        root = Path(project_root).expanduser().resolve()
        findings: List[VerificationFinding] = []
        findings.extend(self._run_gitleaks(root))
        return findings

    def _run_gitleaks(self, root: Path) -> List[VerificationFinding]:
        exe = self._resolve_exe("gitleaks")
        if not exe:
            return [
                VerificationFinding(
                    rule_id="security:gitleaks:skipped",
                    severity="info",
                    message="gitleaks 未安装",
                    location={"project_root": str(root)},
                )
            ]
        try:
            proc = subprocess.run(
                [exe, "detect", "--no-banner", "--source", str(root)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=300,
            )
        except Exception as e:
            return [
                VerificationFinding(
                    rule_id="security:gitleaks:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]
        if proc.returncode == 0:
            return []
        return [
            VerificationFinding(
                rule_id="security:gitleaks:failed",
                severity="error",
                message=(proc.stderr or proc.stdout or "secret scan failed").strip(),
                location={"project_root": str(root), "exit_code": proc.returncode},
            )
        ]

    @staticmethod
    def _resolve_exe(*names: str) -> str | None:
        for name in names:
            p = shutil.which(name)
            if p:
                return p
        cand = Path(sys.executable).resolve().parent
        for name in names:
            path = cand / name
            if path.is_file():
                return str(path)
        return None
