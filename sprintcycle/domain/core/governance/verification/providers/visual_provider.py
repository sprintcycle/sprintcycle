from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from ..model import VerificationFinding


class VisualProvider:
    name = "visual"

    def run(self, project_root: str, context: Dict[str, Any]) -> List[VerificationFinding]:
        root = Path(project_root).expanduser().resolve()
        cmd = (
            context.get("visual_command")
            or context.get("playwright_visual_command")
            or context.get("verify_visual_command")
        )
        if not cmd:
            return [
                VerificationFinding(
                    rule_id="verify:visual:skipped",
                    severity="info",
                    message="视觉验证命令未配置",
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
                timeout=int(context.get("timeout", 900) or 900),
            )
        except Exception as e:
            return [
                VerificationFinding(
                    rule_id="verify:visual:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]
        if proc.returncode == 0:
            return []

        findings: List[VerificationFinding] = []
        payload = (proc.stdout or "").strip()
        if payload:
            try:
                data = json.loads(payload)
                if isinstance(data, list):
                    for item in data[:200]:
                        if not isinstance(item, dict):
                            continue
                        findings.append(
                            VerificationFinding(
                                rule_id=f"verify:visual:{item.get('code', 'diff')}",
                                severity="warning",
                                message=item.get("message", "visual diff"),
                                location={
                                    "file": item.get("file") or item.get("path") or "",
                                    "baseline": item.get("baseline"),
                                    "current": item.get("current"),
                                },
                            )
                        )
            except Exception:
                pass

        if not findings:
            findings.append(
                VerificationFinding(
                    rule_id="verify:visual:failed",
                    severity="error",
                    message=(proc.stderr or proc.stdout or "visual verification failed").strip(),
                    location={"project_root": str(root), "exit_code": proc.returncode},
                )
            )
        return findings
