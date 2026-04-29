"""
SprintCycle Agents 包
包含各种专用 Agent 实现
"""

from .base import BaseAgent, AgentCapability, AgentConfig
from .base import (
    VerificationType,
    VerificationSeverity,
    VerificationResult,
    PageVerificationReport
)
from .ui_verify_agent import UIVerifyAgent, create_ui_verify_agent, quick_verify
from .playwright_integration import PlaywrightClient, AccessibilityNode
from .executor import ConcurrentExecutor, PriorityTask, TaskPriority

# SelfEvolutionAgent (v0.8 新增)
try:
    from .self_evolution_agent import (
        SelfEvolutionAgent,
        EvolutionPhase,
        EvolutionMode,
        EvolutionSnapshot,
        EvolutionResult
    )
    _self_evolution_available = True
except ImportError as e:
    import logging
    logging.warning(f"SelfEvolutionAgent import failed: {e}")
    SelfEvolutionAgent = None
    EvolutionPhase = None
    EvolutionMode = None
    EvolutionSnapshot = None
    EvolutionResult = None
    _self_evolution_available = False

# Backward compatibility: re-export from types.py location
# (types.py has been merged into base.py)
try:
    from .base import (
        VerificationType as _VerificationType,
        VerificationSeverity as _VerificationSeverity,
        VerificationResult as _VerificationResult,
        PageVerificationReport as _PageVerificationReport,
    )
    # Alias for old import path
    VerificationType = _VerificationType
    VerificationSeverity = _VerificationSeverity
    VerificationResult = _VerificationResult
    PageVerificationReport = _PageVerificationReport
except ImportError:
    pass

__all__ = [
    # Base
    "BaseAgent",
    "AgentCapability",
    "AgentConfig",
    
    # Types (verification)
    "VerificationType",
    "VerificationSeverity",
    "VerificationResult",
    "PageVerificationReport",
    
    # UI Verify Agent
    "UIVerifyAgent",
    "create_ui_verify_agent",
    "quick_verify",
    
    # Playwright Client
    "PlaywrightClient",
    "AccessibilityNode",
    
    # Executor
    "ConcurrentExecutor",
    "PriorityTask",
    "TaskPriority",
    
    # SelfEvolutionAgent (v0.8)
    "SelfEvolutionAgent",
    "EvolutionPhase",
    "EvolutionMode",
    "EvolutionSnapshot",
    "EvolutionResult"
]
