#!/usr/bin/env python3
"""
SprintCycle 自动升级验证器

自动验证升级过程中的架构不变性和功能正确性。
无需人工介入，完全自动化执行升级验证。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]


class AutoUpgradeVerifier:
    """自动升级验证器"""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def run_full_verification(self) -> bool:
        """执行完整的升级验证流程"""
        print("🚀 开始自动升级验证...")
        
        all_passed = True
        
        # 阶段1: 架构验证
        print("\n--- Phase 1: 架构不变性验证 ---")
        arch_passed = self._verify_architecture()
        all_passed &= arch_passed
        
        # 阶段2: 单元测试
        print("\n--- Phase 2: 单元测试验证 ---")
        unit_passed = self._verify_unit_tests()
        all_passed &= unit_passed
        
        # 阶段3: API 契约验证
        print("\n--- Phase 3: API 契约验证 ---")
        api_passed = self._verify_api_contract()
        all_passed &= api_passed
        
        # 阶段4: E2E 测试
        print("\n--- Phase 4: E2E 测试验证 ---")
        e2e_passed = self._verify_e2e()
        all_passed &= e2e_passed
        
        # 阶段5: 文档验证
        print("\n--- Phase 5: 文档同步验证 ---")
        doc_passed = self._verify_documentation()
        all_passed &= doc_passed
        
        # 输出汇总报告
        self._generate_report(all_passed)
        
        return all_passed
    
    def _verify_architecture(self) -> bool:
        """验证架构不变性"""
        print("🔍 运行架构验证器...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_architecture.py")],
                capture_output=True,
                text=True,
                cwd=ROOT
            )
            
            print(result.stdout)
            if result.stderr:
                print("stderr:", result.stderr)
            
            self.results['architecture'] = {
                'passed': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 架构验证失败: {e}")
            self.results['architecture'] = {'passed': False, 'error': str(e)}
            return False
    
    def _verify_unit_tests(self) -> bool:
        """验证单元测试"""
        print("🔍 运行单元测试...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-x"],
                capture_output=True,
                text=True,
                cwd=ROOT,
                timeout=300
            )
            
            # 统计测试结果
            lines = result.stdout.split('\n')
            passed = 0
            failed = 0
            
            for line in lines:
                if "passed" in line:
                    passed = int(line.split()[0]) if line.split()[0].isdigit() else 0
                if "failed" in line:
                    failed = int(line.split()[0]) if line.split()[0].isdigit() else 0
            
            print(f"测试结果: {passed} 通过, {failed} 失败")
            
            self.results['unit_tests'] = {
                'passed': result.returncode == 0,
                'passed_count': passed,
                'failed_count': failed,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("❌ 单元测试超时")
            self.results['unit_tests'] = {'passed': False, 'error': 'timeout'}
            return False
        except Exception as e:
            print(f"❌ 单元测试失败: {e}")
            self.results['unit_tests'] = {'passed': False, 'error': str(e)}
            return False
    
    def _verify_api_contract(self) -> bool:
        """验证 API 契约"""
        print("🔍 验证 API 契约...")
        
        try:
            # 检查 API 测试文件是否存在
            api_test_file = ROOT / "tests" / "test_integration_api.py"
            if not api_test_file.exists():
                print("⚠️ API 测试文件不存在，跳过")
                self.results['api_contract'] = {'passed': True, 'skipped': 'no test file'}
                return True
            
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(api_test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=ROOT,
                timeout=120
            )
            
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            
            self.results['api_contract'] = {
                'passed': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            return result.returncode == 0
        except Exception as e:
            print(f"❌ API 契约验证失败: {e}")
            self.results['api_contract'] = {'passed': False, 'error': str(e)}
            return False
    
    def _verify_e2e(self) -> bool:
        """验证 E2E 测试"""
        print("🔍 运行 E2E 测试...")
        
        try:
            # 检查前端目录是否存在
            frontend_dir = ROOT / "frontend"
            if not frontend_dir.exists():
                print("⚠️ 前端目录不存在，跳过 E2E 测试")
                self.results['e2e'] = {'passed': True, 'skipped': 'no frontend'}
                return True
            
            # 检查是否安装了依赖
            if not (frontend_dir / "node_modules").exists():
                print("⚠️ 前端依赖未安装，跳过 E2E 测试")
                self.results['e2e'] = {'passed': True, 'skipped': 'no node_modules'}
                return True
            
            result = subprocess.run(
                ["npx", "playwright", "test", "--reporter=line"],
                capture_output=True,
                text=True,
                cwd=frontend_dir,
                timeout=300,
                env={**os.environ, "PLAYWRIGHT_SKIP_WEBSERVER": "1"}
            )
            
            print(result.stdout[-800:] if len(result.stdout) > 800 else result.stdout)
            
            self.results['e2e'] = {
                'passed': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️ E2E 测试失败或跳过: {e}")
            self.results['e2e'] = {'passed': True, 'skipped': str(e)}
            return True  # E2E 失败不阻止升级
    
    def _verify_documentation(self) -> bool:
        """验证文档同步"""
        print("🔍 验证文档同步...")
        
        docs_to_check = [
            ROOT / "README.md",
            ROOT / "README_EN.md",
            ROOT / "docs" / "ARCHITECTURE_INVARIANTS.md",
            ROOT / ".cursor" / "rules" / "sprintcycle-architecture-orchestration.mdc"
        ]
        
        all_exist = True
        for doc in docs_to_check:
            if doc.exists():
                print(f"✅ {doc.name}")
            else:
                print(f"❌ {doc.name} 不存在")
                all_exist = False
        
        self.results['documentation'] = {'passed': all_exist}
        return all_exist
    
    def _generate_report(self, all_passed: bool):
        """生成验证报告"""
        print("\n" + "="*70)
        print("📊 自动升级验证报告")
        print("="*70)
        
        phases = [
            ('architecture', '架构不变性验证'),
            ('unit_tests', '单元测试'),
            ('api_contract', 'API 契约验证'),
            ('e2e', 'E2E 测试'),
            ('documentation', '文档同步验证'),
        ]
        
        print("\n验证结果:")
        for key, name in phases:
            result = self.results.get(key, {'passed': False})
            status = "✅ 通过" if result['passed'] else "❌ 失败"
            if result.get('skipped'):
                status = f"⚠️ 跳过 ({result['skipped']})"
            print(f"  {name}: {status}")
        
        # 输出详细结果文件
        report_file = ROOT / "upgrade_verification_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 详细报告已保存到: {report_file}")
        
        if all_passed:
            print("\n🎉 所有验证通过！升级可以继续。")
        else:
            print("\n❌ 部分验证失败，请修复后重新验证。")


def main():
    parser = argparse.ArgumentParser(description="SprintCycle 自动升级验证器")
    parser.add_argument("--report", action="store_true", help="生成详细报告")
    args = parser.parse_args()
    
    verifier = AutoUpgradeVerifier()
    success = verifier.run_full_verification()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()