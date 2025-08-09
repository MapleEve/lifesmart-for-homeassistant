"""
LifeSmart Data Processing Layer - 数据处理层
由 @MapleEve 初始创建和维护

此层负责处理从客户端获取的原始数据，包括：
- 数据转换：IEEE754、类型转换等
- 数据验证：格式验证、有效性检查
- 数据处理器：业务逻辑处理器
"""

from .conversion import get_io_friendly_val
from .processors import process_io_data, get_processor_registry
from .validators import validate_io_data, validate_device_data

__all__ = [
    "get_io_friendly_val",
    "validate_io_data",
    "validate_device_data",
    "process_io_data",
    "get_processor_registry",
]
