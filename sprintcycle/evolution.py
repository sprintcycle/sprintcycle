"""
SprintCycle 进化引擎模块 v4.10

提供代码进化和自适应学习功能：
- 失败模式分析
- 策略调整
- 学习历史
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

from .error_helper import ErrorCategory


class EvolutionEngine:
    """
    进化引擎 v4.10
    
    功能：
    - 跟踪失败模式
    - 学习成功策略
    - 适应不同项目特征
    - 提供智能建议
    """
    
    # 错误模式映射 - 用于测试
    ERROR_PATTERNS = {
        ErrorCategory.SYNTAX: ["syntax", "indentation", "parse"],
        ErrorCategory.IMPORT: ["import", "module", "not found"],
        ErrorCategory.RUNTIME: ["key", "type", "value", "attribute", "index"],
        ErrorCategory.LOGIC: ["recursion", "infinite", "logic"],
        ErrorCategory.AIDER: ["rate limit", "api", "token", "quota"],
        ErrorCategory.EMPTY_OUTPUT: ["empty", "no output", "blank"],
        ErrorCategory.NO_CHANGES: ["no changes", "unchanged", "skipped"],
    }
    
    def __init__(self, data_dir: str = ".sprintcycle"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "evolution_history.json"
        self.strategy_file = self.data_dir / "evolution_strategies.json"
        self.history = self._load_history()
        self.strategies = self._load_strategies()
    
    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_history(self):
        """保存历史记录"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history[-1000:], f, indent=2)
    
    def _load_strategies(self) -> Dict:
        """加载策略"""
        if self.strategy_file.exists():
            try:
                with open(self.strategy_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self._get_default_strategies()
    
    def _get_default_strategies(self) -> Dict:
        """获取默认策略"""
        return {
            "syntax_error": {
                "action": "format",
                "timeout": 60,
                "retry": 1
            },
            "import_error": {
                "action": "install",
                "timeout": 120,
                "retry": 2
            },
            "runtime_error": {
                "action": "debug",
                "timeout": 180,
                "retry": 1
            },
            "timeout": {
                "action": "split",
                "timeout": 300,
                "retry": 0
            }
        }
    
    def classify_error(self, error_message: str) -> ErrorCategory:
        """分类错误 - 用于测试"""
        error_lower = error_message.lower()
        
        # 检查各个错误模式
        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern in error_lower:
                    return category
        
        return ErrorCategory.UNKNOWN
    
    def record_execution(self, task: str, result: Dict) -> None:
        """记录执行结果"""
        record = {
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(record)
        self._save_history()
    
    def get_failure_patterns(self) -> Dict[str, int]:
        """获取失败模式统计"""
        patterns = defaultdict(int)
        
        for record in self.history:
            if not record.get("result", {}).get("success", True):
                error = record.get("result", {}).get("error", "")
                error_type = self._extract_error_type(error)
                patterns[error_type] += 1
        
        return dict(patterns)
    
    def _extract_error_type(self, error_message: str) -> str:
        """提取错误类型"""
        if "SyntaxError" in error_message:
            return "syntax_error"
        elif "ImportError" in error_message or "ModuleNotFoundError" in error_message:
            return "import_error"
        elif "TimeoutError" in error_message:
            return "timeout_error"
        else:
            return "unknown_error"
    
    def suggest_strategy(self, error_type: str) -> Dict:
        """建议处理策略"""
        return self.strategies.get(error_type, self.strategies.get("runtime_error", {}))
    
    def adapt_timeout(self, task_type: str) -> int:
        """自适应超时时间"""
        base_timeout = 120
        
        # 分析历史执行时间
        relevant_records = [
            r for r in self.history
            if task_type in r.get("task", "")
        ]
        
        if relevant_records:
            durations = [
                r.get("result", {}).get("duration", 0)
                for r in relevant_records
            ]
            if durations:
                avg_duration = sum(durations) / len(durations)
                return int(avg_duration * 1.5)
        
        return base_timeout
    
    def learn_from_success(self, task: str, strategy: Dict) -> None:
        """从成功中学习"""
        key = self._extract_task_pattern(task)
        if key not in self.strategies:
            self.strategies[key] = strategy
        else:
            # 更新策略
            current = self.strategies[key]
            current["success_count"] = current.get("success_count", 0) + 1
        
        self._save_strategies()
    
    def _extract_task_pattern(self, task: str) -> str:
        """提取任务模式"""
        task_lower = task.lower()
        
        if "test" in task_lower:
            return "test_task"
        elif "fix" in task_lower or "repair" in task_lower:
            return "fix_task"
        elif "implement" in task_lower or "create" in task_lower:
            return "implement_task"
        else:
            return "general_task"
    
    def get_evolution_stats(self) -> Dict:
        """获取进化统计"""
        total = len(self.history)
        successes = sum(
            1 for r in self.history
            if r.get("result", {}).get("success", False)
        )
        
        return {
            "total_executions": total,
            "successful": successes,
            "failed": total - successes,
            "success_rate": successes / total if total > 0 else 0,
            "strategies_learned": len(self.strategies)
        }


    def _save_strategies(self):
        """保存策略"""
        with open(self.strategy_file, 'w') as f:
            json.dump(self.strategies, f, indent=2)

__all__ = ["EvolutionEngine"]
