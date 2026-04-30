"""
ErrorRouter - 分层错误路由

实现三层错误处理路由：
- Level 1: StaticAnalyzer (0.1s, 免费)
- Level 2: PatternMatcher (0.01s, 免费)
- Level 3: LLM BugAnalyzer (10-30s, LLM)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RoutingLevel(Enum):
    LEVEL_1_STATIC = "level_1_static"
    LEVEL_2_PATTERN = "level_2_pattern"
    LEVEL_3_LLM = "level_3_llm"
    UNKNOWN = "unknown"


@dataclass
class RoutingContext:
    error_log: str
    file_paths: List[str] = field(default_factory=list)
    project_path: str = "."
    language: str = "python"
    use_cache: bool = True
    max_level: RoutingLevel = RoutingLevel.LEVEL_3_LLM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingResult:
    level: RoutingLevel
    success: bool
    fix_suggestion: Optional[str] = None
    explanation: str = ""
    confidence: float = 0.0
    duration: float = 0.0
    pattern_match: Any = None
    static_results: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def cost(self) -> float:
        costs = {RoutingLevel.LEVEL_1_STATIC: 0.0, RoutingLevel.LEVEL_2_PATTERN: 0.0, RoutingLevel.LEVEL_3_LLM: 0.5}
        return costs.get(self.level, 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "success": self.success,
            "fix_suggestion": self.fix_suggestion,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "duration": self.duration,
            "cost": self.cost,
            "metadata": self.metadata,
        }


class ErrorRouter:
    """分层错误路由器"""
    
    def __init__(self, knowledge_base=None, static_analyzer=None, cache=None, llm_client=None):
        self._knowledge_base = knowledge_base
        self._static_analyzer = static_analyzer
        self._cache = cache
        self._llm_client = llm_client
        self._stats = {"level_1_count": 0, "level_2_count": 0, "level_3_count": 0, "total_duration": 0.0}
    
    @property
    def knowledge_base(self):
        if self._knowledge_base is None:
            from .error_knowledge import get_error_knowledge_base
            self._knowledge_base = get_error_knowledge_base()
        return self._knowledge_base
    
    @property
    def static_analyzer(self):
        if self._static_analyzer is None:
            try:
                from .static_analyzer import StaticAnalyzer
                self._static_analyzer = StaticAnalyzer(".")
            except ImportError:
                logger.warning("StaticAnalyzer not available")
        return self._static_analyzer
    
    async def route(self, error_log: str, context: Optional[RoutingContext] = None) -> RoutingResult:
        start_time = time.time()
        if context is None:
            context = RoutingContext(error_log=error_log)
        else:
            context.error_log = error_log
        
        # Level 1: Static Analysis
        if context.max_level.value in ["level_1_static", "level_2_pattern", "level_3_llm"]:
            result = await self._route_level_1(context)
            if result.success:
                result.duration = time.time() - start_time
                return result
        
        # Level 2: Pattern Matching
        if context.max_level.value in ['level_2_pattern', 'level_3_llm']:
            result = await self._route_level_2(context)
            if result.success:
                result.duration = time.time() - start_time
                return result
        
        # Level 3: Deep Analysis
        if context.max_level.value in ['level_3_llm']:
            result = await self._route_level_3(context)
            result.duration = time.time() - start_time
            return result
        
        return RoutingResult(level=RoutingLevel.UNKNOWN, success=False, explanation="Unable to handle error", duration=time.time() - start_time)
    
    async def _route_level_1(self, context: RoutingContext) -> RoutingResult:
        logger.debug("Level 1: Static Analysis")
        self._stats["level_1_count"] += 1
        if not self.static_analyzer:
            return RoutingResult(level=RoutingLevel.LEVEL_1_STATIC, success=False, explanation="Analyzer not available")
        try:
            results = await asyncio.wait_for(self.static_analyzer.analyze_python(context.file_paths or None), timeout=5.0)
            if results:
                errors = [r for r in results if r.severity == "error"]
                return RoutingResult(
                    level=RoutingLevel.LEVEL_1_STATIC,
                    success=True,
                    explanation=f"Static analysis found {len(errors)} errors",
                    confidence=0.9,
                    static_results=results,
                )
            return RoutingResult(level=RoutingLevel.LEVEL_1_STATIC, success=False, explanation="No issues found")
        except asyncio.TimeoutError:
            return RoutingResult(level=RoutingLevel.LEVEL_1_STATIC, success=False, explanation="Analysis timeout")
        except Exception as e:
            return RoutingResult(level=RoutingLevel.LEVEL_1_STATIC, success=False, explanation=f"Analysis failed: {e}")
    
    async def _route_level_2(self, context: RoutingContext) -> RoutingResult:
        logger.debug("Level 2: Pattern Matching")
        self._stats["level_2_count"] += 1
        try:
            match = self.knowledge_base.match(context.error_log)
            if match and match.confidence >= 0.3:
                return RoutingResult(
                    level=RoutingLevel.LEVEL_2_PATTERN,
                    success=True,
                    fix_suggestion=match.suggested_fix,
                    explanation=f"Matched {match.pattern.error_type}: {match.pattern.root_cause}",
                    confidence=match.confidence,
                    pattern_match=match,
                    metadata={"pattern_id": match.pattern.pattern_id},
                )
            return RoutingResult(level=RoutingLevel.LEVEL_2_PATTERN, success=False, explanation="No pattern matched")
        except Exception as e:
            return RoutingResult(level=RoutingLevel.LEVEL_2_PATTERN, success=False, explanation=f"Matching failed: {e}")
    
    async def _route_level_3(self, context: RoutingContext) -> RoutingResult:
        logger.info("Level 3: Deep LLM Analysis")
        self._stats["level_3_count"] += 1
        if not self._llm_client:
            return RoutingResult(level=RoutingLevel.LEVEL_3_LLM, success=False, explanation="LLM client not available", confidence=0.0)
        try:
            from .agents.analyzer import BugAnalyzerAgent, AnalysisRequest
            from .agents.base import AgentContext
            analyzer = BugAnalyzerAgent(llm_client=self._llm_client)
            agent_ctx = AgentContext(prd_id=context.metadata.get("prd_id", "unknown"))
            request = AnalysisRequest(error_log=context.error_log, file_paths=context.file_paths, use_llm=True)
            result = await analyzer.analyze(request)
            return RoutingResult(
                level=RoutingLevel.LEVEL_3_LLM,
                success=result.report.confidence >= 0.5,
                fix_suggestion="\n".join(result.report.suggestions) if result.report.suggestions else None,
                explanation=result.report.to_summary(),
                confidence=result.report.confidence,
            )
        except ImportError:
            return RoutingResult(level=RoutingLevel.LEVEL_3_LLM, success=False, explanation="Analyzer not available")
        except Exception as e:
            return RoutingResult(level=RoutingLevel.LEVEL_3_LLM, success=False, explanation=f"Analysis failed: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        return {**self._stats, "knowledge_base_size": len(self.knowledge_base.patterns)}


_default_router: Optional[ErrorRouter] = None


def get_error_router() -> ErrorRouter:
    global _default_router
    if _default_router is None:
        _default_router = ErrorRouter()
    return _default_router
