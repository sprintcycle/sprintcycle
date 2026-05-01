"""
Traceback Parser - 错误堆栈解析

支持 Python/JavaScript/Generic 格式的错误堆栈解析。
"""

import re
from typing import Optional

from .bug_models import Location
from .bug_models import StackFrame, ParsedTraceback  # noqa: F401 - re-exported


def parse_traceback(error_log: str, language: str = "python") -> ParsedTraceback:
    """解析错误堆栈信息"""
    parsed = ParsedTraceback()
    parsed.full_traceback = error_log
    
    if language == "python":
        _parse_python_traceback(error_log, parsed)
    elif language in ("javascript", "typescript"):
        _parse_js_traceback(error_log, parsed)
    else:
        _parse_generic_error(error_log, parsed)
    
    return parsed


def _parse_python_traceback(error_log: str, parsed: ParsedTraceback) -> None:
    lines = error_log.strip().split("\n")
    
    if lines:
        error_line = lines[-1].strip()
        match = re.match(r"(\w+):\s*(.*)", error_line)
        if match:
            parsed.error_type = match.group(1)
            parsed.error_message = match.group(2)
        else:
            parsed.error_type = "Error"
            parsed.error_message = error_line
    
    frame_pattern = r'File "(.+)", line (\d+)(?:, in (.+))?\s*\n\s*(.+)'
    matches = re.finditer(frame_pattern, error_log)
    
    for match in matches:
        frame = StackFrame(
            file_path=match.group(1),
            line_number=int(match.group(2)),
            function_name=match.group(3),
            code=match.group(4).strip() if match.group(4) else None,
        )
        parsed.frames.append(frame)
    
    for frame in parsed.frames:
        if not _is_stdlib_path(frame.file_path):
            parsed.location = Location(
                file_path=frame.file_path,
                line_number=frame.line_number,
                function_name=frame.function_name,
            )
            parsed.code_snippet = frame.code
            break
    
    if not parsed.location and parsed.frames:
        frame = parsed.frames[-1]
        parsed.location = Location(
            file_path=frame.file_path,
            line_number=frame.line_number,
            function_name=frame.function_name,
        )
        parsed.code_snippet = frame.code


def _parse_js_traceback(error_log: str, parsed: ParsedTraceback) -> None:
    match = re.search(r"(\w+Error):\s*(.*?)(?:\s+at\s+|\n|$)", error_log, re.DOTALL)
    if match:
        parsed.error_type = match.group(1)
        parsed.error_message = match.group(2).strip()
    
    frame_pattern = r"at\s+(?:(.+?)\s+\)?(.+?):(\d+):(\d+)\)?"
    matches = re.finditer(frame_pattern, error_log)
    
    for match in matches:
        frame = StackFrame(
            file_path=match.group(2),
            line_number=int(match.group(3)),
            function_name=match.group(1),
            column_number=int(match.group(4)),
        )
        parsed.frames.append(frame)
    
    if parsed.frames:
        frame = parsed.frames[0]
        parsed.location = Location(
            file_path=frame.file_path,
            line_number=frame.line_number,
            column_number=frame.column_number,
            function_name=frame.function_name,
        )


def _parse_generic_error(error_log: str, parsed: ParsedTraceback) -> None:
    lines = error_log.strip().split("\n")
    
    if lines:
        match = re.match(r"(\w+Error|\w+Exception):\s*(.*)", lines[-1].strip())
        if match:
            parsed.error_type = match.group(1)
            parsed.error_message = match.group(2)
        else:
            parsed.error_type = "UnknownError"
            parsed.error_message = lines[-1].strip()
    
    path_pattern = r"([/\w]+\.[\w]+):(\d+)"
    match = re.search(path_pattern, error_log)
    if match:
        parsed.location = Location(
            file_path=match.group(1),
            line_number=int(match.group(2)),
        )


def _is_stdlib_path(file_path: str) -> bool:
    stdlib_markers = ("/python3.", "/lib/python", "site-packages", "<")
    return any(m in file_path for m in stdlib_markers)
