"""
SprintCycle Server MCP 工具测试 - 覆盖率提升至50%+

覆盖:
1. list_tools() 工具注册
2. call_tool() 所有工具分支
3. 错误处理路径
4. 边界条件
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from sprintcycle.server import (
    Config, ToolType, AgentType, TaskStatus,
    ExecutionResult, Chorus, SprintChain,
    app, list_tools, call_tool
)
from sprintcycle.chorus import ExecutionLayer


class TestListTools:
    """测试 list_tools() 工具注册"""
    
    def test_list_tools_returns_list(self):
        """验证返回类型是 List[Tool]"""
        result = asyncio.run(list_tools())
        assert isinstance(result, list)
    
    def test_list_tools_has_expected_tools(self):
        """验证包含所有预期工具"""
        result = asyncio.run(list_tools())
        tool_names = [t.name for t in result]
        
        expected = [
            "sprintcycle_list_projects",
            "sprintcycle_list_tools", 
            "sprintcycle_status",
            "sprintcycle_get_sprint_plan",
            "sprintcycle_get_execution_detail",
            "sprintcycle_get_kb_stats",
            "sprintcycle_run_task",
            "sprintcycle_run_sprint",
            "sprintcycle_create_sprint",
            "sprintcycle_plan_from_prd",
            "sprintcycle_auto_run",
            "sprintcycle_run_sprint_by_name",
            "sprintcycle_playwright_verify",
            "sprintcycle_verify_frontend",
            "sprintcycle_verify_visual",
            "sprintcycle_scan_issues",
            "sprintcycle_autofix",
            "sprintcycle_rollback",
        ]
        
        for name in expected:
            assert name in tool_names, f"Missing tool: {name}"
    
    def test_list_tools_count(self):
        """验证工具数量"""
        result = asyncio.run(list_tools())
        assert len(result) >= 15


class TestCallToolListProjects:
    """测试 sprintcycle_list_projects"""
    
    @patch('sprintcycle.server.SprintChain')
    @patch('sprintcycle.server.Path')
    def test_list_projects_no_projects(self, mock_path, mock_chain):
        """测试无项目情况"""
        mock_path.return_value.glob.return_value = []
        
        result = asyncio.run(call_tool("sprintcycle_list_projects", {}))
        assert len(result) == 1
        assert "未找到项目" in result[0].text
    
    @patch('sprintcycle.server.SprintChain')
    @patch('sprintcycle.server.Path')
    def test_list_projects_with_projects(self, mock_path, mock_chain):
        """测试有项目情况"""
        mock_project = MagicMock()
        mock_project.name = "test-project"
        mock_project.is_dir.return_value = True
        mock_project.__truediv__ = lambda self, x: MagicMock(exists=MagicMock(return_value=True))
        
        mock_path.return_value.glob.return_value = [mock_project]
        
        mock_chain_instance = MagicMock()
        mock_chain_instance.get_kb_stats.return_value = {
            'total': 10, 'success_rate': 80
        }
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_list_projects", {}))
        assert len(result) == 1
        assert "test-project" in result[0].text


class TestCallToolListTools:
    """测试 sprintcycle_list_tools"""
    
    def test_list_tools_executor(self):
        """测试列出可用工具"""
        executor = ExecutionLayer()
        result = asyncio.run(call_tool("sprintcycle_list_tools", {}))
        assert len(result) == 1
        assert "可用工具" in result[0].text


class TestCallToolStatus:
    """测试 sprintcycle_status"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    @patch('sprintcycle.server.ExecutionLayer')
    def test_status_basic(self, mock_layer, mock_chain, temp_project):
        """测试基本状态检查"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.get_sprints.return_value = []
        mock_chain_instance.config = {"project": {"name": "TestProject"}}
        mock_chain_instance.get_kb_stats.return_value = {
            'total': 5, 'success_rate': 80, 'avg_duration': 10.5
        }
        mock_chain.return_value = mock_chain_instance
        
        mock_layer_instance = MagicMock()
        mock_layer_instance.list_available.return_value = {"cursor": True, "claude": False}
        mock_layer.return_value = mock_layer_instance
        
        result = asyncio.run(call_tool("sprintcycle_status", {"project_path": temp_project}))
        assert len(result) == 1
        assert "SprintCycle 状态" in result[0].text


class TestCallToolSprintPlan:
    """测试 sprintcycle_get_sprint_plan"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_sprint_plan_empty(self, mock_chain, temp_project):
        """测试无 Sprint 情况"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.get_sprints.return_value = []
        mock_chain_instance.config = {"project": {"name": "Empty"}}
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_get_sprint_plan", {"project_path": temp_project}))
        assert len(result) == 1
        assert "Empty" in result[0].text
    
    @patch('sprintcycle.server.SprintChain')
    def test_sprint_plan_with_sprints(self, mock_chain, temp_project):
        """测试有 Sprint 情况"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.get_sprints.return_value = [
            {"name": "Sprint 1", "status": "completed", "goals": ["goal1"]},
            {"name": "Sprint 2", "status": "in_progress", "goals": ["goal2"]},
            {"name": "Sprint 3", "status": "pending", "goals": ["goal3"]},
        ]
        mock_chain_instance.config = {"project": {"name": "MultiSprint"}}
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_get_sprint_plan", {"project_path": temp_project}))
        assert len(result) == 1
        text = result[0].text
        assert "MultiSprint" in text
        assert "Sprint 1" in text
        assert "Sprint 2" in text


class TestCallToolExecutionDetail:
    """测试 sprintcycle_get_execution_detail"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_execution_detail_empty(self, mock_chain, temp_project):
        """测试无执行结果"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.get_results.return_value = []
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_get_execution_detail", {"project_path": temp_project}))
        assert len(result) == 1
        assert "执行详情" in result[0].text
    
    @patch('sprintcycle.server.SprintChain')
    def test_execution_detail_with_results(self, mock_chain, temp_project):
        """测试有执行结果"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.get_results.return_value = [
            {"success": True, "tool": "cursor", "task": "fix bug", "duration": 5.0, "retries": 0},
            {"success": False, "tool": "claude", "task": "add feature", "duration": 10.0, "retries": 2},
        ]
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_get_execution_detail", {"project_path": temp_project}))
        assert len(result) == 1
        text = result[0].text
        assert "成功" in text
        assert "失败" in text


class TestCallToolKbStats:
    """测试 sprintcycle_get_kb_stats"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_kb_stats(self, mock_chain, temp_project):
        """测试知识库统计"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.get_kb_stats.return_value = {
            'total': 100, 'success': 85, 'success_rate': 85, 'avg_duration': 12.5
        }
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_get_kb_stats", {"project_path": temp_project}))
        assert len(result) == 1
        text = result[0].text
        assert "知识库统计" in text
        assert "100" in text


class TestCallToolRunTask:
    """测试 sprintcycle_run_task"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_run_task_success(self, mock_chain, temp_project):
        """测试任务执行成功"""
        mock_chain_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.retries = 0
        mock_result.tool = "cursor"
        mock_result.duration = 5.5
        mock_result.files_changed = "a.py, b.py"
        mock_result.error = None
        mock_chain_instance.run_task.return_value = mock_result
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_task", {
            "project_path": temp_project,
            "task": "fix the bug"
        }))
        assert len(result) == 1
        assert "成功" in result[0].text
    
    @patch('sprintcycle.server.SprintChain')
    def test_run_task_with_retry(self, mock_chain, temp_project):
        """测试重试任务"""
        mock_chain_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.retries = 3
        mock_result.tool = "claude"
        mock_result.duration = 15.0
        mock_result.files_changed = None
        mock_result.error = None
        mock_chain_instance.run_task.return_value = mock_result
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_task", {
            "project_path": temp_project,
            "task": "complex task",
            "agent": "coder",
            "tool": "claude"
        }))
        assert len(result) == 1
        assert "重试 3" in result[0].text
    
    @patch('sprintcycle.server.SprintChain')
    def test_run_task_failure(self, mock_chain, temp_project):
        """测试任务失败"""
        mock_chain_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.retries = 1
        mock_result.tool = "aider"
        mock_result.duration = 3.0
        mock_result.files_changed = None
        mock_result.error = "Connection timeout"
        mock_chain_instance.run_task.return_value = mock_result
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_task", {
            "project_path": temp_project,
            "task": "failing task"
        }))
        assert len(result) == 1
        assert "失败" in result[0].text


class TestCallToolRunSprint:
    """测试 sprintcycle_run_sprint"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_run_sprint(self, mock_chain, temp_project):
        """测试 Sprint 执行"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.run_sprint.return_value = {
            "sprint_name": "Sprint 1",
            "total": 3,
            "success": 2,
            "results": [
                {"success": True, "tool": "cursor", "task": "task1", "retries": 0},
                {"success": True, "tool": "claude", "task": "task2", "retries": 0},
                {"success": False, "tool": "aider", "task": "task3", "retries": 1},
            ]
        }
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_sprint", {
            "project_path": temp_project,
            "sprint_name": "Sprint 1",
            "tasks": ["task1", "task2", "task3"]
        }))
        assert len(result) == 1
        text = result[0].text
        assert "Sprint 1" in text
        assert "2/3" in text


class TestCallToolCreateSprint:
    """测试 sprintcycle_create_sprint"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_create_sprint(self, mock_chain, temp_project):
        """测试创建 Sprint"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.create_sprint.return_value = {
            "name": "New Sprint",
            "goals": ["goal1", "goal2"]
        }
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_create_sprint", {
            "project_path": temp_project,
            "sprint_name": "New Sprint",
            "goals": ["goal1", "goal2"]
        }))
        assert len(result) == 1
        assert "Sprint 已创建" in result[0].text
        assert "New Sprint" in result[0].text


class TestCallToolPlanFromPRD:
    """测试 sprintcycle_plan_from_prd"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_plan_from_prd_success(self, mock_chain, temp_project):
        """测试从 PRD 生成计划成功"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.auto_plan_from_prd.return_value = {
            "sprints": [
                {"name": "Sprint A", "tasks": ["t1", "t2"]},
                {"name": "Sprint B", "tasks": ["t3"]},
            ]
        }
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_plan_from_prd", {
            "project_path": temp_project,
            "prd_path": "/tmp/prd.md"
        }))
        assert len(result) == 1
        assert "PRD 生成" in result[0].text
        assert "2" in result[0].text
    
    @patch('sprintcycle.server.SprintChain')
    def test_plan_from_prd_error(self, mock_chain, temp_project):
        """测试从 PRD 生成计划失败"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.auto_plan_from_prd.return_value = {
            "error": "PRD file not found"
        }
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_plan_from_prd", {
            "project_path": temp_project,
            "prd_path": "/tmp/missing.md"
        }))
        assert len(result) == 1
        assert "错误" in result[0].text


class TestCallToolAutoRun:
    """测试 sprintcycle_auto_run"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_auto_run(self, mock_chain, temp_project):
        """测试自动执行所有 Sprint"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.run_all_sprints.return_value = [
            {"sprint_name": "Sprint 1", "success": 2, "total": 2},
            {"sprint_name": "Sprint 2", "success": 1, "total": 3},
        ]
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_auto_run", {
            "project_path": temp_project
        }))
        assert len(result) == 1
        assert "2" in result[0].text


class TestCallToolRunSprintByName:
    """测试 sprintcycle_run_sprint_by_name"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_run_sprint_by_name_success(self, mock_chain, temp_project):
        """测试按名称执行 Sprint"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.run_sprint_by_name.return_value = {
            "sprint_name": "Beta",
            "total": 5,
            "success": 4,
            "results": [
                {"success": True, "tool": "cursor", "task": "task1", "retries": 0},
            ]
        }
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_sprint_by_name", {
            "project_path": temp_project,
            "sprint_name": "Beta"
        }))
        assert len(result) == 1
        assert "Beta" in result[0].text
    
    @patch('sprintcycle.server.SprintChain')
    def test_run_sprint_by_name_error(self, mock_chain, temp_project):
        """测试按名称执行 Sprint 出错"""
        mock_chain_instance = MagicMock()
        mock_chain_instance.run_sprint_by_name.return_value = {
            "error": "Sprint not found"
        }
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_sprint_by_name", {
            "project_path": temp_project,
            "sprint_name": "Missing"
        }))
        assert len(result) == 1
        assert "错误" in result[0].text


class TestCallToolPlaywrightVerify:
    """测试 sprintcycle_playwright_verify"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_playwright_verify_missing_url(self):
        """测试缺少 URL 参数"""
        result = asyncio.run(call_tool("sprintcycle_playwright_verify", {}))
        assert len(result) == 1
        assert "请提供 url" in result[0].text
    
    def test_playwright_verify_import_error(self):
        """测试 Playwright 导入失败"""
        result = asyncio.run(call_tool("sprintcycle_playwright_verify", {
            "project_path": ".",
            "url": "http://localhost:3000"
        }))
        assert len(result) == 1


class TestCallToolVerifyFrontend:
    """测试 sprintcycle_verify_frontend"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_verify_frontend_missing_url(self):
        """测试缺少 URL"""
        result = asyncio.run(call_tool("sprintcycle_verify_frontend", {}))
        assert len(result) == 1
        assert "请提供 url" in result[0].text


class TestCallToolVerifyVisual:
    """测试 sprintcycle_verify_visual"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_verify_visual_missing_url(self):
        """测试缺少 URL"""
        result = asyncio.run(call_tool("sprintcycle_verify_visual", {}))
        assert len(result) == 1
        assert "请提供 url" in result[0].text


class TestCallToolScanIssues:
    """测试 sprintcycle_scan_issues"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_scan_issues_import_error(self, temp_project):
        """测试 ProjectScanner 导入失败"""
        result = asyncio.run(call_tool("sprintcycle_scan_issues", {
            "project_path": temp_project
        }))
        assert len(result) == 1


class TestCallToolAutofix:
    """测试 sprintcycle_autofix"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_autofix_import_error(self, temp_project):
        """测试 AutoFixEngine 导入失败"""
        result = asyncio.run(call_tool("sprintcycle_autofix", {
            "project_path": temp_project
        }))
        assert len(result) == 1


class TestCallToolRollback:
    """测试 sprintcycle_rollback"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_rollback_import_error(self, temp_project):
        """测试 AutoFixEngine 导入失败"""
        result = asyncio.run(call_tool("sprintcycle_rollback", {
            "project_path": temp_project
        }))
        assert len(result) == 1


class TestCallToolUnknown:
    """测试未知工具"""
    
    def test_unknown_tool(self):
        """测试未知工具处理"""
        result = asyncio.run(call_tool("sprintcycle_unknown_tool", {}))
        assert len(result) == 1
        assert "未知工具" in result[0].text


class TestCallToolEdgeCases:
    """边界条件和错误处理"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_run_task_no_files(self, mock_chain, temp_project):
        """测试无文件修改的任务"""
        mock_chain_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.retries = 0
        mock_result.tool = "cursor"
        mock_result.duration = 1.0
        mock_result.files_changed = None
        mock_result.error = None
        mock_chain_instance.run_task.return_value = mock_result
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_task", {
            "project_path": temp_project,
            "task": "test"
        }))
        assert "无修改" in result[0].text
    
    @patch('sprintcycle.server.SprintChain')
    def test_run_task_long_error(self, mock_chain, temp_project):
        """测试长错误消息截断"""
        mock_chain_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.retries = 0
        mock_result.tool = "claude"
        mock_result.duration = 1.0
        mock_result.files_changed = None
        mock_result.error = "A" * 500
        mock_chain_instance.run_task.return_value = mock_result
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_task", {
            "project_path": temp_project,
            "task": "test"
        }))
        assert len(result[0].text) < len(mock_result.error) + 100


class TestCallToolToolAgentEnum:
    """测试工具和代理枚举转换"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @patch('sprintcycle.server.SprintChain')
    def test_with_agent_enum(self, mock_chain, temp_project):
        """测试带代理枚举"""
        mock_chain_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.retries = 0
        mock_result.tool = "cursor"
        mock_result.duration = 1.0
        mock_result.files_changed = "x.py"
        mock_result.error = None
        mock_chain_instance.run_task.return_value = mock_result
        mock_chain.return_value = mock_chain_instance
        
        result = asyncio.run(call_tool("sprintcycle_run_task", {
            "project_path": temp_project,
            "task": "test",
            "agent": "coder",
            "tool": "cursor"
        }))
        assert "成功" in result[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=sprintcycle.server", "--cov-report=term-missing"])
