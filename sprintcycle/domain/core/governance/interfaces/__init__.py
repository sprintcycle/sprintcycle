"""Domain Governance Interfaces - 治理接口协议"""

from .governance import (
    ArchitectureCheckProtocol,
    GovernanceCheckProtocol,
    GovernanceCheckResult,
    QualityGateProtocol,
)

__all__ = [
    "GovernanceCheckResult",
    "GovernanceCheckProtocol",
    "ArchitectureCheckProtocol",
    "QualityGateProtocol",
]
