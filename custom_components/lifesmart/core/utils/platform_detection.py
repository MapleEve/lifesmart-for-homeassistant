"""
LifeSmart 平台检测工具模块。

此模块从helpers.py迁移而来，专门负责设备平台检测和映射功能。
按照HA规范，将工具函数从业务逻辑中分离出来。

现在使用新的mapping引擎，消除了硬编码的业务逻辑。

主要功能:
- 设备平台检测和映射
- 动态分类设备处理
- 多平台设备支持
- 子设备检测和过滤
"""

from typing import Any

from ..device.mapping_engine import mapping_engine


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

    这个函数现在使用新的mapping引擎，支持动态分类设备和复杂业务逻辑。
    单个物理设备可以使用不同IO口支持多个平台。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        返回平台名称到IO口列表的映射，例如:
        {
            "switch": ["P1"],
            "sensor": ["P2"]
        }
    """
    # 使用新的mapping引擎解析设备映射
    return mapping_engine.resolve_device_mapping(device)


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
    现在使用mapping驱动判断设备是否为瞬时按钮类型。

    Args:
        device_type: 设备类型
        sub_key: 子设备键名

    Returns:
        是否为瞬时按钮设备
    """
    # 使用mapping引擎获取设备配置
    from ..device.mapping import DEVICE_MAPPING

    device_config = DEVICE_MAPPING.get(device_type, {})

    # 检查binary_sensor平台的IO配置
    binary_sensor_config = device_config.get("binary_sensor", {})
    io_config = binary_sensor_config.get(sub_key, {})

    # 根据IO配置判断是否为瞬时按钮
    return io_config.get("momentary", False)


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
    from ..device.mapping import DEVICE_MAPPING

    device_type = get_device_effective_type(device)
    device_config = DEVICE_MAPPING.get(device_type, {})

    # 获取binary_sensor平台的IO配置
    binary_sensor_config = device_config.get("binary_sensor", {})
    return binary_sensor_config.get(sub_key, {})
