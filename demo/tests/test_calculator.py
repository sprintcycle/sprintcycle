"""Calculator 测试"""
import pytest
from calculator import Calculator

class TestCalculator:
    def setup_method(self):
        self.calc = Calculator()
    
    def test_add(self):
        assert self.calc.add(1, 2) == 3.0
    
    def test_divide_by_zero(self):
        with pytest.raises((ZeroDivisionError, ValueError)):
            self.calc.divide(1, 0)
