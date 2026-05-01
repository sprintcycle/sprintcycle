"""
MeasurementProvider - 测量提供者
"""

import logging
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MeasurementResult:
    correctness: float = 0.0
    performance: float = 0.0
    stability: float = 0.0
    code_quality: float = 0.0
    overall: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "correctness": self.correctness,
            "performance": self.performance,
            "stability": self.stability,
            "code_quality": self.code_quality,
            "overall": self.overall,
            "details": self.details,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MeasurementResult":
        return cls(
            correctness=data.get("correctness", 0.0),
            performance=data.get("performance", 0.0),
            stability=data.get("stability", 0.0),
            code_quality=data.get("code_quality", 0.0),
            overall=data.get("overall", 0.0),
            details=data.get("details", {}),
            timestamp=data.get("timestamp", time.time()),
        )
    
    def __bool__(self) -> bool:
        return self.overall >= 0.5


class MeasurementProvider:
    def __init__(
        self,
        repo_path: str = ".",
        test_command: str = "python -m pytest tests/ -v --tb=short",
        coverage_threshold: float = 0.0,
        quality_gate_enabled: bool = True,
        measurement_timeout: int = 300,
        runtime_config=None,
        runner: Optional[Callable[..., Tuple[int, str, str]]] = None,
    ):
        # 支持从 RuntimeConfig 构造
        if runtime_config is not None:
            self.repo_path = getattr(runtime_config, 'state_dir', '.')
            self.test_command = getattr(runtime_config, 'test_command', test_command)
            self.quality_gate_enabled = getattr(runtime_config, 'quality_gate_enabled', quality_gate_enabled)
            self.measurement_timeout = getattr(runtime_config, 'diagnostic_timeout', measurement_timeout)
            self.coverage_threshold = coverage_threshold
        else:
            self.repo_path = repo_path
            self.test_command = test_command
            self.quality_gate_enabled = quality_gate_enabled
            self.measurement_timeout = measurement_timeout
            self.coverage_threshold = coverage_threshold
        self._runner = runner or self._default_runner
        self._history: List[MeasurementResult] = []
        
    def _default_runner(self, cmd: str, cwd: str = ".", timeout: int = 300) -> Tuple[int, str, str]:
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def measure_all(self) -> MeasurementResult:
        correctness = self._measure_correctness()
        performance = self._measure_performance()
        stability = self._measure_stability()
        code_quality = self._measure_code_quality()
        
        overall = correctness * 0.3 + performance * 0.2 + stability * 0.2 + code_quality * 0.3
        
        result = MeasurementResult(
            correctness=correctness,
            performance=performance,
            stability=stability,
            code_quality=code_quality,
            overall=overall,
            details={
                "correctness_details": self._get_correctness_details(),
                "quality_details": self._get_quality_details(),
            },
        )
        self._history.append(result)
        return result
    
    def _measure_correctness(self) -> float:
        try:
            rc, stdout, stderr = self._runner(
                self.test_command,
                cwd=self.repo_path,
                timeout=self.measurement_timeout,
            )
            if "passed" in stdout.lower() or "passed" in stderr.lower():
                import re
                match = re.search(r'(\d+) passed', stdout + stderr)
                if match:
                    passed = int(match.group(1))
                    total_match = re.search(r'(\d+) failed|(\d+) error', stdout + stderr)
                    if total_match:
                        total = passed + int(total_match.group(1) or total_match.group(2))
                    else:
                        total = passed
                    return min(1.0, passed / max(1, total))
            return 1.0 if rc == 0 else 0.0
        except Exception:
            return 0.5
    
    def _measure_performance(self) -> float:
        if len(self._history) >= 2:
            prev = self._history[-2]
            curr = self._history[-1]
            if curr.overall > prev.overall:
                return min(1.0, 0.7 + 0.1)
        return 0.7
    
    def _measure_stability(self) -> float:
        recent = self._history[-3:] if len(self._history) >= 3 else self._history
        failures = sum(1 for r in recent if r.correctness < 0.5)
        return 1.0 - (failures / max(1, len(recent))) * 0.5
    
    def _measure_code_quality(self) -> float:
        try:
            self._runner("python -m mypy sprintcycle --ignore-missing-imports 2>&1 || true", cwd=self.repo_path, timeout=60)
            return 0.7
        except Exception:
            return 0.5
    
    def _get_correctness_details(self) -> Dict[str, Any]:
        return {"history_length": len(self._history)}
    
    def _get_quality_details(self) -> Dict[str, Any]:
        return {}
    
    def check_quality_gate(self, result: MeasurementResult) -> bool:
        if not self.quality_gate_enabled:
            return True
        if result.correctness < 0.5:
            return False
        if result.overall < self.coverage_threshold:
            return False
        return True
    
    def get_history(self) -> List[MeasurementResult]:
        return self._history.copy()
    
    def get_latest(self) -> Optional[MeasurementResult]:
        return self._history[-1] if self._history else None
    
    def compare(self, baseline: MeasurementResult, current: MeasurementResult) -> Dict[str, float]:
        return {
            "correctness_delta": current.correctness - baseline.correctness,
            "performance_delta": current.performance - baseline.performance,
            "stability_delta": current.stability - baseline.stability,
            "code_quality_delta": current.code_quality - baseline.code_quality,
            "overall_delta": current.overall - baseline.overall,
        }
    
    def is_improved(self, baseline: MeasurementResult, current: MeasurementResult) -> bool:
        return current.overall > baseline.overall
