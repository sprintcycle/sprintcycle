"""
PRD 解析器单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

from sprintcycle.prd.parser import PRDParser, PRDParseError, YAMLError
from sprintcycle.prd.models import PRD, ExecutionMode


class TestPRDParser:
    """PRD 解析器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.parser = PRDParser()
    
    def test_parse_valid_prd(self):
        """测试解析有效 PRD"""
        prd_content = """
project:
  name: "test-project"
  path: "/root/test"
  version: "v1.0.0"

mode: "normal"

sprints:
  - name: "Sprint 1"
    goals:
      - "完成开发"
    tasks:
      - task: |
          实现功能
        agent: "coder"
        target: "src/main.py"
"""
        prd = self.parser.parse_string(prd_content)
        
        assert prd.project.name == "test-project"
        assert prd.project.path == "/root/test"
        assert prd.project.version == "v1.0.0"
        assert prd.mode == ExecutionMode.NORMAL
        assert len(prd.sprints) == 1
        assert prd.sprints[0].name == "Sprint 1"
        assert len(prd.sprints[0].tasks) == 1
        assert prd.sprints[0].tasks[0].agent == "coder"
    
    def test_parse_evolution_prd(self):
        """测试解析自进化 PRD"""
        prd_content = """
project:
  name: "sprintcycle"
  path: "/root/sprintcycle"
  version: "v0.6.0"

mode: "evolution"

evolution:
  targets:
    - "sprintcycle/evolution/engine.py"
    - "sprintcycle/evolution/client.py"
  goals:
    - "优化性能"
    - "提升可读性"
  constraints:
    - "保持 API 兼容"

sprints:
  - name: "Sprint 1"
    tasks:
      - task: |
          优化引擎
        agent: "evolver"
        target: "sprintcycle/evolution/engine.py"
"""
        prd = self.parser.parse_string(prd_content)
        
        assert prd.is_evolution_mode
        assert prd.evolution is not None
        assert len(prd.evolution.targets) == 2
        assert "优化性能" in prd.evolution.goals
    
    def test_parse_empty_file(self):
        """测试解析空文件"""
        with pytest.raises(PRDParseError):
            self.parser.parse_string("")
    
    def test_parse_invalid_yaml(self):
        """测试解析无效 YAML"""
        invalid_yaml = """
project:
  name: "test"
  - invalid list
"""
        with pytest.raises(YAMLError):
            self.parser.parse_string(invalid_yaml)
    
    def test_parse_missing_project_name(self):
        """测试解析缺少项目名"""
        prd_content = """
project:
  path: "/root/test"

sprints:
  - name: "Sprint 1"
    tasks:
      - task: "实现功能"
        agent: "coder"
"""
        with pytest.raises(PRDParseError) as exc_info:
            self.parser.parse_string(prd_content)
        assert "project.name" in str(exc_info.value)
    
    def test_parse_missing_sprints(self):
        """测试解析缺少 sprints"""
        prd_content = """
project:
  name: "test"
  path: "/root/test"
"""
        with pytest.raises(PRDParseError) as exc_info:
            self.parser.parse_string(prd_content)
        assert "sprints" in str(exc_info.value)
    
    def test_parse_file(self):
        """测试从文件解析"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
project:
  name: "test-file"
  path: "/root/test"
  version: "v1.0.0"

sprints:
  - name: "Sprint 1"
    tasks:
      - task: "测试任务"
        agent: "coder"
""")
            temp_path = f.name
        
        try:
            prd = self.parser.parse_file(temp_path)
            assert prd.project.name == "test-file"
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_not_exists(self):
        """测试文件不存在"""
        with pytest.raises(PRDParseError) as exc_info:
            self.parser.parse_file("/nonexistent/file.yaml")
        assert "文件不存在" in str(exc_info.value)


class TestPRDModels:
    """PRD 模型测试"""
    
    def test_prd_total_tasks(self):
        """测试总任务数计算"""
        from sprintcycle.prd.models import PRDProject, PRDSprint, PRDTask
        
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
            sprints=[
                PRDSprint(
                    name="Sprint 1",
                    tasks=[
                        PRDTask(task="task1", agent="coder"),
                        PRDTask(task="task2", agent="coder"),
                    ]
                ),
                PRDSprint(
                    name="Sprint 2",
                    tasks=[
                        PRDTask(task="task3", agent="tester"),
                    ]
                ),
            ]
        )
        
        assert prd.total_tasks == 3
    
    def test_prd_to_dict(self):
        """测试 PRD 序列化"""
        from sprintcycle.prd.models import PRDProject
        
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
        )
        
        prd_dict = prd.to_dict()
        assert prd_dict["project"]["name"] == "test"
        assert prd_dict["mode"] == "normal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
