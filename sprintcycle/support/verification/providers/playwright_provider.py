from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from ..model import VerificationFinding


class PlaywrightProvider:
    name = "playwright"

    def run(self, project_root: str, context: Dict[str, Any]) -> List[VerificationFinding]:
        root = Path(project_root).expanduser().resolve()
        cmd = context.get("playwright_command") or context.get("verify_e2e_command")
        if not cmd:
            return [
                VerificationFinding(
                    rule_id="verify:playwright:skipped",
                    severity="info",
                    message="Playwright 验证命令未配置",
                    location={"project_root": str(root)},
                )
            ]
        if isinstance(cmd, str):
            cmd = [cmd]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=int(context.get("timeout", 1800) or 1800),
            )
        except Exception as e:
            return [
                VerificationFinding(
                    rule_id="verify:playwright:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]
        if proc.returncode == 0:
            return []
        return [
            VerificationFinding(
                rule_id="verify:playwright:failed",
                severity="error",
                message=(proc.stderr or proc.stdout or "Playwright verification failed").strip(),
                location={"project_root": str(root), "exit_code": proc.returncode},
            )
        ]
