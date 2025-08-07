"""
LifeSmart 工具函数模块。

此模块包含各种工具函数，从helpers.py中分离出来以提高代码组织性。
按照HA规范，将工具函数独立成模块。

主要组件:
- conversion.py: 数据转换工具
- platform_detection.py: 平台检测工具
"""

# 数据转换工具
from .conversion import (
    is_ieee754_float_type,
    get_io_precision,
    convert_ieee754_float,
    get_io_friendly_val,
    get_f_fan_mode,
    get_tf_fan_mode,
    apply_enhanced_conversion,
    get_enhanced_io_value,
    normalize_device_names,
    convert_temperature_decimal,
    convert_percentage_value,
    convert_fan_speed_to_mode,
)

# 平台检测工具
from .platform_detection import (
    get_device_platform_mapping,
    is_binary_sensor,
    is_climate,
    is_cover,
    is_light,
    is_sensor,
    is_switch,
    get_binary_sensor_subdevices,
    get_climate_subdevices,
    get_cover_subdevices,
    get_light_subdevices,
    get_sensor_subdevices,
    get_switch_subdevices,
    expand_wildcard_ios,
    get_device_effective_type,
    safe_get,
)

__all__ = [
    # 平台检测工具
    "get_device_platform_mapping",
    "is_binary_sensor",
    "is_climate",
    "is_cover",
    "is_light",
    "is_sensor",
    "is_switch",
    "get_binary_sensor_subdevices",
    "get_climate_subdevices",
    "get_cover_subdevices",
    "get_light_subdevices",
    "get_sensor_subdevices",
    "get_switch_subdevices",
    "expand_wildcard_ios",
    "get_device_effective_type",
    "safe_get",
    # 数据转换工具
    "is_ieee754_float_type",
    "get_io_precision",
    "convert_ieee754_float",
    "get_io_friendly_val",
    "get_f_fan_mode",
    "get_tf_fan_mode",
    "apply_enhanced_conversion",
    "get_enhanced_io_value",
    "normalize_device_names",
    "convert_temperature_decimal",
    "convert_percentage_value",
    "convert_fan_speed_to_mode",
]
