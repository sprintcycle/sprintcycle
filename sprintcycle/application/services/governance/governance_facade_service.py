"""Governance Facade 应用层服务 - 封装 domain 层的 GovernanceFacade。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sprintcycle.domain.core.governance.core.facade import GovernanceFacade, create_governance_facade
from sprintcycle.domain.generic.ports.config import RuntimeConfigProtocol


class GovernanceFacadeService:
    """Governance Facade 的应用层包装服务。"""

    def __init__(self, project_path: str, config: RuntimeConfigProtocol):
        self._project_path = project_path
        self._config = config
        self._facade = create_governance_facade(
            project_path=project_path,
            config=config,
        )

    @property
    def facade(self) -> GovernanceFacade:
        """获取底层 GovernanceFacade 实例。"""
        return self._facade

    def review(self, execution_id: str) -> Any:
        """执行治理审查。"""
        return self._facade.review(execution_id)

    def check(self, gate: str = "review") -> Any:
        """执行治理检查。"""
        return self._facade.check(gate)

    def history(self, limit: int = 50) -> Any:
        """获取治理历史记录。"""
        return self._facade.history(limit=limit)

    def lifecycle(self, execution_id: str = "") -> Any:
        """获取生命周期治理信息。"""
        return self._facade.lifecycle(execution_id=execution_id)

    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """获取最新治理报告。"""
        return self._facade.get_latest_report()
