"""错误处理架构单元测试"""
import asyncio
import os
import tempfile
import pytest


class TestErrorKnowledgeBase:
    """测试错误知识库"""
    
    @pytest.fixture
    def kb(self):
        from sprintcycle.execution.error_knowledge import ErrorKnowledgeBase, reset_error_knowledge_base
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = ErrorKnowledgeBase(storage_path=f"{tmpdir}/test_knowledge", auto_save=False)
            yield kb
            reset_error_knowledge_base()
    
    def test_default_patterns_loaded(self, kb):
        assert len(kb.patterns) > 0
        assert len(kb.patterns) >= 10
    
    def test_pattern_match_nameerror(self, kb):
        match = kb.match("NameError: name 'x' is not defined")
        assert match is not None
        assert match.pattern.error_type == "NameError"
    
    def test_pattern_match_importerror(self, kb):
        match = kb.match("ModuleNotFoundError: No module named 'requests'")
        assert match is not None
        assert match.pattern.error_type == "ImportError"
    
    def test_add_custom_pattern(self, kb):
        from sprintcycle.execution.error_knowledge import ErrorPattern
        pattern = ErrorPattern(
            pattern=r"CustomError: (.+)", error_type="CustomError",
            root_cause="自定义错误", suggested_fix="处理自定义错误",
        )
        pattern_id = kb.add_pattern(pattern)
        assert kb.get_pattern(pattern_id) is not None


class TestErrorRouter:
    """测试错误路由器"""
    
    @pytest.fixture
    def router(self):
        from sprintcycle.execution.error_router import ErrorRouter
        return ErrorRouter()
    
    @pytest.mark.asyncio
    async def test_route_simple_error(self, router):
        result = await router.route("NameError: name 'x' is not defined")
        assert result is not None
        assert result.level.value in ["level_2_pattern", "level_1_static", "level_3_llm"]


class TestRollbackManager:
    """测试回滚管理器"""
    
    @pytest.fixture
    def rollback_mgr(self):
        from sprintcycle.execution.rollback import RollbackManager
        with tempfile.TemporaryDirectory() as tmpdir:
            yield RollbackManager(backup_dir=f"{tmpdir}/test_backups", max_backups_per_file=5)
    
    @pytest.mark.asyncio
    async def test_backup_file(self, rollback_mgr):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# test file\nprint('hello')\n")
            temp_path = f.name
        try:
            record = await rollback_mgr.backup(temp_path, "测试备份")
            assert record is not None
            assert record.backup_id.startswith("bk_")
        finally:
            os.unlink(temp_path)


class TestErrorHandler:
    """测试统一错误处理器"""
    
    @pytest.fixture
    def handler(self):
        from sprintcycle.execution.error_handler import ErrorHandler
        return ErrorHandler(enable_rollback=False, enable_cache=False)
    
    @pytest.mark.asyncio
    async def test_handle_nameerror(self, handler):
        from sprintcycle.execution.error_handler import ErrorContext
        context = ErrorContext(error_log="NameError: name 'x' is not defined", project_path=".")
        result = await handler.handle(context)
        assert result is not None
        assert result.error_log == context.error_log
        assert "ERROR_DETECTED" in result.events_emitted


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_flow(self):
        from sprintcycle.execution.error_handler import ErrorHandler, ErrorContext
        from sprintcycle.execution.events import EventType
        
        handler = ErrorHandler(enable_rollback=False, enable_cache=False)
        context = ErrorContext(error_log="SyntaxError: invalid syntax", project_path=".")
        result = await handler.handle(context)
        assert result is not None
        assert result.duration > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
