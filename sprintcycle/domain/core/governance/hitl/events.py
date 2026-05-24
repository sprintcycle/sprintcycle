"""HITL 事件类型。"""

from __future__ import annotations

from enum import Enum


class HitlEventType(str, Enum):
    REQUEST_OPEN = "hitl.request.open"
    REQUEST_UPDATED = "hitl.request.updated"
    REQUEST_MODIFIED = "hitl.request.modified"
    PATCH_APPLIED = "hitl.patch.applied"
    CONTEXT_REFLOWED = "hitl.context.reflowed"
    REPLAY_TRIGGERED = "hitl.replay.triggered"
    REQUEST_RESOLVED = "hitl.request.resolved"
