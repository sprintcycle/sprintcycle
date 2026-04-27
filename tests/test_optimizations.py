"""
测试 optimizations.py 中的优化类
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
    ErrorCategory
)


class TestRollbackManager:
    """测试 RollbackManager"""
    
    def test_init(self, tmp_path):
        """测试初始化"""
        manager = RollbackManager(str(tmp_path))
        assert manager.project_path == tmp_path
        assert manager.backup_dir.exists()
    
    def test_backup_files(self, tmp_path):
        """测试文件备份"""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        manager = RollbackManager(str(tmp_path))
        result = manager.backup_files(["test.py"])
        
        assert "test.py" in result["backed_up"]
        assert result["backup_id"] is not None
        assert len(result["failed"]) == 0
    
    def test_restore_files(self, tmp_path):
        """测试文件恢复"""
        test_file = tmp_path / "test.py"
        test_file.write_text("original")
        
        manager = RollbackManager(str(tmp_path))
        backup_result = manager.backup_files(["test.py"])
        backup_id = backup_result["backup_id"]
        
        test_file.write_text("modified")
        restore_result = manager.restore_files(backup_id, ["test.py"])
        assert restore_result["success"] is True
        assert test_file.read_text() == "original"
    
    def test_list_backups(self, tmp_path):
        """测试列出备份"""
        test_file = tmp_path / "test.py"
        test_file.write_text("hello")
        
        manager = RollbackManager(str(tmp_path))
        manager.backup_files(["test.py"])
        manager.backup_files(["test.py"])
        
        backups = manager.list_backups()
        assert len(backups) == 2
    
    def test_get_backup_diff(self, tmp_path):
        """测试获取备份差异"""
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\n")
        
        manager = RollbackManager(str(tmp_path))
        backup_result = manager.backup_files(["test.py"])
        backup_id = backup_result["backup_id"]
        
        test_file.write_text("line1\nline2 modified\nline3\nline4\n")
        diff_result = manager.get_backup_diff(backup_id, "test.py")
        
        assert "diff" in diff_result
        assert diff_result["added_lines"] >= 1
        assert diff_result["removed_lines"] >= 1
    
    def test_auto_backup_before_edit(self, tmp_path):
        """测试编辑前自动备份"""
        test_file = tmp_path / "test.py"
        test_file.write_text("original")
        
        manager = RollbackManager(str(tmp_path))
        result = manager.auto_backup_before_edit(["test.py"], reason="功能修改")
        
        assert "test.py" in result["backed_up"]
        assert result.get("reason") == "功能修改"
        assert result.get("auto") is True


class TestTimeoutHandler:
    """测试 TimeoutHandler"""
    
    def test_init(self):
        """测试初始化"""
        handler = TimeoutHandler(max_retries=2, default_timeout=60)
        assert handler.max_retries == 2
        assert handler.default_timeout == 60
    
    def test_execute_with_timeout_success(self):
        """测试超时执行成功"""
        handler = TimeoutHandler()
        result = handler.execute_with_timeout(lambda: "success", timeout=5)
        assert result == "success"
    
    def test_execute_with_timeout_timeout(self):
        """测试超时情况"""
        handler = TimeoutHandler()
        
        def slow_func():
            time.sleep(0.1)
            return "done"
        
        result = handler.execute_with_timeout(slow_func, timeout=1)
        assert result == "done"
    
    def test_predict_timeout(self):
        """测试超时预测"""
        handler = TimeoutHandler()
        
        assert handler.predict_timeout("code", "simple") == 60
        assert handler.predict_timeout("code", "medium") == 120
        assert handler.predict_timeout("code", "complex") == 300
        assert handler.predict_timeout("test", "medium") == 60
        assert handler.predict_timeout("unknown", "medium") == handler.default_timeout
    
    def test_should_skip(self):
        """测试跳过判断"""
        handler = TimeoutHandler(max_retries=2)
        assert handler.should_skip(1) is False
        assert handler.should_skip(2) is True
        assert handler.should_skip(3) is True


class TestErrorHelper:
    """测试 ErrorHelper"""
    
    def test_format_error(self):
        """测试错误格式化"""
        error_output = "SyntaxError: invalid syntax\n  File 'test.py', line 1"
        formatted = ErrorHelper.format_error(error_output, {"task": "测试任务"})
        
        assert "🔴 执行失败" in formatted
        assert "测试任务" in formatted
    
    def test_get_fix_command(self):
        """测试获取修复命令"""
        cmd = ErrorHelper.get_fix_command(ErrorCategory.SYNTAX, "error")
        assert "py_compile" in cmd
        
        cmd = ErrorHelper.get_fix_command(ErrorCategory.IMPORT, "error")
        assert "pip" in cmd
    
    def test_suggest_next_steps(self):
        """测试下一步建议"""
        record = type('obj', (object,), {
            'error_category': ErrorCategory.SYNTAX,
            'task': 'test',
            'error_message': 'error',
            'root_cause': 'cause',
            'solution_hint': 'hint',
            'timestamp': '2024-01-01',
            'files_involved': [],
            'retry_count': 0
        })()
        
        steps = ErrorHelper.suggest_next_steps(record)
        assert len(steps) > 0
    
    def test_get_error_statistics(self):
        """测试错误统计"""
        errors = [
            {"category": "syntax", "files": ["a.py"]},
            {"category": "syntax", "files": ["a.py", "b.py"]},
            {"category": "runtime", "files": ["c.py"]}
        ]
        
        stats = ErrorHelper.get_error_statistics(errors)
        
        assert stats["total"] == 3
        assert stats["by_category"]["syntax"] == 2
        assert stats["by_category"]["runtime"] == 1
        assert stats["by_file"]["a.py"] == 2
    
    def test_get_error_statistics_empty(self):
        """测试空错误统计"""
        stats = ErrorHelper.get_error_statistics([])
        assert stats["total"] == 0
        assert stats["trend"] == "无数据"
    
    def test_generate_error_report(self):
        """测试生成错误报告"""
        errors = [
            {"category": "syntax", "files": ["a.py"], "recent": False},
            {"category": "syntax", "files": ["a.py", "b.py"], "recent": True}
        ]
        
        report = ErrorHelper.generate_error_report(errors, "markdown")
        assert "错误报告" in report
        assert "总错误数" in report
        
        json_report = ErrorHelper.generate_error_report(errors, "json")
        assert "stats" in json_report


class TestFileTracker:
    """测试 FileTracker"""
    
    def test_should_exclude(self):
        """测试排除逻辑"""
        assert FileTracker.should_exclude("node_modules/test.py", ["node_modules"]) is True
        assert FileTracker.should_exclude("test.py", ["node_modules"]) is False
    
    def test_extract_changed_files(self):
        """测试提取变更文件"""
        output = """
        Created test.py
        Applied edit to main.py
        Modified utils.py
        """
        
        result = FileTracker.extract_changed_files(output)
        
        assert "added" in result
        assert "modified" in result
        assert "deleted" in result


class TestTaskSplitter:
    """测试 TaskSplitter"""
    
    def test_init(self):
        """测试初始化"""
        splitter = TaskSplitter()
        assert splitter.config is not None
    
    def test_analyze_task(self):
        """测试任务分析"""
        splitter = TaskSplitter()
        result = splitter.analyze_task("实现推荐算法")
        
        assert "should_split" in result
        assert "reasons" in result
        assert "sub_tasks" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestResponseCache:
    """测试 ResponseCache (v4.9 新增)"""
    
    def test_cache_init(self, tmp_path):
        """测试缓存初始化"""
        from sprintcycle.cache import ResponseCache, CacheStrategy
        
        cache = ResponseCache(
            cache_dir=str(tmp_path / "cache"),
            max_size_mb=10,
            strategy=CacheStrategy.LRU,
        )
        assert cache.max_size_bytes == 10 * 1024 * 1024
        assert cache.strategy == CacheStrategy.LRU
    
    def test_cache_set_get(self, tmp_path):
        """测试缓存写入和读取"""
        from sprintcycle.cache import ResponseCache
        
        cache = ResponseCache(cache_dir=str(tmp_path / "cache"))
        
        test_data = {"key": "value", "list": [1, 2, 3]}
        cache.set("https://api.example.com/test", test_data)
        
        result = cache.get("https://api.example.com/test")
        assert result == test_data
    
    def test_cache_miss(self, tmp_path):
        """测试缓存未命中"""
        from sprintcycle.cache import ResponseCache
        
        cache = ResponseCache(cache_dir=str(tmp_path / "cache"))
        
        result = cache.get("https://api.example.com/nonexistent")
        assert result is None
    
    def test_cache_invalidate(self, tmp_path):
        """测试缓存失效"""
        from sprintcycle.cache import ResponseCache
        
        cache = ResponseCache(cache_dir=str(tmp_path / "cache"))
        
        cache.set("https://api.example.com/test", {"data": "value"})
        assert cache.get("https://api.example.com/test") is not None
        
        count = cache.invalidate(url="https://api.example.com/test")
        assert count == 1
        assert cache.get("https://api.example.com/test") is None
    
    def test_cache_stats(self, tmp_path):
        """测试缓存统计"""
        from sprintcycle.cache import ResponseCache
        
        cache = ResponseCache(cache_dir=str(tmp_path / "cache"))
        
        cache.set("https://api.example.com/test1", {"data": "value1"})
        cache.get("https://api.example.com/test1")  # 命中
        cache.get("https://api.example.com/test2")  # 未命中
        
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
    
    def test_cache_clear(self, tmp_path):
        """测试清空缓存"""
        from sprintcycle.cache import ResponseCache
        
        cache = ResponseCache(cache_dir=str(tmp_path / "cache"))
        
        cache.set("https://api.example.com/test1", {"data": "value1"})
        cache.set("https://api.example.com/test2", {"data": "value2"})
        
        cache.clear()
        
        assert cache.get("https://api.example.com/test1") is None
        assert cache.get("https://api.example.com/test2") is None


class TestErrorHelperExtended:
    """测试扩展后的 ErrorHelper (v4.9)"""
    
    def test_friendly_messages(self):
        """测试友好错误消息"""
        from sprintcycle.optimizations import ErrorHelper
        
        # 测试格式化错误消息包含友好提示
        error_output = "SyntaxError: invalid syntax"
        formatted = ErrorHelper.format_error(error_output)
        
        assert "💡" in formatted  # 应该有友好提示
        assert "SyntaxError" in formatted
    
    def test_fix_commands(self):
        """测试修复命令提示"""
        from sprintcycle.optimizations import ErrorHelper, ErrorCategory
        
        # 测试各错误类别的修复命令
        assert ErrorCategory.SYNTAX in ErrorHelper.FIX_COMMANDS
        assert ErrorCategory.IMPORT in ErrorHelper.FIX_COMMANDS
        assert ErrorCategory.NETWORK in ErrorHelper.FIX_COMMANDS
        
        # 检查命令结构
        syntax_info = ErrorHelper.FIX_COMMANDS[ErrorCategory.SYNTAX]
        assert "commands" in syntax_info
        assert "hint" in syntax_info
        assert len(syntax_info["commands"]) > 0


class TestEvolutionEngineExtended:
    """测试扩展后的 EvolutionEngine (v4.9)"""
    
    def test_extended_error_patterns(self):
        """测试扩展的错误模式"""
        from sprintcycle.optimizations import EvolutionEngine, ErrorCategory
        
        engine = EvolutionEngine("/tmp/test_project")
        
        # 测试新添加的错误模式
        patterns = engine.ERROR_PATTERNS
        
        # 检查是否有扩展的模式类别
        assert ErrorCategory.LOGIC in patterns
        assert ErrorCategory.AIDER in patterns
        assert ErrorCategory.EMPTY_OUTPUT in patterns
        assert ErrorCategory.NO_CHANGES in patterns
    
    def test_classify_extended_errors(self):
        """测试扩展错误的分类"""
        from sprintcycle.optimizations import EvolutionEngine, ErrorCategory
        
        engine = EvolutionEngine("/tmp/test_project")
        
        # 测试新错误类型
        assert engine.classify_error("KeyError: 'unknown_key'") == ErrorCategory.RUNTIME
        assert engine.classify_error("RecursionError: maximum recursion") == ErrorCategory.LOGIC
        assert engine.classify_error("rate limit exceeded") == ErrorCategory.AIDER
