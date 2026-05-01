"""
PRD 解析器

解析 YAML 格式的 PRD 文件，转换为 Python 数据结构
"""

import yaml
import logging
from pathlib import Path
from typing import Union, Dict, Any, Optional

from .models import (
    PRD, PRDProject, PRDSprint, PRDTask,
    PRDEvolutionParams, ExecutionMode
)
from .validator import PRDValidator, ValidationResult

logger = logging.getLogger(__name__)


class YAMLError(ValueError):
    """YAML 解析错误"""
    pass


class PRDParseError(ValueError):
    """PRD 解析错误"""
    pass


class PRDParser:
    """
    PRD 文件解析器
    
    支持解析 YAML 格式的 PRD 文件，提取项目信息、Sprint 定义和任务配置
    """
    
    # Agent 类型映射
    VALID_AGENTS = {"coder", "evolver", "tester"}
    
    # 执行模式映射
    MODE_MAPPING = {
        "normal": ExecutionMode.NORMAL,
        "evolution": ExecutionMode.EVOLUTION,
        "self_evolution": ExecutionMode.EVOLUTION,
    }
    
    def __init__(self, validator: Optional[PRDValidator] = None):
        """
        初始化解析器
        
        Args:
            validator: PRD 验证器（可选）
        """
        self.validator = validator or PRDValidator()
    
    def parse_file(self, file_path: Union[str, Path]) -> PRD:
        """
        解析 PRD 文件
        
        Args:
            file_path: PRD 文件路径
            
        Returns:
            PRD 对象
            
        Raises:
            YAMLError: YAML 格式错误
            PRDParseError: PRD 结构错误
        """
        path = Path(file_path)
        
        if not path.exists():
            raise PRDParseError(f"文件不存在: {path}")
        
        if not path.suffix in {".yaml", ".yml"}:
            raise PRDParseError(f"不支持的文件格式: {path.suffix}，仅支持 .yaml 或 .yml")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise YAMLError(f"YAML 解析失败: {e}")
        except UnicodeDecodeError:
            raise YAMLError(f"文件编码错误，请使用 UTF-8 编码")
        except Exception as e:
            raise YAMLError(f"读取文件失败: {e}")
        
        if data is None:
            raise PRDParseError("PRD 文件为空")
        
        return self.parse_dict(data, source_path=str(path))
    
    def parse_string(self, content: str, source_path: str = "<string>") -> PRD:
        """
        解析 PRD 字符串
        
        Args:
            content: PRD YAML 内容
            source_path: 来源路径（用于错误提示）
            
        Returns:
            PRD 对象
        """
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise YAMLError(f"YAML 解析失败: {e}")
        
        if data is None:
            raise PRDParseError("PRD 内容为空")
        
        return self.parse_dict(data, source_path=source_path)
    
    def parse_dict(self, data: Dict[str, Any], source_path: str = "<dict>") -> PRD:
        """
        解析 PRD 字典数据
        
        Args:
            data: PRD 字典数据
            source_path: 来源路径（用于错误提示）
            
        Returns:
            PRD 对象
        """
        try:
            # 解析项目信息
            project = self._parse_project(data.get("project", {}))
            
            # 解析执行模式
            mode_str = data.get("mode", "normal")
            mode = self.MODE_MAPPING.get(mode_str.lower(), ExecutionMode.NORMAL)
            
            # 解析进化配置
            evolution = None
            if mode == ExecutionMode.EVOLUTION:
                evolution = self._parse_evolution(data.get("evolution", {}))
            
            # 解析 Sprint 列表
            sprints_data = data.get("sprints", [])
            if not sprints_data:
                raise PRDParseError(f"{source_path}: 缺少 sprints 定义")
            
            sprints = [self._parse_sprint(s, i) for i, s in enumerate(sprints_data)]
            
            # 构建 PRD 对象
            prd = PRD(
                project=project,
                mode=mode,
                evolution=evolution,
                sprints=sprints,
                metadata={"source_path": source_path},
            )
            
            # 验证 PRD
            validation_result = self.validator.validate(prd)
            if not validation_result.is_valid:
                errors = "\n  - ".join(validation_result.errors)
                raise PRDParseError(f"{source_path}: PRD 验证失败:\n  - {errors}")
            
            logger.info(f"✅ 成功解析 PRD: {project.name} (包含 {len(sprints)} 个 Sprint, {prd.total_tasks} 个任务)")
            return prd
            
        except PRDParseError:
            raise
        except Exception as e:
            raise PRDParseError(f"{source_path}: 解析失败: {e}")
    
    def _parse_project(self, data: Dict[str, Any]) -> PRDProject:
        """解析项目信息"""
        name = data.get("name")
        if not name:
            raise PRDParseError("缺少 project.name")
        
        path = data.get("path")
        if not path:
            raise PRDParseError("缺少 project.path")
        
        return PRDProject(
            name=name,
            path=path,
            version=data.get("version", "v1.0.0"),
        )
    
    def _parse_evolution(self, data: Dict[str, Any]) -> PRDEvolutionParams:
        """解析进化配置"""
        return PRDEvolutionParams(
            targets=data.get("targets", []),
            goals=data.get("goals", []),
            constraints=data.get("constraints", []),
            max_variations=data.get("max_variations", 5),
            iterations=data.get("iterations", 3),
        )
    
    def _parse_sprint(self, data: Dict[str, Any], index: int) -> PRDSprint:
        """解析 Sprint 定义"""
        name = data.get("name")
        if not name:
            raise PRDParseError(f"Sprint #{index + 1}: 缺少 name")
        
        # 解析目标列表（兼容 goals 和 goal 两种写法）
        goals = data.get("goals", [])
        if not goals and "goal" in data:
            goals = [data["goal"]] if isinstance(data["goal"], str) else data["goal"]
        
        # 解析任务列表
        tasks_data = data.get("tasks", [])
        if not tasks_data:
            raise PRDParseError(f"Sprint '{name}': 缺少 tasks")
        
        tasks = [self._parse_task(t, i, name) for i, t in enumerate(tasks_data)]
        
        return PRDSprint(
            name=name,
            goals=goals,
            tasks=tasks,
        )
    
    def _parse_task(self, data: Dict[str, Any], index: int, sprint_name: str) -> PRDTask:
        """解析任务定义"""
        # 解析任务描述（支持多种格式）
        task_content = data.get("task") or data.get("description") or data.get("name", "")
        if not task_content:
            raise PRDParseError(f"Sprint '{sprint_name}' Task #{index + 1}: 缺少 task 描述")
        
        # 解析 Agent 类型
        agent = data.get("agent", "coder")
        if agent not in self.VALID_AGENTS:
            logger.warning(f"Sprint '{sprint_name}' Task #{index + 1}: 未知的 agent 类型 '{agent}'，使用 'coder'")
            agent = "coder"
        
        # 解析目标路径
        target = data.get("target")
        
        # 解析约束条件
        constraints = data.get("constraints", [])
        if isinstance(constraints, str):
            constraints = [constraints]
        
        return PRDTask(
            task=task_content,
            agent=agent,
            target=target,
            constraints=constraints,
            expected_output=data.get("expected_output"),
            timeout=data.get("timeout", 600),
        )
    
    @classmethod
    def from_prd(cls, prd: PRD) -> dict[str, Any]:
        """
        从 PRD 对象创建调度信息（用于后续调度）
        
        Args:
            prd: PRD 对象
            
        Returns:
            调度信息字典
        """
        return {
            "project": prd.project.to_dict(),
            "mode": prd.mode.value,
            "total_sprints": len(prd.sprints),
            "total_tasks": prd.total_tasks,
            "is_evolution": prd.is_evolution_mode,
        }
