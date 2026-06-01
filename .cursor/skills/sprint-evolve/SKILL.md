---
name: sprint-evolve
description: SprintCycle 自动化进化 - 自动检测、评估、执行和验证完整闭环
author: SprintCycle Team
version: 1.0.0
---

# SprintCycle 自动化进化 Skill

## Overview

本 Skill 实现 SprintCycle 的自动化进化闭环，无需人工干预即可完成：
1. 架构不变性检测
2. 优化方向识别与排序
3. 自动执行优化工作流
4. 验证与自动修正

## Triggers

### Command Trigger
```
/sprint-evolve
```

### Keywords
- "进化"
- "自动优化"
- "自我改进"
- "架构进化"

## Workflow Phases

### Phase 1: Automated Detection

**Actions:**
1. Run architecture validator: `python scripts/validate_architecture.py --json`
2. Run unit tests: `pytest tests/ --json-report`
3. Analyze codebase for optimization opportunities
4. Collect metrics and generate baseline

**Output:**
- JSON report with violations, warnings, and opportunities

### Phase 2: Intelligent Prioritization

**Actions:**
1. Analyze detected issues using scoring algorithm
2. Apply business value weighting
3. Consider implementation complexity
4. Rank opportunities by priority score

**Scoring Criteria:**
| Factor | Weight | Description |
|--------|--------|-------------|
| Architecture Impact | 30% | How much it improves architectural compliance |
| Business Value | 25% | Direct business benefit |
| Complexity | 20% | Implementation difficulty (lower = better) |
| Risk | 15% | Risk of breaking changes |
| Test Coverage | 10% | Existing test coverage |

**Output:**
- Top 3 optimization directions with scores

### Phase 3: Automated Execution

**Actions:**
1. For each top optimization:
   - Execute corresponding optimization workflow
   - Handle field consolidation
   - Handle DDD governance
   - Handle compatibility cleanup
   - Handle frontend-backend alignment
2. Update all affected files
3. Synchronize documentation

**Workflow Integration:**
- Uses `sprint-optimize` command logic
- Follows `sprintcycle-optimization.mdc` rules
- Maintains business logic integrity

### Phase 4: Validation & Correction

**Actions:**
1. Run full verification suite
2. Analyze results
3. Auto-correct simple issues
4. Generate comprehensive report

**Auto-correction Rules:**
- Fix import issues
- Update deprecated patterns
- Resolve minor violations
- Flag complex issues for manual review

## Configuration

### Settings
```yaml
auto_evolve:
  enabled: true
  max_optimizations_per_run: 3
  min_score_threshold: 70
  auto_correction_enabled: true
  dry_run_mode: false
```

### Flags
- `--dry-run`: Simulate without actual changes
- `--force`: Force execution even with warnings
- `--silent`: Suppress detailed output
- `--report-only`: Generate report without execution

## Output Formats

### Summary Report
```markdown
## SprintCycle Evolution Report

### Detection Results
- Architecture Violations: X
- Warnings: Y
- Opportunities Found: Z

### Top 3 Optimization Directions

1. [Score: XX] Optimization Type - Description
   - Impact: High/Medium/Low
   - Complexity: Low/Medium/High
   - Risk: Low/Medium/High

2. [Score: YY] Optimization Type - Description
   - ...

3. [Score: ZZ] Optimization Type - Description
   - ...

### Execution Results
- Executed: X optimizations
- Successful: Y
- Partially completed: Z
- Failed: W

### Validation Results
- Architecture: ✅/❌
- Unit Tests: ✅/❌
- Integration: ✅/❌

### Recommendations
- Manual review required for: ...
- Next steps: ...
```

## Error Handling

### Retry Logic
- Transient errors: Retry up to 3 times
- Persistent errors: Skip and continue
- Critical errors: Stop execution and report

### Fallback Mechanisms
- If validation fails: Rollback changes
- If execution fails: Generate detailed error report
- If correction fails: Flag for manual intervention

## Integration Points

### Inputs
1. `scripts/validate_architecture.py` - Architecture validation
2. `pytest` - Unit testing
3. `scripts/auto_upgrade_verify.py` - Full verification

### Outputs
1. Evolution report (Markdown)
2. Execution log
3. Rollback scripts
4. GitHub PR draft

## Security Considerations

- All changes are reversible
- No destructive operations without confirmation
- Audit logging enabled
- Permission checks for sensitive operations

## Performance Optimization

- Parallel execution where possible
- Caching validation results
- Incremental analysis for large codebases
- Timeout controls for long-running operations

---

## Implementation Notes

### Skill Structure
```
.cursors/skills/sprint-evolve/
├── SKILL.md          # This file
├── evolve.py         # Main evolution logic
├── analyzer.py       # Optimization analyzer
├── executor.py       # Workflow executor
└── reporter.py       # Report generator
```

### Dependencies
- Python 3.11+
- loguru for logging
- pytest for testing
- jsonschema for validation

### API

#### evolve()
```python
def evolve(
    dry_run: bool = False,
    force: bool = False,
    silent: bool = False,
    report_only: bool = False
) -> EvolutionResult:
    """
    Execute the full evolution cycle.
    
    Args:
        dry_run: Simulate without changes
        force: Ignore warnings
        silent: Minimal output
        report_only: Generate report only
    
    Returns:
        EvolutionResult with results
    """
```

#### analyze()
```python
def analyze() -> AnalysisResult:
    """Analyze codebase for optimization opportunities."""
```

#### execute_optimization()
```python
def execute_optimization(
    optimization: Optimization,
    dry_run: bool = False
) -> ExecutionResult:
    """Execute a single optimization."""
```

#### validate()
```python
def validate() -> ValidationResult:
    """Run full validation suite."""
```

---

*Last updated: 2026-06-01*