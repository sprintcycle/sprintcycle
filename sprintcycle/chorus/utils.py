"""
chorus.utils - 工具函数
"""
from typing import Any, Dict, List


def normalize_files_changed(files_changed: Any) -> Dict[str, List[str]]:
    """
    统一处理 files_changed 类型，确保返回标准格式
    
    支持的类型:
    - Dict: {"added": [], "modified": [], "deleted": [], "screenshots": []}
    - List: ["file1", "file2", ...]
    - None: 返回空字典
    - 其他: 尝试转换为字符串列表
    
    Returns:
        Dict[str, List[str]]: 标准格式的 files_changed
    """
    from loguru import logger
    
    default: Dict[str, List[str]] = {"added": [], "modified": [], "deleted": [], "screenshots": []}
    
    if files_changed is None:
        return default
    
    if isinstance(files_changed, dict):
        return {
            "added": files_changed.get("added", []),
            "modified": files_changed.get("modified", []),
            "deleted": files_changed.get("deleted", []),
            "screenshots": files_changed.get("screenshots", [])
        }
    
    if isinstance(files_changed, list):
        return {
            "added": [],
            "modified": files_changed,
            "deleted": [],
            "screenshots": []
        }
    
    logger.warning(f"files_changed 类型不支持: {type(files_changed)}, 使用默认值")
    return default


def extract_files_list(files_changed: Any) -> List[str]:
    """从 files_changed 中提取所有文件列表"""
    normalized = normalize_files_changed(files_changed)
    result = []
    for file_list in normalized.values():
        if isinstance(file_list, list):
            result.extend(file_list)
    return result


def has_changes(files_changed: Any) -> bool:
    """检查是否有任何文件变更"""
    files_list = extract_files_list(files_changed)
    return len(files_list) > 0


def get_change_summary(files_changed: Any) -> str:
    """获取变更摘要"""
    normalized = normalize_files_changed(files_changed)
    parts = []
    if normalized["added"]:
        parts.append(f"+{len(normalized['added'])} 新增")
    if normalized["modified"]:
        parts.append(f"~{len(normalized['modified'])} 修改")
    if normalized["deleted"]:
        parts.append(f"-{len(normalized['deleted'])} 删除")
    if normalized["screenshots"]:
        parts.append(f"[{len(normalized['screenshots'])} 截图]")
    
    if not parts:
        return "无变更"
    return " ".join(parts)
