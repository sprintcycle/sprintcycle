#!/usr/bin/env python3
"""
冒烟测试 - Smoke Runner

启动app，逐个打HTTP endpoint，检查是否5xx/AttributeError。

输出：结构化JSON，Trae可以直接读取作为修复上下文。
"""

import asyncio
import json
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import httpx

class SmokeRunner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.issues: List[Dict[str, Any]] = []
        self.base_url = "http://localhost:8000"
        self.server_process = None
    
    def _add_issue(self, endpoint: str, status_code: int, issue_type: str, message: str):
        """添加问题记录"""
        self.issues.append({
            "endpoint": endpoint,
            "status_code": status_code,
            "type": issue_type,
            "message": message,
            "severity": "error" if status_code >= 500 else "warning"
        })
    
    def _start_server(self) -> bool:
        """启动开发服务器"""
        try:
            os.chdir(self.project_root)
            
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_root)
            
            self.server_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "sprintcycle.interfaces.http.app:create_app", "--host", "0.0.0.0", "--port", "8000"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("⏳ 等待服务器启动...")
            time.sleep(5)
            
            try:
                response = httpx.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    print("✅ 服务器启动成功")
                    return True
            except Exception:
                pass
            
            print("⏳ 再等待5秒...")
            time.sleep(5)
            
            try:
                response = httpx.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    print("✅ 服务器启动成功")
                    return True
            except Exception as e:
                print(f"❌ 服务器启动失败: {e}")
                self._stop_server()
                return False
            
            return False
        except Exception as e:
            print(f"❌ 启动服务器时发生错误: {e}")
            return False
    
    def _stop_server(self):
        """停止服务器"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("🛑 服务器已停止")
            except Exception:
                self.server_process.kill()
    
    def _discover_endpoints(self) -> List[str]:
        """发现所有HTTP端点"""
        endpoints = [
            "/health",
            "/",
            "/api/clients",
            "/api/config",
            "/api/config/schema",
            "/api/config/history",
            "/api/execution",
            "/api/execution/status",
            "/api/lifecycle",
            "/api/governance",
            "/api/suggestions",
            "/api/hitl",
        ]
        return endpoints
    
    async def _test_endpoint(self, client: httpx.AsyncClient, endpoint: str) -> Dict[str, Any]:
        """测试单个端点"""
        result = {
            "endpoint": endpoint,
            "status_code": 0,
            "success": False,
            "error": None,
            "response_time": 0.0
        }
        
        try:
            start_time = time.time()
            response = await client.get(f"{self.base_url}{endpoint}")
            response_time = time.time() - start_time
            
            result["status_code"] = response.status_code
            result["response_time"] = response_time
            
            if response.status_code >= 500:
                result["success"] = False
                result["error"] = response.text
                self._add_issue(endpoint, response.status_code, "server_error", f"5xx错误: {response.text}")
            elif response.status_code >= 400:
                result["success"] = False
                result["error"] = response.text
            else:
                result["success"] = True
                
        except Exception as e:
            result["error"] = str(e)
            self._add_issue(endpoint, 0, "connection_error", f"连接失败: {e}")
        
        return result
    
    async def _run_smoke_tests(self) -> List[Dict[str, Any]]:
        """运行所有冒烟测试"""
        results = []
        endpoints = self._discover_endpoints()
        
        async with httpx.AsyncClient(timeout=10) as client:
            tasks = [self._test_endpoint(client, endpoint) for endpoint in endpoints]
            results = await asyncio.gather(*tasks)
        
        return results
    
    def run(self) -> Dict[str, Any]:
        """运行完整的冒烟测试"""
        self.issues = []
        results = []
        
        print("🚀 启动冒烟测试...")
        
        if not self._start_server():
            return {
                "status": "failed",
                "error": "无法启动服务器",
                "issues": self.issues,
                "results": [],
                "summary": {"errors": 1, "warnings": 0}
            }
        
        try:
            print("🔍 开始测试端点...")
            results = asyncio.run(self._run_smoke_tests())
        finally:
            self._stop_server()
        
        return {
            "status": "completed",
            "results": results,
            "issues": self.issues,
            "summary": {
                "errors": len([i for i in self.issues if i["severity"] == "error"]),
                "warnings": len([i for i in self.issues if i["severity"] == "warning"]),
                "total_tests": len(results),
                "passed": len([r for r in results if r["success"]])
            }
        }

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    runner = SmokeRunner(project_root)
    result = runner.run()
    
    print("\n" + "="*60)
    print("冒烟测试结果")
    print("="*60)
    
    for test_result in result["results"]:
        status = "✅" if test_result["success"] else "❌"
        print(f"{status} {test_result['endpoint']}")
        if not test_result["success"]:
            print(f"   状态码: {test_result['status_code']}")
            print(f"   错误: {test_result['error']}")
        print()
    
    print("发现的问题:")
    print("-" * 40)
    for issue in result["issues"]:
        severity = "❌" if issue["severity"] == "error" else "⚠️"
        print(f"{severity} {issue['endpoint']}")
        print(f"   {issue['message']}")
    
    print(f"\n总计: {result['summary']['passed']}/{result['summary']['total_tests']} 通过")
    print(f"错误: {result['summary']['errors']}, 警告: {result['summary']['warnings']}")
    
    output_path = os.path.join(project_root, "harness", "smoke_runner_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 报告已保存到: {output_path}")
    
    sys.exit(0 if result["summary"]["errors"] == 0 else 1)

if __name__ == "__main__":
    main()