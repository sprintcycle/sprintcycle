"""测试 Application Layer Protocols"""

import pytest
from sprintcycle.application.protocols import (
    FeedbackProtocol,
    LifecycleProtocol,
)


class MockLifecycleProtocol(LifecycleProtocol):
    """测试用 Lifecycle 实现"""
    
    def __init__(self):
        self._stage = "dev"
    
    def can_promote(self, stage: str) -> bool:
        valid_stages = ["dev", "staging", "prod"]
        current_idx = valid_stages.index(self._stage) if self._stage in valid_stages else -1
        target_idx = valid_stages.index(stage) if stage in valid_stages else -1
        return target_idx > current_idx
    
    def promote(self, stage: str) -> dict:
        self._stage = stage
        return {"success": True, "stage": stage}


class MockFeedbackProtocol(FeedbackProtocol):
    """测试用 Feedback 实现"""
    
    def process_feedback(self, task_result):
        return [
            {"type": "suggestion", "message": "Consider error handling"},
            {"type": "improvement", "message": "Add logging"},
        ]


class TestLifecycleProtocol:
    """测试 LifecycleProtocol"""
    
    def test_can_promote_valid(self):
        impl = MockLifecycleProtocol()
        assert impl.can_promote("staging") is True
        assert impl.can_promote("prod") is True
    
    def test_can_promote_invalid(self):
        impl = MockLifecycleProtocol()
        assert impl.can_promote("dev") is False
        assert impl.can_promote("unknown") is False
    
    def test_promote_updates_stage(self):
        impl = MockLifecycleProtocol()
        result = impl.promote("staging")
        assert result["success"] is True
        assert result["stage"] == "staging"


class TestFeedbackProtocol:
    """测试 FeedbackProtocol"""
    
    def test_process_feedback_returns_suggestions(self):
        impl = MockFeedbackProtocol()
        result = impl.process_feedback({})
        assert len(result) == 2
        assert result[0]["type"] == "suggestion"
