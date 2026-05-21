"""
Domain Errors - 错误处理领域模型

包含错误分类、路由、知识库等核心领域逻辑。
"""

from .error_knowledge import (
    ErrorKnowledgeBase,
    ErrorPattern,
    PatternMatch,
    get_error_knowledge_base,
    reset_error_knowledge_base,
)
from .error_router import (
    ErrorRouter,
    RoutingContext,
    RoutingLevel,
    RoutingResult,
    get_error_router,
)

__all__ = [
    "ErrorKnowledgeBase",
    "ErrorPattern",
    "PatternMatch",
    "get_error_knowledge_base",
    "reset_error_knowledge_base",
    "ErrorRouter",
    "RoutingLevel",
    "RoutingContext",
    "RoutingResult",
    "get_error_router",
]
