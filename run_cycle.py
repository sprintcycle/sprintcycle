#!/usr/bin/env python3
"""
SprintCycle 独立执行器
用法: python run_cycle.py <项目路径> [PRD路径] [--autofix] [--scan]
"""
import sys
import os
import argparse
from pathlib import Path

# 设置环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("LLM_API_KEY", "YOUR_API_KEY_HERE")

from sprintcycle.server import Chorus, KnowledgeBase
from sprintcycle.scanner import ProjectScanner
from sprintcycle.autofix import AutoFixEngine
from sprintcycle.health_check import ProjectHealthChecker
from sprintcycle.prd_splitter import PRDSplitter

def main():
    parser = argparse.ArgumentParser(description="SprintCycle - 敏捷开发周期管理引擎")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("prd_path", nargs="?", default=None, help="PRD 路径")
    parser.add_argument("--autofix", action="store_true", help="扫描并自动修复问题")
    parser.add_argument("--scan", action="store_true", help="仅扫描问题不修复")
    parser.add_argument("--health", action="store_true", help="运行健康检查")
    args = parser.parse_args()
    
    project_path = args.project_path
    prd_path = args.prd_path
    
    print("╔════════════════════════════════════════╗")
    print("║       SprintCycle - 冲刺周期引擎        ║")
    print("╚════════════════════════════════════════╝")
    print(f"📁 项目路径: {project_path}")
    
    # 初始化 KnowledgeBase 和 Chorus
    kb = KnowledgeBase(project_path)
    chorus = Chorus(kb)
    
    # 健康检查
    if args.health:
        print("\n🏥 运行健康检查...")
        checker = ProjectHealthChecker(project_path)
        report = checker.check_all()
        print(f"状态: {report.overall_status}")
        print(f"通过: {report.passed} | 警告: {report.warnings} | 错误: {report.errors}")
        for c in report.checks:
            icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(c.status, "❓")
            print(f"  {icon} {c.name}: {c.message}")
        print()
    
    # 扫描问题
    if args.scan or args.autofix:
        print("\n🔍 扫描项目问题...")
        scanner = ProjectScanner(project_path)
        result = scanner.scan()
        print(f"扫描: {result.scanned_files} 文件, 耗时 {result.scan_duration:.2f}s")
        print(f"问题: {result.critical_count} 严重, {result.warning_count} 警告, {result.info_count} 信息")
        
        if result.issues:
            print("\n发现的问题:")
            for issue in result.issues[:10]:
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.severity.value, "⚪")
                print(f"  {icon} {issue.file_path}: {issue.message[:60]}")
            if len(result.issues) > 10:
                print(f"  ... 还有 {len(result.issues) - 10} 个问题")
        
        # 自动修复
        if args.autofix:
            print("\n🔧 自动修复问题...")
            fixer = AutoFixEngine(project_path)
            session = fixer.scan_and_fix(auto=True)
            print(f"处理: {len(session.fixes)} 问题")
            print(f"成功: {sum(1 for f in session.fixes if f.success)}")
            print(f"失败: {sum(1 for f in session.fixes if not f.success)}")
            print(f"备份: {len(session.rollbacks)} 文件")
            
            if session.rollbacks:
                print("\n💡 如需回滚，运行: python run_cycle.py {project_path} --rollback")
        print()
    
    # 如果有 PRD，拆分 Sprint
    if prd_path and Path(prd_path).exists():
        print(f"\n📋 从 PRD 生成冲刺规划: {prd_path}")
        splitter = PRDSplitter()
        # 分析 PRD
        analysis = splitter.analyze_prd(prd_path)
        print(f"✅ PRD 分析完成")
        print(f"   Sprint 数: {analysis['sprint_count']}")
        print(f"   任务数: {analysis['total_tasks']}")
        print(f"   预估时间: {analysis['estimated_time']:.0f}s")
        
        # 拆分 PRD
        split_result = splitter.split_prd(prd_path, Path(project_path).name)
        print(f"\n✅ 已拆分 {split_result.split_count} 个 PRD 文件")
        for p in split_result.split_prds:
            print(f"   - {p}")
    
    # 执行任务
    print("\n🚀 开始执行任务...")
    
    # 如果有拆分后的 PRD，执行任务
    if prd_path and Path(prd_path).exists():
        # 加载拆分后的第一个 PRD 或原始 PRD
        splitter = PRDSplitter()
        split_result = splitter.split_prd(prd_path, Path(project_path).name)
        prd_to_execute = split_result.split_prds[0] if split_result.split_prds else prd_path
        
        # 加载 PRD 数据
        import yaml
        with open(prd_to_execute, 'r', encoding='utf-8') as f:
            prd_data = yaml.safe_load(f)
        
        sprints = prd_data.get('sprints', [])
        print(f"\n执行 {len(sprints)} 个 Sprint...")
        
        total_tasks = 0
        total_success = 0
        
        for sprint in sprints:
            print(f"\n🎯 {sprint['name']}")
            tasks = sprint.get('tasks', [])
            for i, task in enumerate(tasks, 1):
                task_str = task if isinstance(task, str) else task.get('task', '')
                if not task_str:
                    continue
                print(f"   [{i}/{len(tasks)}] 执行: {task_str[:60]}...")
                res = chorus.dispatch(project_path, task_str, None, None, None, None)
                status = "✅" if res.success else "❌"
                print(f"   [{i}/{len(tasks)}] {status} | {res.duration:.1f}s")
                if not res.success:
                    print(f"      错误: {res.error[:100] if res.error else 'Unknown'}")
                total_tasks += 1
                if res.success:
                    total_success += 1
        
        print(f"\n总计: {total_success}/{total_tasks} 任务成功")
    else:
        print("⚠️ 未提供 PRD 文件，跳过 Sprint 执行")
    
    # 知识库统计
    stats = kb.get_stats()
    print(f"\n📚 知识库统计:")
    print(f"   总任务数: {stats.get('total_tasks', 0)}")
    print(f"   成功率: {stats.get('success_rate', 0):.1f}%")

if __name__ == "__main__":
    main()
