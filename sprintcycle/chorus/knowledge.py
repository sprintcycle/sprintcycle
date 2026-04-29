"""
chorus.knowledge - 知识库管理
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

from loguru import logger

from .progress import ExecutionResult
from .utils import normalize_files_changed, extract_files_list, has_changes


class KnowledgeBase:
    """
    知识库 - 记录和检索历史经验
    v4.10: 增强 files_changed 处理
    """
    
    def __init__(self, project_path: str):
        self.path = Path(project_path) / ".sprintcycle" / "knowledge.json"
        self.data = self._load()
    
    def _load(self) -> Dict:
        if self.path.exists():
            with open(self.path) as f:
                return json.load(f)
        return {"tasks": [], "patterns": [], "solutions": []}
    
    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def record_task(self, task: str, result: ExecutionResult, files: List[str]):
        """记录任务执行结果 - v4.10 增强 files_changed 处理"""
        files_list = files
        normalized = normalize_files_changed(result.files_changed)
        
        if isinstance(normalized, dict):
            files_list = []
            for file_list in normalized.values():
                if isinstance(file_list, list):
                    files_list.extend(file_list)
        
        task_entry = {
            "task": task,
            "success": result.success,
            "tool": result.tool,
            "files": files_list,
            "files_changed": result.files_changed,
            "has_changes": len(files_list) > 0,
            "duration": result.duration,
            "timestamp": datetime.now().isoformat()
        }
        
        if result.error:
            task_entry["error"] = result.error
        if result.error_reason:
            task_entry["error_reason"] = result.error_reason
        
        if hasattr(result, 'review') and result.review:
            task_entry['review'] = result.review
        
        self.data["tasks"].append(task_entry)
        
        if result.success and files_list:
            pattern = {"type": "file_pattern", "files": files_list, "for_task": task[:50]}
            self.data["patterns"].append(pattern)
        
        self._save()
    
    def find_similar(self, task: str) -> List[Dict]:
        """查找相似任务的历史"""
        results = []
        task_keywords = set(task.lower().split())
        
        for t in self.data["tasks"][-20:]:
            hist_keywords = set(t["task"].lower().split())
            overlap = len(task_keywords & hist_keywords)
            if overlap > 2:
                results.append(t)
        
        return results[:3]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        tasks = self.data["tasks"]
        if not tasks:
            return {"total": 0, "total_tasks": 0, "success_rate": 0}
        
        success = sum(1 for t in tasks if t["success"])
        return {
            "total": len(tasks),
            "total_tasks": len(tasks),
            "success": success,
            "success_rate": round(success / len(tasks) * 100, 1),
            "avg_duration": round(sum(t["duration"] for t in tasks) / len(tasks), 1)
        }
    
    def add_entry(self, entry: Dict):
        """添加一条知识条目"""
        self.data.setdefault("solutions", []).append(entry)
        self._save()

    def record_task_entry(self, task_entry: Dict):
        """记录完整的 task_entry（包含 review 和 verification） - v4.10 增强"""
        from enum import Enum
        
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
        
        files_changed_raw = task_entry.get("files_changed", {})
        files_changed = normalize_files_changed(files_changed_raw)
        files_list = extract_files_list(files_changed)
        
        record = {
            "task": task_entry.get("task", ""),
            "success": task_entry.get("status") == "completed",
            "tool": task_entry.get("tool", "aider"),
            "files": task_entry.get("files", files_list),
            "files_changed": files_changed,
            "has_changes": has_changes(files_changed),
            "duration": task_entry.get("duration_seconds", 0),
            "timestamp": task_entry.get("completed_at", datetime.now().isoformat()),
            "review": sanitize(task_entry.get("review")),
            "verification": sanitize(task_entry.get("verification")),
            "validation": sanitize(task_entry.get("validation")),
        }
        
        if task_entry.get("error"):
            record["error"] = task_entry["error"]
        if task_entry.get("error_reason"):
            record["error_reason"] = task_entry["error_reason"]
        
        record = {k: v for k, v in record.items() if v is not None and v != {} and v != []}
        
        self.data["tasks"].append(record)
        
        files_to_use = record.get("files", files_list)
        if record.get("success") and files_to_use:
            pattern = {"type": "file_pattern", "files": files_to_use, "for_task": record["task"][:50]}
            self.data["patterns"].append(pattern)
        
        self._save()
        logger.success(f"已保存任务到 knowledge.json: {record['task'][:40]}...")
