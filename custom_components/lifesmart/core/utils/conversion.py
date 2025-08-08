"""
LifeSmart 数据转换工具模块。

此模块从helpers.py迁移而来，专门负责各种数据转换功能。
按照HA规范，将工具函数从业务逻辑中分离出来。

主要功能:
- IEEE754浮点数转换
- IO数据类型转换
- 增强版映射结构数据转换
- 风扇模式转换
- 友好值转换
"""

import struct
from typing import Any

from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)

from ..const import (
    DEVICE_DATA_KEY,
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


def apply_enhanced_conversion(
    conversion_type: str, data: dict, io_config: dict
) -> float | int | bool | None:
    """
    应用增强版转换规则。

    从helpers.py迁移的增强版数据转换功能。

    Args:
        conversion_type: 转换类型
        data: IO数据字典
        io_config: IO配置信息

    Returns:
        转换后的值
    """
    if not data:
        return None

    io_type = data.get("type", 0)
    io_val = data.get("val", 0)
    v_field = data.get("v")

    # 基础转换类型
    if conversion_type == "raw_value":
        return io_val
    elif conversion_type == "type_bit_0":
        return bool(io_type & 1)
    elif conversion_type == "val_direct":
        return io_val
    elif conversion_type == "v_field":
        return v_field if v_field is not None else io_val
    elif conversion_type == "friendly_val":
        return get_io_friendly_val(io_type, io_val)
    elif conversion_type == "ieee754_float":
        if is_ieee754_float_type(io_type):
            return convert_ieee754_float(io_val)
        return float(io_val)
    elif conversion_type == "val_div_10":
        return float(io_val) / 10.0
    elif conversion_type == "brightness":
        # 亮度转换 (0-100范围)
        if io_type & 1:  # 开启状态
            return min(100, max(0, int(io_val)))
        return 0
    elif conversion_type == "voltage_to_percentage":
        # 电压转百分比转换（电池电量）
        if v_field is not None:
            return min(100, max(0, int(v_field)))
        # 简单的电压到百分比映射
        voltage = float(io_val) / 100.0  # 假设原始值是实际电压*100
        if voltage >= 4.2:
            return 100
        elif voltage >= 3.7:
            return int((voltage - 3.7) / 0.5 * 100)
        elif voltage >= 3.0:
            return int((voltage - 3.0) / 0.7 * 20)
        else:
            return 0

    # 未知转换类型，返回原值
    return io_val


def get_enhanced_io_value(device: dict, sub_key: str, io_config: dict) -> Any:
    """
    从增强版映射结构配置中获取IO口的转换值。

    Args:
        device: 设备字典
        sub_key: IO口键名
        io_config: IO口的增强配置信息

    Returns:
        转换后的值
    """
    from .platform_detection import safe_get  # 避免循环导入

    device_data = device.get(DEVICE_DATA_KEY, {})
    io_data = safe_get(device_data, sub_key, default={})

    if not io_data:
        return None

    conversion_type = io_config.get("conversion", "raw_value")
    return apply_enhanced_conversion(conversion_type, io_data, io_config)


def normalize_device_names(dev_dict: dict) -> dict:
    """
    规范化设备名称。

    从helpers.py迁移，用于处理设备名称标准化。

    Args:
        dev_dict: 原始设备字典

    Returns:
        规范化后的设备字典
    """
    if not isinstance(dev_dict, dict):
        return dev_dict

    normalized = dev_dict.copy()

    # 规范化设备名称
    if "name" in normalized:
        name = normalized["name"]
        if isinstance(name, str):
            # 移除多余空格
            name = " ".join(name.split())
            # 统一中英文标点符号
            name = name.replace("（", "(").replace("）", ")")
            normalized["name"] = name

    return normalized


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


def get_binary_sensor_attributes(
    device_type: str, sub_key: str, sub_data: dict, is_on: bool
) -> dict:
    """
    获取binary_sensor的设备属性。

    从binary_sensor.py的_get_attributes方法迁移而来，
    集中处理各种设备的属性生成逻辑。

    Args:
        device_type: 设备类型
        sub_key: 子设备键名
        sub_data: 子设备数据
        is_on: 当前状态

    Returns:
        属性字典
    """
    from ..const import UNLOCK_METHOD
    import datetime

    val = sub_data.get("val", 0)

    # 门锁事件的特殊属性
    if (
        device_type
        in {
            "SL_LK_LS",
            "SL_LK_GTM",
            "SL_LK_AG",
            "SL_LK_SG",
            "SL_LK_YL",
            "SL_P_BDLK",
            "OD_JIUWANLI_LOCK1",
            "SL_LK_SWIFTE",
            "SL_LK_TY",
            "SL_LK_DJ",
        }
        and sub_key == "EVTLO"
    ):
        return {
            "unlocking_method": UNLOCK_METHOD.get(val >> 12, "Unknown"),
            "unlocking_user": val & 0xFFF,
            "device_type": device_type,
            "unlocking_success": is_on,
            "last_updated": datetime.datetime.fromtimestamp(
                sub_data.get("valts", 0) / 1000
            ).strftime("%Y-%m-%d %H:%M:%S"),
        }

    # 门锁报警的属性
    if (
        device_type
        in {
            "SL_LK_LS",
            "SL_LK_GTM",
            "SL_LK_AG",
            "SL_LK_SG",
            "SL_LK_YL",
            "SL_P_BDLK",
            "OD_JIUWANLI_LOCK1",
            "SL_LK_SWIFTE",
            "SL_LK_TY",
            "SL_LK_DJ",
        }
        and sub_key == "ALM"
    ):
        return {"alarm_type": val}

    # 水浸传感器的属性
    if device_type == "SL_SC_WA" and sub_key == "WA":
        return {"conductivity_level": val, "water_detected": val != 0}

    # 温控阀门的告警传感器添加详细属性
    if device_type == "SL_CP_VL" and sub_key == "P5":
        return {
            "high_temp_protection": bool(val & 0b1),
            "low_temp_protection": bool(val & 0b10),
            "internal_sensor_fault": bool(val & 0b100),
            "external_sensor_fault": bool(val & 0b1000),
            "low_battery": bool(val & 0b10000),
            "device_offline": bool(val & 0b100000),
        }

    # 默认返回原始数据
    return dict(sub_data)


def convert_binary_sensor_state(device_type: str, sub_key: str, sub_data: dict) -> bool:
    """
    转换binary_sensor的状态。

    从binary_sensor.py的_parse_state方法迁移而来，
    集中处理各种设备的状态解析逻辑。

    Args:
        device_type: 设备类型
        sub_key: 子设备键名
        sub_data: 子设备数据

    Returns:
        布尔状态值
    """
    val = sub_data.get("val", 0)
    type_val = sub_data.get("type", 0)

    # 门窗感应器特殊处理
    if device_type in {"SL_SC_G", "SL_SC_BG", "SL_SC_GS"}:
        if device_type == "SL_SC_GS" and sub_key in {"P1", "P2"}:
            return type_val & 1 == 1
        if device_type == "SL_SC_BG" and sub_key == "AXS":
            return val != 0  # 非0表示检测到震动
        return val == 0 if sub_key == "G" else val != 0

    # 云防系列设备特殊处理
    if device_type in {"SL_DF_GG", "SL_DF_MM", "SL_DF_SR", "SL_DF_BB", "SL_DF_KP"}:
        return type_val & 1 == 1

    # 动态感应器
    if device_type in {"SL_SC_MHW", "SL_SC_BM", "SL_SC_CM", "SL_BP_MZ"}:
        return val != 0

    # 门锁事件
    if device_type in {
        "SL_LK_LS",
        "SL_LK_GTM",
        "SL_LK_AG",
        "SL_LK_SG",
        "SL_LK_YL",
        "SL_P_BDLK",
        "OD_JIUWANLI_LOCK1",
        "SL_LK_SWIFTE",
        "SL_LK_TY",
        "SL_LK_DJ",
    }:
        if sub_key == "EVTLO":
            unlock_type = sub_data.get("type", 0)
            unlock_user = val & 0xFFF
            return (
                val != 0
                and unlock_type & 0x01 == 1
                and unlock_user != 0
                and val >> 12 != 15
            )
        if sub_key == "ALM":
            return val > 0

    # 通用控制器
    if device_type in {"SL_P", "SL_JEMA"}:
        return type_val & 1 == 1

    # 水浸传感器
    if device_type == "SL_SC_WA" and sub_key == "WA":
        return val != 0  # 非0表示检测到水

    # 烟雾感应器
    if device_type == "SL_P_A" and sub_key == "P1":
        return val != 0  # 非0表示检测到烟雾

    # 人体存在感应器
    if device_type == "SL_P_RM" and sub_key == "P1":
        return val != 0  # 非0表示检测到人体存在

    # 云防门窗感应器
    if device_type == "SL_DF_GG" and sub_key == "A":
        return val == 0  # 云防门窗：0=开，1=关

    # 温控设备
    if device_type in {
        "V_AIR_P",
        "SL_CP_DN",
        "SL_CP_AIR",
        "SL_CP_VL",
        "SL_TR_ACIPM",
        "V_FRESH_P",
        "SL_NATURE",
        "SL_DN",
        "SL_FCU",
        "SL_UACCB",
        "V_SZJSXR_P",
        "V_T8600_P",
    }:
        if sub_key == "P5":  # 温控阀门告警 (val 是 bitmask)
            return val > 0
        # 其他所有温控器的附属开关/阀门都遵循 type&1==1 为开启的规则
        return type_val & 1 == 1

    # 其他传感器默认处理
    return val != 0
