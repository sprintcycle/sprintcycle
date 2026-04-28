"""StateManager 单元测试"""

import pytest
import threading
import time
from sprintcycle.state_manager import (
    StateManager, StateScope, StateEvent, StateEventType,
    get_state_manager, get_state, set_state
)


class TestStateManager:
    """状态管理器测试"""
    
    def setup_method(self):
        """每个测试前重置状态"""
        sm = get_state_manager()
        sm.reset()
    
    def test_singleton(self):
        """测试单例模式"""
        sm1 = StateManager()
        sm2 = StateManager()
        assert sm1 is sm2
    
    def test_get_set(self):
        """测试基本 get/set"""
        sm = get_state_manager()
        
        # 设置值
        sm.set(StateScope.GLOBAL, "test_key", "test_value")
        
        # 获取值
        assert sm.get(StateScope.GLOBAL, "test_key") == "test_value"
        
        # 获取默认值
        assert sm.get(StateScope.GLOBAL, "nonexistent", "default") == "default"
    
    def test_delete(self):
        """测试删除"""
        sm = get_state_manager()
        
        sm.set(StateScope.GLOBAL, "delete_key", "value")
        assert sm.get(StateScope.GLOBAL, "delete_key") == "value"
        
        sm.delete(StateScope.GLOBAL, "delete_key")
        assert sm.get(StateScope.GLOBAL, "delete_key") is None
    
    def test_history(self):
        """测试历史记录"""
        sm = get_state_manager()
        
        sm.set(StateScope.GLOBAL, "history_key", "v1")
        sm.set(StateScope.GLOBAL, "history_key", "v2")
        
        history = sm.get_history(StateScope.GLOBAL)
        assert len(history) >= 2
    
    def test_version(self):
        """测试版本号"""
        sm = get_state_manager()
        
        initial_version = sm.get_version(StateScope.GLOBAL)
        sm.set(StateScope.GLOBAL, "version_key", "value")
        new_version = sm.get_version(StateScope.GLOBAL)
        
        assert new_version > initial_version
    
    def test_event_bus(self):
        """测试事件总线"""
        sm = get_state_manager()
        events = []
        
        def callback(event):
            events.append(event)
        
        sm.event_bus.subscribe("test:*", callback)
        sm.set(StateScope.GLOBAL, "test:event", "value")
        
        assert len(events) > 0
    
    def test_watch(self):
        """测试状态监听"""
        sm = get_state_manager()
        changes = []
        
        # 使用带两个参数的回调
        def on_change(new_val, old_val):
            changes.append((new_val, old_val))
        
        unwatch = sm.watch(StateScope.GLOBAL, "watch_key", on_change)
        
        sm.set(StateScope.GLOBAL, "watch_key", "value1")
        sm.set(StateScope.GLOBAL, "watch_key", "value2")
        
        assert len(changes) == 2
        assert changes[0] == ("value1", None)
        assert changes[1] == ("value2", "value1")
    
    def test_snapshot(self):
        """测试快照"""
        sm = get_state_manager()
        
        sm.set(StateScope.GLOBAL, "snap_key", "snap_value")
        snapshot = sm.get_snapshot(StateScope.GLOBAL)
        
        assert snapshot.scope == StateScope.GLOBAL
        assert snapshot.state["snap_key"] == "snap_value"
    
    def test_concurrent_access(self):
        """测试并发访问"""
        sm = get_state_manager()
        errors = []
        
        def writer(thread_id):
            for i in range(100):
                try:
                    sm.set(StateScope.GLOBAL, f"key_{thread_id}", i)
                except Exception as e:
                    errors.append(e)
        
        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def setup_method(self):
        sm = get_state_manager()
        sm.reset()
    
    def test_get_state(self):
        set_state(StateScope.GLOBAL, "conv_key", "conv_value")
        assert get_state(StateScope.GLOBAL, "conv_key") == "conv_value"
