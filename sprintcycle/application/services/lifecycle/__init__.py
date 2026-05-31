"""Lifecycle application services.

This module provides the unified LifecycleService that consolidates:
- LifecycleRootService functionality
- WebLifecycleOrchestrationService functionality

**Design Principles:**
- Single entry point for all lifecycle operations
- Follows hexagonal architecture (ports and adapters)
- Stateless service with dependency injection
- Uses request data classes to avoid parameter explosion
"""

from .lifecycle_service import LifecycleService


__all__ = ["LifecycleService"]