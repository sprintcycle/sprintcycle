"""HTTP handlers for lifecycle management.

This module provides REST API endpoints for lifecycle operations,
following hexagonal architecture patterns.

**Endpoints:**
- POST /lifecycle: Create a new lifecycle
- GET /lifecycle/{execution_id}: Get lifecycle by ID
- PUT /lifecycle/{execution_id}/transition: Transition to new stage
- POST /lifecycle/{execution_id}/recovery: Trigger recovery
- GET /lifecycle/{execution_id}/validation: Validate lifecycle

**Design Principles:**
- Adapters convert HTTP requests to domain requests
- Delegates business logic to LifecycleService
- Returns JSON responses matching domain model structure
- Follows RESTful conventions
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sprintcycle.application.services.lifecycle import LifecycleService
from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleSubstage,
    BuildLifecycleRequest,
    BuildLifecycleRequestBuilder,
    TransitionRequest,
    TransitionRequestBuilder,
    RecoveryRequest,
    RecoveryRequestBuilder,
    WebLifecycleRequest,
    WebLifecycleRequestBuilder,
)


class LifecycleHandler:
    """
    HTTP handler for lifecycle operations.
    
    This class acts as an adapter between HTTP layer and application services,
    following hexagonal architecture principles.
    """
    
    def __init__(self, service: Optional[LifecycleService] = None):
        self._service = service or LifecycleService()
    
    # =========================================================================
    # Lifecycle Creation
    # =========================================================================
    
    def create_lifecycle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lifecycle from HTTP request data."""
        try:
            request = BuildLifecycleRequestBuilder() \
                .with_execution_id(request_data.get("execution_id", "")) \
                .with_task_id(request_data.get("task_id", "")) \
                .with_project_path(request_data.get("project_path", "")) \
                .with_task_type(request_data.get("task_type", "project_optimization")) \
                .with_intent(request_data.get("intent", "")) \
                .with_metadata(**(request_data.get("metadata", {}))) \
                .build()
            
            lifecycle = self._service.create_lifecycle(request)
            return self._success_response(lifecycle)
        
        except ValueError as e:
            return self._error_response(str(e), 400)
    
    def orchestrate_web(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate a lifecycle from web request data."""
        try:
            request = WebLifecycleRequestBuilder() \
                .with_execution_id(request_data.get("execution_id", "")) \
                .with_task_id(request_data.get("task_id", "")) \
                .with_project_path(request_data.get("project_path", "")) \
                .with_request_id(request_data.get("request_id", "")) \
                .with_source(request_data.get("source", "web")) \
                .with_intent(request_data.get("intent", "")) \
                .with_governance_session_id(request_data.get("governance_session_id", "")) \
                .with_evolution_request_id(request_data.get("evolution_request_id", "")) \
                .with_runtime_id(request_data.get("runtime_id", "")) \
                .with_evidence(**(request_data.get("evidence", {}))) \
                .with_correlation_data(**(request_data.get("correlation", {}))) \
                .with_metadata(**(request_data.get("metadata", {}))) \
                .build()
            
            lifecycle = self._service.orchestrate_web_request(request)
            return self._success_response(lifecycle)
        
        except ValueError as e:
            return self._error_response(str(e), 400)
    
    # =========================================================================
    # Lifecycle Retrieval
    # =========================================================================
    
    def get_lifecycle(self, execution_id: str) -> Dict[str, Any]:
        """Get lifecycle by execution ID."""
        try:
            lifecycle = self._service.from_dict({"execution_id": execution_id})
            return self._success_response(lifecycle)
        
        except Exception as e:
            return self._error_response(f"Lifecycle not found: {str(e)}", 404)
    
    def get_lifecycle_state(self, execution_id: str) -> Dict[str, Any]:
        """Get current lifecycle state."""
        result = self.get_lifecycle(execution_id)
        if result.get("error"):
            return result
        
        return {
            "execution_id": result.get("execution_id"),
            "stage": result.get("stage"),
            "phase": result.get("phase"),
            "status": result.get("status"),
            "is_terminal": result.get("is_terminal"),
            "allowed_next_stages": result.get("allowed_next_stages", []),
        }
    
    # =========================================================================
    # Stage Transitions
    # =========================================================================
    
    def transition_stage(self, execution_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transition lifecycle to a new stage."""
        try:
            lifecycle = self._service.from_dict({"execution_id": execution_id})
            
            target_stage = LifecycleSubstage.from_string(request_data.get("stage", ""))
            reason = request_data.get("reason", "")
            
            request = TransitionRequestBuilder() \
                .with_execution_id(execution_id) \
                .with_task_id(request_data.get("task_id", "")) \
                .with_target_stage(target_stage) \
                .with_reason(reason) \
                .build()
            
            lifecycle = self._service.transition_stage(lifecycle, request)
            return self._success_response(lifecycle)
        
        except ValueError as e:
            return self._error_response(str(e), 400)
    
    def advance_stage(self, execution_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Advance to the next stage."""
        try:
            lifecycle = self._service.from_dict({"execution_id": execution_id})
            reason = request_data.get("reason", "Advancing to next stage")
            
            lifecycle = self._service.advance_to_next_stage(lifecycle, reason)
            return self._success_response(lifecycle)
        
        except ValueError as e:
            return self._error_response(str(e), 400)
    
    # =========================================================================
    # Recovery
    # =========================================================================
    
    def trigger_recovery(self, execution_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger recovery for a failed lifecycle."""
        try:
            lifecycle = self._service.from_dict({"execution_id": execution_id})
            
            request = RecoveryRequestBuilder() \
                .with_execution_id(execution_id) \
                .with_task_id(request_data.get("task_id", "")) \
                .with_failure_kind(request_data.get("failure_kind", "")) \
                .with_failure_reason(request_data.get("failure_reason", "")) \
                .with_failure_code(request_data.get("failure_code", "")) \
                .build()
            
            lifecycle = self._service.trigger_recovery(lifecycle, request)
            return self._success_response(lifecycle)
        
        except ValueError as e:
            return self._error_response(str(e), 400)
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate_lifecycle(self, execution_id: str) -> Dict[str, Any]:
        """Validate a lifecycle state."""
        try:
            lifecycle = self._service.from_dict({"execution_id": execution_id})
            errors = self._service.validate_lifecycle(lifecycle)
            
            return {
                "execution_id": execution_id,
                "is_valid": not errors,
                "validation_errors": errors,
            }
        
        except Exception as e:
            return self._error_response(f"Validation failed: {str(e)}", 400)
    
    def validate_transition(self, execution_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a proposed transition."""
        try:
            lifecycle = self._service.from_dict({"execution_id": execution_id})
            target_stage = LifecycleSubstage.from_string(request_data.get("stage", ""))
            
            error = self._service.validate_transition(lifecycle, target_stage)
            
            return {
                "execution_id": execution_id,
                "from_stage": lifecycle.substage.value,
                "to_stage": target_stage.value,
                "is_valid": error is None,
                "error": error,
            }
        
        except ValueError as e:
            return self._error_response(str(e), 400)
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _success_response(self, lifecycle: LifecycleRoot) -> Dict[str, Any]:
        """Build a success response from lifecycle."""
        return {
            "success": True,
            **lifecycle.to_dict(),
        }
    
    def _error_response(self, message: str, status_code: int) -> Dict[str, Any]:
        """Build an error response."""
        return {
            "success": False,
            "error": message,
            "status_code": status_code,
        }


__all__ = ["LifecycleHandler"]