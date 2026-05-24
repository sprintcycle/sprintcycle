"""治理报告历史快照（轮转），供 Dashboard 趋势与审计。"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from ..arch_guard.model import GuardReport as GovernanceReport

_TS_GATE_RE = re.compile(r"^(\d{8}T\d{6}Z)_(planning|review)\.json$")


def _report_dir(project_path: str, runtime_config: Any) -> Path:
    rel = (getattr(runtime_config, "governance_report_dir", None) or ".sprintcycle").strip() or ".sprintcycle"
    root = Path(project_path).expanduser().resolve()
    return (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)


def history_dir(project_path: str, runtime_config: Any) -> Path:
    return _report_dir(project_path, runtime_config) / "governance_history"


def append_history_snapshot(
    report: GovernanceReport,
    project_path: str,
    runtime_config: Any,
) -> Optional[Path]:
    """将当前报告追加写入 ``governance_history/<UTC>_<gate>.json``，并按 ``governance_history_max_files`` 裁剪。"""
    max_n = int(getattr(runtime_config, "governance_history_max_files", 50) or 50)
    if max_n <= 0:
        return None
    hdir = history_dir(project_path, runtime_config)
    try:
        hdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        gate = str(report.gate or "review").strip().lower()
        if gate not in ("planning", "review"):
            gate = "review"
        path = hdir / f"{ts}_{gate}.json"
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        _prune_history_dir(hdir, max_n)
        return path
    except Exception as e:
        logger.warning("写入治理历史快照失败: {}", e)
        return None


def _prune_history_dir(hdir: Path, max_files: int) -> None:
    files = sorted([p for p in hdir.glob("*.json") if p.is_file()], key=lambda p: p.name, reverse=True)
    for old in files[max_files:]:
        try:
            old.unlink()
        except Exception:
            pass


def list_history_entries(project_path: str, runtime_config: Any, *, limit: int = 50) -> List[Dict[str, Any]]:
    """返回最近若干条历史元数据（新→旧）。"""
    hdir = history_dir(project_path, runtime_config)
    if not hdir.is_dir():
        return []
    rows: List[Dict[str, Any]] = []
    for p in sorted(hdir.glob("*.json"), key=lambda x: x.name, reverse=True):
        if len(rows) >= max(1, limit):
            break
        m = _TS_GATE_RE.match(p.name)
        if not m:
            continue
        ts, gate = m.group(1), m.group(2)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        viol = data.get("violations") or []
        n_err = sum(1 for v in viol if isinstance(v, dict) and v.get("severity") == "error")
        n_warn = sum(1 for v in viol if isinstance(v, dict) and v.get("severity") == "warning")
        rows.append(
            {
                "file": p.name,
                "written_at": ts,
                "gate": gate,
                "error_count": n_err,
                "warning_count": n_warn,
                "violation_count": len(viol),
            }
        )
    return rows
