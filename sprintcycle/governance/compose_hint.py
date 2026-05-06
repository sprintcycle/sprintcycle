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


def check_compose_supply_chain_hints(compose_path: Path, services: dict) -> List[GovernanceViolation]:
    """
    供应链加深（E-3 v2）：``image:...:latest`` 提示；``build`` 时检查 Dockerfile 是否存在。
    与 ``check_compose_hints`` 独立，由 ``GovernanceRunner`` 在 ``governance_compose_supply_chain`` 为真时追加调用。
    """
    violations: List[GovernanceViolation] = []
    loc_base = {"file": str(compose_path)}
    compose_dir = compose_path.parent

    for name, svc in services.items():
        if not isinstance(svc, dict) or not svc:
            continue
        sid = str(name)
        img = svc.get("image")
        if isinstance(img, str) and (img.endswith(":latest") or img == "latest"):
            violations.append(
                GovernanceViolation(
                    rule_id="compose:image_latest",
                    severity="warning",
                    message=f"服务「{sid}」使用 latest 标签镜像，生产环境建议钉 digest 或固定版本: {img}",
                    location={**loc_base, "service": sid},
                )
            )

        bld = svc.get("build")
        if bld is None:
            continue
        ctx_dir = compose_dir
        dockerfile = "Dockerfile"
        if isinstance(bld, str):
            ctx_dir = (compose_dir / bld).resolve()
        elif isinstance(bld, dict):
            ctxt = bld.get("context", ".")
            ctx_dir = (compose_dir / str(ctxt)).resolve()
            if bld.get("dockerfile"):
                dockerfile = str(bld["dockerfile"])
        df = ctx_dir / dockerfile
        if not df.is_file():
            violations.append(
                GovernanceViolation(
                    rule_id="compose:dockerfile_missing",
                    severity="warning",
                    message=f"服务「{sid}」build 指向的 Dockerfile 不存在: {df}",
                    location={**loc_base, "service": sid},
                )
            )

    return violations
