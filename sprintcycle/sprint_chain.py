#!/usr/bin/env python3
"""
SprintCycle SprintChain 模块
包含 Sprint 执行层、任务批处理、检查点管理等
"""
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import yaml
import os

from loguru import logger

# 导入 Chorus 模块
from .chorus import (
    Config, ToolType, AgentType, TaskStatus, ExecutionResult, 
    KnowledgeBase, ExecutionLayer, ChorusAdapter, Chorus
)

# 依赖管理
try:
    from .optimizations import DependencyManager, ResultValidator
except ImportError:
    DependencyManager = None


# ============================================================
# SprintChain - Sprint 执行层
# ============================================================

class SprintChain:
    """Sprint 链式执行器"""
    
    def __init__(self, project_path: str, review_enabled: bool = False):
        self.project_path = Path(project_path)
        self.config_path = self.project_path / ".sprintcycle" / "config.yaml"
        self.results_path = self.project_path / ".sprintcycle" / "results"
        self.checkpoint_path = self.project_path / ".sprintcycle" / "checkpoints"
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化组件
        self.kb = KnowledgeBase(str(self.project_path))
        self.chorus = Chorus(self.kb)
        self.review_enabled = review_enabled
        self.reviewer = None
        
        if self.review_enabled:
            try:
                from .reviewer import ReviewerAgent
                self.reviewer = ReviewerAgent()
            except ImportError:
                logger.warning("ReviewerAgent 未安装，审查功能不可用")
    
    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        return {"project": {"name": Path(self.project_path).name}, "sprint_chain": []}
    
    def _save_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, allow_unicode=True)
    
    def _save_result(self, task: str, result: ExecutionResult, name: str = None):
        self.results_path.mkdir(parents=True, exist_ok=True)
        data = {
            "task": task, "task_name": name or f"task_{datetime.now():%H%M%S}",
            "success": result.success, "files_changed": result.files_changed,
            "tool": result.tool, "duration": result.duration, "retries": result.retries,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.results_path / f"{data['task_name']}_{datetime.now():%Y%m%d_%H%M%S}.json", "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_sprints(self) -> List[Dict]:
        return self.config.get("sprint_chain", [])
    
    def create_sprint(self, name: str, goals: List[str]) -> Dict:
        sprint = {"id": f"sprint_{len(self.get_sprints())+1}", "name": name, "goals": goals, "status": "pending"}
        self.config.setdefault("sprint_chain", []).append(sprint)
        self._save_config()
        return sprint
    
    def run_task(self, task: str, files: List[str] = None, 
                 agent: AgentType = None, tool: ToolType = None, 
                 name: str = None, on_progress: callable = None) -> ExecutionResult:
        result = self.chorus.dispatch(self.project_path, task, files, agent, tool, on_progress)
        
        # 阶段2: 审查流程
        if self.review_enabled and result.success and self.reviewer:
            review_result = self.reviewer.review_execution(
                self.project_path,
                result.files_changed,
                result.output if hasattr(result, 'output') else None
            )
            
            # 添加审查结果
            result.review = {
                "passed": review_result.passed,
                "issues_count": len(review_result.issues),
                "summary": review_result.summary,
                "feedback": self.reviewer.generate_feedback(review_result) if not review_result.passed else "审查通过"
            }
            
            if not review_result.passed:
                result.needs_fix = True
                result.fix_suggestions = self.reviewer.get_fix_suggestions(review_result)
        
        self._save_result(task, result, name)
        return result
    
    def run_sprint(self, sprint_name: str, tasks: List[Dict], tool: ToolType = None,
                   on_task_complete: callable = None) -> Dict:
        """运行 Sprint，支持进度回调"""
        results = []
        success = 0
        
        for i, t in enumerate(tasks, 1):
            logger.info(f"任务 {i}/{len(tasks)}: {t['task'][:50]}...")
            
            a = AgentType.from_string(t.get("agent")) if t.get("agent") else None
            r = self.run_task(t["task"], t.get("files"), a, tool)
            
            results.append({
                "task": t["task"], "success": r.success, 
                "tool": r.tool, "retries": r.retries,
                "files_changed": r.files_changed
            })
            
            if r.success:
                success += 1
            
            if on_task_complete:
                on_task_complete(i, len(tasks), r)
        
        return {"sprint_name": sprint_name, "total": len(tasks), "success": success, "results": results}
    
    def get_results(self) -> List[Dict]:
        results = []
        if self.results_path.exists():
            for f in sorted(self.results_path.glob("*.json")):
                with open(f) as fp:
                    results.append(json.load(fp))
        return results
    
    def get_kb_stats(self) -> Dict:
        return self.kb.get_stats()

    def parse_sprint_file(self, file_path: str) -> List[Dict]:
        """解析 Markdown 格式的 Sprint 规划文件，提取任务列表"""
        import re
        tasks = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 匹配 ### Task N: 标题
        pattern = r'### Task\s+\d+:\s*(.*?)\n(.*?)(?=\n###|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        for title, body in matches:
            title = title.strip()
            subtasks = []
            for line in body.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    subtasks.append(line[2:].strip())
            tasks.append({
                "task": title,
                "subtasks": subtasks,
                "files": []
            })
        return tasks

    def auto_plan_from_prd(self, prd_path: str) -> Dict:
        """从 PRD 文档自动生成 Sprint 规划"""
        import yaml
        import re
        
        # 检查文件是否存在
        if not Path(prd_path).exists():
            return {
                "error": f"PRD文件不存在: {prd_path}",
                "sprints": []
            }
        
        try:
            with open(prd_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                "error": f"读取PRD文件失败: {str(e)}",
                "sprints": []
            }
        
        # 尝试 YAML 格式
        if 'sprints:' in content or 'project:' in content:
            try:
                yaml_content = content
                if yaml_content.startswith('#'):
                    lines = yaml_content.split('\n')
                    yaml_lines = [l for l in lines if not l.strip().startswith('#') or l.strip() == '#']
                    yaml_content = '\n'.join(yaml_lines)
                
                prd_data = yaml.safe_load(yaml_content)
                if prd_data and 'sprints' in prd_data:
                    sprints = []
                    for s in prd_data['sprints']:
                        tasks = []
                        for t in s.get('tasks', []):
                            task_text = t.get('task', '') if isinstance(t, dict) else str(t)
                            agent = t.get('agent', 'coder') if isinstance(t, dict) else 'coder'
                            tasks.append({
                                "task": task_text,
                                "agent": agent,
                                "subtasks": [],
                                "files": []
                            })
                        sprints.append({
                            "name": s.get('name', 'Sprint'),
                            "goals": s.get('goals', []),
                            "tasks": tasks,
                            "status": "pending"
                        })
                    
                    for s in sprints:
                        self.config.setdefault("sprint_chain", []).append(s)
                    self._save_config()
                    logger.info(f"从 YAML PRD 解析了 {len(sprints)} 个 Sprint")
                    return {"sprints": sprints, "error": None}
            except yaml.YAMLError as e:
                logger.warning(f"YAML 解析失败: {e}，尝试 Markdown 格式")
        
        # Markdown 格式解析
        section_match = re.search(r'##?\s*开发优先级\s*\n(.*?)(?=\n##?\s|\Z)', content, re.DOTALL)
        if not section_match:
            return {"sprints": [], "error": "未找到开发优先级章节"}
        
        section = section_match.group(1)
        sprint_pattern = r'###\s+(?:Sprint\s+\d+|P\d+):\s*(.*?)\n(.*?)(?=\n###\s+(?:Sprint\s+\d+|P\d+):|\Z)'
        
        sprints = []
        for match in re.finditer(sprint_pattern, section, re.DOTALL):
            sprint_title = match.group(1).strip()
            sprint_body = match.group(2)
            tasks = []
            
            for line in sprint_body.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    task_text = line[2:].strip()
                    if task_text.startswith('文件:') or task_text.startswith('File:'):
                        continue
                    agent = 'coder'
                    if '【tester】' in task_text or '[tester]' in task_text.lower():
                        agent = 'tester'
                        task_text = task_text.replace('【tester】', '').replace('[tester]', '').strip()
                    tasks.append({
                        "task": task_text,
                        "agent": agent,
                        "subtasks": [],
                        "files": []
                    })
            
            sprints.append({
                "name": sprint_title,
                "tasks": tasks,
                "status": "pending"
            })
        
        for s in sprints:
            self.config.setdefault("sprint_chain", []).append(s)
        self._save_config()
        return {"sprints": sprints, "error": None}

    # P1: 分批执行配置
    BATCH_SIZE = 5  # 每批最多 5 个任务
    
    def _run_task_batch(self, tasks: List[Dict], completed_task_ids: List[str]) -> List[Dict]:
        """执行一批任务"""
        results = []
        
        for task_entry in tasks:
            # 依赖检查
            dep_result = DependencyManager.check_dependencies(task_entry, completed_task_ids)
            if not dep_result['satisfied']:
                logger.warning(f"任务依赖未满足: {dep_result['missing']}")
                task_entry['status'] = 'blocked'
                results.append(task_entry)
                continue
            
            task_entry["status"] = "running"
            task_entry["started_at"] = datetime.now().isoformat()
            
            result = self.run_task(
                task_entry["task"],
                task_entry.get("files"),
                agent=None,
                tool=None,
                name=None,
                on_progress=None
            )
            
            task_entry["status"] = "completed" if result.success else "failed"
            task_entry["completed_at"] = datetime.now().isoformat()
            task_entry["duration_seconds"] = round(result.duration, 1)
            task_entry["files_changed"] = result.files_changed
            
            if result.files_changed:
                files_list = []
                for file_list in result.files_changed.values():
                    if isinstance(file_list, list):
                        files_list.extend(file_list)
                task_entry['files'] = files_list
            
            # P0-3: 审查结果
            if self.review_enabled and result.success and self.reviewer:
                review_result = self.reviewer.review_execution(
                    self.project_path,
                    result.files_changed,
                    result.output if hasattr(result, 'output') else None
                )
                task_entry['review'] = {
                    'passed': review_result.passed,
                    'issues': review_result.issues if hasattr(review_result, 'issues') else [],
                    'suggestions': review_result.suggestions if hasattr(review_result, 'suggestions') else [],
                    'issues_count': len(review_result.issues) if hasattr(review_result, 'issues') else 0,
                    'summary': review_result.summary
                }
                if not review_result.passed:
                    logger.warning(f"审查失败: {review_result.summary}")
            
            # 结果验证
            validation = ResultValidator.validate(task_entry['task'], result.files_changed, self.project_path)
            task_entry['validation'] = validation
            if not validation['valid']:
                logger.warning(f"验证失败: {validation['issues']}")
            if validation['warnings']:
                logger.warning(f"警告: {validation['warnings']}")
            if result.split_suggestion:
                logger.info(f"拆分建议: {result.split_suggestion}")
            
            # 五源验证
            five_source = FiveSourceVerifier.verify_all(str(self.project_path), task_entry['task'], result.files_changed)
            task_entry['verification'] = {
                'passed': five_source.get('passed', True),
                'cli': five_source.get('cli', {}),
                'tests': five_source.get('tests', {}),
                'backend': five_source.get('backend', {}),
                'files_checked': five_source.get('files_checked', [])
            }
            task_entry['five_source_result'] = five_source
            if not five_source['passed']:
                logger.warning(f"五源验证失败: {five_source['summary']}")
            
            # 失败分析
            if not result.success:
                engine = EvolutionEngine()
                modified_files = result.files_changed.get('modified', []) if isinstance(result.files_changed, dict) else result.files_changed
                analysis = engine.analyze_failure(task_entry['task'], result.output, list(modified_files))
                task_entry['failure_analysis'] = {
                    'category': analysis.error_category.value,
                    'root_cause': analysis.root_cause,
                    'solution': analysis.solution_hint
                }
                knowledge = engine.extract_knowledge(analysis)
                self.kb.add_entry(knowledge)
                logger.error(f"失败分析: {analysis.error_category.value} - {analysis.root_cause}")
            
            # 记录已完成的任务 ID
            if result.success:
                completed_task_ids.append(task_entry['task'])
            
            # 保存完整的 task_entry 到 knowledge.json
            self.kb.record_task_entry(task_entry)
            
            results.append(task_entry)
        
        return results
    
    def _save_checkpoint(self, sprint_name: str, tasks: List[Dict]):
        """保存检查点"""
        
        def sanitize(obj):
            if obj is None:
                return None
            if isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, list):
                result = [sanitize(item) for item in obj]
                return result if any(r is not None for r in result) else None
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    sv = sanitize(v)
                    if sv is not None:
                        result[k] = sv
                return result if result else None
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, '__dict__'):
                return sanitize(obj.__dict__)
            if hasattr(obj, '__dataclass_fields__'):
                return sanitize({f: getattr(obj, f) for f in obj.__dataclass_fields__})
            return str(obj)
        
        cleaned_tasks = [sanitize(t) for t in tasks]
        
        checkpoint = {
            "sprint_name": sprint_name,
            "timestamp": datetime.now().isoformat(),
            "tasks": cleaned_tasks
        }
        checkpoint_path = Path(self.project_path) / ".sprintcycle" / "checkpoints"
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        checkpoint_file = checkpoint_path / f"{sprint_name.replace(' ', '_')}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def run_all_sprints(self, on_task_complete: callable = None) -> List[Dict]:
        """按顺序执行所有待执行的 Sprint（分批执行）"""
        results = []
        
        for sprint in self.get_sprints():
            if sprint.get("status") == "completed":
                continue
            
            tasks = []
            for t in sprint.get("tasks", []):
                task_entry = {
                    "task": t.get("task", ""),
                    "files": t.get("files", []),
                    "agent": None,
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "duration_seconds": 0,
                    "files_changed": {}
                }
                tasks.append(task_entry)
            
            # 使用拓扑排序确保任务顺序正确
            try:
                tasks = DependencyManager.topological_sort(tasks)
            except:
                pass  # 如果依赖管理不可用，保持原顺序
            
            # 分批执行
            completed_task_ids = []
            all_task_results = []
            
            for i in range(0, len(tasks), self.BATCH_SIZE):
                batch = tasks[i:i+self.BATCH_SIZE]
                batch_num = i // self.BATCH_SIZE + 1
                total_batches = (len(tasks) + self.BATCH_SIZE - 1) // self.BATCH_SIZE
                logger.info(f"执行批次 {batch_num}/{total_batches} ({len(batch)} 个任务)")
                
                batch_results = self._run_task_batch(batch, completed_task_ids)
                all_task_results.extend(batch_results)
                
                for t in batch_results:
                    if t.get("status") == "completed":
                        completed_task_ids.append(t["task"])
                
                # 批次间隔保存检查点
                self._save_checkpoint(sprint["name"], all_task_results)
                
                if i + self.BATCH_SIZE < len(tasks):
                    logger.debug("批次间隔，保存检查点...")
            
            # 更新 sprint 状态
            sprint["status"] = "completed"
            self._save_config()
            
            sprint_result = {
                "sprint_name": sprint["name"],
                "total": len(all_task_results),
                "success": sum(1 for t in all_task_results if t["status"] == "completed"),
                "results": all_task_results
            }
            results.append(sprint_result)
        
        return results

    def run_sprint_by_name(self, sprint_name: str, tool: ToolType = None) -> Dict:
        for sprint in self.get_sprints():
            if sprint.get("name") == sprint_name:
                tasks = []
                for t in sprint.get("tasks", []):
                    tasks.append({
                        "task": t.get("task", ""),
                        "files": t.get("files", []),
                        "agent": None
                    })
                return self.run_sprint(sprint_name, tasks, tool)
        return {"sprint_name": sprint_name, "total": 0, "success": 0, "results": [], "error": "Sprint not found"}


# 导出公共接口
__all__ = [
    "SprintChain",
    "ExecutionResult"
]
