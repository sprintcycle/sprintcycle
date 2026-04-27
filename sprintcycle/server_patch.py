"""
server.py 补丁 - 集成五大优化

将此内容合并到 server.py 中
"""

# 1. 在文件开头添加导入
"""
from .optimizations import (
    FileTracker, TaskSplitter, SplitConfig,
    ExecutionLog, TaskStatus, SprintStatus, CodeDelta
)
"""

# 2. 更新 Config.DEFAULT_CONFIG
"""
DEFAULT_CONFIG = {
    "aider": {...},
    "claude": {...},
    "cursor": {...},
    "scheduler": {...},
    "task": {
        "split_threshold_seconds": 60,  # 可配置的任务拆分阈值
        "suggest_split": True,
        "auto_split": False
    }
}
"""

# 3. 更新 ExecutionResult dataclass
"""
@dataclass
class ExecutionResult:
    success: bool
    output: str
    files_changed: Dict  # 改为 Dict，包含 added/modified/deleted
    tool: ToolType
    duration: float
    retries: int = 0
    validation: Dict = field(default_factory=dict)
    split_suggestion: List[str] = field(default_factory=list)
    log: ExecutionLog = field(default_factory=ExecutionLog)
"""

# 4. 更新 KnowledgeBase.record_task
"""
def record_task(self, task: str, result: ExecutionResult, files: Dict):
    entry = {
        "task": task,
        "task_type": self._classify_task(task),
        "success": result.success,
        "duration": result.duration,
        "tool": result.tool,
        "retries": result.retries,
        "timestamp": datetime.now().isoformat(),
        "files": {
            "added": files.get("added", []),
            "modified": files.get("modified", []),
            "deleted": files.get("deleted", [])
        },
        "split_suggestion": result.split_suggestion,
        "lines_changed": FileTracker.count_lines(files, result.output)
    }
    self.data["tasks"].append(entry)
    self.data["stats"]["total"] = self.data["stats"].get("total", 0) + 1
    if result.success:
        self.data["stats"]["success"] = self.data["stats"].get("success", 0) + 1
    self._save()
"""

# 5. 更新 ExecutionLayer._run_once
"""
def _run_once(self, project_path: str, task: str, files: List[str], 
              tool: ToolType, timeout: int) -> ExecutionResult:
    # ... 执行代码 ...
    
    # 解析文件变更
    files_dict = FileTracker.parse_files(output)
    
    # 检查是否需要拆分
    splitter = TaskSplitter(SplitConfig(
        threshold_seconds=self.config.get("task", {}).get("split_threshold_seconds", 60)
    ))
    split_suggestion = splitter.check_and_suggest(task, duration)
    
    return ExecutionResult(
        success=True,
        output=output,
        files_changed=files_dict,
        tool=tool,
        duration=duration,
        retries=retry_count,
        split_suggestion=split_suggestion
    )
"""

# 6. 更新 SprintChain.run_all_sprints
"""
def run_all_sprints(self, on_task_complete: callable = None) -> List[Dict]:
    results = []
    
    for sprint in self.get_sprints():
        if sprint.get("status") == "completed":
            print(f"⏭️ Sprint {sprint['name']} 已完成，跳过")
            continue
        
        # 更新 Sprint 状态
        sprint["status"] = "running"
        sprint["started_at"] = datetime.now().isoformat()
        self._save_config()
        
        print(f"\n🎯 Sprint: {sprint['name']}")
        sprint_results = []
        
        for i, task in enumerate(sprint.get("tasks", []), 1):
            if task.get("status") == "completed":
                print(f"  ⏭️ 任务 {i} 已完成，跳过")
                continue
            
            # 更新任务状态
            task["status"] = "running"
            task["started_at"] = datetime.now().isoformat()
            self._save_config()
            
            print(f"  📌 任务 {i}/{len(sprint['tasks'])}: {task['task'][:30]}...")
            
            result = self.run_task(
                task["task"],
                task.get("files", []),
                name=f"task_{i}"
            )
            
            # 更新任务详情
            task["status"] = "completed" if result.success else "failed"
            task["completed_at"] = datetime.now().isoformat()
            task["duration_seconds"] = round(result.duration, 1)
            task["files_changed"] = result.files_changed
            task["split_suggestion"] = result.split_suggestion
            
            # 如果有拆分建议，显示
            if result.split_suggestion:
                print(f"    ⚠️ 任务耗时 {result.duration:.0f}s，建议拆分:")
                for s in result.split_suggestion[:3]:
                    print(f"       {s}")
            
            self._save_config()  # 实时保存
            
            if on_task_complete:
                on_task_complete(i, len(sprint["tasks"]), result)
            
            sprint_results.append({
                "task": task["task"],
                "success": result.success,
                "duration": result.duration,
                "files": result.files_changed
            })
        
        # 更新 Sprint 完成状态
        success_count = sum(1 for r in sprint_results if r["success"])
        sprint["status"] = "completed" if success_count == len(sprint_results) else "partial"
        sprint["completed_at"] = datetime.now().isoformat()
        self._save_config()
        
        results.append({
            "sprint_name": sprint["name"],
            "results": sprint_results,
            "total": len(sprint["tasks"]),
            "success": success_count
        })
    
    return results
"""
