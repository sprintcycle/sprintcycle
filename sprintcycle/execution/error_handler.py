"""
ErrorHandler - 统一错误处理入口

整合所有错误处理组件，提供统一的错误处理接口。
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    error_log: str
    project_path: str = "."
    file_paths: List[str] = field(default_factory=list)
    language: str = "python"
    prd_id: str = ""
    sprint_name: str = ""
    task_name: str = ""
    max_level: str = "level_3"
    enable_rollback: bool = True
    enable_cache: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixResult:
    success: bool
    error_log: str
    fix_suggestion: Optional[str] = None
    explanation: str = ""
    level: str = "unknown"
    confidence: float = 0.0
    duration: float = 0.0
    backup_id: Optional[str] = None
    rollback_performed: bool = False
    events_emitted: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success, "error_log": self.error_log[:200], "fix_suggestion": self.fix_suggestion,
            "explanation": self.explanation, "level": self.level, "confidence": self.confidence,
            "duration": self.duration, "backup_id": self.backup_id, "rollback_performed": self.rollback_performed,
            "events_emitted": self.events_emitted, "metadata": self.metadata,
        }


class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, knowledge_base=None, router=None, event_bus=None, rollback_manager=None,
                 cache=None, llm_client=None, enable_rollback=True, enable_cache=True):
        self._knowledge_base = knowledge_base
        self._router = router
        self._event_bus = event_bus
        self._rollback_manager = rollback_manager
        self._cache = cache
        self._llm_client = llm_client
        self.enable_rollback = enable_rollback
        self.enable_cache = enable_cache
        self._stats = {"total_handled": 0, "successful": 0, "failed": 0, "total_duration": 0.0,
                       "level_1_count": 0, "level_2_count": 0, "level_3_count": 0, "rollback_count": 0}
    
    @property
    def knowledge_base(self):
        if self._knowledge_base is None:
            from .error_knowledge import get_error_knowledge_base
            self._knowledge_base = get_error_knowledge_base()
        return self._knowledge_base
    
    @property
    def router(self):
        if self._router is None:
            from .error_router import get_error_router
            self._router = get_error_router()
            self._router._knowledge_base = self.knowledge_base
            if self._llm_client:
                self._router._llm_client = self._llm_client
        return self._router
    
    @property
    def event_bus(self):
        if self._event_bus is None:
            from .events import get_event_bus
            self._event_bus = get_event_bus()
        return self._event_bus
    
    @property
    def rollback_manager(self):
        if self._rollback_manager is None:
            from .rollback import get_rollback_manager
            self._rollback_manager = get_rollback_manager()
        return self._rollback_manager
    
    async def handle(self, context: ErrorContext) -> FixResult:
        start_time = time.time()
        events_emitted: List[str] = []
        backup_id: Optional[str] = None
        
        logger.info(f"ErrorHandler processing: {context.error_log[:100]}...")
        self._stats["total_handled"] += 1
        
        # Emit ERROR_DETECTED
        await self._emit_event("ERROR_DETECTED", {"error_log": context.error_log, "project_path": context.project_path})
        events_emitted.append("ERROR_DETECTED")
        
        try:
            # Backup files if enabled
            if self.enable_rollback and context.file_paths:
                backup_id = await self._backup_files(context.file_paths, context)
                if backup_id:
                    context.metadata["backup_id"] = backup_id
            
            # Route error
            routing_result = await self._route_error(context)
            
            # Emit analysis complete
            await self._emit_event("ERROR_ANALYSIS_COMPLETE", {
                "success": routing_result.success, "level": routing_result.level.value if hasattr(routing_result.level, 'value') else str(routing_result.level),
                "confidence": routing_result.confidence,
            })
            events_emitted.append("ERROR_ANALYSIS_COMPLETE")
            
            # Record to knowledge base
            if routing_result.success and routing_result.pattern_match:
                pattern = routing_result.pattern_match.pattern
                self.knowledge_base.record_fix(
                    error_log=context.error_log, pattern_id=pattern.pattern_id,
                    fix_applied=routing_result.fix_suggestion or "", success=routing_result.success,
                    duration=time.time() - start_time,
                    metadata={"level": routing_result.level.value, "confidence": routing_result.confidence},
                )
            
            duration = time.time() - start_time
            self._stats["total_duration"] += duration
            
            level_key = f"{routing_result.level.value}_count"
            if level_key in self._stats:
                self._stats[level_key] += 1
            
            if routing_result.success:
                self._stats["successful"] += 1
            else:
                self._stats["failed"] += 1
            
            return FixResult(
                success=routing_result.success, error_log=context.error_log,
                fix_suggestion=routing_result.fix_suggestion, explanation=routing_result.explanation,
                level=routing_result.level.value if hasattr(routing_result.level, 'value') else str(routing_result.level),
                confidence=routing_result.confidence, duration=duration, backup_id=backup_id,
                rollback_performed=False, events_emitted=events_emitted,
                metadata={"routing_metadata": routing_result.metadata, "context_metadata": context.metadata},
            )
        except Exception as e:
            logger.error(f"ErrorHandler failed: {e}")
            self._stats["failed"] += 1
            return FixResult(success=False, error_log=context.error_log, explanation=f"Processing exception: {e}",
                            duration=time.time() - start_time, backup_id=backup_id, rollback_performed=False, events_emitted=events_emitted)
    
    async def handle_batch(self, contexts: List[ErrorContext]) -> List[FixResult]:
        return [await self.handle(ctx) for ctx in contexts]
    
    async def rollback(self, backup_id: str) -> bool:
        try:
            result = await self.rollback_manager.rollback(backup_id)
            await self._emit_event("ROLLBACK_COMPLETE", {"backup_id": backup_id, "success": result.success})
            self._stats["rollback_count"] += 1
            return result.success
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    async def _route_error(self, context: ErrorContext):
        from .error_router import RoutingContext, RoutingLevel
        level_map = {"level_1": RoutingLevel.LEVEL_1_STATIC, "level_2": RoutingLevel.LEVEL_2_PATTERN, "level_3": RoutingLevel.LEVEL_3_LLM}
        max_level = level_map.get(context.max_level, RoutingLevel.LEVEL_3_LLM)
        routing_context = RoutingContext(
            error_log=context.error_log, file_paths=context.file_paths, project_path=context.project_path,
            language=context.language, use_cache=self.enable_cache, max_level=max_level,
            metadata={"prd_id": context.prd_id, "sprint_name": context.sprint_name, "task_name": context.task_name},
        )
        return await self.router.route(context.error_log, routing_context)
    
    async def _backup_files(self, file_paths: List[str], context: ErrorContext) -> Optional[str]:
        try:
            first_backup_id = None
            for file_path in file_paths:
                record = await self.rollback_manager.backup(
                    file_path=file_path, description=f"ErrorHandler backup: {context.error_log[:50]}",
                    operation="pre_fix", prd_id=context.prd_id, sprint_name=context.sprint_name, task_name=context.task_name,
                )
                if record and first_backup_id is None:
                    first_backup_id = record.backup_id
            if first_backup_id:
                await self._emit_event("ROLLBACK_STARTED", {"backup_id": first_backup_id, "files": file_paths})
            return first_backup_id
        except Exception as e:
            logger.warning(f"File backup failed: {e}")
            return None
    
    async def _emit_event(self, event_type_name: str, data: Dict[str, Any]) -> None:
        try:
            from .events import Event, EventType
            event_type = EventType[event_type_name]
            await self.event_bus.emit(Event(type=event_type, data=data))
        except Exception as e:
            logger.debug(f"Event emission failed: {e}")
    
    def get_patterns(self) -> List[Any]:
        return list(self.knowledge_base.patterns.values())
    
    def add_pattern(self, pattern: Any) -> str:
        return self.knowledge_base.add_pattern(pattern)
    
    def match_error(self, error_log: str) -> Optional[Any]:
        return self.knowledge_base.match(error_log)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats, "knowledge_base_size": len(self.knowledge_base.patterns),
            "success_rate": self._stats["successful"] / self._stats["total_handled"] if self._stats["total_handled"] > 0 else 0,
            "avg_duration": self._stats["total_duration"] / self._stats["total_handled"] if self._stats["total_handled"] > 0 else 0,
        }
    
    def reset_statistics(self) -> None:
        self._stats = {"total_handled": 0, "successful": 0, "failed": 0, "total_duration": 0.0,
                       "level_1_count": 0, "level_2_count": 0, "level_3_count": 0, "rollback_count": 0}


_default_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    global _default_handler
    if _default_handler is None:
        _default_handler = ErrorHandler()
    return _default_handler


def reset_error_handler() -> ErrorHandler:
    global _default_handler
    _default_handler = ErrorHandler()
    return _default_handler
