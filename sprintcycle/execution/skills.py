"""场景驱动 Skill 编排。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .marketplace import OpenClawMarketplaceClient
from .protocols import SkillLifecycleSnapshot
from .skill_store import SkillStore


@dataclass
class SkillMatch:
    skill_id: str
    scene: str
    path: str
    version: str = "latest"
    reason: str = ""
    status: str = "pending_injection"
    hooks: List[str] = field(default_factory=lambda: ["after_plan", "before_execute", "before_review", "after_retro"])
    checklist: List[Dict[str, Any]] = field(default_factory=list)
    checksum: str = ""
    market_source: str = "openclaw"

    def snapshot(self) -> SkillLifecycleSnapshot:
        return SkillLifecycleSnapshot(
            skill_id=self.skill_id,
            scene=self.scene,
            version=self.version,
            source=self.market_source,
            status=self.status,
            path=self.path,
            checksum=self.checksum,
        )


class SkillOrchestrator:
    def __init__(self, skills_root: str = "skills", skill_store: Optional[SkillStore] = None, marketplace: Optional[OpenClawMarketplaceClient] = None) -> None:
        self.skills_root = Path(skills_root)
        self._skill_store = skill_store or SkillStore()
        self._marketplace = marketplace or OpenClawMarketplaceClient(skill_store=self._skill_store)
        self._pending: list[SkillMatch] = []
        self._injected: list[SkillMatch] = []

    def identify_scene(self, task_text: str, context: Dict[str, Any]) -> str:
        lowered = f"{task_text} {context.get('project_goals', '')}".lower()
        if any(k in lowered for k in ("支付", "wechat", "payment", "微信支付")):
            return "payment"
        return "general"

    def match_skills(self, scene: str) -> list[SkillMatch]:
        if scene == "payment":
            return [
                SkillMatch(skill_id="wechat-pay", scene=scene, path=str(self.skills_root / "wechat-pay" / "SKILL.md"), reason="支付接入"),
                SkillMatch(skill_id="payment-security", scene=scene, path=str(self.skills_root / "payment-security" / "SKILL.md"), reason="支付安全审查", checklist=[
                    {"category": "security", "title": "支付签名校验", "required": True},
                    {"category": "security", "title": "回调幂等性", "required": True},
                ]),
            ]
        return []

    def after_plan(self, task_text: str, context: Dict[str, Any]) -> list[SkillMatch]:
        scene = self.identify_scene(task_text, context)
        matches = self.match_skills(scene)
        self._pending = matches
        context["skill_scene"] = scene
        context["pending_skills"] = [m.snapshot().to_dict() for m in matches]
        return matches

    def before_execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        injected = []
        for match in self._pending:
            path = Path(match.path)
            if path.exists():
                content = path.read_text(encoding="utf-8")
                injected.append({"skill_id": match.skill_id, "content": content, "hooks": match.hooks, "version": match.version, "checksum": match.checksum, "market_source": match.market_source})
                match.status = "injected"
        self._injected = list(self._pending)
        context["injected_skills"] = injected
        return context

    def before_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        review_checklists = context.setdefault("review_checklists", [])
        for match in self._injected:
            if match.checklist:
                review_checklists.extend(match.checklist)
            if match.skill_id == "payment-security":
                review_checklists.append({"category": "skill", "title": "支付安全合规检查清单", "required": True, "source": "skill"})
        return context

    def after_retro(self, context: Dict[str, Any]) -> None:
        context.pop("injected_skills", None)
        context.pop("pending_skills", None)
        self._pending.clear()
        self._injected.clear()

    def refresh_from_marketplace(self, skill_id: str, version: str) -> None:
        artifact = self._skill_store.get_latest_artifact(skill_id)
        if artifact is None:
            return
        artifact.version = version
        artifact.status = "installed"
        self._skill_store.upsert_artifact(artifact)
        self._marketplace.refresh_skill_state(skill_id, version, status="installed", path=artifact.path)


__all__ = ["SkillMatch", "SkillOrchestrator"]
