"""扩展测试 SprintChain 功能"""
import pytest
import tempfile
import os
from sprintcycle.sprint_chain import SprintChain


class TestSprintChain:
    """测试 SprintChain 类"""
    
    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "test_project")
            os.makedirs(project_path)
            yield project_path
    
    @pytest.fixture
    def chain(self, temp_project):
        """创建 SprintChain 实例"""
        return SprintChain(project_path=temp_project)
    
    def test_create_chain(self, chain, temp_project):
        """测试创建链"""
        assert chain.project_path.name == "test_project"
    
    def test_project_path(self, chain, temp_project):
        """测试项目路径"""
        assert "test_project" in str(chain.project_path)
    
    def test_default_review_disabled(self, chain):
        """测试默认禁用审查"""
        assert chain.review_enabled is False
    
    def test_review_enabled(self, temp_project):
        """测试启用审查"""
        chain = SprintChain(project_path=temp_project, review_enabled=True)
        assert chain.review_enabled is True


class TestSprintChainConfig:
    """测试 SprintChain 配置"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "test_project")
            os.makedirs(project_path)
            yield project_path
    
    @pytest.fixture
    def chain(self, temp_project):
        return SprintChain(project_path=temp_project)
    
    def test_load_config_default(self, chain):
        """测试加载默认配置"""
        config = chain._load_config()
        assert isinstance(config, dict)
        assert "project" in config
    
    def test_get_sprints_empty(self, chain):
        """测试获取空的 sprints"""
        sprints = chain.get_sprints()
        assert isinstance(sprints, list)


class TestSprintChainCreate:
    """测试创建 Sprint"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "test_project")
            os.makedirs(project_path)
            yield project_path
    
    @pytest.fixture
    def chain(self, temp_project):
        return SprintChain(project_path=temp_project)
    
    def test_create_sprint(self, chain):
        """测试创建 Sprint"""
        sprint = chain.create_sprint(name="Sprint 1", goals=["Goal 1", "Goal 2"])
        assert sprint["name"] == "Sprint 1"
        assert len(sprint["goals"]) == 2
        assert sprint["status"] == "pending"
    
    def test_get_sprints_after_create(self, chain):
        """测试创建后获取 sprints"""
        chain.create_sprint(name="Sprint 1", goals=["Goal 1"])
        sprints = chain.get_sprints()
        assert len(sprints) == 1
        assert sprints[0]["name"] == "Sprint 1"


class TestSprintChainKnowledgeBase:
    """测试知识库功能"""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "test_project")
            os.makedirs(project_path)
            yield project_path
    
    @pytest.fixture
    def chain(self, temp_project):
        return SprintChain(project_path=temp_project)
    
    def test_knowledge_base_exists(self, chain):
        """测试知识库存在"""
        assert hasattr(chain, 'kb')
    
    def test_get_kb_stats(self, chain):
        """测试获取知识库统计"""
        stats = chain.get_kb_stats()
        assert isinstance(stats, dict)
