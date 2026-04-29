"""扩展异常测试 - 针对低覆盖率模块"""
import pytest
from sprintcycle.exceptions import (
    SprintCycleError,
    ConfigurationError,
    ConfigFileNotFoundError,
    ConfigValidationError,
    TaskExecutionError,
    TaskTimeoutError,
    TaskValidationError,
    KnowledgeBaseError,
    KnowledgeNotFoundError,
    KnowledgeWriteError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolTimeoutError,
    ValidationError,
    RollbackError,
    FileOperationError,
    EXCEPTION_REGISTRY,
    get_exception_by_name,
)


class TestSprintCycleError:
    """SprintCycle基础异常类测试"""
    
    def test_basic_error_with_message(self):
        """测试基本错误消息"""
        err = SprintCycleError("Test error message")
        assert str(err) == "Test error message"
        assert err.message == "Test error message"
        assert err.details == {}
    
    def test_error_with_details(self):
        """测试带详情字典的错误"""
        details = {"key": "value", "count": 42}
        err = SprintCycleError("Error with details", details=details)
        assert err.details == details
        assert "key" in err.details
    
    def test_to_dict(self):
        """测试转换为字典格式"""
        details = {"info": "test"}
        err = SprintCycleError("Dict test", details=details)
        d = err.to_dict()
        assert d["error_type"] == "SprintCycleError"
        assert d["message"] == "Dict test"
        assert d["details"] == details


class TestConfigurationError:
    """配置相关异常测试"""
    
    def test_config_error_without_key(self):
        """测试不带config_key的配置错误"""
        err = ConfigurationError("Config error")
        assert err.message == "Config error"
        assert err.config_key is None
    
    def test_config_error_with_key(self):
        """测试带config_key的配置错误"""
        err = ConfigurationError("Missing config", config_key="api_key")
        assert err.config_key == "api_key"
        assert err.details["config_key"] == "api_key"


class TestConfigFileNotFoundError:
    """配置文件未找到异常测试"""
    
    def test_config_file_not_found(self):
        """测试配置文件未找到错误"""
        err = ConfigFileNotFoundError("/path/to/config.yaml")
        assert "配置文件未找到" in err.message
        assert err.config_path == "/path/to/config.yaml"
        assert err.config_key == "/path/to/config.yaml"


class TestConfigValidationError:
    """配置验证失败异常测试"""
    
    def test_config_validation_error(self):
        """测试配置验证失败错误"""
        err = ConfigValidationError(
            "Invalid value",
            config_key="timeout",
            expected="int",
            actual="string"
        )
        assert err.expected == "int"
        assert err.actual == "string"
        assert err.details["expected"] == "int"
        assert err.details["actual"] == "string"


class TestTaskExecutionError:
    """任务执行异常测试"""
    
    def test_task_error_basic(self):
        """测试基本任务错误"""
        err = TaskExecutionError("Task failed")
        assert err.task is None
        assert err.agent is None
    
    def test_task_error_with_context(self):
        """测试带上下文的任务错误"""
        err = TaskExecutionError(
            "Task execution failed",
            task="build",
            agent="builder",
            tool="gcc"
        )
        assert err.task == "build"
        assert err.agent == "builder"
        assert err.tool == "gcc"
        assert err.details["task"] == "build"
        assert err.details["agent"] == "builder"
        assert err.details["tool"] == "gcc"


class TestTaskTimeoutError:
    """任务超时异常测试"""
    
    def test_task_timeout_error(self):
        """测试任务超时错误"""
        long_task = "A" * 100  # 超过50字符
        err = TaskTimeoutError(long_task, 300)
        assert err.timeout_seconds == 300
        assert err.details["timeout_seconds"] == 300


class TestTaskValidationError:
    """任务验证失败异常测试"""
    
    def test_task_validation_error(self):
        """测试任务验证失败错误"""
        errors = ["field1 is required", "field2 must be int"]
        err = TaskValidationError("Validation failed", task="validate", validation_errors=errors)
        assert err.validation_errors == errors
        assert err.details["validation_errors"] == errors


class TestKnowledgeBaseError:
    """知识库异常测试"""
    
    def test_kb_error_without_path(self):
        """测试不带路径的知识库错误"""
        err = KnowledgeBaseError("KB operation failed")
        assert err.kb_path is None
    
    def test_kb_error_with_path(self):
        """测试带路径的知识库错误"""
        err = KnowledgeBaseError("KB read failed", kb_path="/data/kb")
        assert err.kb_path == "/data/kb"
        assert err.details["kb_path"] == "/data/kb"


class TestKnowledgeNotFoundError:
    """知识未找到异常测试"""
    
    def test_knowledge_not_found(self):
        """测试知识未找到错误"""
        err = KnowledgeNotFoundError("/path/to/knowledge.md")
        assert err.kb_path == "/path/to/knowledge.md"
        assert "未找到" in err.message


class TestKnowledgeWriteError:
    """知识写入异常测试"""
    
    def test_knowledge_write_error(self):
        """测试知识写入错误"""
        err = KnowledgeWriteError("/path/to/knowledge.md")
        assert err.kb_path == "/path/to/knowledge.md"


class TestKnowledgeNotFoundError:
    """知识未找到异常测试"""
    
    def test_knowledge_not_found(self):
        """测试知识未找到错误"""
        err = KnowledgeNotFoundError("search query")
        assert err.kb_path is None
        assert "未找到" in err.message


class TestKnowledgeWriteError:
    """知识写入异常测试"""
    
    def test_knowledge_write_error(self):
        """测试知识写入错误"""
        err = KnowledgeWriteError("Write failed", kb_path="/path/to/knowledge.md")
        assert err.kb_path == "/path/to/knowledge.md"
class TestToolExecutionError:
    """工具执行异常测试"""
    
    def test_tool_error_basic(self):
        """测试基本工具错误"""
        err = ToolExecutionError("Tool failed", tool="gcc")
        assert err.tool == "gcc"
        assert err.exit_code is None
    
    def test_tool_error_with_exit_code(self):
        """测试带退出码的工具错误"""
        err = ToolExecutionError("Tool failed", tool="gcc", exit_code=1)
        assert err.exit_code == 1
        assert err.details["exit_code"] == 1
    
    def test_tool_error_with_output(self):
        """测试带输出的工具错误"""
        err = ToolExecutionError("Tool failed", tool="gcc", stdout="output", stderr="error")
        assert err.stdout == "output"
        assert err.stderr == "error"
    
    def test_tool_error_output_truncation(self):
        """测试输出截断"""
        long_output = "x" * 1000
        err = ToolExecutionError("Tool failed", tool="gcc", stdout=long_output)
        assert len(err.details["stdout"]) <= 500


class TestToolNotFoundError:
    """工具未找到异常测试"""
    
    def test_tool_not_found(self):
        """测试工具未找到错误"""
        err = ToolNotFoundError("gcc")
        assert err.tool == "gcc"
        assert "未找到" in err.message
    
    def test_tool_not_found_with_paths(self):
        """测试带搜索路径的工具未找到错误"""
        err = ToolNotFoundError("gcc", search_paths=["/usr/bin", "/usr/local/bin"])
        assert err.details["search_paths"] == ["/usr/bin", "/usr/local/bin"]


class TestToolTimeoutError:
    """工具超时异常测试"""
    
    def test_tool_timeout_error(self):
        """测试工具超时错误"""
        err = ToolTimeoutError("gcc", 60)
        assert err.tool == "gcc"
        assert err.timeout_seconds == 60
        assert err.details["timeout_seconds"] == 60
    
    def test_tool_timeout_with_partial_output(self):
        """测试带部分输出的超时错误"""
        err = ToolTimeoutError("gcc", 60, partial_output="partial")
        assert err.details["partial_output"] == "partial"


class TestValidationError:
    """验证异常测试"""
    
    def test_validation_error_basic(self):
        """测试基本验证错误"""
        err = ValidationError("Invalid input")
        assert err.field is None
        assert err.value is None
    
    def test_validation_error_with_field(self):
        """测试带字段的验证错误"""
        err = ValidationError("Invalid email", field="email", value="not-an-email")
        assert err.field == "email"
        assert err.value == "not-an-email"
    
    def test_validation_error_value_truncation(self):
        """测试值截断"""
        long_value = "x" * 200
        err = ValidationError("Too long", field="text", value=long_value)
        assert len(err.details["value"]) <= 100


class TestRollbackError:
    """回滚异常测试"""
    
    def test_rollback_error_basic(self):
        """测试基本回滚错误"""
        err = RollbackError("Rollback failed")
        assert err.backup_path is None
    
    def test_rollback_error_with_path(self):
        """测试带备份路径的回滚错误"""
        err = RollbackError("Rollback failed", backup_path="/path/to/backup")
        assert err.backup_path == "/path/to/backup"
        assert err.details["backup_path"] == "/path/to/backup"


class TestFileOperationError:
    """文件操作异常测试"""
    
    def test_file_error_basic(self):
        """测试基本文件错误"""
        err = FileOperationError("File operation failed")
        assert err.file_path is None
        assert err.operation is None
    
    def test_file_error_with_context(self):
        """测试带上下文的文件错误"""
        err = FileOperationError("Read failed", file_path="/path/file.txt", operation="read")
        assert err.file_path == "/path/file.txt"
        assert err.operation == "read"
        assert err.details["file_path"] == "/path/file.txt"
        assert err.details["operation"] == "read"


class TestExceptionRegistry:
    """异常注册表测试"""
    
    def test_registry_has_all_exceptions(self):
        """测试注册表包含所有异常"""
        assert "SprintCycleError" in EXCEPTION_REGISTRY
        assert "ConfigurationError" in EXCEPTION_REGISTRY
        assert "ToolExecutionError" in EXCEPTION_REGISTRY
    
    def test_get_exception_by_name_valid(self):
        """测试获取有效名称的异常类"""
        cls = get_exception_by_name("ToolExecutionError")
        assert cls == ToolExecutionError
    
    def test_get_exception_by_name_invalid(self):
        """测试获取无效名称的异常类"""
        cls = get_exception_by_name("NonExistentError")
        assert cls == SprintCycleError
