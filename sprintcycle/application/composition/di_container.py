"""Dependency injection container for SprintCycle application.

This module provides centralized dependency injection using dependency-injector library,
following hexagonal architecture principles.

**Usage:**
```python
from sprintcycle.application.composition.di_container import container, get_container

# Get services
lifecycle_service = container.lifecycle_service()
cache = container.cache_backend()
```
"""

from __future__ import annotations

from typing import Any, Optional


# =============================================================================
# Container Singleton Instance
# =============================================================================

_container_instance: Optional["Container"] = None


def get_container() -> "Container":
    """Get the singleton container instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = Container()
    return _container_instance


def create_container(project_path: str = ".") -> "Container":
    """Create and initialize a new container instance."""
    global _container_instance
    _container_instance = Container(project_path=project_path)
    return _container_instance


def initialize_http_infrastructure(project_path: str) -> None:
    """Initialize HTTP layer infrastructure."""
    create_container(project_path=project_path)


# =============================================================================
# Container Class (compatibility wrapper)
# =============================================================================

class Container:
    """
    Dependency injection container for SprintCycle (compatibility wrapper).

    This container provides a simple facade over the actual dependency resolution.
    For most services, we use lazy loading and factory patterns.
    """

    def __init__(self, project_path: str = "."):
        self._project_path = project_path
        self._cache = {}

    def _resolve(self, key: str, factory: callable, *args, **kwargs):
        """Lazy resolve a service."""
        if key not in self._cache:
            self._cache[key] = factory(*args, **kwargs)
        return self._cache[key]

    @property
    def infrastructure(self):
        """Infrastructure services (compatibility)."""
        return self

    @property
    def governance(self):
        """Governance services (compatibility)."""
        return self

    @property
    def observability(self):
        """Observability services (compatibility)."""
        return self

    # =====================================================================
    # Infrastructure services
    # =====================================================================

    def cache_backend(self, runtime: Optional[Any] = None, project_path: str = ".") -> Any:
        """Get the cache backend."""
        from sprintcycle.infrastructure.adapters.generic.cache.factory import (
            create_cache_backend,
        )
        key = f"cache_backend_{project_path}"
        if key not in self._cache:
            self._cache[key] = create_cache_backend(
                runtime=runtime,
                project_path=project_path or self._project_path
            )
        return self._cache[key]

    def state_store(self, store_dir: Optional[str] = None) -> Any:
        """Get the state store."""
        from sprintcycle.infrastructure.adapters.core.execution.state_store import (
            create_state_store,
        )
        key = "state_store"
        if key not in self._cache:
            self._cache[key] = create_state_store(store_dir=store_dir)
        return self._cache[key]

    # =====================================================================
    # Governance services
    # =====================================================================

    def archguard_adapter(self) -> Any:
        """Get the ArchGuard adapter."""
        from sprintcycle.infrastructure.adapters.core.governance.arch_guard.archon_adapter import (
            ArchonAdapter,
        )
        key = "archguard_adapter"
        if key not in self._cache:
            self._cache[key] = ArchonAdapter()
        return self._cache[key]

    def grimp_adapter(self) -> Any:
        """Get the Grimp adapter."""
        from sprintcycle.infrastructure.adapters.core.governance.arch_guard.grimp_adapter import (
            GrimpAdapter,
        )
        key = "grimp_adapter"
        if key not in self._cache:
            self._cache[key] = GrimpAdapter()
        return self._cache[key]

    def import_linter_adapter(self) -> Any:
        """Get the Import Linter adapter."""
        from sprintcycle.infrastructure.adapters.core.governance.arch_guard.import_linter import (
            ImportLinterAdapter,
        )
        key = "import_linter_adapter"
        if key not in self._cache:
            self._cache[key] = ImportLinterAdapter()
        return self._cache[key]

    def ruff_adapter(self) -> Any:
        """Get the Ruff adapter."""
        from sprintcycle.infrastructure.adapters.core.governance.arch_guard.ruff_adapter import (
            RuffAdapter,
        )
        key = "ruff_adapter"
        if key not in self._cache:
            self._cache[key] = RuffAdapter()
        return self._cache[key]

    def typecheck_adapter(self) -> Any:
        """Get the TypeCheck adapter."""
        from sprintcycle.infrastructure.adapters.core.governance.arch_guard.typecheck_adapter import (
            TypecheckAdapter,
        )
        key = "typecheck_adapter"
        if key not in self._cache:
            self._cache[key] = TypecheckAdapter()
        return self._cache[key]

    # =====================================================================
    # Runtime config services
    # =====================================================================

    def runtime_config(self, project_path: Optional[str] = None) -> Any:
        """Get the runtime config."""
        from sprintcycle.infrastructure.adapters.generic.config.runtime_config import (
            get_runtime_config,
        )
        key = "runtime_config"
        if key not in self._cache:
            self._cache[key] = get_runtime_config(
                project_path=project_path or self._project_path
            )
        return self._cache[key]

    def rate_limit_adapter(self) -> Any:
        """Get the rate limit adapter."""
        from sprintcycle.infrastructure.adapters.generic.config.rate_limit import (
            RateLimitAdapter,
        )
        key = "rate_limit_adapter"
        if key not in self._cache:
            self._cache[key] = RateLimitAdapter()
        return self._cache[key]

    def audit_adapter(self) -> Any:
        """Get the audit adapter."""
        from sprintcycle.infrastructure.adapters.generic.integrations.audit import (
            AuditAdapter,
        )
        key = "audit_adapter"
        if key not in self._cache:
            self._cache[key] = AuditAdapter()
        return self._cache[key]

    # =====================================================================
    # Observability services
    # =====================================================================

    def observability_facade(self) -> Any:
        """Get the observability facade."""
        from sprintcycle.infrastructure.adapters.generic.observability.facade import (
            ObservabilityFacade,
        )
        key = "observability_facade"
        if key not in self._cache:
            self._cache[key] = ObservabilityFacade()
        return self._cache[key]

    def diagnostic_adapter(self) -> Any:
        """Get the diagnostic adapter."""
        from sprintcycle.infrastructure.adapters.generic.observability.diagnostics.adapter import (
            DiagnosticAdapter,
        )
        key = "diagnostic_adapter"
        if key not in self._cache:
            self._cache[key] = DiagnosticAdapter()
        return self._cache[key]

    # =====================================================================
    # Lifecycle services
    # =====================================================================

    def lifecycle_state_machine(self) -> Any:
        """Get the lifecycle state machine."""
        from sprintcycle.domain.core.lifecycle import get_lifecycle_state_machine
        key = "lifecycle_state_machine"
        if key not in self._cache:
            self._cache[key] = get_lifecycle_state_machine()
        return self._cache[key]

    def lifecycle_service(self) -> Any:
        """Get the lifecycle service."""
        from sprintcycle.application.services.lifecycle import LifecycleService
        key = "lifecycle_service"
        if key not in self._cache:
            self._cache[key] = LifecycleService(
                state_machine=self.lifecycle_state_machine()
            )
        return self._cache[key]


# =============================================================================
# Global Container Instance
# =============================================================================

container = get_container()


# =============================================================================
# Backward-compatible module-level providers
# =============================================================================

def lifecycle_service() -> Any:
    """Get the lifecycle service (backward compatible)."""
    return container.lifecycle_service()


def lifecycle_state_machine() -> Any:
    """Get the lifecycle state machine (backward compatible)."""
    return container.lifecycle_state_machine()


# =============================================================================
# Module Exports
# =============================================================================

SprintCycleContainer = Container

__all__ = [
    "Container",
    "SprintCycleContainer",
    "get_container",
    "create_container",
    "container",
    "lifecycle_service",
    "lifecycle_state_machine",
    "initialize_http_infrastructure",
]
