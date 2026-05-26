"""Governance Facade 测试 - 覆盖治理统一入口"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from sprintcycle.domain.core.governance.core.facade import GovernanceFacade, create_governance_facade
from sprintcycle.domain.core.governance.hitl.facade import HitlFacade
from sprintcycle.domain.core.governance.core.runner import GovernanceRunner


class TestGovernanceFacade:
    """测试 GovernanceFacade 统一入口"""

    def test_facade_creation(self):
        """测试 facade 创建"""
        mock_hitl = AsyncMock(spec=HitlFacade)
        mock_runner = MagicMock(spec=GovernanceRunner)
        mock_runner.governance_check = MagicMock(return_value={"passed": True})
        mock_runner.run_planning_gate = AsyncMock(return_value={"gate": "planning", "passed": True})
        mock_runner.run_review_gate = AsyncMock(return_value={"gate": "review", "passed": True})

        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            hitl=mock_hitl,
            runner=mock_runner,
        )

        assert facade._project_path == "/test/project"
        assert facade._hitl == mock_hitl
        assert facade._runner == mock_runner

    def test_facade_lazy_runner(self):
        """测试懒加载 runner"""
        facade = GovernanceFacade(project_path="/test/project", config={})

        assert facade._runner is None
        runner = facade.runner
        assert runner is not None
        assert facade._runner is runner

    @pytest.mark.asyncio
    async def test_observe(self):
        """测试 observe 方法"""
        mock_hitl = AsyncMock(spec=HitlFacade)
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            hitl=mock_hitl,
        )

        await facade.observe(
            event_type="test_event",
            execution_id="exec-1",
            scope="test_scope",
            title="Test",
            summary="Test summary",
        )

        mock_hitl.observe.assert_called_once_with(
            event_type="test_event",
            execution_id="exec-1",
            scope="test_scope",
            title="Test",
            summary="Test summary",
        )

    @pytest.mark.asyncio
    async def test_request_human_decision(self):
        """测试 request_human_decision 方法"""
        mock_hitl = AsyncMock(spec=HitlFacade)
        mock_hitl.request_human_decision.return_value = {"request_id": "req-1"}
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            hitl=mock_hitl,
        )

        result = await facade.request_human_decision(
            execution_id="exec-1",
            gate="EXECUTION_APPROVAL",
            title="Test Decision",
            summary="Test summary",
            context={"key": "value"},
        )

        assert result == {"request_id": "req-1"}
        mock_hitl.request_human_decision.assert_called_once()

    @pytest.mark.asyncio
    async def test_summary(self):
        """测试 summary 方法"""
        mock_hitl = AsyncMock(spec=HitlFacade)
        mock_hitl.summary.return_value = {"pending_count": 0, "history_count": 5}
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            hitl=mock_hitl,
        )

        result = await facade.summary(execution_id="exec-1", limit=10)

        assert result == {"pending_count": 0, "history_count": 5}
        mock_hitl.summary.assert_called_once_with("exec-1", 10)

    @pytest.mark.asyncio
    async def test_list_pending(self):
        """测试 list_pending 方法"""
        mock_hitl = AsyncMock(spec=HitlFacade)
        mock_hitl.list_pending.return_value = []
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            hitl=mock_hitl,
        )

        result = await facade.list_pending(execution_id="exec-1")

        assert result == []
        mock_hitl.list_pending.assert_called_once_with("exec-1")

    @pytest.mark.asyncio
    async def test_list_history(self):
        """测试 list_history 方法"""
        mock_hitl = AsyncMock(spec=HitlFacade)
        mock_hitl.list_history.return_value = []
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            hitl=mock_hitl,
        )

        result = await facade.list_history(execution_id="exec-1", limit=50)

        assert result == []
        mock_hitl.list_history.assert_called_once_with("exec-1", 50)

    @pytest.mark.asyncio
    async def test_get_request(self):
        """测试 get_request 方法"""
        mock_hitl = AsyncMock(spec=HitlFacade)
        mock_hitl.get_request.return_value = {"request_id": "req-1"}
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            hitl=mock_hitl,
        )

        result = await facade.get_request("req-1")

        assert result == {"request_id": "req-1"}
        mock_hitl.get_request.assert_called_once_with("req-1")

    @pytest.mark.asyncio
    async def test_submit_decision(self):
        """测试 submit_decision 方法"""
        mock_hitl = AsyncMock(spec=HitlFacade)
        mock_hitl.submit_decision.return_value = {"status": "approved"}
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            hitl=mock_hitl,
        )

        result = await facade.submit_decision("req-1", "approve", note="OK")

        assert result == {"status": "approved"}
        mock_hitl.submit_decision.assert_called_once_with("req-1", "approve", note="OK")

    def test_governance_check(self):
        """测试 governance_check 方法"""
        mock_runner = MagicMock(spec=GovernanceRunner)
        mock_runner.governance_check = MagicMock(return_value={"passed": True})
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            runner=mock_runner,
        )

        result = facade.governance_check(gate="review", project_path="/test/project")

        assert result == {"passed": True}
        mock_runner.governance_check.assert_called_once_with(gate="review", project_path="/test/project")

    @pytest.mark.asyncio
    async def test_run_planning_gate(self):
        """测试 run_planning_gate 方法"""
        mock_runner = AsyncMock(spec=GovernanceRunner)
        mock_runner.run_planning_gate = AsyncMock(return_value={"gate": "planning", "passed": True})
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            runner=mock_runner,
        )

        result = await facade.run_planning_gate("/test/project", extra_context={"key": "value"})

        assert result == {"gate": "planning", "passed": True}
        mock_runner.run_planning_gate.assert_called_once_with("/test/project", extra_context={"key": "value"})

    @pytest.mark.asyncio
    async def test_run_review_gate(self):
        """测试 run_review_gate 方法"""
        mock_runner = AsyncMock(spec=GovernanceRunner)
        mock_runner.run_review_gate = AsyncMock(return_value={"gate": "review", "passed": True})
        facade = GovernanceFacade(
            project_path="/test/project",
            config={},
            runner=mock_runner,
        )

        result = await facade.run_review_gate("/test/project")

        assert result == {"gate": "review", "passed": True}
        mock_runner.run_review_gate.assert_called_once_with("/test/project")

    def test_create_governance_facade(self):
        """测试 create_governance_facade 工厂函数"""
        facade = create_governance_facade("/test/project", {})

        assert isinstance(facade, GovernanceFacade)
        assert facade._project_path == "/test/project"
