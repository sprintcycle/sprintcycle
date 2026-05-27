"""Public execution API routes.

HTTP endpoints for external execution API.
"""

from __future__ import annotations


from fastapi import APIRouter, Request

from sprintcycle.interfaces.http.handlers.execution import ExecutionHandler
from sprintcycle.interfaces.http.request_context import RequestContext
from sprintcycle.application.orchestration.sprint_orchestrator import SprintOrchestrator
from sprintcycle.domain.ports.config import get_runtime_config


def build_public_execution_router(handler: ExecutionHandler, project_path: str) -> APIRouter:
    """Build public execution router.

    Args:
        handler: Execution handler instance.
        project_path: Project root path.

    Returns:
        APIRouter: Public execution routes router.
    """
    router = APIRouter(prefix="/api/v1")

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=project_path,
            client_type=request.headers.get("x-client-type", "public"),
        )

    @router.post("/plan")
    async def plan(request: Request, payload: dict) -> dict:
        """Plan an execution.

        Args:
            request: FastAPI request object.
            payload: Plan request data.

        Returns:
            dict: Plan result.
        """
        _ctx(request)
        config = get_runtime_config(project_path)
        orchestrator = SprintOrchestrator(project_path=project_path, config=config)
        result = orchestrator.plan(
            intent=payload.get("intent", ""),
            mode=payload.get("mode", "auto"),
            target=payload.get("target"),
            release_plan_yaml=payload.get("release_plan_yaml"),
            release_plan_path=payload.get("release_plan_path"),
            product=payload.get("product"),
            reference_paths=payload.get("reference_paths"),
            write_policy=payload.get("write_policy", "auto"),
        )
        return result.to_dict() if hasattr(result, "to_dict") else dict(result)

    @router.post("/run")
    async def run(request: Request, payload: dict) -> dict:
        """Run an execution.

        Args:
            request: FastAPI request object.
            payload: Run request data.

        Returns:
            dict: Run result.
        """
        _ctx(request)
        config = get_runtime_config(project_path)
        orchestrator = SprintOrchestrator(project_path=project_path, config=config)
        result = orchestrator.run(
            intent=payload.get("intent"),
            mode=payload.get("mode", "auto"),
            target=payload.get("target"),
            release_plan_yaml=payload.get("release_plan_yaml"),
            release_plan_path=payload.get("release_plan_path"),
            product=payload.get("product"),
            execution_id=payload.get("execution_id"),
            resume=payload.get("resume", False),
            reference_paths=payload.get("reference_paths"),
            write_policy=payload.get("write_policy", "auto"),
        )
        return result.to_dict() if hasattr(result, "to_dict") else dict(result)

    @router.get("/diagnose")
    async def diagnose(request: Request) -> dict:
        """Diagnose execution.

        Args:
            request: FastAPI request object.

        Returns:
            dict: Diagnosis result.
        """
        _ctx(request)
        result = handler.diagnose()
        return result

    @router.post("/status")
    async def status(request: Request, payload: dict) -> dict:
        """Get execution status.

        Args:
            request: FastAPI request object.
            payload: Status request data with execution_id.

        Returns:
            dict: Status result.
        """
        _ctx(request)
        result = handler.status(execution_id=payload.get("execution_id", ""))
        return result

    @router.post("/rollback")
    async def rollback(request: Request, payload: dict) -> dict:
        """Rollback an execution.

        Args:
            request: FastAPI request object.
            payload: Rollback request data with execution_id.

        Returns:
            dict: Rollback result.
        """
        _ctx(request)
        result = handler.rollback(execution_id=payload.get("execution_id", ""))
        return result

    @router.post("/stop")
    async def stop(request: Request, payload: dict) -> dict:
        """Stop an execution.

        Args:
            request: FastAPI request object.
            payload: Stop request data with execution_id.

        Returns:
            dict: Stop result.
        """
        _ctx(request)
        result = handler.stop_execution(execution_id=payload.get("execution_id", ""))
        return result

    return router
