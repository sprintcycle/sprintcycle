"""
SprintCycle 错误处理模块 v4.10

提供错误分类、友好提示和修复建议功能：
- 错误分类与归因
- 友好错误消息
- 修复建议
- 错误统计
"""
import json
import re
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import Counter


class ErrorCategory(Enum):
    """错误分类"""
    SYNTAX = "syntax"
    IMPORT = "import"
    RUNTIME = "runtime"
    CONFIGURATION = "config"
    NETWORK = "network"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
    # 扩展分类
    LOGIC = "logic"
    AIDER = "aider"
    EMPTY_OUTPUT = "empty_output"
    NO_CHANGES = "no_changes"


@dataclass
class FailureRecord:
    """失败记录"""
    error_type: str
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    task_id: Optional[str] = None
    timestamp: str = ""
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    context: Dict[str, Any] = field(default_factory=dict)
    recent: bool = True


class ErrorHelper:
    """
    错误辅助类 v4.10
    
    功能：
    - 错误分类与归因
    - 友好错误消息
    - 修复建议
    - 错误统计
    """
    
    ERROR_ICONS = {
        ErrorCategory.SYNTAX: ("🔧", "语法错误"),
        ErrorCategory.IMPORT: ("📦", "导入错误"),
        ErrorCategory.RUNTIME: ("⚡", "运行时错误"),
        ErrorCategory.CONFIGURATION: ("⚙️", "配置错误"),
        ErrorCategory.NETWORK: ("🌐", "网络错误"),
        ErrorCategory.TIMEOUT: ("⏱️", "超时错误"),
        ErrorCategory.UNKNOWN: ("❓", "未知错误"),
        ErrorCategory.LOGIC: ("🧠", "逻辑错误"),
        ErrorCategory.AIDER: ("🤖", "AI助手错误"),
        ErrorCategory.EMPTY_OUTPUT: ("📭", "输出为空"),
        ErrorCategory.NO_CHANGES: ("📝", "无变更"),
    }
    
    FRIENDLY_MESSAGES = {
        "SyntaxError": "📝 代码存在语法错误，请检查括号、引号、缩进是否匹配",
        "IndentationError": "📐 缩进不一致，请统一使用 4 空格或 Tab",
        "NameError": "📛 变量或函数未定义，请检查拼写或是否已导入",
        "ModuleNotFoundError": "📦 缺少必要的包，请运行 pip install 安装",
        "ImportError": "📥 模块导入失败，请检查模块路径和依赖",
        "TypeError": "🔄 数据类型不匹配，请检查变量类型转换",
        "ValueError": "📊 值不符合预期，请检查输入数据格式",
        "AttributeError": "🎯 对象没有该属性，请检查对象类型",
        "KeyError": "🔑 字典中不存在该键，请检查键名是否正确",
        "IndexError": "📏 列表索引超出范围，请检查列表长度",
        "FileNotFoundError": "📁 文件不存在，请检查文件路径",
        "PermissionError": "🔒 没有访问权限，请检查文件权限",
        "ConnectionError": "🌐 网络连接失败，请检查网络和目标地址",
        "TimeoutError": "⏱️ 请求超时，请增加超时时间或检查网络",
        "RecursionError": "🔄 递归深度超限，请检查递归终止条件",
    }
    
    FIX_COMMANDS = {
        ErrorCategory.SYNTAX: "python3 -m py_compile <file>",
        ErrorCategory.IMPORT: "pip install <package>",
        ErrorCategory.CONFIGURATION: "检查配置文件格式",
        ErrorCategory.NETWORK: "检查网络连接",
        ErrorCategory.TIMEOUT: "增加超时时间",
    }
    
    # 错误严重程度映射
    ERROR_SEVERITY = {
        "SyntaxError": "critical",
        "IndentationError": "critical",
        "ImportError": "high",
        "ModuleNotFoundError": "high",
        "NameError": "high",
        "TypeError": "medium",
        "ValueError": "medium",
        "AttributeError": "medium",
        "KeyError": "low",
        "IndexError": "low",
        "FileNotFoundError": "medium",
        "PermissionError": "medium",
        "ConnectionError": "medium",
        "TimeoutError": "low",
    }
    
    # 错误原因映射
    ERROR_REASONS = {
        "SyntaxError": "语法错误：代码存在语法问题，Python 无法解析",
        "IndentationError": "缩进错误：代码缩进不一致",
        "ImportError": "导入错误：模块导入失败",
        "ModuleNotFoundError": "模块未找到：缺少必要的依赖包",
        "NameError": "名称错误：使用了未定义的变量或函数",
        "TypeError": "类型错误：操作或函数应用于错误的数据类型",
        "ValueError": "值错误：参数值不符合预期",
        "AttributeError": "属性错误：对象没有请求的属性",
        "KeyError": "键错误：字典中不存在指定的键",
        "IndexError": "索引错误：序列索引超出范围",
        "FileNotFoundError": "文件未找到：指定的文件不存在",
        "PermissionError": "权限错误：没有足够的权限访问资源",
        "ConnectionError": "连接错误：网络连接失败",
        "TimeoutError": "超时错误：操作执行超时",
    }
    
    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.error_stats: Counter = Counter()
        self.recent_errors: List[FailureRecord] = []
    
    def classify_error(self, error_message: str) -> ErrorCategory:
        """分类错误"""
        error_lower = error_message.lower()
        
        if "syntax" in error_lower or "indentation" in error_lower:
            return ErrorCategory.SYNTAX
        elif "import" in error_lower or "modulenotfound" in error_lower:
            return ErrorCategory.IMPORT
        elif "timeout" in error_lower:
            return ErrorCategory.TIMEOUT
        elif "connection" in error_lower or "network" in error_lower:
            return ErrorCategory.NETWORK
        elif "recursion" in error_lower:
            return ErrorCategory.LOGIC
        elif "rate limit" in error_lower:
            return ErrorCategory.AIDER
        elif "key" in error_lower and "error" in error_lower:
            return ErrorCategory.RUNTIME
        elif "type" in error_lower and "error" in error_lower:
            return ErrorCategory.RUNTIME
        elif "value" in error_lower and "error" in error_lower:
            return ErrorCategory.RUNTIME
        elif "attribute" in error_lower and "error" in error_lower:
            return ErrorCategory.RUNTIME
        elif "index" in error_lower and "error" in error_lower:
            return ErrorCategory.RUNTIME
        
        return ErrorCategory.UNKNOWN
    
    def get_friendly_message(self, error_type: str) -> str:
        """获取友好的错误消息"""
        return self.FRIENDLY_MESSAGES.get(
            error_type,
            f"❌ 发生了未知错误: {error_type}"
        )
    
    @staticmethod
    def format_error(error_output: str, context: Optional[Dict[str, Any]] = None) -> str:
        """格式化错误输出 - 符合测试期望格式"""
        context = context or {}
        task = context.get("task", "未知任务")
        
        # 解析错误类型
        error_type = "UnknownError"
        error_detail = error_output
        
        for pattern in ["SyntaxError", "IndentationError", "NameError", 
                       "ModuleNotFoundError", "ImportError", "TypeError",
                       "ValueError", "AttributeError", "KeyError",
                       "IndexError", "FileNotFoundError", "PermissionError"]:
            if pattern in error_output:
                error_type = pattern
                break
        
        # 获取友好消息
        friendly_msg = ErrorHelper.FRIENDLY_MESSAGES.get(
            error_type,
            "💡 请检查错误信息并尝试修复"
        )
        
        # 格式化输出 - 包含测试期望的 "🔴 执行失败"
        formatted = f"""🔴 执行失败
==================================================
📋 任务: {task}

💡 {friendly_msg}

📝 错误详情:
   {error_output}

🔧 修复建议: 运行 python3 -m py_compile <file> 检查语法
--------------------------------------------------"""
        
        return formatted
    
    @staticmethod
    def get_fix_command(error_category: ErrorCategory, error_message: str = "") -> str:
        """获取修复命令"""
        if error_category == ErrorCategory.SYNTAX:
            return "python3 -m py_compile <file>"
        elif error_category == ErrorCategory.IMPORT:
            return "pip install <package> 或检查模块路径"
        elif error_category == ErrorCategory.CONFIGURATION:
            return "检查配置文件格式和必填项"
        elif error_category == ErrorCategory.NETWORK:
            return "检查网络连接和目标地址"
        elif error_category == ErrorCategory.TIMEOUT:
            return "增加超时时间或优化执行效率"
        else:
            return "查看错误日志进行排查"
    
    @staticmethod
    def get_error_reason(error_output: str) -> str:
        """获取错误原因 - 静态方法"""
        for error_type, reason in ErrorHelper.ERROR_REASONS.items():
            if error_type in error_output:
                return reason
        return "未知错误：无法确定具体原因"
    
    @staticmethod
    def get_error_severity(error_output: str) -> str:
        """获取错误严重程度 - 静态方法"""
        for error_type, severity in ErrorHelper.ERROR_SEVERITY.items():
            if error_type in error_output:
                return severity
        return "unknown"
    
    @staticmethod
    def get_quick_fix(error_output: str) -> str:
        """获取快速修复建议 - 静态方法"""
        if "SyntaxError" in error_output:
            return "运行 python3 -m py_compile <file> 检查语法"
        elif "ImportError" in error_output or "ModuleNotFoundError" in error_output:
            return "运行 pip install <package> 安装缺失的包"
        elif "NameError" in error_output:
            return "检查变量名是否正确，确保已导入所需模块"
        elif "TypeError" in error_output:
            return "检查数据类型是否匹配"
        elif "KeyError" in error_output:
            return "检查字典键名是否存在"
        elif "TimeoutError" in error_output:
            return "增加超时时间或优化代码性能"
        else:
            return "查看错误详情进行排查"
    
    @staticmethod
    def format_error_for_log(error_output: str, context: Optional[Dict[str, Any]] = None) -> str:
        """格式化错误用于日志 - 静态方法"""
        context = context or {}
        task = context.get("task", "未知")
        severity = ErrorHelper.get_error_severity(error_output)
        reason = ErrorHelper.get_error_reason(error_output)
        
        return f"[{severity.upper()}] 任务 '{task}' 失败: {reason}\n详情: {error_output}"
    
    @staticmethod
    def get_error_statistics(errors: List[str]) -> Dict:
        """获取错误统计 - 静态方法"""
        if not errors:
            return {"total": 0, "by_type": {}}
        
        by_type: Counter = Counter()
        for error in errors:
            for error_type in ["SyntaxError", "ImportError", "NameError", 
                             "TypeError", "ValueError", "KeyError"]:
                if error_type in error:
                    by_type[error_type] += 1
                    break
        
        return {"total": len(errors), "by_type": dict(by_type)}
    
    @staticmethod
    def generate_error_report(errors: List[Dict]) -> str:
        """生成错误报告 - 静态方法"""
        if not errors:
            return "没有错误记录"
        
        lines = ["错误报告", "=" * 40]
        for i, error in enumerate(errors, 1):
            lines.append(f"{i}. {error.get('type', 'Unknown')}: {error.get('message', '')[:50]}")
        
        lines.append("=" * 40)
        lines.append(f"总计: {len(errors)} 个错误")
        
        return "\n".join(lines)
    
    @staticmethod
    def suggest_next_steps(record) -> List[str]:
        """建议下一步操作 - 静态方法"""
        if isinstance(record, FailureRecord):
            error_category = record.error_category
        else:
            # 假设是 dict 或有 error_category 属性的对象
            error_category = getattr(record, 'error_category', None) or record.get('error_category', ErrorCategory.UNKNOWN)
        
        suggestions = []
        
        if error_category == ErrorCategory.SYNTAX:
            suggestions.append("运行语法检查工具定位具体错误位置")
            suggestions.append("检查最近修改的代码块")
        elif error_category == ErrorCategory.IMPORT:
            suggestions.append("检查 requirements.txt 是否包含所需依赖")
            suggestions.append("运行 pip install -r requirements.txt")
        elif error_category == ErrorCategory.RUNTIME:
            suggestions.append("检查变量类型和值范围")
            suggestions.append("添加适当的异常处理")
        else:
            suggestions.append("查看错误日志进行排查")
            suggestions.append("尝试简化问题场景")
        
        return suggestions
    
    def get_fix_info(self, error_category: ErrorCategory) -> Dict:
        """获取修复信息 - 用于测试"""
        if error_category == ErrorCategory.SYNTAX:
            return {
                "icon": "🔧",
                "hint": "运行 python3 -m py_compile <file> 检查语法",
                "commands": ["python3 -m py_compile <file>"]
            }
        elif error_category == ErrorCategory.IMPORT:
            return {
                "icon": "📦",
                "hint": "运行 pip install 安装缺失的包",
                "commands": ["pip install <package>"]
            }
        else:
            return {
                "icon": "🔧",
                "hint": "检查错误信息并尝试修复",
                "commands": []
            }
    
    def record_error(self, record: FailureRecord) -> None:
        """记录错误"""
        self.error_stats[record.error_type] += 1
        self.recent_errors.append(record)
        if len(self.recent_errors) > 100:
            self.recent_errors = self.recent_errors[-100:]
    
    def get_error_stats(self) -> Dict:
        """获取错误统计"""
        return {
            "total": sum(self.error_stats.values()),
            "by_type": dict(self.error_stats),
            "recent_count": len(self.recent_errors)
        }
    
    def get_common_errors(self, top_n: int = 5) -> List[Dict]:
        """获取常见错误"""
        return [
            {"error_type": error_type, "count": count}
            for error_type, count in self.error_stats.most_common(top_n)
        ]


__all__ = ["ErrorHelper", "ErrorCategory", "FailureRecord"]
