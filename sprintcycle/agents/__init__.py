"""
SprintCycle Agents 包
包含各种专用 Agent 实现
"""

from .base import BaseAgent, AgentCapability
from .types import (
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
    logger.warning(f"SelfEvolutionAgent import failed: {e}")
    SelfEvolutionAgent = None
    EvolutionPhase = None
    EvolutionMode = None
    EvolutionSnapshot = None
    EvolutionResult = None
    _self_evolution_available = False

__all__ = [
    # Base
    "BaseAgent",
    "AgentCapability",
    
    # Types
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
