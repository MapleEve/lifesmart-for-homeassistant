"""
LifeSmart Platform Layer - 平台适配层
由 @MapleEve 初始创建和维护

此层负责Home Assistant平台集成，包括：
- 平台检测：动态检测设备支持的平台
- 平台适配器：各个平台的适配逻辑
- 实体创建：为各平台创建合适的实体
"""

from .platform_detection import (
    get_device_platform_mapping,
    get_sensor_subdevices,
    get_binary_sensor_subdevices,
    get_switch_subdevices,
    get_light_subdevices,
    get_cover_subdevices,
    get_climate_subdevices,
)

__all__ = [
    "get_device_platform_mapping",
    "get_sensor_subdevices",
    "get_binary_sensor_subdevices",
    "get_switch_subdevices",
    "get_light_subdevices",
    "get_cover_subdevices",
    "get_climate_subdevices",
]
