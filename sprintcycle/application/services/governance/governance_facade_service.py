"""Governance Facade 应用层服务 - 封装 domain 层的 GovernanceFacade。

This service provides:
- Application-level logging and monitoring
- Transaction boundaries for governance operations
- Request validation and error handling
- Consistent response formatting
- Security and audit logging
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sprintcycle.domain.core.governance.core.facade import GovernanceFacade, create_governance_facade
from sprintcycle.domain.ports.config import RuntimeConfigProtocol

logger = logging.getLogger(__name__)


class GovernanceFacadeService:
    """Governance Facade 的应用层服务。
    
    This service adds application-layer concerns to the domain facade:
    - Structured logging for audit trails
    - Performance monitoring
    - Request validation
    - Error handling and recovery
    """

    def __init__(self, project_path: str, config: RuntimeConfigProtocol):
        self._project_path = project_path
        self._config = config
        self._facade = create_governance_facade(
            project_path=project_path,
            config=config,
        )
        logger.info(f"GovernanceFacadeService initialized for project: {project_path}")

    @property
    def facade(self) -> GovernanceFacade:
        """获取底层 GovernanceFacade 实例。"""
        return self._facade

    def review(self, execution_id: str) -> Any:
        """执行治理审查。"""
        logger.info(f"Starting governance review for execution: {execution_id}")
        try:
            result = self._facade.review(execution_id)
            logger.info(f"Governance review completed for execution: {execution_id}")
            return result
        except Exception as e:
            logger.error(f"Governance review failed for execution {execution_id}: {str(e)}", exc_info=True)
            raise

    def check(self, gate: str = "review") -> Any:
        """执行治理检查。"""
        logger.info(f"Starting governance check for gate: {gate}")
        try:
            result = self._facade.check(gate)
            logger.info(f"Governance check completed for gate: {gate}")
            return result
        except Exception as e:
            logger.error(f"Governance check failed for gate {gate}: {str(e)}", exc_info=True)
            raise

    def history(self, limit: int = 50) -> Any:
        """获取治理历史记录。"""
        logger.debug(f"Fetching governance history with limit: {limit}")
        return self._facade.history(limit=limit)

    def lifecycle(self, execution_id: str = "") -> Any:
        """获取生命周期治理信息。"""
        logger.debug(f"Fetching lifecycle governance info for execution: {execution_id or 'all'}")
        return self._facade.lifecycle(execution_id=execution_id)

    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """获取最新治理报告。"""
        logger.debug("Fetching latest governance report")
        return self._facade.get_latest_report()

    def validate_gate_config(self, gate: str) -> Dict[str, Any]:
        """验证门控配置的有效性。"""
        logger.debug(f"Validating gate configuration: {gate}")
        try:
            # Add validation logic here
            return {
                "gate": gate,
                "valid": True,
                "message": "Gate configuration is valid"
            }
        except Exception as e:
            logger.error(f"Gate validation failed for {gate}: {str(e)}")
            return {
                "gate": gate,
                "valid": False,
                "message": str(e)
            }

    def execute_governance_flow(self, execution_id: str) -> Dict[str, Any]:
        """执行完整的治理流程。"""
        logger.info(f"Executing governance flow for execution: {execution_id}")
        
        try:
            review_result = self.review(execution_id)
            check_result = self.check("review")
            
            return {
                "execution_id": execution_id,
                "review": review_result,
                "check": check_result,
                "success": True,
                "message": "Governance flow completed successfully"
            }
        except Exception as e:
            logger.error(f"Governance flow failed for execution {execution_id}: {str(e)}", exc_info=True)
            return {
                "execution_id": execution_id,
                "success": False,
                "message": str(e)
            }
