"""Suggestion classifier.

Keeps classification lightweight and rule-driven for the first release.
"""

from __future__ import annotations

from typing import List

from .models import Suggestion, SuggestionImpactScope


class SuggestionClassifier:
    KEYWORDS = {
        "governance": ["governance", "gate", "review", "审批"],
        "rollback": ["rollback", "回滚", "restore"],
        "observability": ["observe", "observability", "dashboard", "replay", "监控"],
        "execution": ["executor", "execution", "run", "执行"],
        "release_plan": ["release plan", "plan", "release", "sprint", "计划"],
        "code": ["code", "api", "module", "refactor", "重构"],
        "documentation": ["docs", "document", "文档"],
    }

    async def classify(self, suggestion: Suggestion) -> Suggestion:
        text = f"{suggestion.title} {suggestion.summary} {suggestion.details}".lower()
        scopes: List[SuggestionImpactScope] = []
        for scope, keywords in self.KEYWORDS.items():
            if any(k.lower() in text for k in keywords):
                scopes.append(scope)  # type: ignore[arg-type]
        if not scopes:
            scopes.append("governance")
        suggestion.impact_scope = list(dict.fromkeys(scopes))
        return suggestion
