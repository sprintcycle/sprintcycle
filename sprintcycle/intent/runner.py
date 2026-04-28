"""
Runner 意图处理器

处理 PRD 文件的直接执行
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from .base import IntentHandler, IntentResult
from ..prd.models import PRD
from ..prd.parser import PRDParser

logger = logging.getLogger(__name__)


class RunnerHandler(IntentHandler):
    """PRD 文件执行器"""
    
    def execute(self, prd: PRD) -> IntentResult:
        """执行 PRD"""
        logger.info(f"🚀 开始执行 PRD: {prd.project.name}")
        
        if not self.validate_prd(prd):
            return IntentResult(
                success=False,
                prd=prd,
                error="PRD 验证失败",
            )
        
        try:
            sprint_results = asyncio.run(
                self.dispatcher.execute_prd(prd, max_concurrent=3)
            )
            
            from ..scheduler.dispatcher import ExecutionStatus
            success = all(
                r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
                for r in sprint_results
            )
            
            return self._build_result(success, prd, sprint_results)
            
        except Exception as e:
            logger.exception("PRD 执行失败")
            return IntentResult(
                success=False,
                prd=prd,
                error=str(e),
            )
    
    @staticmethod
    def parse_prd_file(file_path: str) -> PRD:
        """解析 PRD 文件"""
        parser = PRDParser()
        return parser.parse_file(file_path)
