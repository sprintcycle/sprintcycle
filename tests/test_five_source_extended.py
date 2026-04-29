"""扩展五源验证测试 - 针对 five_source.py 低覆盖率模块"""
import pytest
import tempfile
from pathlib import Path
from sprintcycle.five_source import FiveSourceVerifier


class TestFiveSourceVerifier:
    """五源验证器测试"""
    
    def test_verifier_initialization(self):
        """测试验证器初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            assert verifier.project_path == Path(tmpdir)
            assert verifier.sprintcycle_dir == Path(tmpdir) / "sprintcycle"
    
    def test_verify_all_structure(self):
        """测试完整验证返回结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            # Create minimal project structure
            cli_file = Path(tmpdir) / "cli.py"
            cli_file.write_text("#!/usr/bin/env python3\nprint('cli')\n")
            
            results = verifier.verify_all()
            assert "cli" in results
            assert "backend" in results
            assert "tests" in results
            assert "docs" in results
            assert "config" in results
    
    def test_verify_cli_not_found(self):
        """测试CLI验证-文件不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            result = verifier._verify_cli()
            assert result["passed"] is False
            assert "不存在" in result["details"]
    
    def test_verify_cli_found(self):
        """测试CLI验证-文件存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            cli_file = Path(tmpdir) / "cli.py"
            cli_file.write_text("#!/usr/bin/env python3\nprint('test')\n")
            
            result = verifier._verify_cli()
            assert result["passed"] is True
            assert "验证通过" in result["details"]
    
    def test_verify_backend_not_found(self):
        """测试后端验证-文件不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            result = verifier._verify_backend()
            assert result["passed"] is False
    
    def test_verify_backend_found(self):
        """测试后端验证-文件存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            # Backend expects sprintcycle/api/server.py
            backend_file = Path(tmpdir) / "sprintcycle" / "api" / "server.py"
            backend_file.parent.mkdir(parents=True)
            backend_file.write_text("# Server\n")
            
            result = verifier._verify_backend()
            assert result["passed"] is True
    
    def test_verify_tests_not_found(self):
        """测试测试验证-目录不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            result = verifier._verify_tests()
            assert result["passed"] is False
    
    def test_verify_tests_found(self):
        """测试测试验证-目录存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            tests_dir = Path(tmpdir) / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_example.py").write_text("def test_example():\n    assert True\n")
            
            result = verifier._verify_tests()
            assert result["passed"] is True
            assert "test_count" in result
    
    def test_verify_docs_not_found(self):
        """测试文档验证-文件不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            result = verifier._verify_docs()
            assert result["passed"] is False
    
    def test_verify_docs_found_readme(self):
        """测试文档验证-README存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            readme = Path(tmpdir) / "README.md"
            readme.write_text("# Project\n")
            
            result = verifier._verify_docs()
            assert result["passed"] is True
    
    def test_verify_docs_found_multiple(self):
        """测试文档验证-多文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            (Path(tmpdir) / "README.md").write_text("# Project\n")
            (Path(tmpdir) / "CONTRIBUTING.md").write_text("# Contributing\n")
            
            result = verifier._verify_docs()
            assert result["passed"] is True
    
    def test_verify_config_not_found(self):
        """测试配置验证-文件不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            result = verifier._verify_config()
            assert result["passed"] is False
            assert "missing" in result
    
    def test_verify_config_all_present(self):
        """测试配置验证-所有文件存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            # Create all required config files
            (Path(tmpdir) / "config.yaml").write_text("key: value\n")
            (Path(tmpdir) / "requirements.txt").write_text("# requirements\n")
            (Path(tmpdir) / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            
            result = verifier._verify_config()
            assert result["passed"] is True
            assert len(result.get("present", [])) == 3
    
    def test_verify_config_partial(self):
        """测试配置验证-部分文件存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FiveSourceVerifier(tmpdir)
            (Path(tmpdir) / "config.yaml").write_text("key: value\n")
            
            result = verifier._verify_config()
            assert result["passed"] is False
            assert "missing" in result
            assert "config.yaml" not in result["missing"]
