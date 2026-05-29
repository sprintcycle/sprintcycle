from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from sprintcycle.domain.core.governance.common.model import Finding as VerificationFinding


class PytestProvider:
    name = "pytest"

    def run(self, project_root: str, context: Dict[str, Any]) -> List[VerificationFinding]:
        root = Path(project_root).expanduser().resolve()
        cmd = context.get("pytest_command") or ["python", "-m", "pytest", "-q"]
        if isinstance(cmd, str):
            cmd = [cmd]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=int(context.get("timeout", 600) or 600),
            )
        except Exception as e:
            return [
                VerificationFinding(
                    rule_id="test:pytest:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]
        if proc.returncode == 0:
            return []
        return [
            VerificationFinding(
                rule_id="test:pytest:failed",
                severity="error",
                message=(proc.stderr or proc.stdout or "pytest failed").strip(),
                location={"project_root": str(root), "exit_code": proc.returncode},
            )
        ]
