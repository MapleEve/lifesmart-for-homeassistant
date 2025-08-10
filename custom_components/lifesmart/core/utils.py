"""转发模块：compatibility layer for core.utils

这是为了测试兼容性而创建的转发模块，将旧的 core.utils 导入
转发到新的架构位置。
"""

# 从platform_detection模块导入平台检测函数
from .platform.platform_detection import (
    get_switch_subdevices,
    get_binary_sensor_subdevices,
    get_cover_subdevices,
    get_sensor_subdevices,
    get_light_subdevices,
    is_binary_sensor,
    is_climate,
    is_cover,
    is_light,
    is_sensor,
    is_switch,
    safe_get,  # safe_get在platform_detection中
)

# 从data/conversion.py导入数据转换函数
from .data.conversion import (
    normalize_device_names,
)

__all__ = [
    # 平台检测函数
    "get_switch_subdevices",
    "get_binary_sensor_subdevices", 
    "get_cover_subdevices",
    "get_sensor_subdevices",
    "get_light_subdevices",
    "is_binary_sensor",
    "is_climate",
    "is_cover", 
    "is_light",
    "is_sensor",
    "is_switch",
    # 通用辅助函数
    "normalize_device_names",
    "safe_get",
]