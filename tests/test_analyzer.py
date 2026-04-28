"""
BugAnalyzerAgent 单元测试

测试 Bug 分析 Agent 的各项功能：
- 错误日志解析
- 根因分析模式匹配
- 代码定位
- 修复建议生成
- 自动修复执行
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

from sprintcycle.execution.agents.analyzer import (
    BugAnalyzerAgent,
    ParsedTraceback,
    PatternMatch,
    ROOT_CAUSE_PATTERNS,
)
from sprintcycle.execution.agents.bug_models import (
    BugReport,
    BugSeverity,
    ErrorCategory,
    Location,
    FixSuggestion,
    FixResult,
    AnalysisRequest,
)
from sprintcycle.execution.agents.base import AgentContext


class TestBugAnalyzerAgent:
    """BugAnalyzerAgent 测试类"""
    
    @pytest.fixture
    def analyzer(self):
        """创建 BugAnalyzerAgent 实例"""
        config = None
        return BugAnalyzerAgent(config)
    
    @pytest.fixture
    def context(self):
        """创建测试上下文"""
        return AgentContext(
            prd_id="test_prd",
            sprint_name="Test Sprint",
        )
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)


class TestTracebackParsing(TestBugAnalyzerAgent):
    """错误日志解析测试"""
    
    def test_parse_nameerror(self, analyzer):
        """测试解析 NameError"""
        error_log = """Traceback (most recent call last):
  File "main.py", line 10, in <module>
    print(x)
NameError: name 'x' is not defined"""
        
        result = analyzer._parse_traceback(error_log, "python")
        
        assert result.error_type == "NameError"
        assert "not defined" in result.error_message
        assert len(result.frames) > 0
        assert result.location is not None
    
    def test_parse_typeerror(self, analyzer):
        """测试解析 TypeError"""
        error_log = """Traceback (most recent call last):
  File "utils.py", line 25, in add
    return a + b
TypeError: unsupported operand type(s) for +: 'int' and 'str'"""
        
        result = analyzer._parse_traceback(error_log, "python")
        
        assert result.error_type == "TypeError"
        assert "unsupported operand" in result.error_message
    
    def test_parse_import_error(self, analyzer):
        """测试解析 ImportError"""
        error_log = """Traceback (most recent call last):
  File "main.py", line 5, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'"""
        
        result = analyzer._parse_traceback(error_log, "python")
        
        assert result.error_type == "ModuleNotFoundError"
        assert "requests" in result.error_message
    
    def test_parse_syntax_error(self, analyzer):
        """测试解析 SyntaxError"""
        error_log = """  File "main.py", line 10
    if x =
         ^
SyntaxError: invalid syntax"""
        
        result = analyzer._parse_traceback(error_log, "python")
        
        assert result.error_type == "SyntaxError"
        assert "invalid syntax" in result.error_message
    
    def test_parse_zero_division(self, analyzer):
        """测试解析 ZeroDivisionError"""
        error_log = """Traceback (most recent call last):
  File "calc.py", line 15, in divide
    return a / b
ZeroDivisionError: division by zero"""
        
        result = analyzer._parse_traceback(error_log, "python")
        
        assert result.error_type == "ZeroDivisionError"
        assert "division by zero" in result.error_message
    
    def test_parse_key_error(self, analyzer):
        """测试解析 KeyError"""
        error_log = """Traceback (most recent call last):
  File "dict.py", line 8, in get_value
    return data['key']
KeyError: 'key'"""
        
        result = analyzer._parse_traceback(error_log, "python")
        
        assert result.error_type == "KeyError"
        assert "'key'" in result.error_message


class TestPatternMatching(TestBugAnalyzerAgent):
    """根因分析模式匹配测试"""
    
    def test_match_nameerror_pattern(self, analyzer):
        """测试 NameError 模式匹配"""
        match = analyzer._match_pattern("NameError", "name 'x' is not defined")
        
        assert match.category == ErrorCategory.NAME
        assert match.severity == BugSeverity.MEDIUM
        assert len(match.fixes) > 0
        assert match.confidence > 0.8
    
    def test_match_typeerror_pattern(self, analyzer):
        """测试 TypeError 模式匹配"""
        match = analyzer._match_pattern(
            "TypeError", 
            "unsupported operand type(s) for +: 'int' and 'str'"
        )
        
        assert match.category == ErrorCategory.TYPE
        assert match.severity == BugSeverity.MEDIUM
        assert "类型不匹配" in match.root_cause
    
    def test_match_import_error_pattern(self, analyzer):
        """测试 ImportError 模式匹配"""
        match = analyzer._match_pattern(
            "ImportError", 
            "No module named 'numpy'"
        )
        
        assert match.category == ErrorCategory.IMPORT
        assert match.severity == BugSeverity.HIGH
        assert any("pip install" in f for f in match.fixes)
    
    def test_match_attribute_error_pattern(self, analyzer):
        """测试 AttributeError 模式匹配"""
        match = analyzer._match_pattern(
            "AttributeError",
            "'NoneType' object has no attribute 'strip'"
        )
        
        assert match.category == ErrorCategory.ATTRIBUTE
        assert match.severity == BugSeverity.MEDIUM
    
    def test_match_unknown_pattern(self, analyzer):
        """测试未知错误类型"""
        match = analyzer._match_pattern(
            "CustomError",
            "some unknown error message"
        )
        
        assert match.category == ErrorCategory.UNKNOWN
        assert match.confidence < 0.5


class TestBugReportGeneration(TestBugAnalyzerAgent):
    """Bug 报告生成测试"""
    
    @pytest.mark.asyncio
    async def test_generate_nameerror_report(self, analyzer):
        """测试生成 NameError 报告"""
        request = AnalysisRequest(
            error_log="""Traceback (most recent call last):
  File "main.py", line 10, in <module>
    print(x)
NameError: name 'x' is not defined""",
            file_paths=[],
        )
        
        result = await analyzer.analyze(request)
        
        assert result.report.error_type == "NameError"
        assert result.report.severity == BugSeverity.MEDIUM
        assert len(result.report.suggestions) > 0
        assert result.report.root_cause != ""
    
    @pytest.mark.asyncio
    async def test_generate_typeerror_report(self, analyzer):
        """测试生成 TypeError 报告"""
        request = AnalysisRequest(
            error_log="""Traceback (most recent call last):
  File "calc.py", line 20, in add
    return a + b
TypeError: unsupported operand type(s) for +: 'int' and 'str'""",
            file_paths=[],
        )
        
        result = await analyzer.analyze(request)
        
        assert result.report.error_type == "TypeError"
        assert result.report.category == ErrorCategory.TYPE
    
    @pytest.mark.asyncio
    async def test_generate_import_error_report(self, analyzer):
        """测试生成 ImportError 报告"""
        request = AnalysisRequest(
            error_log="""Traceback (most recent call last):
  File "main.py", line 5, in <module>
    import pandas
ModuleNotFoundError: No module named 'pandas'""",
            file_paths=[],
        )
        
        result = await analyzer.analyze(request)
        
        assert result.report.error_type == "ModuleNotFoundError"
        assert result.report.severity == BugSeverity.HIGH
        assert any("pip install" in s for s in result.report.suggestions)


class TestFixSuggestion(TestBugAnalyzerAgent):
    """修复建议生成测试"""
    
    @pytest.mark.asyncio
    async def test_suggest_nameerror_fix(self, analyzer):
        """测试 NameError 修复建议"""
        report = BugReport(
            error_type="NameError",
            error_message="name 'x' is not defined",
            root_cause="变量未定义",
            suggestions=["检查变量定义"],
        )
        
        suggestions = await analyzer.suggest_fix(report)
        
        assert len(suggestions) > 0
        assert any("x" in s.old_code or "x" in s.new_code for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_suggest_typeerror_fix(self, analyzer):
        """测试 TypeError 修复建议"""
        report = BugReport(
            error_type="TypeError",
            error_message="unsupported operand type(s) for +: 'int' and 'str'",
            root_cause="类型不匹配",
            suggestions=["添加类型检查"],
        )
        
        suggestions = await analyzer.suggest_fix(report)
        
        assert len(suggestions) > 0
        assert any("type" in s.explanation.lower() for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_suggest_import_error_fix(self, analyzer):
        """测试 ImportError 修复建议"""
        report = BugReport(
            error_type="ImportError",
            error_message="No module named 'requests'",
            root_cause="依赖未安装",
            suggestions=["pip install requests"],
        )
        
        suggestions = await analyzer.suggest_fix(report)
        
        assert len(suggestions) > 0
        assert any(suggestion.is_automated for suggestion in suggestions)


class TestApplyFix(TestBugAnalyzerAgent):
    """自动修复执行测试"""
    
    @pytest.mark.asyncio
    async def test_apply_fix_create_file(self, analyzer, temp_dir):
        """测试创建新文件"""
        file_path = Path(temp_dir) / "new_file.py"
        
        suggestion = FixSuggestion(
            file_path=str(file_path),
            old_code="",
            new_code="x = 10\nprint(x)",
            explanation="创建新文件",
            confidence=0.9,
        )
        
        result = await analyzer.apply_fix(suggestion)
        
        assert result.success is True
        assert file_path.exists()
        assert "x = 10" in file_path.read_text()
    
    @pytest.mark.asyncio
    async def test_apply_fix_replace_content(self, analyzer, temp_dir):
        """测试替换文件内容"""
        file_path = Path(temp_dir) / "test.py"
        file_path.write_text("old_value = 10\nprint(old_value)")
        
        suggestion = FixSuggestion(
            file_path=str(file_path),
            old_code="old_value",
            new_code="new_value",
            explanation="替换变量名",
            confidence=0.9,
        )
        
        result = await analyzer.apply_fix(suggestion)
        
        assert result.success is True
        assert "new_value" in file_path.read_text()
        assert result.backup_path is not None
    
    @pytest.mark.asyncio
    async def test_apply_fix_create_backup(self, analyzer, temp_dir):
        """测试创建备份"""
        file_path = Path(temp_dir) / "backup_test.py"
        original_content = "x = 1\ny = 2"
        file_path.write_text(original_content)
        
        suggestion = FixSuggestion(
            file_path=str(file_path),
            old_code="x = 1",
            new_code="x = 100",
            explanation="修改值",
            confidence=0.9,
        )
        
        result = await analyzer.apply_fix(suggestion)
        
        assert result.success is True
        assert result.backup_path is not None
        backup_file = Path(result.backup_path)
        assert backup_file.exists()
        assert backup_file.read_text() == original_content


class TestCodeLocation(TestBugAnalyzerAgent):
    """代码定位测试"""
    
    @pytest.mark.asyncio
    async def test_locate_in_files(self, analyzer, temp_dir):
        """测试在文件中定位问题代码"""
        # 创建测试文件
        file1 = Path(temp_dir) / "main.py"
        file1.write_text("def main():\n    x = 10\n    print(x)\n    y = undefined_var\n")
        
        file2 = Path(temp_dir) / "utils.py"
        file2.write_text("def helper():\n    return 42\n")
        
        report = BugReport(
            error_type="NameError",
            error_message="name 'undefined_var' is not defined",
            root_cause="变量未定义",
            suggestions=["定义变量"],
        )
        
        locations = await analyzer.locate(report, [str(file1), str(file2)])
        
        assert len(locations) > 0
        assert any("undefined_var" in loc.code_snippet for loc in locations if loc.code_snippet)
    
    @pytest.mark.asyncio
    async def test_locate_empty_keywords(self, analyzer, temp_dir):
        """测试空关键词不匹配"""
        file1 = Path(temp_dir) / "empty.py"
        file1.write_text("x = 10\ny = 20\n")
        
        report = BugReport(
            error_type="Error",
            error_message="some error",
            root_cause="unknown",
            suggestions=[],
        )
        
        locations = await analyzer.locate(report, [str(file1)])
        
        # 应该返回空列表，因为没有关键词
        assert len(locations) == 0


class TestAgentExecution(TestBugAnalyzerAgent):
    """Agent 执行测试"""
    
    @pytest.mark.asyncio
    async def test_execute_with_error_log(self, analyzer, context):
        """测试使用错误日志执行分析"""
        error_log = """Traceback (most recent call last):
  File "main.py", line 10, in <module>
    print(x)
NameError: name 'x' is not defined"""
        
        result = await analyzer.execute(error_log, context)
        
        assert result.success is True
        assert result.output != ""
        assert "NameError" in result.output
        assert len(result.artifacts) > 0
    
    @pytest.mark.asyncio
    async def test_execute_without_error_log(self, analyzer, context):
        """测试没有错误日志时执行失败"""
        result = await analyzer.execute("some task without error", context)
        
        assert result.success is False
        assert "未找到" in result.error or "error" in result.error.lower()


class TestBugModels(TestBugAnalyzerAgent):
    """数据模型测试"""
    
    def test_location_str(self):
        """测试 Location 字符串表示"""
        loc = Location(
            file_path="main.py",
            line_number=10,
            column_number=5,
            function_name="main",
        )
        
        result = str(loc)
        
        assert "main.py" in result
        assert "10" in result
        assert "5" in result
        assert "main" in result
    
    def test_bug_report_summary(self):
        """测试 BugReport 摘要生成"""
        report = BugReport(
            error_type="NameError",
            error_message="name 'x' is not defined",
            severity=BugSeverity.MEDIUM,
            root_cause="变量未定义",
            suggestions=["定义变量", "检查拼写"],
        )
        
        summary = report.to_summary()
        
        assert "MEDIUM" in summary
        assert "NameError" in summary
        assert "变量未定义" in summary
    
    def test_fix_suggestion_diff(self):
        """测试 FixSuggestion diff 生成"""
        suggestion = FixSuggestion(
            file_path="test.py",
            old_code="x = 1",
            new_code="x = 2",
            explanation="修改值",
            line_start=10,
            line_end=10,
        )
        
        diff = suggestion.generate_diff()
        
        assert "---" in diff
        assert "+++" in diff
        assert "- x = 1" in diff
        assert "+ x = 2" in diff
    
    def test_fix_result_summary(self):
        """测试 FixResult 摘要生成"""
        result = FixResult(
            success=True,
            file_path="test.py",
            lines_changed=5,
        )
        
        summary = result.to_summary()
        
        assert "✅" in summary
        assert "test.py" in summary
        assert "5" in summary


class TestErrorCategory(TestBugAnalyzerAgent):
    """错误分类测试"""
    
    def test_type_to_category_mapping(self, analyzer):
        """测试错误类型到分类的映射"""
        test_cases = [
            ("NameError", ErrorCategory.NAME),
            ("TypeError", ErrorCategory.TYPE),
            ("ImportError", ErrorCategory.IMPORT),
            ("AttributeError", ErrorCategory.ATTRIBUTE),
            ("IndexError", ErrorCategory.INDEX),
            ("KeyError", ErrorCategory.KEY),
            ("SyntaxError", ErrorCategory.SYNTAX),
            ("ValueError", ErrorCategory.VALUE),
        ]
        
        for error_type, expected_category in test_cases:
            result = analyzer._type_to_category(error_type)
            assert result == expected_category, f"Failed for {error_type}"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
