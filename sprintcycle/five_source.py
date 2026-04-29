"""
SprintCycle 五源验证模块 v4.10

验证项目的五个关键来源：
1. CLI - 命令行工具
2. Backend - 后端 API 服务
3. Tests - 测试套件
4. Docs - 文档
5. Config - 配置文件
"""
import os
from pathlib import Path
from typing import Dict, List, Any


class FiveSourceVerifier:
    """
    五源验证器 v4.10
    
    验证项目的五个关键来源：
    1. CLI - 命令行工具
    2. Backend - 后端 API 服务
    3. Tests - 测试套件
    4. Docs - 文档
    5. Config - 配置文件
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.sprintcycle_dir = self.project_path / "sprintcycle"
    
    def verify_all(self) -> Dict[str, Any]:
        """执行完整验证"""
        results = {
            "cli": self._verify_cli(),
            "backend": self._verify_backend(),
            "tests": self._verify_tests(),
            "docs": self._verify_docs(),
            "config": self._verify_config(),
        }
        r = dict(results); r["all_passed"] = all(r.get("passed", False) for r in r.values())
        return results
    
    def _verify_cli(self) -> Dict[str, Any]:
        """验证 CLI 工具"""
        cli_files = [
            self.project_path / "cli.py",
            self.sprintcycle_dir / "cli.py" if self.sprintcycle_dir.exists() else None,
        ]
        
        found = None
        for cli_file in cli_files:
            if cli_file and cli_file.exists():
                found = cli_file
                break
        
        if not found:
            return {
                "passed": False,
                "details": "CLI 文件不存在 (cli.py)",
                "required": str(self.project_path / "cli.py")
            }
        
        try:
            with open(found, 'r') as f:
                f.read(100)
            executable = os.access(found, os.X_OK)
            return {
                "passed": True,
                "details": f"CLI 验证通过: {found.name}",
                "path": str(found),
                "executable": executable
            }
        except Exception as e:
            return {
                "passed": False,
                "details": f"CLI 文件无法读取: {str(e)}",
                "path": str(found)
            }
    
    def _verify_backend(self) -> Dict:
        """验证 Backend API 服务"""
        api_server = self.sprintcycle_dir / "api" / "server.py"
        
        if not api_server.exists():
            return {
                "passed": False,
                "details": "API Server 文件不存在",
                "required": str(api_server)
            }
        
        try:
            with open(api_server, 'r') as f:
                content = f.read()
            
            has_health = any(marker in content for marker in [
                'health', 'HealthCheck', 'ping', '/health', '/status'
            ])
            
            return {
                "passed": True,
                "details": "API Server 存在",
                "path": str(api_server),
                "has_health_endpoint": has_health
            }
        except Exception as e:
            return {
                "passed": False,
                "details": f"API Server 无法读取: {str(e)}"
            }
    
    def _verify_tests(self) -> Dict:
        """验证测试套件"""
        tests_dir = self.project_path / "tests"
        
        if not tests_dir.exists():
            return {
                "passed": False,
                "details": "测试目录不存在",
                "required": str(tests_dir)
            }
        
        test_files = list(tests_dir.glob("test_*.py"))
        
        if not test_files:
            return {
                "passed": False,
                "details": "没有找到测试文件",
                "required": str(tests_dir / "test_*.py")
            }
        
        total_tests = 0
        for tf in test_files:
            try:
                with open(tf, 'r') as f:
                    content = f.read()
                    total_tests += content.count("def test_")
            except:
                pass
        
        return {
            "passed": True,
            "details": f"测试套件正常: {len(test_files)} 文件, ~{total_tests} 测试",
            "test_files": len(test_files),
            "test_count": total_tests
        }
    
    def _verify_docs(self) -> Dict:
        """验证文档"""
        readme = self.project_path / "README.md"
        readme_cn = self.project_path / "README_CN.md"
        docs_dir = self.project_path / "docs"
        
        has_readme = readme.exists() or readme_cn.exists()
        has_docs = docs_dir.exists() and any(docs_dir.iterdir())
        
        if not has_readme:
            return {
                "passed": False,
                "details": "README 文件不存在",
                "required": str(readme)
            }
        
        return {
            "passed": True,
            "details": "文档完整" if has_docs else "README 存在 (无 docs 目录)",
            "has_readme": has_readme,
            "has_docs": has_docs
        }
    
    def _verify_config(self) -> Dict:
        """验证配置文件"""
        required_configs = {
            "config.yaml": self.project_path / "config.yaml",
            "requirements.txt": self.project_path / "requirements.txt",
            "pyproject.toml": self.project_path / "pyproject.toml",
        }
        
        missing = []
        present = []
        
        for name, path in required_configs.items():
            if path.exists():
                present.append(name)
            else:
                missing.append(name)
        
        if missing:
            return {
                "passed": False,
                "details": f"缺少配置文件: {', '.join(missing)}",
                "missing": missing,
                "present": present
            }
        
        return {
            "passed": True,
            "details": "所有配置文件完整",
            "present": present
        }


__all__ = ["FiveSourceVerifier"]
