"""Hook 应用层服务 - 封装 domain 层的 HookRegistry。"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, List

from sprintcycle.domain.generic.interfaces.hooks import (
    HookRegistry,
    HookDefinition,
    HookContext,
    HookResult,
    HookPhase,
    HookPolicy,
    HookHandler,
)


class HookService:
    """HookRegistry 的应用层包装服务。"""

    def __init__(self):
        self._registry = HookRegistry()

    @property
    def registry(self) -> HookRegistry:
        """获取底层 HookRegistry 实例。"""
        return self._registry

    def register_hook(self, hook: HookDefinition) -> None:
        """注册钩子定义。"""
        self._registry.register(hook)

    def register_event_handler(self, event_name: str, handler: Callable[..., Any]) -> None:
        """注册事件处理器。"""
        self._registry.register_event_handler(event_name, handler)

    def emit(self, *, domain: str, action: str, phase: HookPhase, context: HookContext) -> List[HookResult]:
        """触发钩子事件。"""
        return self._registry.emit(domain=domain, action=action, phase=phase, context=context)

    def emit_domain_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """触发领域事件。"""
        self._registry.emit_domain_event(event_name, payload)

    def matching(self, *, domain: str, action: str, phase: HookPhase) -> List[HookDefinition]:
        """获取匹配的钩子。"""
        return list(self._registry.matching(domain=domain, action=action, phase=phase))
