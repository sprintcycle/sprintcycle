"""HITL 事件类型。"""

from __future__ import annotations

from enum import Enum


class HitlEventType(str, Enum):
    REQUEST_CREATED = "hitl.request.created"
    REQUEST_PENDING = "hitl.request.pending"
    REQUEST_APPROVED = "hitl.request.approved"
    REQUEST_REJECTED = "hitl.request.rejected"
    REQUEST_MODIFIED = "hitl.request.modified"
    REQUEST_EXPIRED = "hitl.request.expired"
    REQUEST_RESUMED = "hitl.request.resumed"
