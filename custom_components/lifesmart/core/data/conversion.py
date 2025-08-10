"""
LifeSmart 数据转换工具模块。
由 @MapleEve 初始创建和维护

此模块从helpers.py迁移而来，专门负责各种数据转换功能。
按照HA规范，将工具函数从业务逻辑中分离出来。

主要功能:
- IEEE754浮点数转换
- IO数据类型转换
- 风扇模式转换
- 友好值转换
"""

import struct

from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)

from ..const import (
    IO_TYPE_FLOAT_MASK,
    IO_TYPE_FLOAT_VALUE,
    IO_TYPE_EXCEPTION,
)


def is_ieee754_float_type(io_type: int) -> bool:
    """
    判断IO类型是否为IEEE754浮点类型。

    Args:
        io_type: IO口的type值

    Returns:
        如果是浮点类型返回True，否则返回False

    Reference:
        只有满足条件 (io_type & 0x7e) == 0x2 的IO数据其值才是浮点类型数据
    """
    return (io_type & IO_TYPE_FLOAT_MASK) == IO_TYPE_FLOAT_VALUE


def get_io_precision(io_type: int) -> int:
    """
    获取IO类型的精度系数。

    Args:
        io_type: IO口的type值

    Returns:
        精度系数，用于数据转换

    Reference:
        根据官方文档附录3.5，不同IO类型有不同的精度系数
    """
    # 根据type值的低位确定精度系数
    precision_bits = (io_type >> 8) & 0xFF
    if precision_bits == 0:
        return 1
    elif precision_bits == 1:
        return 10
    elif precision_bits == 2:
        return 100
    elif precision_bits == 3:
        return 1000
    else:
        return 1


def convert_ieee754_float(io_val: int) -> float:
    """
    将32位整数转换为IEEE754浮点数。

    Args:
        io_val: 32位整数表示的IEEE754浮点数

    Returns:
        转换后的浮点数值

    Reference:
        官方文档附录3.4 IO值浮点类型说明
        例如：1024913643表示的是浮点值：0.03685085
    """
    return struct.unpack("!f", struct.pack("!i", io_val))[0]


def get_io_friendly_val(io_type: int, io_val: int) -> float | None:
    """
    获取IO口的友好值（实际值）。

    Args:
        io_type: IO口的type值
        io_val: IO口的val值

    Returns:
        转换后的实际值，异常时返回None

    Reference:
        官方文档附录3.5 IO实际值转换及Type定义说明
    """
    # 参数类型检查，防止运行时错误
    if not isinstance(io_type, int) or not isinstance(io_val, int):
        return None

    # 异常数据返回None
    if io_type == IO_TYPE_EXCEPTION:
        return None

    # 浮点类型特殊处理
    if is_ieee754_float_type(io_type):
        try:
            return convert_ieee754_float(io_val)
        except (struct.error, ValueError):
            return None

    # 普通整型数据，根据精度系数转换
    try:
        precision = get_io_precision(io_type)
        return float(io_val) / precision if precision > 1 else float(io_val)
    except (ValueError, ZeroDivisionError):
        return None


def get_f_fan_mode(val: int) -> str:
    """
    根据 F 口的 val 值获取风扇模式。

    Args:
        val: F口的val值

    Returns:
        风扇模式字符串

    Reference:
        官方文档中F口风速定义
    """
    if val < 30:
        return FAN_LOW
    return FAN_MEDIUM if val < 65 else FAN_HIGH


def get_tf_fan_mode(val: int) -> str | None:
    """
    根据 tF 口的 val 值获取风扇模式。

    Args:
        val: tF口的val值

    Returns:
        风扇模式字符串，停止时返回None

    Reference:
        官方文档中tF口风速定义
    """
    if 30 >= val > 0:
        return FAN_LOW
    if val <= 65:
        return FAN_MEDIUM
    if val <= 100:
        return FAN_HIGH
    if val == 101:
        return FAN_AUTO
    return None  # 风扇停止时返回 None


def normalize_device_names(dev_dict: dict) -> dict:
    """
    规范化设备名称。

    从helpers.py迁移，用于处理设备名称标准化。
    现在支持复杂的占位符替换功能。

    Args:
        dev_dict: 原始设备字典

    Returns:
        规范化后的设备字典
    """
    import re

    if not isinstance(dev_dict, dict):
        return dev_dict

    # 深拷贝设备字典，避免修改原始数据
    normalized = _deep_copy_dict(dev_dict)

    # 规范化主设备名称
    if "name" in normalized:
        name = normalized["name"]
        if isinstance(name, str):
            # 移除多余空格
            name = " ".join(name.split())
            # 统一中英文标点符号
            name = name.replace("（", "(").replace("）", ")")
            normalized["name"] = name

    # 处理子设备名称占位符替换
    parent_name = normalized.get("name", "")
    if isinstance(parent_name, str) and "_chd" in normalized:
        chd_data = normalized["_chd"]
        if isinstance(chd_data, dict) and "m" in chd_data:
            m_data = chd_data["m"]
            if isinstance(m_data, dict) and "_chd" in m_data:
                sub_chd_data = m_data["_chd"]
                if isinstance(sub_chd_data, dict):
                    # 遍历所有子设备进行名称处理
                    for sub_key, sub_device in sub_chd_data.items():
                        if isinstance(sub_device, dict) and "name" in sub_device:
                            sub_name = sub_device["name"]
                            if isinstance(sub_name, str):
                                # 替换 {$EPN} 占位符为父设备名称
                                processed_name = sub_name.replace("{$EPN}", parent_name)

                                # 替换其他占位符为其内容（去掉花括号）
                                # 正则表达式匹配 {大写字母、数字、下划线} 的模式
                                processed_name = re.sub(
                                    r"\{([A-Z0-9_]+)\}", r"\1", processed_name
                                )

                                # 清理多余的空格
                                processed_name = " ".join(processed_name.split())

                                # 更新处理后的名称
                                sub_device["name"] = processed_name

    return normalized


def _deep_copy_dict(original: dict) -> dict:
    """
    深拷贝字典，避免修改原始数据。

    Args:
        original: 原始字典

    Returns:
        深拷贝后的字典
    """
    result = {}
    for key, value in original.items():
        if isinstance(value, dict):
            result[key] = _deep_copy_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _deep_copy_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def convert_temperature_decimal(temp_val: int) -> float:
    """
    转换温度十进制值。

    Args:
        temp_val: 温度值(温度*10)

    Returns:
        实际温度值
    """
    return float(temp_val) / 10.0


def convert_percentage_value(val: int, max_val: int = 100) -> int:
    """
    转换百分比值。

    Args:
        val: 原始值
        max_val: 最大值

    Returns:
        百分比值(0-100)
    """
    if max_val <= 0:
        return 0
    percentage = int(val * 100 / max_val)
    return min(100, max(0, percentage))


def convert_fan_speed_to_mode(speed_val: int) -> str:
    """
    将风速值转换为风扇模式。

    Args:
        speed_val: 风速值

    Returns:
        风扇模式字符串
    """
    if speed_val == 0:
        return "off"
    elif speed_val <= 30:
        return FAN_LOW
    elif speed_val <= 65:
        return FAN_MEDIUM
    elif speed_val <= 100:
        return FAN_HIGH
    elif speed_val == 101:
        return FAN_AUTO
    else:
        return FAN_AUTO  # 默认自动模式


def convert_binary_sensor_state(io_data: dict) -> bool:
    """
    转换二进制传感器状态。

    Args:
        io_data: IO数据字典

    Returns:
        传感器状态
    """
    io_type = io_data.get("type", 0)
    return (io_type & 1) == 1


def get_binary_sensor_attributes(io_data: dict) -> dict:
    """
    获取二进制传感器属性。

    Args:
        io_data: IO数据字典

    Returns:
        传感器属性字典
    """
    attributes = {}

    # 添加原始数据到属性中（调试用）
    if "val" in io_data:
        attributes["raw_value"] = io_data["val"]
    if "type" in io_data:
        attributes["raw_type"] = io_data["type"]

    return attributes


# 废弃函数已删除 - 使用新的逻辑处理器系统
# apply_enhanced_conversion 和 get_enhanced_io_value 已被 process_io_data 替代
