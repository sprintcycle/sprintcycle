"""用户意图演化闭环（精简版）。

目标不是把用户需求视为静态输入，而是把它视为可持续更新的动态对象。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger


class IntentDriftType(Enum):
    """意图漂移类型。"""

    NONE = "none"
    LOCAL_EDIT = "local_edit"
    REPLAN = "replan"
    FULL_RESET = "full_reset"


@dataclass
class IntentSnapshot:
    """一次意图快照，用于对比前后变化。"""

    intent: str
    normalized_intent: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "user"
    iteration: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "normalized_intent": self.normalized_intent,
            "constraints": self.constraints,
            "goals": self.goals,
            "context": self.context,
            "source": self.source,
            "iteration": self.iteration,
        }


@dataclass
class IntentEvolutionDecision:
    """对意图漂移的判定结果。"""

    drift_type: IntentDriftType
    confidence: float = 0.0
    reason: str = ""
    impact_scope: str = "unknown"
    should_replan: bool = False
    should_reset: bool = False
    signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drift_type": self.drift_type.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "impact_scope": self.impact_scope,
            "should_replan": self.should_replan,
            "should_reset": self.should_reset,
            "signals": self.signals,
        }


class UserIntentEvolutionLoop:
    """意图演化闭环。

    职责：
    1. 记录初始意图与后续修正
    2. 根据执行反馈和新输入判断是否漂移
    3. 决定局部修改 / 重规划 / 重做
    4. 将经验沉淀到 knowledge
    """

    def __init__(
        self,
        memory_store: Optional[Any] = None,
        feedback_loop: Optional[Any] = None,
        knowledge_repo: Optional[Any] = None,
    ):
        self._memory_store = memory_store
        self._feedback_loop = feedback_loop
        self._knowledge_repo = knowledge_repo
        self._snapshots: List[IntentSnapshot] = []
        self._events: List[Dict[str, Any]] = []

    def start(self, intent: str, **context: Any) -> IntentSnapshot:
        snapshot = IntentSnapshot(
            intent=intent,
            normalized_intent=self._normalize(intent),
            constraints=dict(context.get("constraints") or {}),
            goals=list(context.get("goals") or []),
            context=dict(context),
            source=str(context.get("source") or "user"),
            iteration=len(self._snapshots) + 1,
        )
        self._snapshots.append(snapshot)
        self._events.append({"event": "start", "snapshot": snapshot.to_dict()})
        return snapshot

    def revise(self, intent: str, **context: Any) -> IntentSnapshot:
        snapshot = IntentSnapshot(
            intent=intent,
            normalized_intent=self._normalize(intent),
            constraints=dict(context.get("constraints") or {}),
            goals=list(context.get("goals") or []),
            context=dict(context),
            source=str(context.get("source") or "user"),
            iteration=len(self._snapshots) + 1,
        )
        self._snapshots.append(snapshot)
        self._events.append({"event": "revise", "snapshot": snapshot.to_dict()})
        return snapshot

    def detect_drift(
        self,
        previous: Optional[IntentSnapshot],
        current_intent: str,
        execution_feedback: Optional[Dict[str, Any]] = None,
    ) -> IntentEvolutionDecision:
        current = self._normalize(current_intent)
        if previous is None:
            return IntentEvolutionDecision(IntentDriftType.NONE, confidence=0.0, reason="no baseline")

        base = previous.normalized_intent or self._normalize(previous.intent)
        signals: List[str] = []
        if current != base:
            signals.append("intent_text_changed")

        if execution_feedback:
            if execution_feedback.get("failed_tasks", 0) > 0:
                signals.append("execution_failure")
            if execution_feedback.get("suggestions"):
                signals.append("feedback_suggestions")
            if execution_feedback.get("scope_changed"):
                signals.append("scope_changed")

        return self._classify(signals, current, base)

    def classify_from_signals(self, signals: List[str], severity: float = 0.0) -> IntentEvolutionDecision:
        return self._classify(list(signals), None, None, severity=severity)

    def record_learning(
        self,
        *,
        decision: IntentEvolutionDecision,
        intent: str,
        execution_feedback: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        payload = {
            "intent": intent,
            "decision": decision.to_dict(),
            "execution_feedback": execution_feedback or {},
            "metadata": metadata or {},
        }
        self._events.append({"event": "learning", "payload": payload})

        if self._memory_store is not None:
            try:
                memory = self._memory_store.store(
                    memory_type="intent_evolution",
                    content=payload,
                    tags=[decision.drift_type.value, decision.impact_scope],
                    success=not decision.should_reset,
                    score=max(0.1, min(1.0, decision.confidence)),
                    metadata={"source": "UserIntentEvolutionLoop"},
                )
                return memory.to_dict() if hasattr(memory, "to_dict") else None
            except Exception:
                pass

        if self._knowledge_repo is not None and decision.should_replan:
            try:
                card = self._knowledge_repo.add(
                    domain="intent_evolution",
                    outcome=decision.reason,
                    body=intent,
                    lessons={"decision": decision.to_dict(), "feedback": execution_feedback or {}},
                    tags=[decision.drift_type.value, decision.impact_scope],
                    scores={"confidence": decision.confidence},
                )
                return card.to_dict() if hasattr(card, "to_dict") else None
            except Exception as e:
                logger.debug("failed to persist intent evolution knowledge: {}", e)
        return None

    def recent_snapshots(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._snapshots]

    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @staticmethod
    def _normalize(intent: str) -> str:
        return " ".join((intent or "").strip().lower().split())

    def _classify(
        self,
        signals: List[str],
        current: Optional[str],
        base: Optional[str],
        *,
        severity: float = 0.0,
    ) -> IntentEvolutionDecision:
        if not signals:
            return IntentEvolutionDecision(IntentDriftType.NONE, confidence=0.0, reason="no drift signals")

        changed = current is not None and base is not None and current != base
        if severity >= 0.8 or (changed and len(signals) >= 2):
            return IntentEvolutionDecision(
                IntentDriftType.FULL_RESET,
                confidence=min(1.0, 0.75 + severity * 0.25),
                reason="需求发生明显漂移，需要重做链路",
                impact_scope="full",
                should_replan=True,
                should_reset=True,
                signals=signals,
            )

        if changed or "scope_changed" in signals or len(signals) >= 2:
            return IntentEvolutionDecision(
                IntentDriftType.REPLAN,
                confidence=min(1.0, 0.55 + 0.2 * len(signals) + severity * 0.2),
                reason="需求范围发生变化，需要重规划",
                impact_scope="plan",
                should_replan=True,
                should_reset=False,
                signals=signals,
            )

        return IntentEvolutionDecision(
            IntentDriftType.LOCAL_EDIT,
            confidence=min(1.0, 0.45 + 0.15 * len(signals) + severity * 0.1),
            reason="局部信息更新，可做增量修正",
            impact_scope="local",
            should_replan=False,
            should_reset=False,
            signals=signals,
        )


__all__ = [
    "IntentDriftType",
    "IntentSnapshot",
    "IntentEvolutionDecision",
    "UserIntentEvolutionLoop",
]
