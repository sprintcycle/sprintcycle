from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from ..model import VerificationFinding


class CliProvider:
    name = "cli"

    def run(self, project_root: str, context: Dict[str, Any]) -> List[VerificationFinding]:
        root = Path(project_root).expanduser().resolve()
        cmd = context.get("cli_command")
        if not cmd:
            return [
                VerificationFinding(
                    rule_id="verify:cli:skipped",
                    severity="info",
                    message="CLI 验证命令未配置",
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
                timeout=int(context.get("timeout", 600) or 600),
            )
        except Exception as e:
            return [
                VerificationFinding(
                    rule_id="verify:cli:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]
        if proc.returncode == 0:
            return []
        return [
            VerificationFinding(
                rule_id="verify:cli:failed",
                severity="error",
                message=(proc.stderr or proc.stdout or "CLI verification failed").strip(),
                location={"project_root": str(root), "exit_code": proc.returncode},
            )
        ]
