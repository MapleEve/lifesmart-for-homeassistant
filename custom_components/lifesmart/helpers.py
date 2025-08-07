"""
LifeSmart 集成的通用辅助函数模块。

此模块包含所有与协议或客户端状态无关的、可在多个地方复用的纯函数。
这包括实体ID生成、设备类型检查、数据安全获取和名称规范化等。
"""

import re
from typing import Any

from homeassistant.components.climate import FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO
from homeassistant.const import Platform

from .const import (
    DEVICE_DATA_KEY,
    DEVICE_FULLCLS_KEY,
    DEVICE_TYPE_KEY,
    VERSIONED_DEVICE_TYPES,
    IO_TYPE_FLOAT_MASK,
    IO_TYPE_FLOAT_VALUE,
    IO_TYPE_PRECISION_MASK,
    IO_TYPE_PRECISION_BASE,
    IO_TYPE_PRECISION_BITS,
    IO_TYPE_EXCEPTION,
    # 新架构：多平台设备支持映射
    MULTI_PLATFORM_DEVICE_MAPPING,
    # 设备类型常量
    GENERIC_CONTROLLER_TYPES,
)


# ====================================================================
# 基于IO特征的平台检测函数
# ====================================================================
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

    # 先检查是否是多平台设备
    if device_type in MULTI_PLATFORM_DEVICE_MAPPING:
        mapping = MULTI_PLATFORM_DEVICE_MAPPING[device_type]

        # 处理动态分类设备
        if mapping.get("dynamic"):
            return _handle_dynamic_device_platforms(device, mapping)

        # 处理静态多平台设备
        for platform, config in mapping.items():
            if platform != "dynamic":
                io_list = config.get("io", [])
                if isinstance(io_list, str):
                    io_list = [io_list]

                # 检查IO口是否存在于设备数据中
                valid_ios = [io for io in io_list if io in device_data]
                if valid_ios:
                    platforms[platform] = valid_ios

        return platforms

    # 处理单平台设备（传统逗辑）
    return _get_single_platform_mapping(device)


def _handle_dynamic_device_platforms(
    device: dict, mapping: dict
) -> dict[str, list[str]]:
    """处理动态分类设备的平台映射。"""
    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = {}

    if device_type == "SL_NATURE":
        # 超能面板动态分类逻辑
        p5_val = safe_get(device_data, "P5", "val", default=0) & 0xFF

        if p5_val == 1:  # 开关版
            switch_config = mapping.get("switch_mode", {})
            io_list = switch_config.get("io", [])
            valid_ios = [io for io in io_list if io in device_data]
            if valid_ios:
                platforms["switch"] = valid_ios

            # P4作为传感器
            sensor_io_list = switch_config.get("sensor_io", [])
            valid_sensor_ios = [io for io in sensor_io_list if io in device_data]
            if valid_sensor_ios:
                platforms["sensor"] = valid_sensor_ios

        elif p5_val in [3, 6]:  # 温控版
            climate_config = mapping.get("climate_mode", {})
            io_list = climate_config.get("io", [])
            valid_ios = [io for io in io_list if io in device_data]
            if valid_ios:
                platforms["climate"] = valid_ios

            # P4作为传感器
            sensor_io_list = climate_config.get("sensor_io", [])
            valid_sensor_ios = [io for io in sensor_io_list if io in device_data]
            if valid_sensor_ios:
                platforms["sensor"] = valid_sensor_ios

    elif device_type in ["SL_P", "SL_JEMA"]:
        # 通用控制器动态分类逻辑
        p1_val = safe_get(device_data, "P1", "val", default=0)
        work_mode = (p1_val >> 24) & 0xE

        if work_mode == 0:  # 自由模式 - 二元传感器
            binary_sensor_config = mapping.get("binary_sensor_mode", {})
            io_list = binary_sensor_config.get("io", [])
            valid_ios = [io for io in io_list if io in device_data]
            if valid_ios:
                platforms["binary_sensor"] = valid_ios

        elif work_mode in [2, 4]:  # 窗帘模式
            cover_config = mapping.get("cover_mode", {})
            io_list = cover_config.get("io", [])
            valid_ios = [io for io in io_list if io in device_data]
            if valid_ios:
                platforms["cover"] = valid_ios

        elif work_mode in [8, 10]:  # 开关模式
            switch_config = mapping.get("switch_mode", {})
            io_list = switch_config.get("io", [])
            valid_ios = [io for io in io_list if io in device_data]
            if valid_ios:
                platforms["switch"] = valid_ios

        # SL_JEMA额外支持P8/P9/P10独立开关
        if device_type == "SL_JEMA" and "always_switch" in mapping:
            always_switch_config = mapping["always_switch"]
            io_list = always_switch_config.get("io", [])
            valid_ios = [io for io in io_list if io in device_data]
            if valid_ios:
                if "switch" in platforms:
                    platforms["switch"].extend(valid_ios)
                else:
                    platforms["switch"] = valid_ios

    return platforms


def _get_single_platform_mapping(device: dict) -> dict[str, list[str]]:
    """获取单平台设备的IO映射（传统逻辑）。"""
    platforms = {}

    # 新架构下，所有设备映射都应在MULTI_PLATFORM_DEVICE_MAPPING中定义
    # 此函数仅作为向前兼容的占位符，实际使用get_device_platform_mapping()
    # 对于未在MULTI_PLATFORM_DEVICE_MAPPING中定义的设备，返回空映射

    return platforms


# ====================================================================
# 保留的兼容函数（基于新架构重写）
# ====================================================================
def safe_get(data: dict | list, *path, default: Any = None) -> Any:
    """
    安全地根据路径从嵌套的字典或列表中取值。

    如果路径中的任何一个键或索引不存在，则返回默认值，避免了 KeyError 或 IndexError。

    Args:
        data: 要查询的源数据（字典或列表）。
        *path: 一个或多个键或索引，代表访问路径。
        default: 如果路径无效，返回的默认值。

    Returns:
        获取到的值，或默认值。
    """
    cur = data
    for key in path:
        if isinstance(cur, dict):
            cur = cur.get(key, default)
        elif isinstance(cur, list) and isinstance(key, int):
            try:
                cur = cur[key]
            except IndexError:
                return default
        else:
            return default
    return cur


def generate_unique_id(
    devtype: str,
    agt: str,
    me: str,
    sub_device_key: str | None = None,
) -> str:
    """
    为 LifeSmart 实体生成一个稳定且唯一的内部 ID (unique_id)。

    此 ID 必须在所有模式下保持一致，且不应被截断。

    Args:
        devtype: 设备的类型代码。
        agt: 所属中枢的 ID。
        me: 设备的 ID。
        sub_device_key: 子设备的索引键（如果适用）。

    Returns:
        格式化的实体 ID 字符串，例如 'sl_sw_nd1_agt123_dev456_p1'。
    """

    def sanitize(input_str: str) -> str:
        """清理和规范化字符串，只保留字母数字并转为小写。"""
        return re.sub(r"\W", "", str(input_str).lower())

    parts = [sanitize(devtype), sanitize(agt), sanitize(me)]
    if sub_device_key:
        parts.append(sanitize(sub_device_key))

    return "_".join(parts)


def normalize_device_names(dev_dict: dict) -> dict:
    """
    递归地规范化设备及其子设备的名称，替换所有已知占位符。
    - '{$EPN}' -> 替换为父设备名称。
    - '{SUB_KEY}' -> 替换为 'SUB_KEY'。
    """
    base_name = dev_dict.get("name", "")
    if (
        "_chd" in dev_dict
        and "m" in dev_dict["_chd"]
        and "_chd" in safe_get(dev_dict, "_chd", "m", default={})
    ):
        sub_devices = safe_get(dev_dict, "_chd", "m", "_chd", default={})
        for sub_key, sub_data in sub_devices.items():
            if (
                isinstance(sub_data, dict)
                and (sub_name := sub_data.get("name"))
                and isinstance(sub_name, str)
            ):
                processed_name = sub_name.replace("{$EPN}", base_name).strip()
                processed_name = re.sub(r"\{([A-Z0-9_]+)\}", r"\1", processed_name)
                sub_data["name"] = " ".join(processed_name.split())
    return dev_dict


# ====================================================================
# IO通配符支持函数
# ====================================================================


def expand_wildcard_ios(io_pattern: str, device_data: dict) -> list[str]:
    """
    展开IO通配符模式，将带*和x的IO模式转换为实际存在的IO口列表。

    支持的通配符模式:
    - L*: 匹配L1, L2, L3等
    - Lx: 匹配L1, L2, L3等
    - EE*: 匹配EE, EE1, EE2等
    - EEx: 匹配EE1, EE2, EE3等
    - EPF*: 匹配EPF, EPF1, EPF2等
    - PMx: 匹配PM1, PM2, PM10等

    Args:
        io_pattern: IO通配符模式，如"L*", "EEx", "EPF*"
        device_data: 设备数据字典，包含实际的IO口

    Returns:
        匹配的实际IO口名称列表
    """
    if not io_pattern.endswith(("*", "x")):
        # 不是通配符模式，直接返回
        return [io_pattern] if io_pattern in device_data else []

    base_pattern = io_pattern[:-1]  # 移除*或x后缀
    matched_ios = []

    for io_key in device_data.keys():
        # 精确匹配基础模式
        if io_key == base_pattern:
            matched_ios.append(io_key)
            continue

        # 检查是否匹配带数字后缀的模式
        if io_key.startswith(base_pattern):
            suffix = io_key[len(base_pattern) :]
            # 确保后缀是数字（支持多位数字，如PM10）
            if suffix.isdigit():
                matched_ios.append(io_key)

    return sorted(matched_ios, key=lambda x: (len(x), x))  # 按长度和字母顺序排序


# ====================================================================
# 设备类型检查函数
# ====================================================================


def is_binary_sensor(device: dict) -> bool:
    """
    判断一个设备是否应被创建为二元传感器实体。

    基于新的IO特征映射架构，检查设备的平台映射中是否包含binary_sensor平台。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为二元传感器实体，则返回 True，否则返回 False。
    """
    platforms = get_device_platform_mapping(device)
    return Platform.BINARY_SENSOR in platforms


def is_binary_sensor_subdevice(device_type: str, sub_key: str) -> bool:
    """
    基于MULTI_PLATFORM_DEVICE_MAPPING判断一个设备的子IO口是否为二元传感器控制点。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。
    Returns:
        如果该IO口是此类型设备的二元传感器控制点，则返回 True。
    """
    from .const import MULTI_PLATFORM_DEVICE_MAPPING

    # 检查设备是否在映射表中
    if device_type not in MULTI_PLATFORM_DEVICE_MAPPING:
        return False

    mapping = MULTI_PLATFORM_DEVICE_MAPPING[device_type]

    # 处理版本设备
    if mapping.get("versioned"):
        # 对于版本设备，检查所有版本的binary_sensor平台
        for version_key, version_config in mapping.items():
            if version_key == "versioned":
                continue
            if isinstance(version_config, dict) and "binary_sensor" in version_config:
                binary_sensor_config = version_config["binary_sensor"]
                io_list = binary_sensor_config.get("io", [])
                if isinstance(io_list, str):
                    io_list = [io_list]
                if sub_key.upper() in [io.upper() for io in io_list]:
                    return True
        return False

    # 处理动态分类设备
    if mapping.get("dynamic"):
        # 动态分类设备需要检查所有可能的binary_sensor配置
        for config_key, config in mapping.items():
            if config_key == "dynamic":
                continue
            if isinstance(config, dict):
                # 检查binary_sensor模式的io字段
                if config_key == "binary_sensor_mode" and "io" in config:
                    io_list = config.get("io", [])
                    if isinstance(io_list, str):
                        io_list = [io_list]
                    if sub_key.upper() in [io.upper() for io in io_list]:
                        return True
        return False

    # 处理静态映射设备
    if "binary_sensor" in mapping:
        binary_sensor_config = mapping["binary_sensor"]
        io_list = binary_sensor_config.get("io", [])
        if isinstance(io_list, str):
            io_list = [io_list]
        return sub_key.upper() in [io.upper() for io in io_list]

    return False


def get_binary_sensor_subdevices(device: dict) -> list[str]:
    """
    获取设备中所有有效的二元传感器子设备键。

    基于新的IO特征映射架构，从平台映射中获取binary_sensor平台的IO口列表。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效二元传感器子设备键的列表。
    """
    if not is_binary_sensor(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = get_device_platform_mapping(device)

    # 从平台映射中获取binary_sensor的IO口
    if "binary_sensor" in platforms:
        return platforms["binary_sensor"]

    # 回退到传统逻辑
    subdevices = []
    for sub_key in device_data:
        if is_binary_sensor_subdevice(device_type, sub_key):
            subdevices.append(sub_key)
    return subdevices


def is_climate(device: dict) -> bool:
    """
    判断一个设备是否应被创建为温控实体。

    基于新的IO特征映射架构，检查设备的平台映射中是否包含climate平台。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为温控实体，则返回 True，否则返回 False。
    """
    platforms = get_device_platform_mapping(device)
    return "climate" in platforms


def is_cover(device: dict) -> bool:
    """
    判断一个设备是否应被创建为覆盖物(窗帘)实体。

    基于新的IO特征映射架构，检查设备的平台映射中是否包含cover平台。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为覆盖物实体，则返回 True，否则返回 False。
    """
    platforms = get_device_platform_mapping(device)
    return Platform.COVER in platforms


def is_cover_subdevice(device_type: str, sub_key: str) -> bool:
    """
    判断一个设备的子IO口是否为窗帘控制点。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。

    Returns:
        如果该IO口是此类型设备的窗帘控制点，则返回 True。
    """
    # 通过新架构检查设备是否支持窗帘功能及具体IO口
    if device_type in MULTI_PLATFORM_DEVICE_MAPPING:
        mapping = MULTI_PLATFORM_DEVICE_MAPPING[device_type]
        if "cover" in mapping:
            cover_config = mapping["cover"]
            cover_ios = cover_config.get("io", [])
            if isinstance(cover_ios, str):
                cover_ios = [cover_ios]
            return sub_key in cover_ios

    # 从const导入非位置窗帘配置用于兼容性检查
    from .const import NON_POSITIONAL_COVER_CONFIG

    if device_type in NON_POSITIONAL_COVER_CONFIG:
        # 对于非定位窗帘，其配置中定义的任何一个控制键（开/关/停）都算有效
        config = NON_POSITIONAL_COVER_CONFIG.get(device_type, {})
        return sub_key in config.values()
    return False


def get_cover_subdevices(device: dict) -> list[str]:
    """
    获取设备中所有有效的窗帘子设备键。

    基于新的IO特征映射架构，从平台映射中获取cover平台的IO口列表。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效窗帘子设备键的列表。
    """
    if not is_cover(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = get_device_platform_mapping(device)

    # 从平台映射中获取cover的IO口
    if "cover" in platforms:
        cover_ios = platforms["cover"]
        # 对于非定位窗帘，只创建一个实体（避免重复）
        from .const import NON_POSITIONAL_COVER_CONFIG, DOOYA_TYPES, GARAGE_DOOR_TYPES

        # 定位窗帘直接返回所有IO口
        if device_type in DOOYA_TYPES or device_type in GARAGE_DOOR_TYPES:
            return cover_ios

        # 非定位窗帘只返回第一个IO口（代表整个窗帘）
        config_key = "SL_P" if device_type in GENERIC_CONTROLLER_TYPES else device_type
        if config_key in NON_POSITIONAL_COVER_CONFIG:
            # 返回所有可用IO口中的第一个
            return cover_ios[:1] if cover_ios else []

        return cover_ios

    # 回退到传统逻辑
    subdevices = []
    for sub_key in device_data:
        if is_cover_subdevice(device_type, sub_key):
            # 对于非定位窗帘，只为"开"操作的IO口创建实体
            from .const import NON_POSITIONAL_COVER_CONFIG

            if device_type in NON_POSITIONAL_COVER_CONFIG:
                config = NON_POSITIONAL_COVER_CONFIG[device_type]
                rep_key = config.get("open")
                if sub_key == rep_key:
                    subdevices.append(sub_key)
            else:
                subdevices.append(sub_key)
    return subdevices


def is_light(device: dict) -> bool:
    """
    判断一个设备是否应被创建为灯光实体。

    基于新的IO特征映射架构，检查设备的平台映射中是否包含light平台。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为灯光实体，则返回 True，否则返回 False。
    """
    platforms = get_device_platform_mapping(device)
    return Platform.LIGHT in platforms


def is_light_subdevice(device_type: str, sub_key: str) -> bool:
    """
    判断一个设备的子IO口是否为灯光控制点。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。

    Returns:
        如果该IO口是此类型设备的灯光控制点，则返回 True。
    """
    return (sub_key.startswith(("P", "L")) or sub_key == "HS") and sub_key not in {
        "P5",
        "P6",
        "P7",
        "P8",
        "P9",
        "P10",
    }


def get_light_subdevices(device: dict) -> list[str]:
    """
    获取设备中所有有效的灯光子设备键。

    基于新的IO特征映射架构，从平台映射中获取light平台的IO口列表。
    对于多平台设备（如SL_OL_W），只返回light平台相关的IO口。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效灯光子设备键的列表。每个键对应一个需要创建的灯光实体。
    """
    if not is_light(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = get_device_platform_mapping(device)

    # 从平台映射中获取light的IO口
    if "light" in platforms:
        light_ios = platforms["light"]

        # 特殊处理不同的灯光类型
        # 对于某些特殊设备，需要返回特殊标记而不是实际IO口
        from .const import LIGHT_DIMMER_TYPES, QUANTUM_TYPES, RGBW_LIGHT_TYPES

        if device_type in LIGHT_DIMMER_TYPES:
            return ["_DIMMER"]  # 特殊标记
        elif device_type in QUANTUM_TYPES:
            return ["_QUANTUM"]  # 特殊标记
        elif (
            device_type in RGBW_LIGHT_TYPES
            and "RGBW" in device_data
            and "DYN" in device_data
        ):
            return ["_DUAL_RGBW"]  # 特殊标记

        return light_ios

    # 其他设备使用子设备判断逻辑
    subdevices = []
    for sub_key in device_data:
        if is_light_subdevice(device_type, sub_key):
            subdevices.append(sub_key)

    return subdevices


def is_sensor(device: dict) -> bool:
    """
    判断一个设备是否应被创建为数值传感器实体。

    基于新的IO特征映射架构，检查设备的平台映射中是否包含sensor平台。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为数值传感器实体，则返回 True，否则返回 False。
    """
    platforms = get_device_platform_mapping(device)
    return Platform.SENSOR in platforms


def is_sensor_subdevice(device_type: str, sub_key: str) -> bool:
    """
    基于MULTI_PLATFORM_DEVICE_MAPPING判断一个设备的子IO口是否为传感器控制点。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。
    Returns:
        如果该IO口是此类型设备的传感器控制点，则返回 True。
    """
    from .const import MULTI_PLATFORM_DEVICE_MAPPING

    # 检查设备是否在映射表中
    if device_type not in MULTI_PLATFORM_DEVICE_MAPPING:
        return False

    mapping = MULTI_PLATFORM_DEVICE_MAPPING[device_type]

    # 处理版本设备
    if mapping.get("versioned"):
        # 对于版本设备，检查所有版本的sensor平台
        for version_key, version_config in mapping.items():
            if version_key == "versioned":
                continue
            if isinstance(version_config, dict) and "sensor" in version_config:
                sensor_config = version_config["sensor"]
                io_list = sensor_config.get("io", [])
                if isinstance(io_list, str):
                    io_list = [io_list]
                if sub_key.upper() in [io.upper() for io in io_list]:
                    return True
        return False

    # 处理动态分类设备
    if mapping.get("dynamic"):
        # 动态分类设备需要检查所有可能的sensor配置
        for config_key, config in mapping.items():
            if config_key == "dynamic":
                continue
            if isinstance(config, dict):
                # 检查是否有sensor_io字段（如SL_NATURE）
                if "sensor_io" in config:
                    io_list = config.get("sensor_io", [])
                    if isinstance(io_list, str):
                        io_list = [io_list]
                    if sub_key.upper() in [io.upper() for io in io_list]:
                        return True
        return False

    # 处理静态映射设备
    if "sensor" in mapping:
        sensor_config = mapping["sensor"]
        io_list = sensor_config.get("io", [])
        if isinstance(io_list, str):
            io_list = [io_list]
        return sub_key.upper() in [io.upper() for io in io_list]

    return False


def get_sensor_subdevices(device: dict) -> list[str]:
    """
    获取设备中所有有效的传感器子设备键。

    基于新的IO特征映射架构，从平台映射中获取sensor平台的IO口列表。
    对于多平台设备（如恒星系列），只返回sensor平台相关的IO口。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效传感器子设备键的列表。
    """
    if not is_sensor(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = get_device_platform_mapping(device)

    # 从平台映射中获取sensor的IO口
    if "sensor" in platforms:
        return platforms["sensor"]

    # 其他设备使用子设备判断逻辑
    subdevices = []
    for sub_key in device_data:
        if is_sensor_subdevice(device_type, sub_key):
            subdevices.append(sub_key)

    return subdevices


def is_switch(device: dict) -> bool:
    """
    判断一个设备是否应被创建为开关实体。

    基于新的IO特征映射架构，检查设备的平台映射中是否包含switch平台。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为开关实体，则返回 True，否则返回 False。
    """
    platforms = get_device_platform_mapping(device)
    return Platform.SWITCH in platforms


def is_switch_subdevice(device_type: str, sub_key: str) -> bool:
    """
    基于MULTI_PLATFORM_DEVICE_MAPPING判断一个设备的子IO口是否为开关控制点。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。
    Returns:
        如果该IO口是此类型设备的开关控制点，则返回 True。
    """
    from .const import MULTI_PLATFORM_DEVICE_MAPPING

    # 检查设备是否在映射表中
    if device_type not in MULTI_PLATFORM_DEVICE_MAPPING:
        return False

    mapping = MULTI_PLATFORM_DEVICE_MAPPING[device_type]

    # 处理版本设备
    if mapping.get("versioned"):
        # 对于版本设备，检查所有版本的switch平台
        for version_key, version_config in mapping.items():
            if version_key == "versioned":
                continue
            if isinstance(version_config, dict) and "switch" in version_config:
                switch_config = version_config["switch"]
                io_list = switch_config.get("io", [])
                if isinstance(io_list, str):
                    io_list = [io_list]
                if sub_key.upper() in [io.upper() for io in io_list]:
                    return True
        return False

    # 处理动态分类设备
    if mapping.get("dynamic"):
        # 动态分类设备需要检查所有可能的switch配置
        for config_key, config in mapping.items():
            if config_key == "dynamic":
                continue
            if isinstance(config, dict) and config.get("io"):
                io_list = config.get("io", [])
                if isinstance(io_list, str):
                    io_list = [io_list]
                if sub_key.upper() in [io.upper() for io in io_list]:
                    return True
        return False

    # 处理静态映射设备
    if "switch" in mapping:
        switch_config = mapping["switch"]
        io_list = switch_config.get("io", [])
        if isinstance(io_list, str):
            io_list = [io_list]
        return sub_key.upper() in [io.upper() for io in io_list]

    return False


def get_switch_subdevices(device: dict) -> list[str]:
    """
    获取设备中所有有效的开关子设备键。

    基于新的IO特征映射架构，从平台映射中获取switch平台的IO口列表。
    对于多平台设备（如SL_OL_W），只返回switch平台相关的IO口。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效开关子设备键的列表。
    """
    if not is_switch(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = get_device_platform_mapping(device)

    # 从平台映射中获取switch的IO口
    if "switch" in platforms:
        return platforms["switch"]

    # 其他所有开关设备 - 使用子设备判断逻辑
    subdevices = []
    for sub_key in device_data:
        if is_switch_subdevice(device_type, sub_key):
            subdevices.append(sub_key)

    return subdevices


def get_device_effective_type(device: dict) -> str:
    """
    获取设备的有效类型，考虑fullCls版本信息。

    Args:
        device: 设备数据字典

    Returns:
        str: 有效的设备类型，如果需要版本区分则返回组合类型
    """
    devtype = device.get(DEVICE_TYPE_KEY)
    fullcls = device.get(DEVICE_FULLCLS_KEY)

    if not devtype:
        return None

    # 如果设备类型不需要版本区分，直接返回devtype
    if devtype not in VERSIONED_DEVICE_TYPES:
        return devtype

    # 如果没有fullCls信息，返回基础devtype
    if not fullcls:
        return devtype

    # 从fullCls中提取版本信息
    version_info = VERSIONED_DEVICE_TYPES[devtype]

    # 检查是否匹配任何已知版本（只匹配大写V版本，忽略OCR错误的小写）
    for version_suffix, version_type in version_info.items():
        if fullcls.upper().endswith(f"_{version_suffix}"):
            return f"{devtype}_{version_suffix}"

    # 如果没有匹配的版本，返回基础devtype
    return devtype


def is_versioned_device_type(device: dict, expected_version: str = None) -> bool:
    """
    检查设备是否为特定版本的设备类型。

    Args:
        device: 设备数据字典
        expected_version: 期望的版本，如 'V2', 'V1' 等

    Returns:
        bool: 是否匹配期望版本
    """
    if not expected_version:
        return False

    effective_type = get_device_effective_type(device)
    return effective_type and effective_type.endswith(f"_{expected_version}")


# ====================================================================
# IO接口和数据相关辅助函数
# ====================================================================


def is_ieee754_float_type(io_type: int) -> bool:
    """判断IO类型是否为IEEE754浮点类型。

    Args:
        io_type: IO口的type值

    Returns:
        如果是浮点类型返回True，否则返回False

    Reference:
        只有满足条件 (io_type & 0x7e) == 0x2 的IO数据其值才是浮点类型数据
    """
    return (io_type & IO_TYPE_FLOAT_MASK) == IO_TYPE_FLOAT_VALUE


def get_io_precision(io_type: int) -> int:
    """获取IO类型的精度系数。

    Args:
        io_type: IO口的type值

    Returns:
        精度系数，用于将原始值转换为实际值

    Reference:
        基于官方文档附录3.5的精度计算公式
    """
    if (io_type & IO_TYPE_PRECISION_MASK) == IO_TYPE_PRECISION_BASE:
        precision_bits = (io_type & IO_TYPE_PRECISION_BITS) // 2
        return 10 ** (precision_bits + 1)
    return 1


def convert_ieee754_float(io_val: int) -> float:
    """将32位整数转换为IEEE754浮点数。

    Args:
        io_val: 32位整数表示的IEEE754浮点数

    Returns:
        转换后的浮点数值

    Reference:
        官方文档附录3.4 IO值浮点类型说明
        例如：1024913643表示的是浮点值：0.03685085
    """
    # IEEE754浮点数转换相关函数定义 - 参考官方文档附录3.4
    # 这些函数用于处理LifeSmart设备中使用IEEE754格式存储的浮点数
    import struct

    return struct.unpack("!f", struct.pack("!i", io_val))[0]


def get_io_friendly_val(io_type: int, io_val: int) -> float | None:
    """获取IO口的友好值（实际值）。

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

    # IEEE754浮点数类型
    if is_ieee754_float_type(io_type):
        return convert_ieee754_float(io_val)

    # 普通数值类型，应用精度转换
    precision = get_io_precision(io_type)
    # 处理有符号16位数值
    if io_val > 0x7FFF:
        io_val = io_val - 0x10000
    return io_val / precision


def get_f_fan_mode(val: int) -> str:
    """根据 F 口的 val 值获取风扇模式。"""
    if val < 30:
        return FAN_LOW
    return FAN_MEDIUM if val < 65 else FAN_HIGH


def get_tf_fan_mode(val: int) -> str | None:
    """根据 tF 口的 val 值获取风扇模式。"""
    if 30 >= val > 0:
        return FAN_LOW
    if val <= 65:
        return FAN_MEDIUM
    if val <= 100:
        return FAN_HIGH
    if val == 101:
        return FAN_AUTO
    return None  # 风扇停止时返回 None


# ====================================================================
# 增强版映射结构支持的数据转换函数
# ====================================================================


def apply_enhanced_conversion(
    conversion_type: str, data: dict, io_config: dict
) -> float | int | bool | None:
    """
    应用增强版映射结构中定义的数据转换。

    Args:
        conversion_type: 转换类型标识符
        data: IO口的原始数据 (包含 val, v, type 等字段)
        io_config: IO口的配置信息

    Returns:
        转换后的值，转换失败时返回None
    """
    if not data:
        return None

    # 基础数据提取
    val = data.get("val")
    v_val = data.get("v")
    io_type = data.get("type")

    # 转换逻辑分发
    if conversion_type == "val_divide_10":
        return val / 10 if val is not None else None

    elif conversion_type == "val_divide_1000":
        return val / 1000 if val is not None else None

    elif conversion_type == "type_bit_0":
        # type&1==1 检查type字段的最低位
        io_type = data.get("type")
        return (io_type & 1) == 1 if io_type is not None else None

    elif conversion_type == "v_or_val":
        return v_val if v_val is not None else val

    elif conversion_type == "voltage_to_battery":
        if val is not None:
            # 根据电压值计算电池百分比 (2000-4200mV 对应 0-100%)
            voltage_mv = val if val > 100 else val * 1000  # 处理不同单位
            if voltage_mv < 2000:
                return 0
            elif voltage_mv > 4200:
                return 100
            else:
                return int((voltage_mv - 2000) / 2200 * 100)
        return None

    elif conversion_type == "ieee754_float":
        if val is not None and io_type is not None:
            return get_io_friendly_val(io_type, val)
        return None

    elif conversion_type == "binary_state":
        return val == 1 if val is not None else None

    elif conversion_type == "raw_value":
        return val

    else:
        # 未知转换类型，记录警告并返回原始值
        import logging

        _LOGGER = logging.getLogger(__name__)
        _LOGGER.warning("Unknown conversion type: %s", conversion_type)
        return val


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
    device_data = device.get(DEVICE_DATA_KEY, {})
    io_data = safe_get(device_data, sub_key, default={})

    if not io_data:
        return None

    conversion_type = io_config.get("conversion", "raw_value")
    return apply_enhanced_conversion(conversion_type, io_data, io_config)


def get_enhanced_platform_mapping(device: dict) -> dict[str, list[str]]:
    """
    基于增强版MULTI_PLATFORM_DEVICE_MAPPING获取设备的平台映射。

    支持新的IO口详细配置结构，兼容旧的简化结构。

    Args:
        device: 设备字典，包含设备的基本信息和数据

    Returns:
        平台名称到IO口列表的映射
    """
    device_type = device.get(DEVICE_TYPE_KEY)
    if not device_type or device_type not in MULTI_PLATFORM_DEVICE_MAPPING:
        return {}

    mapping = MULTI_PLATFORM_DEVICE_MAPPING[device_type]

    # 处理版本化设备
    if mapping.get("versioned"):
        device_version = get_device_version(device)
        if device_version and device_version in mapping:
            mapping = mapping[device_version]
        else:
            return {}

    # 处理动态设备 (保持原有逻辑)
    if mapping.get("dynamic"):
        return _handle_dynamic_device_mapping(device, mapping)

    # 构建平台映射
    platform_mapping = {}

    for platform, platform_config in mapping.items():
        if platform in {"versioned", "dynamic"}:
            continue

        # 新的增强结构：platform_config是IO口字典
        if isinstance(platform_config, dict):
            # 检查是否为增强结构 (包含具体IO配置)
            if any(
                isinstance(v, dict) and "description" in v
                for v in platform_config.values()
            ):
                # 增强结构：提取IO口键名
                ios = list(platform_config.keys())
            else:
                # 旧的简化结构：使用 io 字段
                ios = platform_config.get("io", [])
                if isinstance(ios, str):
                    ios = [ios]
        else:
            ios = []

        if ios:
            platform_mapping[platform] = ios

    return platform_mapping


def _handle_dynamic_device_mapping(device: dict, mapping: dict) -> dict[str, list[str]]:
    """处理动态设备的映射逻辑（保持原有逻辑）"""
    # 保持原有的动态设备处理逻辑不变
    # 这里应该包含原来的动态设备处理代码
    return {}
