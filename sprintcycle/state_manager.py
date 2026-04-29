"""
SprintCycle 统一状态管理模块
解决全局状态分散、状态不一致的问题
"""

import json
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict


class StateScope(Enum):
    """状态作用域"""
    GLOBAL = "global"
    SPRINT = "sprint"
    TASK = "task"
    AGENT = "agent"
    RESOURCE = "resource"


class StateEventType(Enum):
    """状态事件类型"""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESET = "reset"


@dataclass
class StateEvent:
    """状态变更事件"""
    scope: StateScope
    key: str
    event_type: StateEventType
    old_value: Any = None
    new_value: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope": self.scope.value,
            "key": self.key,
            "event_type": self.event_type.value,
            "old_value": self._serialize(self.old_value),
            "new_value": self._serialize(self.new_value),
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @staticmethod
    def _serialize(value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        elif hasattr(value, '__dict__'):
            return str(value)
        return value


@dataclass
class StateSnapshot:
    """状态快照"""
    scope: StateScope
    state: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 0


class EventBus:
    """事件总线 - 用于状态变更事件发布订阅"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def subscribe(self, event_pattern: str, callback: Callable) -> None:
        with self._lock:
            self._subscribers[event_pattern].append(callback)
    
    def unsubscribe(self, event_pattern: str, callback: Callable) -> None:
        with self._lock:
            if event_pattern in self._subscribers:
                try:
                    self._subscribers[event_pattern].remove(callback)
                except ValueError:
                    pass
    
    def publish(self, event: StateEvent) -> None:
        with self._lock:
            for pattern, callbacks in list(self._subscribers.items()):
                if self._match_pattern(pattern, event.key):
                    for callback in callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            print(f"Event callback error: {e}")
    
    def _match_pattern(self, pattern: str, key: str) -> bool:
        if pattern == key or pattern == "*":
            return True
        if pattern.endswith('*'):
            return key.startswith(pattern[:-1])
        if pattern.startswith('*'):
            return key.endswith(pattern[1:])
        return False


class StateManager:
    """统一状态管理核心类"""
    
    _instance: Optional['StateManager'] = None
    _lock = threading.RLock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._state: Dict[StateScope, Dict[str, Any]] = {scope: {} for scope in StateScope}
        self._versions: Dict[StateScope, int] = {scope: 0 for scope in StateScope}
        self._history: Dict[StateScope, List[StateEvent]] = defaultdict(list)
        self._max_history_size = 1000
        self._event_bus = EventBus()
        self._watchers: Dict[str, Set[Callable]] = defaultdict(set)
        self._rwlock = threading.RLock()
        self._persist_path: Optional[Path] = None
    
    @property
    def event_bus(self) -> EventBus:
        return self._event_bus
    
    def set_persist_path(self, path: Path) -> None:
        self._persist_path = path
    
    def get(self, scope: StateScope, key: str, default: Any = None) -> Any:
        with self._rwlock:
            return self._state.get(scope, {}).get(key, default)
    
    def set(self, scope: StateScope, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        with self._rwlock:
            old_value = self._state.get(scope, {}).get(key)
            if scope not in self._state:
                self._state[scope] = {}
            self._state[scope][key] = value
            self._versions[scope] += 1
            
            event = StateEvent(
                scope=scope,
                key=key,
                event_type=StateEventType.CREATED if old_value is None else StateEventType.UPDATED,
                old_value=old_value,
                new_value=value,
                metadata=metadata or {}
            )
            self._history[scope].append(event)
            self._trim_history(scope)
            self._event_bus.publish(event)
            self._notify_watchers(scope, key, old_value, value)
    
    def delete(self, scope: StateScope, key: str) -> bool:
        with self._rwlock:
            if scope in self._state and key in self._state[scope]:
                old_value = self._state[scope].pop(key)
                self._versions[scope] += 1
                event = StateEvent(scope=scope, key=key, event_type=StateEventType.DELETED, old_value=old_value)
                self._history[scope].append(event)
                self._event_bus.publish(event)
                self._notify_watchers(scope, key, old_value, None)
                return True
            return False
    
    def watch(self, scope: StateScope, key: str, callback: Callable[[Any, Any], None]) -> Callable:
        """监听状态变更，callback(new_value, old_value)"""
        pattern = f"{scope.value}:{key}"
        
        # 直接使用回调，不做包装
        self._watchers[pattern].add(callback)
        self._event_bus.subscribe(pattern, callback)
        
        def unwatch():
            self._watchers[pattern].discard(callback)
            self._event_bus.unsubscribe(pattern, callback)
        
        return unwatch
    
    def get_all(self, scope: StateScope) -> Dict[str, Any]:
        with self._rwlock:
            return dict(self._state.get(scope, {}))
    
    def get_snapshot(self, scope: StateScope) -> StateSnapshot:
        with self._rwlock:
            return StateSnapshot(scope=scope, state=dict(self._state.get(scope, {})), version=self._versions.get(scope, 0))
    
    def get_history(self, scope: StateScope, limit: int = 100) -> List[StateEvent]:
        with self._rwlock:
            return list(self._history.get(scope, [])[-limit:])
    
    def get_version(self, scope: StateScope) -> int:
        return self._versions.get(scope, 0)
    
    def reset(self, scope: Optional[StateScope] = None) -> None:
        with self._rwlock:
            if scope:
                self._state[scope] = {}
                self._versions[scope] += 1
            else:
                for s in StateScope:
                    self._state[s] = {}
                    self._versions[s] += 1
    
    def persist(self, path: Optional[Path] = None) -> None:
        path = path or self._persist_path
        if not path:
            raise ValueError("No persist path specified")
        with self._rwlock:
            data = {
                "state": {scope.value: state for scope, state in self._state.items()},
                "versions": {scope.value: v for scope, v in self._versions.items()},
                "timestamp": datetime.now().isoformat()
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self, path: Optional[Path] = None) -> None:
        path = path or self._persist_path
        if not path or not path.exists():
            return
        with self._rwlock:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._state = {StateScope(scope): state for scope, state in data.get("state", {}).items()}
            self._versions = {StateScope(scope): v for scope, v in data.get("versions", {}).items()}
    
    def _notify_watchers(self, scope: StateScope, key: str, old_value: Any, new_value: Any) -> None:
        patterns = [f"{scope.value}:{key}", f"{scope.value}:*", "*"]
        for pattern in patterns:
            for callback in list(self._watchers.get(pattern, set())):
                try:
                    callback(new_value, old_value)
                except Exception as e:
                    print(f"Watcher callback error: {e}")
    
    def _trim_history(self, scope: StateScope) -> None:
        if len(self._history[scope]) > self._max_history_size:
            self._history[scope] = self._history[scope][-self._max_history_size:]
    
    def __repr__(self) -> str:
        return f"StateManager(state_keys={sum(len(s) for s in self._state.values())})"


def get_state_manager() -> StateManager:
    return StateManager()


def get_state(scope: StateScope, key: str, default: Any = None) -> Any:
    return get_state_manager().get(scope, key, default)


def set_state(scope: StateScope, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
    get_state_manager().set(scope, key, value, metadata)
