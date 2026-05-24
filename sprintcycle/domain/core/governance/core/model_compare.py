"""两次 pytest + junitxml 对比（模型/环境切换回归基线）。"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _parse_junit_failures(path: Path) -> Tuple[int, List[str], List[str]]:
    """返回 (failed_count, failed_nodeids, error_messages)。"""
    if not path.is_file():
        return 0, [], []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception:
        return 0, [], ["junit parse error"]
    failed: List[str] = []
    msgs: List[str] = []
    for case in root.iter("testcase"):
        name = case.get("name") or ""
        classname = case.get("classname") or ""
        node = f"{classname}::{name}" if classname else name
        for tag in ("failure", "error"):
            el = case.find(tag)
            if el is not None:
                failed.append(node)
                body = (el.get("message") or el.text or "").strip()[:500]
                msgs.append(f"{node}: {body}")
    return len(failed), failed, msgs


def _merge_env(pairs: Tuple[str, ...]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in pairs:
        if "=" not in p:
            continue
        k, _, v = p.partition("=")
        k = k.strip()
        if k:
            out[k] = v
    return out


def run_pytest_with_junit(
    cwd: Path,
    junit_path: Path,
    extra_env: Dict[str, str],
    pytest_args: List[str],
) -> int:
    env = {**os.environ, **extra_env}
    cmd = [sys.executable, "-m", "pytest", f"--junitxml={junit_path}", *pytest_args]
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env, timeout=600)
    return int(proc.returncode)


def run_model_compare(
    project_root: Path,
    pytest_args: List[str],
    env1_pairs: Tuple[str, ...],
    env2_pairs: Tuple[str, ...],
) -> Dict[str, Any]:
    """
    在同一仓库、相同 pytest 参数下跑两遍，对比失败用例集合。

    ``env1_pairs`` / ``env2_pairs`` 为 ``KEY=VALUE`` 字符串（如 ``LLM_MODEL=a``），用于模拟两次运行环境差异。
    """
    root = project_root.resolve()
    env1 = _merge_env(env1_pairs)
    env2 = _merge_env(env2_pairs)
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        j1 = td_path / "run1.xml"
        j2 = td_path / "run2.xml"
        code1 = run_pytest_with_junit(root, j1, env1, pytest_args)
        code2 = run_pytest_with_junit(root, j2, env2, pytest_args)
        n1, f1, _ = _parse_junit_failures(j1)
        n2, f2, _ = _parse_junit_failures(j2)
        set1, set2 = set(f1), set(f2)
        only_first = sorted(set1 - set2)
        only_second = sorted(set2 - set1)
        common = sorted(set1 & set2)
        return {
            "project_path": str(root),
            "pytest_args": pytest_args,
            "env1": env1,
            "env2": env2,
            "exit_code_run1": code1,
            "exit_code_run2": code2,
            "failed_count_run1": n1,
            "failed_count_run2": n2,
            "failed_only_run1": only_first,
            "failed_only_run2": only_second,
            "failed_both": common,
            "failure_sets_equal": set1 == set2,
        }
