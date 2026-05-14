"""Scoring helpers for the fitness layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class FitnessScorer:
    def score(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        events: List[Dict[str, Any]] = list(payload.get("events") or [])
        score = 50 + min(len(events), 10)
        return {"score": max(0, min(100, score))}
