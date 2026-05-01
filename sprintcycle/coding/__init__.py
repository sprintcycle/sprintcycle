"""
Coding Module - 编码引擎

v0.9.1: 拆分为多个子模块
- strategy.py: 编码策略
- result.py: 结果数据类
- engine.py: 编码引擎
"""

from .strategy import CodingStrategy, CursorStrategy, LLMStrategy, ClaudeStrategy
from .result import CodingEngineResult, CodeReviewResult, CodeFixResult
from .engine import CodingEngine, create_coding_engine
from ..config import CodingConfig, CodingLLMConfig

__all__ = [
    # Strategies
    "CodingStrategy",
    "CursorStrategy",
    "LLMStrategy",
    "ClaudeStrategy",
    # Results
    "CodingEngineResult",
    "CodeReviewResult",
    "CodeFixResult",
    # Engine
    "CodingEngine",
    "create_coding_engine",
    # Config
    "CodingConfig",
    "CodingLLMConfig",
]
