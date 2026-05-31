"""Dependency injection container for SprintCycle application.

This module provides centralized dependency injection configuration
following hexagonal architecture principles.

**Design Principles:**
- Single source of truth for dependency wiring
- Follows hexagonal architecture (ports and adapters)
- Separates domain services from infrastructure implementations
- Supports both singleton and transient scopes

**Container Structure:**
- domain_container: Domain-level dependencies
- application_container: Application service dependencies
- infrastructure_container: Infrastructure/adapter dependencies
- governance_container: Governance adapter dependencies
- observability_container: Observability dependencies
- runtime_config_container: Runtime configuration dependencies

**Usage:**
```python
from sprintcycle.application.composition.di_container import container, get_container

# Get services
lifecycle_service = container.lifecycle_service()
cache = container.infrastructure.cache_backend()
```
"""

from __future__ import annotations

from typing import Any, Callable, Optional


# =============================================================================
# Container Singleton Instance
# =============================================================================

_container_instance: Optional["SprintCycleContainer"] = None


def get_container() -> "SprintCycleContainer":
    """Get the singleton container instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = SprintCycleContainer()
    return _container_instance


def create_container(project_path: str = ".") -> "SprintCycleContainer":
    """Create and initialize a new container instance."""
    global _container_instance
    _container_instance = SprintCycleContainer(project_path=project_path)
    return _container_instance


# =============================================================================
# Override Context Manager for Testing
# =============================================================================

class OverrideContext:
    """Context manager for overriding container services during testing."""
    
    def __init__(self, provider: Callable, override_value: Any):
        self.provider = provider
        self.override_value = override_value
        self._original_value = None
    
    def __enter__(self):
        self._original_value = getattr(self.provider, '_override', None)
        setattr(self.provider, '_override', self.override_value)
        return self.override_value
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        setattr(self.provider, '_override', self._original_value)


class OverrideProvider:
    """Wrapper for service providers that supports overriding."""
    
    def __init__(self, provider: Callable):
        self._provider = provider
        self._override = None
    
    def __call__(self, *args, **kwargs):
        if self._override is not None:
            return self._override
        return self._provider(*args, **kwargs)
    
    def override(self, value: Any) -> OverrideContext:
        """Return a context manager to override this provider."""
        return OverrideContext(self, value)


# =============================================================================
# Infrastructure Sub-container
# =============================================================================

class InfrastructureContainer:
    """Container for infrastructure/adapter services."""
    
    def __init__(self, project_path: str = "."):
        self._project_path = project_path
        self._cache_backend = None
        self._state_store = None
    
    @property
    def cache_backend(self) -> OverrideProvider:
        """Get the cache backend provider."""
        def _get_cache_backend(runtime: Optional[Any] = None, project_path: str = ".") -> Any:
            nonlocal self
            if self._cache_backend is None:
                from sprintcycle.infrastructure.adapters.generic.cache.factory import (
                    create_cache_backend
                )
                self._cache_backend = create_cache_backend(
                    runtime=runtime, 
                    project_path=project_path or self._project_path
                )
            return self._cache_backend
        return OverrideProvider(_get_cache_backend)
    
    @property
    def state_store(self) -> OverrideProvider:
        """Get the state store provider."""
        def _get_state_store(store_dir: Optional[str] = None) -> Any:
            nonlocal self
            if self._state_store is None:
                from sprintcycle.infrastructure.adapters.core.execution.state_store import (
                    create_state_store
                )
                self._state_store = create_state_store(store_dir=store_dir)
            return self._state_store
        return OverrideProvider(_get_state_store)


# =============================================================================
# Governance Sub-container
# =============================================================================

class GovernanceContainer:
    """Container for governance adapter services."""
    
    def __init__(self):
        self._archguard_adapter = None
        self._grimp_adapter = None
        self._import_linter_adapter = None
        self._ruff_adapter = None
        self._typecheck_adapter = None
    
    @property
    def archguard_adapter(self) -> OverrideProvider:
        """Get the ArchGuard adapter provider."""
        def _get_archguard_adapter() -> Any:
            nonlocal self
            if self._archguard_adapter is None:
                from sprintcycle.infrastructure.adapters.core.governance.arch_guard.archon_adapter import (
                    ArchonAdapter
                )
                self._archguard_adapter = ArchonAdapter()
            return self._archguard_adapter
        return OverrideProvider(_get_archguard_adapter)
    
    @property
    def grimp_adapter(self) -> OverrideProvider:
        """Get the Grimp adapter provider."""
        def _get_grimp_adapter() -> Any:
            nonlocal self
            if self._grimp_adapter is None:
                from sprintcycle.infrastructure.adapters.core.governance.arch_guard.grimp_adapter import (
                    GrimpAdapter
                )
                self._grimp_adapter = GrimpAdapter()
            return self._grimp_adapter
        return OverrideProvider(_get_grimp_adapter)
    
    @property
    def import_linter_adapter(self) -> OverrideProvider:
        """Get the Import Linter adapter provider."""
        def _get_import_linter_adapter() -> Any:
            nonlocal self
            if self._import_linter_adapter is None:
                from sprintcycle.infrastructure.adapters.core.governance.arch_guard.import_linter import (
                    ImportLinterAdapter
                )
                self._import_linter_adapter = ImportLinterAdapter()
            return self._import_linter_adapter
        return OverrideProvider(_get_import_linter_adapter)
    
    @property
    def ruff_adapter(self) -> OverrideProvider:
        """Get the Ruff adapter provider."""
        def _get_ruff_adapter() -> Any:
            nonlocal self
            if self._ruff_adapter is None:
                from sprintcycle.infrastructure.adapters.core.governance.arch_guard.ruff_adapter import (
                    RuffAdapter
                )
                self._ruff_adapter = RuffAdapter()
            return self._ruff_adapter
        return OverrideProvider(_get_ruff_adapter)
    
    @property
    def typecheck_adapter(self) -> OverrideProvider:
        """Get the TypeCheck adapter provider."""
        def _get_typecheck_adapter() -> Any:
            nonlocal self
            if self._typecheck_adapter is None:
                from sprintcycle.infrastructure.adapters.core.governance.arch_guard.typecheck_adapter import (
                    TypecheckAdapter
                )
                self._typecheck_adapter = TypecheckAdapter()
            return self._typecheck_adapter
        return OverrideProvider(_get_typecheck_adapter)


# =============================================================================
# Runtime Config Sub-container
# =============================================================================

class RuntimeConfigContainer:
    """Container for runtime configuration services."""
    
    def __init__(self, project_path: str = "."):
        self._project_path = project_path
        self._runtime_config = None
        self._rate_limit_adapter = None
        self._audit_adapter = None
    
    @property
    def runtime_config(self) -> OverrideProvider:
        """Get the runtime config provider."""
        def _get_runtime_config(project_path: Optional[str] = None) -> Any:
            nonlocal self
            if self._runtime_config is None:
                from sprintcycle.infrastructure.adapters.generic.config.runtime_config import (
                    get_runtime_config
                )
                self._runtime_config = get_runtime_config(
                    project_path=project_path or self._project_path
                )
            return self._runtime_config
        return OverrideProvider(_get_runtime_config)
    
    @property
    def rate_limit_adapter(self) -> OverrideProvider:
        """Get the rate limit adapter provider."""
        def _get_rate_limit_adapter() -> Any:
            nonlocal self
            if self._rate_limit_adapter is None:
                from sprintcycle.infrastructure.adapters.generic.config.rate_limit import (
                    RateLimitAdapter
                )
                self._rate_limit_adapter = RateLimitAdapter()
            return self._rate_limit_adapter
        return OverrideProvider(_get_rate_limit_adapter)
    
    @property
    def audit_adapter(self) -> OverrideProvider:
        """Get the audit adapter provider."""
        def _get_audit_adapter() -> Any:
            nonlocal self
            if self._audit_adapter is None:
                from sprintcycle.infrastructure.adapters.generic.integrations.audit import (
                    AuditAdapter
                )
                self._audit_adapter = AuditAdapter()
            return self._audit_adapter
        return OverrideProvider(_get_audit_adapter)


# =============================================================================
# Observability Sub-container
# =============================================================================

class ObservabilityContainer:
    """Container for observability services."""
    
    def __init__(self):
        self._observability_facade = None
        self._diagnostic_adapter = None
    
    @property
    def observability_facade(self) -> OverrideProvider:
        """Get the observability facade provider."""
        def _get_observability_facade() -> Any:
            nonlocal self
            if self._observability_facade is None:
                from sprintcycle.infrastructure.adapters.generic.observability.facade import (
                    ObservabilityFacade
                )
                self._observability_facade = ObservabilityFacade()
            return self._observability_facade
        return OverrideProvider(_get_observability_facade)
    
    @property
    def diagnostic_adapter(self) -> OverrideProvider:
        """Get the diagnostic adapter provider."""
        def _get_diagnostic_adapter() -> Any:
            nonlocal self
            if self._diagnostic_adapter is None:
                from sprintcycle.infrastructure.adapters.generic.observability.diagnostics.adapter import (
                    DiagnosticAdapter
                )
                self._diagnostic_adapter = DiagnosticAdapter()
            return self._diagnostic_adapter
        return OverrideProvider(_get_diagnostic_adapter)


# =============================================================================
# Main Container Class
# =============================================================================

class SprintCycleContainer:
    """
    Dependency injection container for SprintCycle.
    
    Provides access to all application services and dependencies.
    
    **Usage:**
    ```python
    container = SprintCycleContainer()
    
    # Get lifecycle service
    service = container.lifecycle_service()
    
    # Get infrastructure services
    cache = container.infrastructure.cache_backend()
    
    # Get governance services
    archguard = container.governance.archguard_adapter()
    
    # Testing with override
    with container.infrastructure.cache_backend.override(MockCache()):
        # Test code
        pass
    ```
    """
    
    def __init__(self, project_path: str = "."):
        self._project_path = project_path
        self._lifecycle_state_machine = None
        self._lifecycle_service = None
        
        # Initialize sub-containers
        self._infrastructure = InfrastructureContainer(project_path=project_path)
        self._governance = GovernanceContainer()
        self._runtime_config_container = RuntimeConfigContainer(project_path=project_path)
        self._observability = ObservabilityContainer()
    
    @property
    def infrastructure(self) -> InfrastructureContainer:
        """Get the infrastructure sub-container."""
        return self._infrastructure
    
    @property
    def governance(self) -> GovernanceContainer:
        """Get the governance sub-container."""
        return self._governance
    
    @property
    def runtime_config_container(self) -> RuntimeConfigContainer:
        """Get the runtime config sub-container."""
        return self._runtime_config_container
    
    @property
    def observability(self) -> ObservabilityContainer:
        """Get the observability sub-container."""
        return self._observability
    
    @property
    def lifecycle_state_machine(self) -> OverrideProvider:
        """Get the lifecycle state machine provider."""
        def _get_state_machine() -> Any:
            nonlocal self
            if self._lifecycle_state_machine is None:
                from sprintcycle.domain.core.lifecycle import get_lifecycle_state_machine
                self._lifecycle_state_machine = get_lifecycle_state_machine()
            return self._lifecycle_state_machine
        return OverrideProvider(_get_state_machine)
    
    @property
    def lifecycle_service(self) -> OverrideProvider:
        """Get the lifecycle service provider."""
        def _get_lifecycle_service() -> Any:
            nonlocal self
            if self._lifecycle_service is None:
                from sprintcycle.application.services.lifecycle import LifecycleService
                self._lifecycle_service = LifecycleService(
                    state_machine=self._lifecycle_state_machine or self.lifecycle_state_machine()
                )
            return self._lifecycle_service
        return OverrideProvider(_get_lifecycle_service)


# =============================================================================
# Global Container Instance
# =============================================================================

container = get_container()


# =============================================================================
# Module Exports
# =============================================================================

Container = SprintCycleContainer

__all__ = [
    "SprintCycleContainer",
    "Container",
    "get_container",
    "create_container",
    "container",
    "lifecycle_service",
    "lifecycle_state_machine",
]


# =============================================================================
# Backward-compatible module-level providers
# =============================================================================

def lifecycle_service() -> Any:
    """Get the lifecycle service (backward compatible)."""
    return container.lifecycle_service()


def lifecycle_state_machine() -> Any:
    """Get the lifecycle state machine (backward compatible)."""
    return container.lifecycle_state_machine()