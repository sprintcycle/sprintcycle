"""测试 SprintCycle PRD 拆分器"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path
from sprintcycle.prd_splitter import PRDSplitter, SplitResult, split_prd_if_needed


class TestSplitResult:
    """测试 SplitResult 数据类"""
    
    def test_split_result_creation(self):
        """创建拆分结果"""
        result = SplitResult(
            original_prd="/path/to/original.yaml",
            split_prds=["/path/to/part1.yaml"],
            total_sprints=3,
            split_count=1,
            strategy_used="no_split"
        )
        assert result.original_prd == "/path/to/original.yaml"
        assert len(result.split_prds) == 1
        assert result.total_sprints == 3
        assert result.split_count == 1
        assert result.strategy_used == "no_split"


class TestPRDSplitter:
    """测试 PRDSplitter 类"""
    
    @pytest.fixture
    def sample_prd_file(self):
        """创建测试用 PRD 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            prd_data = {
                'project': {'name': 'TestProject', 'path': '/test'},
                'sprints': [
                    {
                        'name': 'Sprint 1 - 设计',
                        'tasks': [
                            {'task': '设计首页', 'agent': 'coder'},
                            {'task': '设计登录页', 'agent': 'coder'}
                        ]
                    },
                    {
                        'name': 'Sprint 2 - 开发',
                        'tasks': [
                            {'task': '实现首页', 'agent': 'coder'},
                            {'task': '实现登录页', 'agent': 'coder'}
                        ]
                    }
                ]
            }
            yaml.dump(prd_data, f, allow_unicode=True)
            return f.name
    
    @pytest.fixture
    def large_prd_file(self):
        """创建大型 PRD 文件（需要拆分）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            prd_data = {
                'project': {'name': 'LargeProject', 'path': '/test'},
                'sprints': [
                    {
                        'name': f'Sprint {i} - 模块{i}',
                        'tasks': [
                            {'task': f'任务{j}', 'agent': 'coder'}
                            for j in range(2)
                        ]
                    }
                    for i in range(5)  # 5个Sprint，超过默认的3个
                ]
            }
            yaml.dump(prd_data, f, allow_unicode=True)
            return f.name
    
    def test_splitter_default_config(self):
        """测试默认配置加载"""
        splitter = PRDSplitter()
        assert 'default' in splitter.config
        assert 'split_mode' in splitter.config
    
    def test_analyze_prd_small(self, sample_prd_file):
        """分析小型 PRD"""
        splitter = PRDSplitter()
        analysis = splitter.analyze_prd(sample_prd_file)
        
        assert analysis['sprint_count'] == 2
        assert analysis['total_tasks'] == 4
        assert analysis['estimated_time'] > 0
        assert analysis['needs_split'] is False
        
        # 清理
        os.unlink(sample_prd_file)
    
    def test_analyze_prd_large(self, large_prd_file):
        """分析大型 PRD"""
        splitter = PRDSplitter()
        analysis = splitter.analyze_prd(large_prd_file)
        
        assert analysis['sprint_count'] == 5
        assert analysis['needs_split'] is True
        
        # 清理
        os.unlink(large_prd_file)
    
    def test_check_needs_split_by_count(self):
        """检查是否需要拆分 - 按数量"""
        splitter = PRDSplitter()
        
        # 不需要拆分
        assert splitter._check_needs_split(2, 300) is False
        
        # 需要拆分
        assert splitter._check_needs_split(5, 300) is True
    
    def test_split_prd_no_need(self, sample_prd_file):
        """测试不需要拆分的 PRD"""
        splitter = PRDSplitter()
        result = splitter.split_prd(sample_prd_file)
        
        assert result.split_count == 1
        assert result.strategy_used == "no_split"
        assert len(result.split_prds) == 1
        assert result.split_prds[0] == sample_prd_file
        
        # 清理
        os.unlink(sample_prd_file)
    
    def test_split_prd_with_split(self, large_prd_file):
        """测试需要拆分的 PRD"""
        splitter = PRDSplitter()
        result = splitter.split_prd(large_prd_file)
        
        assert result.split_count == 2  # 5 sprints / 3 max = 2 parts
        assert result.strategy_used == "auto_split"
        assert len(result.split_prds) == 2
        
        # 验证拆分后的文件
        for split_path in result.split_prds:
            assert os.path.exists(split_path)
            with open(split_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                assert 'project' in data
                assert 'sprints' in data
        
        # 清理拆分文件
        for split_path in result.split_prds:
            os.unlink(split_path)
        os.unlink(large_prd_file)
    
    def test_extract_theme_with_keyword(self):
        """测试提取主题 - 包含关键词"""
        splitter = PRDSplitter()
        
        sprints = [{'name': '登录页面实现'}]
        theme = splitter._extract_theme(sprints, 0)
        assert theme == "login"
    
    def test_extract_theme_without_keyword(self):
        """测试提取主题 - 无关键词"""
        splitter = PRDSplitter()
        
        sprints = [{'name': 'Sprint 1'}]
        theme = splitter._extract_theme(sprints, 0)
        assert theme == "part1"
    
    def test_extract_theme_empty(self):
        """测试提取主题 - 空列表"""
        splitter = PRDSplitter()
        
        theme = splitter._extract_theme([], 0)
        assert theme == "part1"
    
    def test_get_split_execution_order(self):
        """测试获取执行顺序"""
        splitter = PRDSplitter()
        result = SplitResult(
            original_prd="/path/to/orig.yaml",
            split_prds=["/path/to/part1.yaml", "/path/to/part2.yaml"],
            total_sprints=5,
            split_count=2,
            strategy_used="auto_split"
        )
        
        order = splitter.get_split_execution_order(result)
        assert len(order) == 2
        assert order == result.split_prds


class TestSplitPrdIfNeeded:
    """测试便捷函数"""
    
    @pytest.fixture
    def small_prd_file(self):
        """创建小型 PRD 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            prd_data = {
                'project': {'name': 'SmallProject'},
                'sprints': [
                    {'name': 'Sprint 1', 'tasks': [{'task': 'T1'}]}
                ]
            }
            yaml.dump(prd_data, f, allow_unicode=True)
            return f.name
    
    def test_split_prd_if_needed_small(self, small_prd_file):
        """小型 PRD 不拆分"""
        result = split_prd_if_needed(small_prd_file)
        assert len(result) == 1
        assert result[0] == small_prd_file
        
        # 清理
        os.unlink(small_prd_file)
