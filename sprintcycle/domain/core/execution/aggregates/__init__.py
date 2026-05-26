"""Execution subdomain aggregates.

This module provides DDD aggregates for the Execution subdomain.

**Usage:**
```python
from sprintcycle.domain.core.execution.aggregates import (
    ReleasePlanAggregate,
    SprintAggregate,
    TaskResult,
    SprintResult,
    create_release_plan_aggregate,
    create_sprint_aggregate,
)
```
"""

from .execution_aggregates import (
    TaskResult,
    SprintResult,
    SprintAggregate,
    ReleasePlanAggregate,
    create_sprint_aggregate,
    create_release_plan_aggregate,
)

__all__ = [
    "TaskResult",
    "SprintResult",
    "SprintAggregate",
    "ReleasePlanAggregate",
    "create_sprint_aggregate",
    "create_release_plan_aggregate",
]
