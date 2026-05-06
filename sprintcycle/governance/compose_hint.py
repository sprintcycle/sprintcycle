"""Compose 文件轻量门禁（E-3 扩展）：解析 YAML 后按服务提示 restart / healthcheck。"""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from .report import GovernanceViolation


def check_compose_hints(compose_path: Path, text: str) -> List[GovernanceViolation]:
    """
    在已有「全文含 healthcheck」提示之外，对 ``services`` 做逐服务启发式检查。
    解析失败时退化为仅依赖调用方已有的全文扫描（由 runner 负责）。
    """
    violations: List[GovernanceViolation] = []
    loc_base = {"file": str(compose_path)}

    if "healthcheck:" not in text.lower():
        violations.append(
            GovernanceViolation(
                rule_id="compose:healthcheck",
                severity="warning",
                message=f"{compose_path.name} 中未检测到 healthcheck 声明",
                location=loc_base,
            )
        )

    try:
        doc = yaml.safe_load(text)
    except Exception:
        return violations

    if not isinstance(doc, dict):
        return violations
    services = doc.get("services")
    if not isinstance(services, dict):
        return violations

    for name, svc in services.items():
        if not isinstance(svc, dict) or not svc:
            continue
        sid = str(name)
        if "restart" not in svc:
            violations.append(
                GovernanceViolation(
                    rule_id="compose:restart_policy",
                    severity="warning",
                    message=f"服务「{sid}」未设置 restart 策略（建议 unless-stopped）",
                    location={**loc_base, "service": sid},
                )
            )
        if "healthcheck" not in svc:
            violations.append(
                GovernanceViolation(
                    rule_id="compose:service_healthcheck",
                    severity="warning",
                    message=f"服务「{sid}」缺少 healthcheck 块",
                    location={**loc_base, "service": sid},
                )
            )

    return violations
