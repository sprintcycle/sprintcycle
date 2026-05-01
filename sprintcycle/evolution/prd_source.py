"""
Evolution PRD Source - PRD来源抽象

定义多种PRD来源:
- ManualPRDSource: 读取人工编写的PRD文件
- DiagnosticPRDSource: 诊断驱动生成PRD
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import logging

logger = logging.getLogger(__name__)


class PRDSourceType(Enum):
    """PRD来源类型"""
    MANUAL = "manual"
    DIAGNOSTIC = "diagnostic"


@dataclass
class EvolutionPRD:
    """
    进化专用PRD数据结构
    
    与 PRD 模型的区别:
    - 包含更多元数据用于进化追踪
    - 目标更明确（覆盖率、复杂度等可量化指标）
    """
    name: str
    version: str
    path: str
    goals: List[str] = field(default_factory=list)
    sprints: List[Dict[str, Any]] = field(default_factory=list)
    source_type: PRDSourceType = PRDSourceType.MANUAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 进化相关元数据
    confidence: float = 0.5  # PRD生成置信度
    expected_benefit: float = 0.0  # 预期收益
    priority: int = 0  # 优先级
    
    @property
    def total_tasks(self) -> int:
        """总任务数"""
        return sum(len(sprint.get("tasks", [])) for sprint in self.sprints)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "path": self.path,
            "goals": self.goals,
            "sprints": self.sprints,
            "source_type": self.source_type.value,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "expected_benefit": self.expected_benefit,
            "priority": self.priority,
            "total_tasks": self.total_tasks,
        }


class PRDSource(ABC):
    """
    PRD来源抽象基类
    
    所有PRD来源必须实现:
    - generate(): 生成EvolutionPRD列表
    - get_source_type(): 返回来源类型
    """
    
    @abstractmethod
    def generate(self, project_path: str) -> List[EvolutionPRD]:
        """
        生成PRD列表
        
        Args:
            project_path: 项目路径
            
        Returns:
            EvolutionPRD列表
        """
        pass
    
    @abstractmethod
    def get_source_type(self) -> PRDSourceType:
        """返回来源类型"""
        pass


class ManualPRDSource(PRDSource):
    """
    人工PRD来源
    
    从 prd/ 目录读取 YAML 文件生成PRD
    """
    
    def __init__(self, prd_dir: str = "prd"):
        """
        初始化人工PRD来源
        
        Args:
            prd_dir: PRD目录路径（相对于项目根目录）
        """
        self._prd_dir = Path(prd_dir)
    
    def generate(self, project_path: str) -> List[EvolutionPRD]:
        """
        从PRD目录读取YAML文件生成EvolutionPRD
        
        Args:
            project_path: 项目根目录路径
            
        Returns:
            EvolutionPRD列表
        """
        prd_dir = Path(project_path) / self._prd_dir
        if not prd_dir.exists():
            logger.warning(f"PRD目录不存在: {prd_dir}")
            return []
        
        prds = []
        for yaml_file in prd_dir.glob("*.yaml"):
            try:
                prd = self._load_prd(yaml_file, project_path)
                if prd:
                    prds.append(prd)
            except Exception as e:
                logger.error(f"加载PRD文件失败 {yaml_file}: {e}")
        
        # 按优先级排序
        prds.sort(key=lambda x: x.priority, reverse=True)
        return prds
    
    def _load_prd(self, yaml_path: Path, project_path: str) -> Optional[EvolutionPRD]:
        """
        加载单个PRD文件
        
        Args:
            yaml_path: YAML文件路径
            project_path: 项目路径
            
        Returns:
            EvolutionPRD或None
        """
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            # 解析project
            project = data.get("project", {})
            
            # 解析goals
            goals = []
            for sprint in data.get("sprints", []):
                goals.extend(sprint.get("goals", []))
            
            # 解析sprints
            sprints = []
            for i, sprint_data in enumerate(data.get("sprints", [])):
                sprint = {
                    "name": sprint_data.get("name", f"Sprint {i+1}"),
                    "goals": sprint_data.get("goals", []),
                    "tasks": sprint_data.get("tasks", []),
                }
                sprints.append(sprint)
            
            return EvolutionPRD(
                name=project.get("name", yaml_path.stem),
                version=project.get("version", "v1.0.0"),
                path=str(yaml_path),
                goals=goals,
                sprints=sprints,
                source_type=PRDSourceType.MANUAL,
                metadata={
                    "yaml_path": str(yaml_path),
                    "project_path": project_path,
                },
                priority=100,  # 人工PRD最高优先级
                confidence=1.0,
            )
            
        except Exception as e:
            logger.error(f"解析PRD失败 {yaml_path}: {e}")
            return None
    
    def get_source_type(self) -> PRDSourceType:
        return PRDSourceType.MANUAL


class DiagnosticPRDSource(PRDSource):
    """
    诊断驱动PRD来源
    
    通过项目诊断生成PRD:
    1. 调用ProjectDiagnostic进行多维度诊断
    2. 调用DiagnosticPRDGenerator生成结构化PRD
    """
    
    def __init__(
        self,
        diagnostic_provider=None,
        prd_generator=None,
        max_prds: int = 5,
    ):
        """
        初始化诊断PRD来源
        
        Args:
            diagnostic_provider: 诊断提供者
            prd_generator: PRD生成器
            max_prds: 最大PRD数量
        """
        self._diagnostic = diagnostic_provider
        self._generator = prd_generator
        self._max_prds = max_prds
    
    def generate(self, project_path: str) -> List[EvolutionPRD]:
        """
        诊断驱动生成PRD
        
        Args:
            project_path: 项目路径
            
        Returns:
            EvolutionPRD列表
        """
        # 懒加载避免循环导入
        if self._diagnostic is None:
            from sprintcycle.diagnostic import ProjectDiagnostic
            self._diagnostic = ProjectDiagnostic()
        
        if self._generator is None:
            from sprintcycle.diagnostic import DiagnosticPRDGenerator
            self._generator = DiagnosticPRDGenerator()
        
        # 1. 执行诊断
        logger.info(f"开始诊断项目: {project_path}")
        try:
            health_report = self._diagnostic.diagnose(project_path)
        except Exception as e:
            logger.error(f"项目诊断失败: {e}", exc_info=True)
            return []
        
        # 2. 生成PRD
        logger.info("生成PRD...")
        try:
            raw_prds = self._generator.generate(health_report, project_path)
        except Exception as e:
            logger.error(f"PRD生成失败: {e}", exc_info=True)
            return []
        
        # 3. 过滤和排序
        filtered_prds = self._filter_prds(raw_prds)
        filtered_prds.sort(key=lambda x: x.priority, reverse=True)
        
        # 限制数量
        return filtered_prds[:self._max_prds]
    
    def _filter_prds(self, prds: List[EvolutionPRD]) -> List[EvolutionPRD]:
        """
        过滤低质量PRD
        
        Args:
            prds: 原始PRD列表
            
        Returns:
            过滤后的PRD列表
        """
        return [
            prd for prd in prds
            if prd.confidence >= 0.5 and prd.expected_benefit > 0
        ]
    
    def get_source_type(self) -> PRDSourceType:
        return PRDSourceType.DIAGNOSTIC
