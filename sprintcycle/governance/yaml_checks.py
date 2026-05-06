"""从 YAML 加载声明式检查（子进程 + 期望退出码）。"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger

from .report import GovernanceViolation, Severity


def load_governance_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning("治理 YAML 解析失败 {}: {}", path, e)
        return {}


def _truncate(s: str, max_len: int = 6000) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 20] + "\n... [truncated]"


def run_argv_item(
    item: Dict[str, Any],
    project_root: Path,
    gate_label: str,
    *,
    extra_env: Optional[Dict[str, str]] = None,
) -> List[GovernanceViolation]:
    """执行单条 argv 检查（与 ``run_argv_checks`` 语义一致）；可选 ``extra_env`` 并入子进程环境。"""
    violations: List[GovernanceViolation] = []
    root = project_root.resolve()
    rid = str(item.get("id") or item.get("name") or "anonymous-check")
    argv = item.get("argv") or item.get("command")
    if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv):
        violations.append(
            GovernanceViolation(
                rule_id=f"{gate_label}:{rid}",
                severity="error",
                message="检查项缺少合法 argv（字符串列表）",
                location={"item": rid},
            )
        )
        return violations
    cwd_rel = str(item.get("cwd") or ".").strip() or "."
    cwd = (root / cwd_rel).resolve()
    if not str(cwd).startswith(str(root)) and cwd != root:
        violations.append(
            GovernanceViolation(
                rule_id=f"{gate_label}:{rid}",
                severity="error",
                message=f"cwd 必须位于项目根内: {cwd_rel}",
                location={"cwd": str(cwd)},
            )
        )
        return violations
    expect = int(item.get("expect_code", 0))
    timeout = float(item.get("timeout_sec", 120))
    sev_raw = str(item.get("severity", "error")).lower()
    sev: Severity
    if sev_raw == "warning":
        sev = "warning"
    elif sev_raw == "info":
        sev = "info"
    else:
        sev = "error"
    env = os.environ.copy()
    if extra_env:
        for k, v in extra_env.items():
            env[str(k)] = str(v)
    try:
        proc = subprocess.run(
            list(argv),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        violations.append(
            GovernanceViolation(
                rule_id=f"{gate_label}:{rid}",
                severity=sev,
                message=f"检查超时 ({timeout}s): {' '.join(argv)}",
                location={"cwd": str(cwd)},
            )
        )
        return violations
    except Exception as e:
        violations.append(
            GovernanceViolation(
                rule_id=f"{gate_label}:{rid}",
                severity="error",
                message=f"执行失败: {e}",
                location={"argv": argv},
            )
        )
        return violations
    if proc.returncode != expect:
        tail = _truncate((proc.stderr or "") + "\n" + (proc.stdout or ""))
        violations.append(
            GovernanceViolation(
                rule_id=f"{gate_label}:{rid}",
                severity=sev,
                message=(
                    f"退出码 {proc.returncode} 期望 {expect}: {' '.join(argv)}\n{tail.strip()}"
                ),
                location={"cwd": str(cwd), "exit_code": proc.returncode},
            )
        )
    return violations


def run_argv_checks(
    items: List[Dict[str, Any]],
    project_root: Path,
    gate_label: str,
    *,
    extra_env: Optional[Dict[str, str]] = None,
) -> List[GovernanceViolation]:
    violations: List[GovernanceViolation] = []
    root = project_root.resolve()
    for item in items:
        if not isinstance(item, dict):
            continue
        violations.extend(run_argv_item(item, root, gate_label, extra_env=extra_env))
    return violations


def checks_for_gate(data: Dict[str, Any], gate: str) -> List[Dict[str, Any]]:
    """支持顶层 ``planning`` / ``review`` / ``task_after`` 或 ``gates: { … }``。"""
    raw: Any = None
    if "gates" in data and isinstance(data["gates"], dict):
        raw = data["gates"].get(gate.replace("_gate", "")) or data["gates"].get(gate)
    if raw is None:
        raw = data.get(gate) or data.get(f"{gate}_checks")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []
