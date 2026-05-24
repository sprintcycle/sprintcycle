"""Management and suggestion overview aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from sprintcycle.domain.core.governance.suggestion import SuggestionFacade


@dataclass
class ManagementOverviewService:
    suggestion: SuggestionFacade
    evolution_dashboard: Callable[[], Dict[str, Any]]
    evolution_cli: Callable[[], str]

    async def suggestion_overview_raw(self) -> Any:
        return await self.suggestion.overview()

    async def suggestion_overview(self) -> Dict[str, Any]:
        return (await self.suggestion_overview_raw()).to_dict()

    async def suggestion_overview_cli(self) -> str:
        return (await self.suggestion_overview_raw()).to_cli_text()

    async def suggestion_overview_dashboard(self) -> Dict[str, Any]:
        return (await self.suggestion_overview_raw()).to_dashboard_payload()

    async def promotion_readiness(self) -> Dict[str, Any]:
        overview = await self.suggestion_overview_dashboard()
        promotion = overview.get("promotion", {}) if isinstance(overview, dict) else {}
        ready = int(promotion.get("ready", 0)) if isinstance(promotion, dict) else 0
        blocked = int(promotion.get("blocked", 0)) if isinstance(promotion, dict) else 0
        total = ready + blocked
        return {
            "success": True,
            "data": {
                "ready": ready,
                "blocked": blocked,
                "total": total,
                "ready_rate": round((ready / total) * 100, 2) if total else 0.0,
                "reasons": dict(promotion.get("reasons", {}) if isinstance(promotion, dict) else {}),
            },
        }

    async def suggestion_overview_payload(self) -> Dict[str, Any]:
        overview = await self.suggestion.overview()
        if hasattr(overview, "to_dashboard_payload"):
            return overview.to_dashboard_payload()
        return dict(overview or {})

    async def suggestion_list_payload(self, limit: int = 20) -> Dict[str, Any]:
        suggestions = await self.suggestion.list_suggestions(limit=limit)
        if hasattr(suggestions, "to_dashboard_payload"):
            return suggestions.to_dashboard_payload()
        if isinstance(suggestions, dict):
            return dict(suggestions)
        return {"items": list(suggestions or [])}

    async def management_overview_payload(self) -> Dict[str, Any]:
        return {
            "evolution": self.evolution_dashboard(),
            "suggestion": await self.suggestion_overview_dashboard(),
            "project_path": "",
        }

    async def management_overview(self, project_path: str) -> Dict[str, Any]:
        payload = await self.management_overview_payload()
        payload["project_path"] = project_path
        return {"success": True, "data": payload}

    async def management_overview_cli(self, project_path: str) -> str:
        evo_text = self.evolution_cli()
        sug_text = await self.suggestion_overview_cli()
        return "\n".join(["Management Overview", "", "[Evolution]", evo_text, "", "[Suggestion]", sug_text])


__all__ = ["ManagementOverviewService"]
