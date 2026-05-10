"""Loguru 为主；仅对非 sprintcycle 的 stdlib logger 做「窄」桥接，避免与自研 loguru 双写。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger

_STDERR_FMT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)
_FILE_FMT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
)


class InterceptHandler(logging.Handler):
    """第三方库 stdlib ``LogRecord`` → loguru（统一观感）。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _is_sprintcycle_logger(name: str) -> bool:
    return name == "sprintcycle" or name.startswith("sprintcycle.")


def _configure_stdlib_intercept(root: logging.Logger) -> None:
    """根上挂桥；只清理非 sprintcycle 命名空间 logger 的 handler，逼其向 root 汇聚。"""
    root.handlers[:] = [h for h in root.handlers if not isinstance(h, InterceptHandler)]
    root.addHandler(InterceptHandler())
    root.setLevel(logging.DEBUG)

    for name in list(logging.root.manager.loggerDict.keys()):
        if not isinstance(name, str) or _is_sprintcycle_logger(name):
            continue
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True


def configure_sprintcycle_logging(
    *,
    log_file: str = ".sprintcycle/logs/sprintcycle.log",
    stderr_level: str = "INFO",
    file_level: str = "DEBUG",
) -> None:
    """配置 loguru（stderr + 轮转文件），并把第三方 stdlib logging 窄桥接到 loguru。"""
    logger.remove()

    logger.add(
        sys.stderr,
        level=stderr_level,
        format=_STDERR_FMT,
        colorize=sys.stderr.isatty(),
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_path),
        level=file_level,
        format=_FILE_FMT,
        rotation="10 MB",
        retention=5,
        encoding="utf-8",
    )

    _configure_stdlib_intercept(logging.getLogger())
