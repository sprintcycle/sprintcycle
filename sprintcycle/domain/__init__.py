"""领域层 - 按照 DDD 洋葱结构划分子域"""

from . import core
from . import supporting
from . import generic

__all__ = [
    "core",
    "supporting",
    "generic",
]
