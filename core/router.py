"""验证策略路由"""

from typing import Dict, Any, List
from .verifier import FiveSourceVerifier, VerifySource


class VerificationRouter:
    """根据项目类型选择验证策略"""
    
    def __init__(self, verifier: FiveSourceVerifier):
        self.verifier = verifier
    
    async def route(self, project_type: str) -> Dict[str, Any]:
        """根据项目类型路由验证策略"""
        strategies = {
            "web_app": [VerifySource.VISUAL, VerifySource.FRONTEND, VerifySource.BACKEND, VerifySource.TESTS],
            "cli_tool": [VerifySource.CLI, VerifySource.TESTS],
            "api_service": [VerifySource.BACKEND, VerifySource.TESTS],
            "full_stack": [VerifySource.VISUAL, VerifySource.CLI, VerifySource.FRONTEND, VerifySource.BACKEND, VerifySource.TESTS],
        }
        
        sources = strategies.get(project_type, list(VerifySource))
        
        print(f"📋 验证策略: {project_type} -> {[s.value for s in sources]}")
        
        results = []
        for source in sources:
            result = await self.verifier.verify_single(source)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        return {
            "project_type": project_type,
            "passed": passed == len(results),
            "passed_count": passed,
            "total": len(results),
            "results": [r.to_dict() for r in results]
        }
