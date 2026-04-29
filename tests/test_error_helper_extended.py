"""扩展错误辅助测试 - 针对 error_helper.py 低覆盖率模块"""
import pytest
from sprintcycle.error_helper import (
    ErrorCategory,
    FailureRecord,
    ErrorHelper,
)


class TestErrorCategory:
    """错误分类枚举测试"""
    
    def test_all_categories_exist(self):
        """测试所有分类存在"""
        categories = [
            ErrorCategory.SYNTAX,
            ErrorCategory.IMPORT,
            ErrorCategory.RUNTIME,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.UNKNOWN,
            ErrorCategory.LOGIC,
            ErrorCategory.AIDER,
            ErrorCategory.EMPTY_OUTPUT,
            ErrorCategory.NO_CHANGES,
        ]
        assert len(categories) == 11
    
    def test_category_values(self):
        """测试分类值"""
        assert ErrorCategory.SYNTAX.value == "syntax"
        assert ErrorCategory.IMPORT.value == "import"
        assert ErrorCategory.RUNTIME.value == "runtime"


class TestFailureRecord:
    """失败记录数据类测试"""
    
    def test_failure_record_basic(self):
        """测试基本失败记录"""
        record = FailureRecord(
            error_type="SyntaxError",
            error_message="invalid syntax"
        )
        assert record.error_type == "SyntaxError"
        assert record.error_category == ErrorCategory.UNKNOWN
        assert record.recent is True
    
    def test_failure_record_full(self):
        """测试完整失败记录"""
        record = FailureRecord(
            error_type="ImportError",
            error_message="No module named 'xxx'",
            file_path="/path/file.py",
            line_number=42,
            task_id="task-001",
            timestamp="2024-01-01T00:00:00",
            error_category=ErrorCategory.IMPORT,
            context={"env": "test"},
        )
        assert record.file_path == "/path/file.py"
        assert record.line_number == 42
        assert record.task_id == "task-001"
        assert record.error_category == ErrorCategory.IMPORT


class TestErrorHelper:
    """错误辅助类测试"""
    
    def test_error_icons(self):
        """测试错误图标映射"""
        assert ErrorCategory.SYNTAX in ErrorHelper.ERROR_ICONS
        assert ErrorCategory.IMPORT in ErrorHelper.ERROR_ICONS
        assert ErrorCategory.RUNTIME in ErrorHelper.ERROR_ICONS
        icon, desc = ErrorHelper.ERROR_ICONS[ErrorCategory.SYNTAX]
        assert icon == "🔧"
    
    def test_friendly_messages(self):
        """测试友好消息映射"""
        assert "SyntaxError" in ErrorHelper.FRIENDLY_MESSAGES
        assert "IndentationError" in ErrorHelper.FRIENDLY_MESSAGES
        assert "NameError" in ErrorHelper.FRIENDLY_MESSAGES
    
    def test_fix_commands(self):
        """测试修复命令映射"""
        assert ErrorCategory.SYNTAX in ErrorHelper.FIX_COMMANDS
        assert ErrorCategory.IMPORT in ErrorHelper.FIX_COMMANDS
    
    def test_error_reasons(self):
        """测试错误原因映射"""
        assert "SyntaxError" in ErrorHelper.ERROR_REASONS
        assert "ImportError" in ErrorHelper.ERROR_REASONS
    
    def test_classify_error_syntax(self):
        """测试分类语法错误"""
        helper = ErrorHelper()
        category = helper.classify_error("SyntaxError: invalid syntax")
        assert category == ErrorCategory.SYNTAX
    
    def test_classify_error_import(self):
        """测试分类导入错误"""
        helper = ErrorHelper()
        category = helper.classify_error("ModuleNotFoundError: No module named 'x'")
        assert category == ErrorCategory.IMPORT
    
    def test_classify_error_timeout(self):
        """测试分类超时错误"""
        helper = ErrorHelper()
        category = helper.classify_error("TimeoutError: timed out")
        assert category == ErrorCategory.TIMEOUT
    
    def test_classify_error_unknown(self):
        """测试分类未知错误"""
        helper = ErrorHelper()
        category = helper.classify_error("SomeRandomError: unknown")
        assert category == ErrorCategory.UNKNOWN
    
    def test_get_friendly_message(self):
        """测试获取友好消息"""
        helper = ErrorHelper()
        msg = helper.get_friendly_message("SyntaxError")
        assert msg is not None
        assert "语法" in msg or "代码" in msg
    
    def test_format_error(self):
        """测试格式化错误"""
        helper = ErrorHelper()
        formatted = helper.format_error("SyntaxError: test")
        assert "SyntaxError" in formatted
    
    def test_format_error_with_context(self):
        """测试带上下文的格式化错误"""
        helper = ErrorHelper()
        formatted = helper.format_error("Error: test", context={"task": "build"})
        assert "build" in formatted
    
    def test_get_fix_command(self):
        """测试获取修复命令"""
        cmd = ErrorHelper.get_fix_command(ErrorCategory.SYNTAX)
        assert cmd is not None
    
    def test_get_error_reason_known(self):
        """测试获取已知错误原因"""
        reason = ErrorHelper.get_error_reason("SyntaxError: invalid syntax")
        assert reason is not None
        assert reason != "未知错误：无法确定具体原因"
    
    def test_get_error_reason_unknown(self):
        """测试获取未知错误原因"""
        reason = ErrorHelper.get_error_reason("SomeRandomError")
        assert "未知" in reason
    
    def test_get_error_severity(self):
        """测试获取错误严重程度"""
        severity = ErrorHelper.get_error_severity("SyntaxError")
        assert severity in ["low", "medium", "high", "critical", "unknown"]
    
    def test_get_quick_fix_syntax(self):
        """测试语法错误快速修复"""
        fix = ErrorHelper.get_quick_fix("SyntaxError: line 1")
        assert "py_compile" in fix or "语法" in fix
    
    def test_get_quick_fix_import(self):
        """测试导入错误快速修复"""
        fix = ErrorHelper.get_quick_fix("ModuleNotFoundError: no module named 'x'")
        assert "pip" in fix or "安装" in fix
    
    def test_format_error_for_log(self):
        """测试格式化错误日志"""
        formatted = ErrorHelper.format_error_for_log(
            "SyntaxError: test",
            context={"task": "build"}
        )
        assert "build" in formatted
        assert "SyntaxError" in formatted
    
    def test_format_error_for_log_no_context(self):
        """测试无上下文格式化"""
        formatted = ErrorHelper.format_error_for_log("Error: test")
        assert "Error" in formatted
    
    def test_get_error_statistics_empty(self):
        """测试空错误统计"""
        stats = ErrorHelper.get_error_statistics([])
        assert stats["total"] == 0
        assert stats["by_type"] == {}
    
    def test_get_error_statistics(self):
        """测试错误统计"""
        errors = ["SyntaxError: line 1", "SyntaxError: line 2", "ImportError: no mod"]
        stats = ErrorHelper.get_error_statistics(errors)
        assert stats["total"] == 3
        assert stats["by_type"]["SyntaxError"] == 2
        assert stats["by_type"]["ImportError"] == 1
    
    def test_generate_error_report_empty(self):
        """测试生成空错误报告"""
        report = ErrorHelper.generate_error_report([])
        assert "没有错误记录" in report
    
    def test_generate_error_report(self):
        """测试生成错误报告"""
        errors = [
            {"type": "SyntaxError", "message": "invalid syntax"},
            {"type": "ImportError", "message": "no module named 'x'"},
        ]
        report = ErrorHelper.generate_error_report(errors)
        assert "错误报告" in report
        assert "SyntaxError" in report
        assert "总计: 2 个错误" in report
    
    def test_suggest_next_steps_syntax(self):
        """测试语法错误建议"""
        record = FailureRecord(
            error_type="SyntaxError",
            error_message="err",
            error_category=ErrorCategory.SYNTAX
        )
        suggestions = ErrorHelper.suggest_next_steps(record)
        assert len(suggestions) > 0
        assert any("语法" in s or "代码" in s for s in suggestions)
    
    def test_suggest_next_steps_import(self):
        """测试导入错误建议"""
        record = FailureRecord(
            error_type="ImportError",
            error_message="err",
            error_category=ErrorCategory.IMPORT
        )
        suggestions = ErrorHelper.suggest_next_steps(record)
        assert any("pip" in s or "requirements" in s for s in suggestions)
    
    def test_get_fix_info(self):
        """测试获取修复信息"""
        helper = ErrorHelper()
        info = helper.get_fix_info(ErrorCategory.SYNTAX)
        assert "icon" in info
        assert "hint" in info
        assert info["icon"] == "🔧"
    
    def test_record_error(self):
        """测试记录错误"""
        helper = ErrorHelper()
        record = FailureRecord(
            error_type="SyntaxError",
            error_message="test"
        )
        helper.record_error(record)
        stats = helper.get_error_stats()
        assert stats["total"] == 1
        assert stats["recent_count"] == 1
    
    def test_get_common_errors(self):
        """测试获取常见错误"""
        helper = ErrorHelper()
        for _ in range(3):
            helper.record_error(FailureRecord(error_type="SyntaxError", error_message="err1"))
        for _ in range(2):
            helper.record_error(FailureRecord(error_type="ImportError", error_message="err2"))
        
        common = helper.get_common_errors(top_n=2)
        assert len(common) == 2
        assert common[0]["error_type"] == "SyntaxError"
        assert common[0]["count"] == 3
