#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SprintCycle AutoFix Engine"""
import os, json, shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .scanner import Issue, IssueType, IssueSeverity

@dataclass
class FixResult:
    success: bool
    issue: Issue
    fix_content: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None
    reverted: bool = False

@dataclass
class FixSession:
    project_path: str
    start_time: datetime
    fixes: List[FixResult] = field(default_factory=list)
    rollbacks: List[Dict] = field(default_factory=list)

class AutoFixEngine:
    API = "https://api.deepseek.com/v1/chat/completions"
    
    def __init__(self, project_path: str, api_key: str = None):
        self.project_path = Path(project_path).resolve()
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "YOUR_API_KEY_HERE")
        self.session = None
    
    def scan_and_fix(self, auto=True) -> FixSession:
        self.session = FixSession(project_path=str(self.project_path), start_time=datetime.now())
        from .scanner import ProjectScanner
        scanner = ProjectScanner(str(self.project_path))
        result = scanner.scan()
        for issue in result.issues:
            if not auto and not issue.fix_suggestion:
                continue
            fix_result = self._fix_issue(issue)
            self.session.fixes.append(fix_result)
        return self.session
    
    def _fix_issue(self, issue: Issue) -> FixResult:
        if issue.issue_type == IssueType.MISSING_FILE:
            return self._fix_missing_file(issue)
        elif issue.issue_type == IssueType.SYNTAX_ERROR:
            return self._fix_syntax_error(issue)
        elif issue.issue_type == IssueType.CONFIG_ERROR:
            return self._fix_config_error(issue)
        elif issue.issue_type == IssueType.UNUSED_IMPORT:
            return self._fix_unused_import(issue)
        return FixResult(success=False, issue=issue, error="Unknown type")

    def _fix_missing_file(self, issue: Issue) -> FixResult:
        fp = self.project_path / issue.file_path
        content = issue.fix_suggestion or self._gen_content(issue.file_path)
        try:
            fp.parent.mkdir(parents=True, exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            return FixResult(success=True, issue=issue, fix_content=content, file_path=str(fp))
        except Exception as e:
            return FixResult(success=False, issue=issue, error=str(e))

    def _fix_syntax_error(self, issue: Issue) -> FixResult:
        fp = self.project_path / issue.file_path
        if not fp.exists():
            return FixResult(success=False, issue=issue, error="File not found")
        bak = fp.with_suffix(".bak")
        shutil.copy2(fp, bak)
        self.session.rollbacks.append({"type": "file", "original": str(bak), "restored": str(fp)})
        if HAS_REQUESTS:
            code = self._call_ai(fp, issue)
            if code:
                with open(fp, "w") as f: f.write(code)
                return FixResult(success=True, issue=issue, fix_content=code, file_path=str(fp))
        return FixResult(success=False, issue=issue, error="AI unavailable")

    def _fix_config_error(self, issue: Issue) -> FixResult:
        fp = self.project_path / issue.file_path
        if not fp.exists():
            return FixResult(success=False, issue=issue, error="File not found")
        try:
            with open(fp, "r", encoding="utf-8") as f: content = f.read()
            if fp.suffix == ".yaml":
                import yaml; data = yaml.safe_load(content)
                fixed = yaml.dump(data, allow_unicode=True, sort_keys=False)
                with open(fp, "w") as f: f.write(fixed)
            elif fp.suffix == ".json":
                data = json.loads(content)
                fixed = json.dumps(data, indent=2, ensure_ascii=False)
                with open(fp, "w") as f: f.write(fixed)
            return FixResult(success=True, issue=issue, file_path=str(fp))
        except Exception as e:
            return FixResult(success=False, issue=issue, error=str(e))

    def _call_ai(self, fp, issue) -> Optional[str]:
        try:
            with open(fp, "r") as f: code = f.read()
            prompt = f"Fix line {issue.line}: {issue.message}\n\n{code[:500]}"
            resp = requests.post(self.API, headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception: pass
        return None

    def rollback(self) -> int:
        if not self.session: return 0
        count = 0
        for r in self.session.rollbacks:
            try:
                bak = Path(r["original"])
                if bak.exists():
                    shutil.copy2(bak, Path(r["restored"]))
                    bak.unlink()
                    count += 1
            except Exception: pass
        return count

    def get_summary(self) -> Dict:
        if not self.session: return {}
        return {"total": len(self.session.fixes), "fixed": sum(1 for f in self.session.fixes if f.success), "failed": sum(1 for f in self.session.fixes if not f.success)}
