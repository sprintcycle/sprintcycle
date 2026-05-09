"""观测体系对外数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ObservationEvent:
    event_type: str
    execution_id: str
    scope: str
    title: str
    summary: str = ""
    gate: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"


@dataclass
class ObservationGateResult:
    should_trigger: bool
    triggered: bool
    request_id: Optional[str] = None
    decision: Optional[str] = None
    policy: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservationRequestResult:
    request_id: str
    execution_id: str
    gate: str
    status: str
    decision: Optional[str] = None
    note: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
