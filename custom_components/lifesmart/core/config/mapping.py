"""
LifeSmart Device Mapping - 设备映射统一接口
由 @MapleEve 初始创建和维护

此文件提供统一的设备映射接口，整合了：
- 原始设备规格数据
- 映射引擎转换
- 向后兼容的DEVICE_MAPPING
- 第三方设备和版本设备支持
"""

# 导入核心数据和引擎
from .device_specs import DEVICE_SPECS_DATA

# 导入第三方设备映射
from .third_party_mapping import (
    THIRD_PARTY_DEVICES,
    VERSIONED_DEVICE_TYPES,
    get_third_party_device_info,
    get_versioned_device_info,
    is_third_party_device,
    is_versioned_device,
    get_device_support_info,
)


# 尝试导入映射引擎
try:
    from .mapping_engine import mapping_engine

    # 生成向后兼容的DEVICE_MAPPING
    DEVICE_MAPPING = {}
    for device_type, raw_config in DEVICE_SPECS_DATA.items():
        DEVICE_MAPPING[device_type] = mapping_engine.convert_data_to_ha_mapping(
            raw_config
        )
except ImportError:
    # 降级方案 - 直接使用原始数据
    DEVICE_MAPPING = DEVICE_SPECS_DATA

# 导入其他设备分类常量 (从原devices/__init__.py迁移)
DYNAMIC_CLASSIFICATION_DEVICES = [
    "SL_NATURE",  # 根据P5值决定是开关版还是温控版
    "SL_P",  # 根据P1工作模式决定功能
    "SL_JEMA",  # 同SL_P，但额外支持P8/P9/P10独立开关
]


# 导出主要接口
__all__ = [
    "DEVICE_MAPPING",
    "DEVICE_SPECS_DATA",
    "DYNAMIC_CLASSIFICATION_DEVICES",
    "VERSIONED_DEVICE_TYPES",
    "THIRD_PARTY_DEVICES",
    # 新增的第三方设备支持函数
    "get_third_party_device_info",
    "get_versioned_device_info",
    "is_third_party_device",
    "is_versioned_device",
    "get_device_support_info",
]
