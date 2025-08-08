"""
LifeSmart 平台检测工具模块。

此模块从helpers.py迁移而来，专门负责设备平台检测和映射功能。
按照HA规范，将工具函数从业务逻辑中分离出来。

主要功能:
- 设备平台检测和映射
- 动态分类设备处理
- 多平台设备支持
- 子设备检测和过滤
"""

from typing import Any

from ..const import DEVICE_DATA_KEY
from ..device import DEVICE_MAPPING, DYNAMIC_CLASSIFICATION_DEVICES


def safe_get(data: dict | list, *path, default: Any = None) -> Any:
    """
    安全地从嵌套字典/列表中获取值。

    从helpers.py迁移，用于安全地访问嵌套数据结构。

    Args:
        data: 要访问的数据结构
        *path: 访问路径，可以是多个键/索引
        default: 找不到时返回的默认值

    Returns:
        找到的值或默认值

    Example:
        safe_get({"a": {"b": 1}}, "a", "b") -> 1
        safe_get({"a": {"b": 1}}, "a", "c", default=0) -> 0
    """
    try:
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif (
                isinstance(current, list)
                and isinstance(key, int)
                and 0 <= key < len(current)
            ):
                current = current[key]
            else:
                return default
        return current
    except (KeyError, IndexError, TypeError):
        return default


def get_device_platform_mapping(device: dict) -> dict[str, list[str]]:
    """
    根据设备的IO特征获取它支持的平台映射。

    这个函数用于支持多平台设备，解决之前的设备重复定义问题。
    单个物理设备可以使用不同IO口支持多个平台。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        返回平台名称到IO口列表的映射，例如:
        {
            "switch": ["L1"],
            "light": ["dark", "bright"]
        }
    """
    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = {}

    # 检查是否是动态分类设备
    if device_type in DYNAMIC_CLASSIFICATION_DEVICES:
        return _handle_dynamic_device_platforms(device)

    # 检查设备映射中是否有平台配置
    if device_type in DEVICE_MAPPING:
        mapping = DEVICE_MAPPING[device_type]

        # 遍历所有可能的平台
        for platform in [
            "switch",
            "light",
            "sensor",
            "binary_sensor",
            "cover",
            "climate",
            "button",
            "lock",
            "fan",
        ]:
            if platform in mapping:
                platform_config = mapping[platform]
                if isinstance(platform_config, dict):
                    # 提取IO口列表
                    io_list = list(platform_config.keys())
                    # 检查IO口是否存在于设备数据中
                    valid_ios = [io for io in io_list if io in device_data]
                    if valid_ios:
                        platforms[platform] = valid_ios

    return platforms


def _handle_dynamic_device_platforms(device: dict) -> dict[str, list[str]]:
    """处理动态分类设备的平台映射。"""
    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = {}

    if device_type == "SL_NATURE":
        # 超能面板动态分类逻辑
        p5_val = safe_get(device_data, "P5", "val", default=0) & 0xFF

        if p5_val == 1:  # 开关版
            # P1, P2, P3作为开关
            switch_ios = ["P1", "P2", "P3"]
            valid_switch_ios = [io for io in switch_ios if io in device_data]
            if valid_switch_ios:
                platforms["switch"] = valid_switch_ios

            # P4, P5作为传感器
            sensor_ios = ["P4", "P5"]
            valid_sensor_ios = [io for io in sensor_ios if io in device_data]
            if valid_sensor_ios:
                platforms["sensor"] = valid_sensor_ios

        elif p5_val in [3, 6]:  # 温控版
            # 温控设备
            climate_ios = ["P1", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
            valid_climate_ios = [io for io in climate_ios if io in device_data]
            if valid_climate_ios:
                platforms["climate"] = valid_climate_ios

            # P2, P3作为二进制传感器(阀门状态)
            binary_sensor_ios = ["P2", "P3"]
            valid_binary_sensor_ios = [
                io for io in binary_sensor_ios if io in device_data
            ]
            if valid_binary_sensor_ios:
                platforms["binary_sensor"] = valid_binary_sensor_ios

    elif device_type in ["SL_P", "SL_JEMA"]:
        # 通用控制器动态分类逻辑
        p1_val = safe_get(device_data, "P1", "val", default=0)
        work_mode = (p1_val >> 24) & 0xE

        if work_mode == 0:  # 自由模式 - 二元传感器
            binary_sensor_ios = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
            valid_ios = [io for io in binary_sensor_ios if io in device_data]
            if valid_ios:
                platforms["binary_sensor"] = valid_ios

        elif work_mode in [2, 4]:  # 窗帘模式
            cover_ios = ["P2", "P3", "P4"]  # 开/关/停
            valid_ios = [io for io in cover_ios if io in device_data]
            if valid_ios:
                platforms["cover"] = valid_ios

        # SL_JEMA额外的独立开关
        if device_type == "SL_JEMA":
            independent_switch_ios = ["P8", "P9", "P10"]
            valid_switch_ios = [
                io for io in independent_switch_ios if io in device_data
            ]
            if valid_switch_ios:
                if "switch" not in platforms:
                    platforms["switch"] = []
                platforms["switch"].extend(valid_switch_ios)

    return platforms


def is_binary_sensor(device: dict) -> bool:
    """检查设备是否支持binary_sensor平台。"""
    platforms = get_device_platform_mapping(device)
    return "binary_sensor" in platforms


def is_climate(device: dict) -> bool:
    """检查设备是否支持climate平台。"""
    platforms = get_device_platform_mapping(device)
    return "climate" in platforms


def is_cover(device: dict) -> bool:
    """检查设备是否支持cover平台。"""
    platforms = get_device_platform_mapping(device)
    return "cover" in platforms


def is_light(device: dict) -> bool:
    """检查设备是否支持light平台。"""
    platforms = get_device_platform_mapping(device)
    return "light" in platforms


def is_sensor(device: dict) -> bool:
    """检查设备是否支持sensor平台。"""
    platforms = get_device_platform_mapping(device)
    return "sensor" in platforms


def is_switch(device: dict) -> bool:
    """检查设备是否支持switch平台。"""
    platforms = get_device_platform_mapping(device)
    return "switch" in platforms


def get_binary_sensor_subdevices(device: dict) -> list[str]:
    """获取设备的binary_sensor子设备列表。"""
    platforms = get_device_platform_mapping(device)
    return platforms.get("binary_sensor", [])


def get_climate_subdevices(device: dict) -> list[str]:
    """获取设备的climate子设备列表。"""
    platforms = get_device_platform_mapping(device)
    return platforms.get("climate", [])


def get_cover_subdevices(device: dict) -> list[str]:
    """获取设备的cover子设备列表。"""
    platforms = get_device_platform_mapping(device)
    return platforms.get("cover", [])


def get_light_subdevices(device: dict) -> list[str]:
    """获取设备的light子设备列表。"""
    platforms = get_device_platform_mapping(device)
    return platforms.get("light", [])


def get_sensor_subdevices(device: dict) -> list[str]:
    """获取设备的sensor子设备列表。"""
    platforms = get_device_platform_mapping(device)
    return platforms.get("sensor", [])


def get_switch_subdevices(device: dict) -> list[str]:
    """获取设备的switch子设备列表。"""
    platforms = get_device_platform_mapping(device)
    return platforms.get("switch", [])


def expand_wildcard_ios(io_pattern: str, device_data: dict) -> list[str]:
    """
    展开IO通配符模式。

    从helpers.py迁移，用于处理IO口通配符扩展。

    Args:
        io_pattern: IO模式，如"P*"或"L*"
        device_data: 设备数据字典

    Returns:
        匹配的IO口列表

    Example:
        expand_wildcard_ios("P*", {"P1": {}, "P2": {}, "L1": {}}) -> ["P1", "P2"]
    """
    if "*" not in io_pattern:
        return [io_pattern] if io_pattern in device_data else []

    # 简单的通配符匹配
    prefix = io_pattern.rstrip("*")
    matching_ios = []

    for io_key in device_data.keys():
        if io_key.startswith(prefix):
            matching_ios.append(io_key)

    return sorted(matching_ios)


def get_device_effective_type(device: dict) -> str:
    """
    获取设备的有效类型。

    从helpers.py迁移，用于处理版本化设备类型。

    Args:
        device: 设备字典

    Returns:
        有效的设备类型字符串
    """
    device_type = device.get("devtype", "")

    # 检查是否是版本化设备
    if device_type and "_V" in device_type:
        return device_type

    # 检查fullCls字段以确定版本
    full_cls = device.get("fullCls", "")
    if full_cls and device_type:
        if f"{device_type}_V1" in full_cls:
            return f"{device_type}_V1"
        elif f"{device_type}_V2" in full_cls:
            return f"{device_type}_V2"

    return device_type


def is_momentary_button_device(device_type: str, sub_key: str) -> bool:
    """
    判断是否为瞬时按钮设备。

    从binary_sensor.py的_is_momentary_button_device方法迁移而来，
    使用映射驱动判断设备是否为瞬时按钮类型。

    Args:
        device_type: 设备类型
        sub_key: 子设备键名

    Returns:
        是否为瞬时按钮设备
    """
    # 云防遥控器的按键 (SL_DF_BB)
    if device_type == "SL_DF_BB" and sub_key.startswith("eB"):
        return True

    # 门禁感应器的按键部分 (SL_SC_BG)
    if device_type == "SL_SC_BG" and sub_key == "B":
        return True

    return False


def get_binary_sensor_io_config(device: dict, sub_key: str) -> dict:
    """
    获取binary_sensor IO口的配置信息。

    从DEVICE_MAPPING中提取指定IO口的binary_sensor配置。

    Args:
        device: 设备字典
        sub_key: IO口键名

    Returns:
        IO口的配置字典，包含device_class等信息
    """
    from ..device import DEVICE_MAPPING

    device_type = get_device_effective_type(device)
    device_config = DEVICE_MAPPING.get(device_type, {})

    # 获取binary_sensor平台的IO配置
    binary_sensor_config = device_config.get("binary_sensor", {})
    return binary_sensor_config.get(sub_key, {})
