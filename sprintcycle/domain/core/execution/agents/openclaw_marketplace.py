"""OpenClaw 技能市场接入接口。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MarketSkillVersion:
    version: str
    changelog: str = ""
    checksum: str = ""


@dataclass
class MarketSkill:
    skill_id: str
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    versions: List[MarketSkillVersion] = field(default_factory=list)


class OpenClawMarketplaceClient:
    def search(self, query: str, tags: Optional[List[str]] = None) -> List[MarketSkill]:
        return []

    def install(self, skill_id: str, version: str = "latest") -> Dict[str, Any]:
        return {"skill_id": skill_id, "version": version, "installed": False}

    def get_versions(self, skill_id: str) -> List[MarketSkillVersion]:
        return []


__all__ = ["OpenClawMarketplaceClient", "MarketSkill", "MarketSkillVersion"]
