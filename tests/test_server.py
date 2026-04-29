"""SprintCycle Server 模块测试"""
import pytest
import tempfile
from pathlib import Path
from sprintcycle.server import (
    Config, ToolType, AgentType, TaskStatus,
    ExecutionResult, TaskProgress, KnowledgeBase,
    ExecutionLayer, ChorusAdapter, Chorus, SprintChain
)

class TestServerExports:
    def test_config_exists(self):
        assert Config is not None
    
    def test_tool_type_exists(self):
        assert ToolType is not None
    
    def test_agent_type_exists(self):
        assert AgentType is not None
    
    def test_task_status_exists(self):
        assert TaskStatus is not None
    
    def test_chorus_exists(self):
        assert Chorus is not None
    
    def test_sprint_chain_exists(self):
        assert SprintChain is not None


class TestChorus:
    def test_chorus_import(self):
        chorus = Chorus()
        assert chorus is not None


class TestSprintChain:
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_sprint_chain_import(self, temp_project):
        chain = SprintChain(project_path=temp_project)
        assert chain is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
