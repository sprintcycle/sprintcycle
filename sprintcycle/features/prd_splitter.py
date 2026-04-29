"""
SprintCycle PRD 自动拆分器
根据策略配置自动拆分大型 PRD，避免执行超时
"""

import yaml
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class SplitResult:
    """拆分结果"""
    original_prd: str
    split_prds: List[str]
    total_sprints: int
    split_count: int
    strategy_used: str

class PRDSplitter:
    """PRD 自动拆分器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.default_config = self.config.get('default', {})
        self.split_mode = self.config.get('split_mode', {})
        self.project_configs = self.config.get('projects', {})
        self.triggers = self.config.get('split_triggers', [])
        self.output_config = self.config.get('output', {})
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            import os as _os
            _sprint_root = _os.environ.get("SPRINT_ROOT")
            if _sprint_root:
                config_path = str(Path(_sprint_root)) + "/config/prd_split_strategy.yaml"
            else:
                config_path = str(Path(__file__).parent.parent / "config" / "prd_split_strategy.yaml")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # 默认配置
        return {
            'default': {
                'max_sprints_per_prd': 3,
                'max_tasks_per_sprint': 2,
                'timeout_per_task': 120,
                'total_timeout_limit': 600
            },
            'split_mode': {'by_module': {'enabled': True}},
            'projects': {},
            'split_triggers': [
                {'condition': 'sprint_count > 4', 'action': 'auto_split'}
            ],
            'output': {
                'split_prd_dir': str(Path(__file__).parent.parent / "prd" / "split"),
                'naming_pattern': '{original_name}_p{part}.yaml'
            }
        }
    
    def analyze_prd(self, prd_path: str) -> Dict[str, Any]:
        """分析 PRD 文件"""
        with open(prd_path, 'r', encoding='utf-8') as f:
            prd_data = yaml.safe_load(f)
        
        sprints = prd_data.get('sprints', [])
        sprint_count = len(sprints)
        
        # 统计任务数
        total_tasks = 0
        for sprint in sprints:
            tasks = sprint.get('tasks', [])
            total_tasks += len(tasks)
        
        # 估算执行时间
        timeout_per_task = self.default_config.get('timeout_per_task', 120)
        estimated_time = total_tasks * timeout_per_task * 0.5  # 假设平均执行一半超时时间
        
        return {
            'prd_path': prd_path,
            'sprint_count': sprint_count,
            'total_tasks': total_tasks,
            'estimated_time': estimated_time,
            'needs_split': self._check_needs_split(sprint_count, estimated_time)
        }
    
    def _check_needs_split(self, sprint_count: int, estimated_time: float) -> bool:
        """检查是否需要拆分"""
        max_sprints = self.default_config.get('max_sprints_per_prd', 3)
        time_limit = self.default_config.get('total_timeout_limit', 600)
        
        # 检查触发条件
        for trigger in self.triggers:
            condition = trigger.get('condition', '')
            if 'sprint_count' in condition and sprint_count > max_sprints:
                return True
            if 'estimated_time' in condition and estimated_time > time_limit:
                return True
        
        return sprint_count > max_sprints
    
    def split_prd(self, prd_path: str, project_name: Optional[str] = None) -> SplitResult:
        """拆分 PRD 文件"""
        analysis = self.analyze_prd(prd_path)
        
        if not analysis['needs_split']:
            return SplitResult(
                original_prd=prd_path,
                split_prds=[prd_path],
                total_sprints=analysis['sprint_count'],
                split_count=1,
                strategy_used='no_split'
            )
        
        # 加载原始 PRD
        with open(prd_path, 'r', encoding='utf-8') as f:
            prd_data = yaml.safe_load(f)
        
        sprints = prd_data.get('sprints', [])
        project_info = prd_data.get('project', {})
        if isinstance(project_info, str):
            project_info = {'name': project_info, 'path': ''}
        
        # 获取项目特定配置
        project_config = self.project_configs.get(project_name or project_info.get('name', ''), {})
        max_sprints = project_config.get('max_sprints_per_prd', self.default_config.get('max_sprints_per_prd', 3))
        
        # 计算拆分数量
        split_count = (len(sprints) + max_sprints - 1) // max_sprints
        
        # 拆分 Sprint
        split_prds = []
        for i in range(split_count):
            start_idx = i * max_sprints
            end_idx = min((i + 1) * max_sprints, len(sprints))
            sprint_slice = sprints[start_idx:end_idx]
            
            # 生成拆分 PRD
            split_prd_data = {
                'project': {
                    'name': f"{project_info.get('name', 'unknown')}-Part{i+1}",
                    'path': project_info.get('path', '')
                },
                'sprints': sprint_slice
            }
            
            # 生成文件名
            original_name = Path(prd_path).stem
            naming_pattern = self.output_config.get('naming_pattern', '{original_name}_p{part}.yaml')
            theme = self._extract_theme(sprint_slice, i)
            split_filename = naming_pattern.format(
                original_name=original_name,
                part=i+1,
                theme=theme
            )
            
            # 保存拆分 PRD
            _sprint_root = os.environ.get("SPRINT_ROOT")
            _default_split_dir = str(Path(__file__).parent.parent / "prd" / "split")
            split_dir = self.output_config.get('split_prd_dir', _default_split_dir)
            os.makedirs(split_dir, exist_ok=True)
            split_path = os.path.join(split_dir, split_filename)
            
            with open(split_path, 'w', encoding='utf-8') as f:
                yaml.dump(split_prd_data, f, allow_unicode=True, default_flow_style=False)
            
            split_prds.append(split_path)
        
        return SplitResult(
            original_prd=prd_path,
            split_prds=split_prds,
            total_sprints=analysis['sprint_count'],
            split_count=split_count,
            strategy_used='auto_split'
        )
    
    def _extract_theme(self, sprints: List[Dict], part_index: int) -> str:
        """从 Sprint 列表提取主题"""
        if not sprints:
            return f"part{part_index+1}"
        
        # 从第一个 Sprint 的名称提取关键词
        first_sprint_name = sprints[0].get('name', '')
        
        # 提取关键词
        keywords = {
            '设计': 'design',
            '首页': 'home',
            '登录': 'login',
            '个人中心': 'profile',
            '组件': 'component',
            '样式': 'style',
            '测试': 'test',
            '验收': 'verify',
            '性能': 'performance',
            '优化': 'optimize'
        }
        
        for cn, en in keywords.items():
            if cn in first_sprint_name:
                return en
        
        return f"part{part_index+1}"
    
    def get_split_execution_order(self, split_result: SplitResult) -> List[str]:
        """获取拆分 PRD 的执行顺序"""
        return split_result.split_prds

# 便捷函数
def split_prd_if_needed(prd_path: str, project_name: Optional[str] = None) -> List[str]:
    """如果需要则拆分 PRD，返回 PRD 路径列表"""
    splitter = PRDSplitter()
    result = splitter.split_prd(prd_path, project_name)
    return result.split_prds

# 命令行接口
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python prd_splitter.py <prd_path> [project_name]")
        sys.exit(1)
    
    prd_path = sys.argv[1]
    project_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    splitter = PRDSplitter()
    
    # 分析
    analysis = splitter.analyze_prd(prd_path)
    print(f"PRD 分析结果:")
    print(f"  Sprint 数: {analysis['sprint_count']}")
    print(f"  任务数: {analysis['total_tasks']}")
    print(f"  预估时间: {analysis['estimated_time']:.0f}s")
    print(f"  需要拆分: {analysis['needs_split']}")
    
    if analysis['needs_split']:
        print(f"\n拆分 PRD...")
        result = splitter.split_prd(prd_path, project_name)
        print(f"拆分结果:")
        print(f"  原始 PRD: {result.original_prd}")
        print(f"  拆分数量: {result.split_count}")
        print(f"  拆分文件:")
        for p in result.split_prds:
            print(f"    - {p}")
