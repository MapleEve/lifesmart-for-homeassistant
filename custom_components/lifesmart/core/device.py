"""转发模块：compatibility layer for core.device

这是为了测试兼容性而创建的转发模块，将旧的 core.device 导入
转发到新的架构位置。
"""

# 从config/mapping.py导入设备映射数据
from .config.mapping import (
    DEVICE_MAPPING,
    DYNAMIC_CLASSIFICATION_DEVICES,
)

# 从config/cover_mappings.py导入cover相关配置
from .config.cover_mappings import (
    NON_POSITIONAL_COVER_CONFIG,
)

# 从data/processors/导入数据处理器
from .data.processors.logic_processors import *
from .data.processors.io_processors import *

__all__ = [
    "DEVICE_MAPPING",
    "DYNAMIC_CLASSIFICATION_DEVICES", 
    "NON_POSITIONAL_COVER_CONFIG",
]