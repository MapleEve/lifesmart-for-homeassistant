"""
LifeSmart Configuration Layer - 配置映射层
由 @MapleEve 初始创建和维护

此层负责设备配置和映射关系，包括：
- 设备规格定义：所有设备的规格数据
- 映射引擎：将原始数据映射为HA格式
- 设备分类：动态分类和版本管理
"""

from .device_specs import DEVICE_SPECS_DATA
from .mapping import DEVICE_MAPPING
from .mapping_engine import mapping_engine

__all__ = [
    "DEVICE_SPECS_DATA",
    "mapping_engine",
    "DEVICE_MAPPING",
]
