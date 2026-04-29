"""
SprintCycle 文件回滚模块 v4.10

提供文件变更的回滚管理功能：
- 执行前自动备份
- 支持单文件/批量回滚
- 保留回滚历史
- 事务性回滚
"""
import os
import json
import shutil
import uuid
import difflib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class RollbackManager:
    """
    文件变更回滚管理器 v4.10
    
    功能：
    - 执行前自动备份文件
    - 支持单文件/批量回滚
    - 保留回滚历史
    - 事务性回滚（全部成功或全部回滚）
    - 自动备份任务执行前的文件状态
    """
    
    def __init__(self, project_path: str, auto_backup: bool = True, max_backups: int = 10):
        self.project_path = Path(project_path)
        self.backup_dir = self.project_path / ".sprintcycle" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_history: List[Dict] = []
        self._current_backup_id: Optional[str] = None
        self._current_transaction_files: List[str] = []
        self.auto_backup_enabled = auto_backup
        self.max_backups = max_backups
    
    def backup_files(self, files: List[str]) -> Dict:
        """备份指定文件"""
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]
        backup_subdir = self.backup_dir / backup_id
        backup_subdir.mkdir(parents=True, exist_ok=True)
        
        backed_up = []
        failed = []
        
        for file_path in files:
            full_path = self.project_path / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    rel_path = full_path.relative_to(self.project_path)
                    dest_path = backup_subdir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(full_path, dest_path)
                    backed_up.append(file_path)
                except Exception as e:
                    failed.append({"file": file_path, "error": str(e)})
            else:
                failed.append({"file": file_path, "error": "文件不存在"})
        
        record = {
            "backup_id": backup_id,
            "timestamp": datetime.now().isoformat(),
            "backed_up": backed_up,
            "failed": failed,
            "total": len(files)
        }
        self.backup_history.append(record)
        self._cleanup_if_needed()
        return record
    
    def restore_files(self, backup_id: str, files: Optional[List[str]] = None) -> Dict:
        """从备份恢复文件"""
        backup_subdir = self.backup_dir / backup_id
        if not backup_subdir.exists():
            return {"success": False, "error": f"备份不存在: {backup_id}", "restored": [], "failed": []}
        
        if files is None:
            # 恢复所有文件
            files = []
            for root, _, filenames in os.walk(backup_subdir):
                for filename in filenames:
                    rel_path = Path(root) / filename
                    files.append(str(rel_path.relative_to(backup_subdir)))
        
        restored = []
        failed = []
        
        for file_path in files:
            src_path = backup_subdir / file_path
            dest_path = self.project_path / file_path
            
            if src_path.exists():
                try:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dest_path)
                    restored.append(file_path)
                except Exception as e:
                    failed.append({"file": file_path, "error": str(e)})
            else:
                failed.append({"file": file_path, "error": "备份中不存在此文件"})
        
        return {
            "success": len(restored) > 0,
            "restored": restored,
            "failed": failed,
            "backup_id": backup_id
        }
    
    def begin_transaction(self, task_id: str, files: List[str]) -> str:
        """开始事务 - 备份文件并返回事务ID（以 txn_ 开头）"""
        # 生成以 txn_ 开头的事务ID
        backup_id = f"txn_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建备份目录
        backup_subdir = self.backup_dir / backup_id
        backup_subdir.mkdir(parents=True, exist_ok=True)
        
        # 备份文件
        backed_up = []
        for file_path in files:
            full_path = self.project_path / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    rel_path = full_path.relative_to(self.project_path)
                    dest_path = backup_subdir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(full_path, dest_path)
                    backed_up.append(file_path)
                except Exception:
                    pass
        
        record = {
            "backup_id": backup_id,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "backed_up": backed_up,
            "files": files
        }
        self.backup_history.append(record)
        
        self._current_backup_id = backup_id
        self._current_transaction_files = files
        
        return backup_id
    
    def commit_transaction(self, backup_id: Optional[str] = None) -> Dict:
        """v4.10: 提交事务 - 返回字典格式"""
        if backup_id is None:
            backup_id = self._current_backup_id
        
        if not backup_id:
            return {"success": False, "message": "没有活动的事务"}
        
        backup_subdir = self.backup_dir / backup_id
        if backup_subdir.exists():
            shutil.rmtree(backup_subdir)
        
        self.backup_history = [
            r for r in self.backup_history 
            if r.get("backup_id") != backup_id
        ]
        self._current_backup_id = None
        self._current_transaction_files = []
        
        return {"success": True, "message": "事务已提交，备份已清理"}
    
    def rollback_transaction(self, backup_id: Optional[str] = None) -> Dict:
        """v4.10: 回滚事务 - 返回字典格式"""
        if backup_id is None:
            backup_id = self._current_backup_id
        
        if not backup_id:
            return {"success": False, "message": "没有活动的事务"}
        
        result = self.restore_files(backup_id)
        
        if result["success"]:
            # 清理备份
            backup_subdir = self.backup_dir / backup_id
            if backup_subdir.exists():
                shutil.rmtree(backup_subdir)
            
            self.backup_history = [
                r for r in self.backup_history 
                if r.get("backup_id") != backup_id
            ]
            self._current_backup_id = None
            self._current_transaction_files = []
            
            return {"success": True, "message": "事务已回滚", "restored": result["restored"]}
        else:
            return {"success": False, "message": "回滚失败", "error": result.get("failed", [])}
    
    def get_backup_diff(self, backup_id: str, file_path: str) -> str:
        """获取备份与当前文件的差异"""
        backup_subdir = self.backup_dir / backup_id
        backup_file = backup_subdir / file_path
        current_file = self.project_path / file_path
        
        if not backup_file.exists():
            return f"备份中不存在文件: {file_path}"
        
        if not current_file.exists():
            return f"当前文件不存在: {file_path}"
        
        try:
            with open(backup_file, 'r') as f:
                backup_lines = f.readlines()
            with open(current_file, 'r') as f:
                current_lines = f.readlines()
            
            diff = difflib.unified_diff(
                backup_lines,
                current_lines,
                fromfile=f"backup/{file_path}",
                tofile=f"current/{file_path}"
            )
            
            return ''.join(diff)
        except Exception as e:
            return f"生成差异失败: {str(e)}"
    
    def auto_backup_before_edit(self, files: List[str], task_id: Optional[str] = None) -> Dict:
        """编辑前自动备份"""
        if not self.auto_backup_enabled:
            return {"success": True, "message": "自动备份已禁用", "backup_id": None}
        
        task_id = task_id or str(uuid.uuid4())[:8]
        backup_id = f"auto_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = self.backup_files(files)
        result["backup_id"] = backup_id  # 使用新的 backup_id
        result["auto"] = True
        
        return {"success": True, **result}
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                meta_file = backup_dir / "meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r') as f:
                            backups.append(json.load(f))
                    except:
                        backups.append({"backup_id": backup_dir.name})
                else:
                    backups.append({"backup_id": backup_dir.name})
        
        return sorted(backups, key=lambda x: x.get("backup_id", ""), reverse=True)
    
    def delete_backup(self, backup_id: str) -> Dict:
        """删除备份"""
        backup_subdir = self.backup_dir / backup_id
        if not backup_subdir.exists():
            return {"success": False, "error": "备份不存在"}
        
        shutil.rmtree(backup_subdir)
        self.backup_history = [
            r for r in self.backup_history 
            if r.get("backup_id") != backup_id
        ]
        
        return {"success": True, "message": f"备份 {backup_id} 已删除"}
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict]:
        """获取备份信息"""
        for record in self.backup_history:
            if record.get("backup_id") == backup_id:
                return record
        return None
    
    def _cleanup_if_needed(self):
        """清理旧备份"""
        while len(self.backup_history) > self.max_backups:
            old_backup = self.backup_history.pop(0)
            backup_id = old_backup.get("backup_id")
            if backup_id:
                backup_subdir = self.backup_dir / backup_id
                if backup_subdir.exists():
                    shutil.rmtree(backup_subdir)


__all__ = ["RollbackManager"]
