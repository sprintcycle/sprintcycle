"""
测试 optimizations.py v4.10 中的增强类
"""
import pytest
import sys
import os
import tempfile
import time
from pathlib import Path

# 确保 sprintcycle 在路径中
_root_path = Path("/root/sprintcycle")
if str(_root_path) not in sys.path:
    sys.path.insert(0, str(_root_path))

from sprintcycle.optimizations import (
    RollbackManager, 
    TimeoutHandler, 
    ErrorHelper,
    FileTracker,
    TaskSplitter,
    SplitConfig,
    ErrorCategory
)


class TestRollbackManagerV410:
    """测试 RollbackManager v4.10"""
    
    def test_init_v410(self, tmp_path):
        """测试 v4.10 初始化"""
        manager = RollbackManager(str(tmp_path), auto_backup=True, max_backups=5)
        assert manager.project_path == tmp_path
        assert manager.backup_dir.exists()
        assert manager.max_backups == 5
        assert manager.auto_backup_enabled == True
    
    def test_begin_transaction(self, tmp_path):
        """v4.10: 测试事务开始"""
        test_file = tmp_path / "test.py"
        test_file.write_text("original")
        
        manager = RollbackManager(str(tmp_path))
        backup_id = manager.begin_transaction("task_001", ["test.py"])
        
        assert backup_id.startswith("txn_task_001")
        assert manager._current_backup_id == backup_id
    
    def test_commit_transaction(self, tmp_path):
        """v4.10: 测试事务提交"""
        test_file = tmp_path / "test.py"
        test_file.write_text("modified")
        
        manager = RollbackManager(str(tmp_path))
        backup_id = manager.begin_transaction("task_001", ["test.py"])
        
        result = manager.commit_transaction()
        assert result["success"] == True
        assert "已提交" in result["message"]
    
    def test_rollback_transaction(self, tmp_path):
        """v4.10: 测试事务回滚"""
        test_file = tmp_path / "test.py"
        test_file.write_text("original")
        
        manager = RollbackManager(str(tmp_path))
        manager.begin_transaction("task_001", ["test.py"])
        
        # 修改文件
        test_file.write_text("modified")
        
        # 回滚
        result = manager.rollback_transaction()
        assert result["success"] == True
        assert test_file.read_text() == "original"
    
    def test_cleanup_auto(self, tmp_path):
        """v4.10: 测试自动清理"""
        test_file = tmp_path / "test.py"
        test_file.write_text("hello")
        
        manager = RollbackManager(str(tmp_path), max_backups=3)
        
        # 创建超过限制的备份
        for i in range(5):
            manager.backup_files(["test.py"])
        
        assert len(manager.backup_history) <= 3


class TestTimeoutHandlerV410:
    """测试 TimeoutHandler v4.10"""
    
    def test_init_v410(self):
        """测试 v4.10 初始化"""
        handler = TimeoutHandler(
            max_retries=3, 
            default_timeout=60,
            backoff_multiplier=2.0,
            max_backoff=120
        )
        assert handler.max_retries == 3
        assert handler.default_timeout == 60
        assert handler.backoff_multiplier == 2.0
        assert handler.max_backoff == 120
    
    def test_execute_with_retry_v410(self):
        """v4.10: 测试带退避的重试"""
        handler = TimeoutHandler(max_retries=2, default_timeout=1)
        
        call_count = 0
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return {"_timeout": True}
            return "success"
        
        result = handler.execute_with_retry(failing_func)
        assert result["success"] == True
        assert result["attempts"] == 3
    
    def test_execute_with_fallback_v410(self):
        """v4.10: 测试降级策略"""
        handler = TimeoutHandler(max_retries=0, default_timeout=1)
        
        def slow_func():
            return {"_timeout": True}
        
        def fallback_func():
            return "fallback result"
        
        result = handler.execute_with_fallback(slow_func, fallback_func)
        assert result["success"] == True
        assert result["used_fallback"] == True
        assert result["result"] == "fallback result"
    
    def test_get_timeout_stats_v410(self):
        """v4.10: 测试超时统计"""
        handler = TimeoutHandler()
        handler.timeout_history = [
            {"timestamp": "2024-01-01", "timeout_seconds": 30},
            {"timestamp": "2024-01-02", "timeout_seconds": 60},
        ]
        
        stats = handler.get_timeout_stats()
        assert stats["total"] == 2
        assert stats["avg_timeout"] == 45
        assert stats["max_timeout"] == 60


class TestErrorHelperV410:
    """测试 ErrorHelper v4.10"""
    
    def test_get_error_reason_syntax(self):
        """v4.10: 测试语法错误原因获取"""
        error = "SyntaxError: invalid syntax"
        reason = ErrorHelper.get_error_reason(error)
        assert "语法错误" in reason
    
    def test_get_error_reason_timeout(self):
        """v4.10: 测试超时错误原因获取"""
        error = "TIMEOUT"
        reason = ErrorHelper.get_error_reason(error)
        assert "时间限制" in reason, "错误原因应该包含时间限制"
    
    def test_get_error_reason_module(self):
        """v4.10: 测试模块错误原因获取"""
        error = "ModuleNotFoundError: No module named 'requests'"
        reason = ErrorHelper.get_error_reason(error)
        assert "Python 包" in reason
    
    def test_get_error_severity(self):
        """v4.10: 测试错误严重程度"""
        assert ErrorHelper.get_error_severity("SyntaxError: invalid") == "critical"
        assert ErrorHelper.get_error_severity("TypeError: unsupported") == "high"
        assert ErrorHelper.get_error_severity("FileNotFoundError:") == "medium"
    
    def test_get_quick_fix(self):
        """v4.10: 测试快速修复建议"""
        error = "SyntaxError: invalid syntax"
        fix = ErrorHelper.get_quick_fix(error)
        assert "py_compile" in fix or "语法" in fix
        
        error = "ModuleNotFoundError: No module named 'foo'"
        fix = ErrorHelper.get_quick_fix(error)
        assert "pip install" in fix
    
    def test_format_error_for_log(self):
        """v4.10: 测试日志格式化"""
        error = "SyntaxError: invalid syntax"
        formatted = ErrorHelper.format_error_for_log(error, {"task": "test task"})
        assert "CRITICAL" in formatted or "语法错误" in formatted


class TestFilesChangedNormalize:
    """测试 files_changed 类型处理"""
    
    def test_normalize_dict(self):
        """测试字典类型"""
        from sprintcycle.chorus import normalize_files_changed
        
        result = normalize_files_changed({
            "added": ["a.py"],
            "modified": ["b.py"],
            "deleted": [],
            "screenshots": []
        })
        assert result["added"] == ["a.py"]
        assert result["modified"] == ["b.py"]
    
    def test_normalize_list(self):
        """测试列表类型"""
        from sprintcycle.chorus import normalize_files_changed
        
        result = normalize_files_changed(["a.py", "b.py"])
        assert result["modified"] == ["a.py", "b.py"]
        assert result["added"] == []
    
    def test_normalize_none(self):
        """测试 None 类型"""
        from sprintcycle.chorus import normalize_files_changed
        
        result = normalize_files_changed(None)
        assert result == {"added": [], "modified": [], "deleted": [], "screenshots": []}
    
    def test_extract_files_list(self):
        """测试文件列表提取"""
        from sprintcycle.chorus import extract_files_list
        
        result = extract_files_list({
            "added": ["a.py"],
            "modified": ["b.py"],
            "deleted": ["c.py"]
        })
        assert "a.py" in result
        assert "b.py" in result
        assert "c.py" in result
    
    def test_has_changes(self):
        """测试变更检测"""
        from sprintcycle.chorus import has_changes
        
        assert has_changes(["a.py"]) == True
        assert has_changes([]) == False
        assert has_changes({"added": [], "modified": []}) == False
        assert has_changes({"added": ["a.py"]}) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
