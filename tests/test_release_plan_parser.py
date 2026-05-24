"""
ReleasePlan 解析器单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

from sprintcycle.domain.generic.models.release_plan.parser import ReleasePlanParser, ReleasePlanParseError, YAMLError
from sprintcycle.domain.generic.models import ReleasePlan, ExecutionMode


class TestReleasePlanParser:
    """ReleasePlan 解析器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.parser = ReleasePlanParser()
    
    def test_parse_valid_yaml(self):
        """测试解析有效执行计划 YAML"""
        yaml_src = """
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
      - description: |
          实现功能
        agent: "coder"
        target: "src/main.py"
"""
        plan = self.parser.parse_string(yaml_src)
        
        assert plan.project.name == "test-project"
        assert plan.project.path == "/root/test"
        assert plan.project.version == "v1.0.0"
        assert plan.mode == ExecutionMode.NORMAL
        assert len(plan.sprints) == 1
        assert plan.sprints[0].name == "Sprint 1"
        assert len(plan.sprints[0].tasks) == 1
        assert plan.sprints[0].tasks[0].agent == "coder"
        assert plan.sprints[0].tasks[0].spec_ref is None

    def test_parse_spec_ref_on_task(self):
        yaml_src = """
project:
  name: "p"
  path: "/tmp/p"
  version: "v1.0.0"
mode: "normal"
sprints:
  - name: "S1"
    tasks:
      - description: "do"
        agent: "coder"
        spec_ref: "docs/specs/feature.md"
"""
        plan = self.parser.parse_string(yaml_src)
        assert plan.sprints[0].tasks[0].spec_ref == "docs/specs/feature.md"

    def test_parse_evolution_yaml(self):
        """测试解析自进化模式 YAML"""
        yaml_src = """
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
      - description: |
          优化引擎
        agent: "coder"
        target: "sprintcycle/evolution/engine.py"
"""
        plan = self.parser.parse_string(yaml_src)
        
        assert plan.is_evolution_mode
        assert plan.evolution is not None
        assert len(plan.evolution.targets) == 2
        assert "优化性能" in plan.evolution.goals
    
    def test_parse_empty_file(self):
        """测试解析空文件"""
        with pytest.raises(ReleasePlanParseError):
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
        yaml_src = """
project:
  path: "/root/test"

sprints:
  - name: "Sprint 1"
    tasks:
      - description: "实现功能"
        agent: "coder"
"""
        with pytest.raises(ReleasePlanParseError) as exc_info:
            self.parser.parse_string(yaml_src)
        assert "project.name" in str(exc_info.value)
    
    def test_parse_missing_sprints(self):
        """测试解析缺少 sprints"""
        yaml_src = """
project:
  name: "test"
  path: "/root/test"
"""
        with pytest.raises(ReleasePlanParseError) as exc_info:
            self.parser.parse_string(yaml_src)
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
      - description: "测试任务"
        agent: "coder"
""")
            temp_path = f.name
        
        try:
            plan = self.parser.parse_file(temp_path)
            assert plan.project.name == "test-file"
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_not_exists(self):
        """测试文件不存在"""
        with pytest.raises(ReleasePlanParseError) as exc_info:
            self.parser.parse_file("/nonexistent/file.yaml")
        assert "文件不存在" in str(exc_info.value)


class TestReleasePlanModels:
    """ReleasePlan 模型测试"""
    
    def test_release_plan_total_tasks(self):
        """测试总任务数计算"""
        from sprintcycle.domain.generic.models import ProductAnchor, SprintDefinition, SprintBacklogItem
        
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    tasks=[
                        SprintBacklogItem(description="task1", agent="coder"),
                        SprintBacklogItem(description="task2", agent="coder"),
                    ]
                ),
                SprintDefinition(
                    name="Sprint 2",
                    tasks=[
                        SprintBacklogItem(description="task3", agent="tester"),
                    ]
                ),
            ]
        )
        
        assert plan.total_tasks == 3
    
    def test_release_plan_to_dict(self):
        """测试 ReleasePlan 序列化"""
        from sprintcycle.domain.generic.models import ProductAnchor
        
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
        )
        
        out_dict = plan.to_dict()
        assert out_dict["project"]["name"] == "test"
        assert out_dict["mode"] == "normal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
