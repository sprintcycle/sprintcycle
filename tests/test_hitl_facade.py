"""HITL Facade 测试 - 覆盖人工决策接口"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from sprintcycle.domain.core.governance.hitl.facade import (
    HitlFacade,
    HitlEvent,
    HitlGateResult,
    HitlRequestResult,
)
from sprintcycle.domain.core.governance.hitl.types import HitlGate, HitlCorrection, HitlReplayDirective


class TestHitlDataClasses:
    """测试 HITL 数据类"""

    def test_hitl_event_creation(self):
        """测试 HitlEvent 创建"""
        event = HitlEvent(
            event_type="test_event",
            execution_id="exec-1",
            scope="test_scope",
            title="Test Event",
            summary="Test summary",
            gate="review",
            context={"key": "value"},
            metadata={"author": "test"},
            risk_level="high",
        )

        assert event.event_type == "test_event"
        assert event.execution_id == "exec-1"
        assert event.scope == "test_scope"
        assert event.title == "Test Event"
        assert event.summary == "Test summary"
        assert event.gate == "review"
        assert event.context == {"key": "value"}
        assert event.metadata == {"author": "test"}
        assert event.risk_level == "high"

    def test_hitl_gate_result(self):
        """测试 HitlGateResult"""
        result = HitlGateResult(
            should_trigger=True,
            triggered=True,
            request_id="req-1",
            decision="approve",
            policy={"key": "value"},
            metadata={"source": "test"},
        )

        assert result.should_trigger is True
        assert result.triggered is True
        assert result.request_id == "req-1"
        assert result.decision == "approve"
        assert result.policy == {"key": "value"}
        assert result.metadata == {"source": "test"}

    def test_hitl_request_result(self):
        """测试 HitlRequestResult"""
        result = HitlRequestResult(
            request_id="req-1",
            execution_id="exec-1",
            gate="EXECUTION_APPROVAL",
            status="resolved",
            decision="approve",
            note="OK",
            context={"key": "value"},
            metadata={"source": "test"},
        )

        assert result.request_id == "req-1"
        assert result.execution_id == "exec-1"
        assert result.gate == "EXECUTION_APPROVAL"
        assert result.status == "resolved"
        assert result.decision == "approve"
        assert result.note == "OK"
        assert result.context == {"key": "value"}
        assert result.metadata == {"source": "test"}


class TestHitlFacade:
    """测试 HitlFacade"""

    def test_facade_creation(self):
        """测试 facade 创建"""
        mock_service = AsyncMock()
        facade = HitlFacade(mock_service, config={"enabled": True})

        assert facade._service == mock_service
        assert facade._config == {"enabled": True}
        assert facade.service == mock_service

    def test_facade_without_service(self):
        """测试无服务的 facade"""
        facade = HitlFacade(None, config={})

        assert facade._service is None
        assert facade.service is None

    @pytest.mark.asyncio
    async def test_enter_gate_should_not_trigger(self):
        """测试 enter_gate 不应触发"""
        facade = HitlFacade(None, config={"hitl": {"enabled": False}})

        result = await facade.enter_gate(
            execution_id="exec-1",
            gate="EXECUTION_APPROVAL",
            title="Test Gate",
            summary="Test summary",
            context={},
        )

        assert result.should_trigger is False
        assert result.triggered is False

    @pytest.mark.asyncio
    async def test_enter_gate_no_service(self):
        """测试 enter_gate 无服务"""
        class MockConfig:
            hitl_enabled = True
            hitl_gates = "EXECUTION_APPROVAL"
        
        facade = HitlFacade(None, config=MockConfig())

        result = await facade.enter_gate(
            execution_id="exec-1",
            gate="EXECUTION_APPROVAL",
            title="Test Gate",
            summary="Test summary",
            context={},
        )

        assert result.should_trigger is True
        assert result.triggered is False
        assert result.metadata.get("reason") == "hitl_service_unavailable"

    @pytest.mark.asyncio
    async def test_request_human_decision_no_service(self):
        """测试 request_human_decision 无服务"""
        facade = HitlFacade(None, config={})

        result = await facade.request_human_decision(
            execution_id="exec-1",
            gate=HitlGate.EXECUTION_APPROVAL.value,
            title="Test Decision",
            summary="Test summary",
            context={},
        )

        assert result.request_id == ""
        assert result.execution_id == "exec-1"
        assert result.gate == HitlGate.EXECUTION_APPROVAL.value
        assert result.status == "unavailable"
        assert result.metadata.get("reason") == "hitl_service_unavailable"

    @pytest.mark.asyncio
    async def test_request_human_decision_with_service(self):
        """测试 request_human_decision 有服务"""
        mock_service = AsyncMock()
        mock_request = MagicMock()
        mock_request.request_id = "req-1"
        mock_request.execution_id = "exec-1"
        mock_request.status = "pending"
        mock_request.to_dict.return_value = {"request_id": "req-1"}
        mock_service.start_request.return_value = mock_request

        mock_decision = MagicMock()
        mock_decision.value = "approve"
        mock_service.wait_for_decision.return_value = mock_decision

        facade = HitlFacade(mock_service, config={})

        result = await facade.request_human_decision(
            execution_id="exec-1",
            gate=HitlGate.EXECUTION_APPROVAL.value,
            title="Test Decision",
            summary="Test summary",
            context={"key": "value"},
            risk_level="medium",
            wait=True,
        )

        assert result.request_id == "req-1"
        assert result.execution_id == "exec-1"
        assert result.gate == HitlGate.EXECUTION_APPROVAL.value
        assert result.status == "resolved"
        assert result.decision == "approve"

    @pytest.mark.asyncio
    async def test_request_human_decision_no_wait(self):
        """测试 request_human_decision 不等待"""
        mock_service = AsyncMock()
        mock_request = MagicMock()
        mock_request.request_id = "req-1"
        mock_request.execution_id = "exec-1"
        mock_request.status = "pending"
        mock_request.to_dict.return_value = {"request_id": "req-1"}
        mock_service.start_request.return_value = mock_request

        facade = HitlFacade(mock_service, config={})

        result = await facade.request_human_decision(
            execution_id="exec-1",
            gate=HitlGate.EXECUTION_APPROVAL.value,
            title="Test Decision",
            summary="Test summary",
            context={},
            wait=False,
        )

        assert result.request_id == "req-1"
        assert result.status == "pending"
        assert result.decision is None

    @pytest.mark.asyncio
    async def test_submit_decision_no_service(self):
        """测试 submit_decision 无服务"""
        facade = HitlFacade(None, config={})

        result = await facade.submit_decision("req-1", "approve", note="OK")

        assert result is None

    @pytest.mark.asyncio
    async def test_submit_decision_with_service(self):
        """测试 submit_decision 有服务"""
        mock_service = AsyncMock()
        mock_record = MagicMock()
        mock_record.to_dict.return_value = {"status": "approved"}
        mock_service.submit_decision.return_value = mock_record

        facade = HitlFacade(mock_service, config={})

        result = await facade.submit_decision("req-1", "approve", note="OK")

        assert result == {"status": "approved"}
        mock_service.submit_decision.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_request_no_service(self):
        """测试 get_request 无服务"""
        facade = HitlFacade(None, config={})

        result = await facade.get_request("req-1")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_request_with_service(self):
        """测试 get_request 有服务"""
        mock_service = AsyncMock()
        mock_service.get_request.return_value = {"request_id": "req-1", "status": "pending"}

        facade = HitlFacade(mock_service, config={})

        result = await facade.get_request("req-1")

        assert result == {"request_id": "req-1", "status": "pending"}

    @pytest.mark.asyncio
    async def test_list_pending_no_service(self):
        """测试 list_pending 无服务"""
        facade = HitlFacade(None, config={})

        result = await facade.list_pending("exec-1")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_pending_with_service(self):
        """测试 list_pending 有服务"""
        mock_service = AsyncMock()
        mock_service.list_pending.return_value = [{"request_id": "req-1"}]

        facade = HitlFacade(mock_service, config={})

        result = await facade.list_pending("exec-1")

        assert result == [{"request_id": "req-1"}]

    @pytest.mark.asyncio
    async def test_list_history_no_service(self):
        """测试 list_history 无服务"""
        facade = HitlFacade(None, config={})

        result = await facade.list_history("exec-1", limit=10)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_history_with_service(self):
        """测试 list_history 有服务"""
        mock_service = AsyncMock()
        mock_service.list_history.return_value = [{"request_id": "req-1"}, {"request_id": "req-2"}]

        facade = HitlFacade(mock_service, config={})

        result = await facade.list_history("exec-1", limit=10)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_summary(self):
        """测试 summary 方法"""
        mock_service = AsyncMock()
        mock_service.list_pending.return_value = []
        mock_service.list_history.return_value = [{"request_id": "req-1"}, {"request_id": "req-2"}]

        facade = HitlFacade(mock_service, config={})

        result = await facade.summary("exec-1", limit=10)

        assert result["execution_id"] == "exec-1"
        assert result["pending_count"] == 0
        assert result["history_count"] == 2
        assert result["has_service"] is True

    @pytest.mark.asyncio
    async def test_summary_empty(self):
        """测试 summary 空结果"""
        mock_service = AsyncMock()
        mock_service.list_pending.return_value = []
        mock_service.list_history.return_value = []

        facade = HitlFacade(mock_service, config={})

        result = await facade.summary("exec-1")

        assert result["pending_count"] == 0
        assert result["history_count"] == 0
        assert result["latest_request"] is None

    @pytest.mark.asyncio
    async def test_apply_context_patch_no_service(self):
        """测试 apply_context_patch 无服务"""
        facade = HitlFacade(None, config={})

        result = await facade.apply_context_patch(request_id="req-1", context={"key": "value"})

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_apply_context_patch_request_not_found(self):
        """测试 apply_context_patch 请求不存在"""
        mock_service = AsyncMock()
        mock_service.get_request.return_value = None

        facade = HitlFacade(mock_service, config={})

        result = await facade.apply_context_patch(request_id="req-1", context={"key": "value"})

        assert result == {"key": "value"}
