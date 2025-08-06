"""
LifeSmart 集成的通用辅助函数模块。

此模块包含所有与协议或客户端状态无关的、可在多个地方复用的纯函数。
这包括实体ID生成、设备类型检查、数据安全获取和名称规范化等。
"""

import re

from homeassistant.components.climate import FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO
from homeassistant.const import Platform

from .const import (
    CLIMATE_TYPES,
    DEVICE_DATA_KEY,
    DEVICE_FULLCLS_KEY,
    DEVICE_TYPE_KEY,
    GENERIC_CONTROLLER_TYPES,
    VERSIONED_DEVICE_TYPES,
    IO_TYPE_FLOAT_MASK,
    IO_TYPE_FLOAT_VALUE,
    IO_TYPE_PRECISION_MASK,
    IO_TYPE_PRECISION_BASE,
    IO_TYPE_PRECISION_BITS,
    IO_TYPE_EXCEPTION,
    # 新增：多平台设备支持映射
    MULTI_PLATFORM_DEVICE_MAPPING,
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
    """获取单平台设备的IO映射（传统逗辑）。"""
    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    platforms = {}

    # 恒星/辰星/极星系列特殊处理 (STAR_SERIES_IO_MAPPING 未定义，暂时跳过)
    # if device_type in STAR_SERIES_IO_MAPPING:
    #     mapping = STAR_SERIES_IO_MAPPING[device_type]
    # 
    #     # 开关IO口
    #     switch_ios = [io for io in mapping["switch_io"] if io in device_data]
    #     if switch_ios:
    #         platforms["switch"] = switch_ios

        # 电量IO口（作为传感器） - 暂时跳过，mapping未定义
        # battery_io = mapping["battery_io"] 
        # if battery_io in device_data:
        #     platforms["sensor"] = [battery_io]

    # 其他单平台设备的传统逗辑
    # TODO: 在未来版本中，所有设备都应该添加到 MULTI_PLATFORM_DEVICE_MAPPING 中
    # 目前保留的代码用于可能的向后兼容
    # elif device_type in ALL_SWITCH_TYPES:
    #     # 推断可能的开关IO口
    #     common_switch_ios = ["O", "P1", "L1", "L2", "L3", "P2", "P3", "P4"]
    #     valid_ios = [io for io in common_switch_ios if io in device_data]
    #     if valid_ios:
    #         platforms["switch"] = valid_ios
    #
    # elif device_type in ALL_LIGHT_TYPES:
    #     # 推断可能的灯光IO口
    #     common_light_ios = ["RGB", "RGBW", "P1", "P2", "DYN"]
    #     valid_ios = [io for io in common_light_ios if io in device_data]
    #     if valid_ios:
    #         platforms["light"] = valid_ios

    # 温控设备的传统逻辑
    elif device_type in CLIMATE_TYPES:
        # 推断可能的温控IO口
        common_climate_ios = ["O", "MODE", "F", "tT", "T", "P1", "P2", "P3", "P4", "P8"]
        valid_ios = [io for io in common_climate_ios if io in device_data]
        if valid_ios:
            platforms["climate"] = valid_ios

    # 对于不在映射中的设备，尝试基于设备类型推断
    else:
        # 这里可以添加传统设备类型检查逻辑作为回退
        # 但新架构鼓励将所有设备添加到MULTI_PLATFORM_DEVICE_MAPPING中
        pass

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
    判断一个设备的子IO口是否为二元传感器控制点。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。

    Returns:
        如果该IO口是此类型设备的二元传感器控制点，则返回 True。
    """
    from .const import (
        CLIMATE_TYPES,
        LOCK_TYPES,
        BINARY_SENSOR_TYPES,
        WATER_SENSOR_TYPES,
        SMOKE_SENSOR_TYPES,
        RADAR_SENSOR_TYPES,
        DEFED_SENSOR_TYPES,
        BUTTON_SWITCH_TYPES,
    )

    if device_type in CLIMATE_TYPES:
        # 为特定温控器的附属功能创建实体
        if device_type == "SL_CP_DN" and sub_key == "P2":
            return True  # 地暖温控器的窗户开关检测
        if device_type == "SL_CP_AIR" and sub_key == "P2":
            return True  # 风机盘管的窗户开关检测
        if device_type == "SL_CP_VL" and sub_key == "P5":
            return True  # 温控阀门的窗户开关检测
        if device_type in {"SL_NATURE", "SL_FCU"} and sub_key in {"P2", "P3"}:
            return True  # 超能面板和星玉面板的阀门开关检测
        return False  # 默认不为温控设备创建其他二元传感器

    # 门锁事件和报警
    if device_type in LOCK_TYPES and sub_key in {"EVTLO", "ALM"}:
        return True

    # 门窗、动态、振动等传感器
    if device_type in BINARY_SENSOR_TYPES and sub_key in {
        "M",
        "G",
        "B",
        "AXS",
        "P1",
    }:
        return True

    # 水浸传感器
    if device_type in WATER_SENSOR_TYPES and sub_key == "WA":
        return True

    # 烟雾感应器
    if device_type in SMOKE_SENSOR_TYPES and sub_key == "P1":
        return True

    # 人体存在感应器
    if device_type in RADAR_SENSOR_TYPES and sub_key == "P1":
        return True

    # 云防系列传感器判断
    if device_type in DEFED_SENSOR_TYPES and sub_key in {
        "A",
        "A2",
        "M",
        "TR",
        "SR",
        "eB1",
        "eB2",
        "eB3",
        "eB4",
    }:
        return True

    # 按钮开关类型处理
    if device_type in BUTTON_SWITCH_TYPES:
        if device_type == "SL_SC_BB" and sub_key == "B":
            return True  # SL_SC_BB 使用 B 作为按键状态
        if device_type == "SL_SC_BB_V2" and sub_key == "P1":
            return True  # SL_SC_BB_V2 使用 P1 作为按键状态

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
    return "climate" in platforms or device.get("devtype") in CLIMATE_TYPES


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
    from .const import GARAGE_DOOR_TYPES, DOOYA_TYPES, NON_POSITIONAL_COVER_CONFIG

    if device_type in GARAGE_DOOR_TYPES:
        return sub_key in {"P2", "HS"}
    if device_type in DOOYA_TYPES:
        return sub_key == "P1"
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

    # 回退到传统逻辑
    subdevices = []

    # SPOT 类型设备特殊处理
    if device_type in {"MSL_IRCTL", "OD_WE_IRCTL", "SL_SPOT"}:
        if device_type == "MSL_IRCTL" and "RGBW" in device_data:
            subdevices.append("RGBW")
        elif device_type in {"OD_WE_IRCTL", "SL_SPOT"} and "RGB" in device_data:
            subdevices.append("RGB")
        return subdevices

    # 其他设备使用子设备判断逻辑
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
    判断一个设备的子IO口是否为传感器控制点。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。

    Returns:
        如果该IO口是此类型设备的传感器控制点，则返回 True。
    """
    from .const import (
        CLIMATE_TYPES,
        BASIC_ENV_SENSOR_TYPES,
        AIR_QUALITY_SENSOR_TYPES,
        GAS_SENSOR_TYPES,
        NOISE_SENSOR_TYPES,
        METERING_OUTLET_TYPES,
        POWER_METER_TYPES,
        LOCK_TYPES,
        COVER_TYPES,
        DEFED_SENSOR_TYPES,
        SMOKE_SENSOR_TYPES,
        WATER_SENSOR_TYPES,
    )

    if device_type in CLIMATE_TYPES:
        # 温控设备的温度/阀门等状态由 climate 实体内部管理
        if device_type == "SL_CP_DN" and sub_key == "P5":
            return True  # 地暖温控器的附加传感器
        if device_type == "SL_CP_VL" and sub_key == "P6":
            return True  # 温控阀门的附加传感器
        if device_type == "SL_TR_ACIPM" and sub_key in {"P4", "P5"}:
            return True  # 新风系统的PM2.5和CO2传感器
        return False

    # 环境感应器（基础型：温度、湿度、光照、电压）
    if device_type in BASIC_ENV_SENSOR_TYPES or device_type in AIR_QUALITY_SENSOR_TYPES:
        # 基础环境传感器的IO口
        if device_type in {"SL_SC_THL", "SL_SC_BE", "SL_SC_B1"} and sub_key in {
            "T",
            "H",
            "Z",
            "V",
        }:
            return True
        # 空气质量传感器的IO口
        if device_type in AIR_QUALITY_SENSOR_TYPES:
            if device_type == "SL_SC_CQ" and sub_key in {
                "P1",
                "P2",
                "P3",
                "P4",
                "P5",
                "P6",
            }:
                return True  # 温度、湿度、CO2、TVOC、电量、USB供电
            if device_type == "SL_SC_CA" and sub_key in {"P1", "P2", "P3", "P4", "P5"}:
                return True  # 温度、湿度、CO2、电量、USB供电
            if device_type == "SL_SC_CH" and sub_key in {"P1"}:
                return True  # 甲醛浓度(P2/P3为配置口，不是传感器)
        return False

    # 气体感应器
    if device_type in GAS_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    # 门锁电量
    if device_type in LOCK_TYPES and sub_key == "BAT":
        return True

    # 窗帘位置
    if device_type in COVER_TYPES and sub_key == "P8":
        return True

    # 计量插座
    if device_type in METERING_OUTLET_TYPES and sub_key in {"P2", "P3", "P4"}:
        return True

    # 噪音感应器
    if device_type in NOISE_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    # ELIQ电量计量器
    if device_type in POWER_METER_TYPES and sub_key in {"EPA", "EE", "EP"}:
        return True

    # 云防系列传感器
    if device_type in DEFED_SENSOR_TYPES and sub_key in {"T", "V"}:
        return True

    # 烟雾传感器
    if device_type in SMOKE_SENSOR_TYPES and sub_key == "P2":
        return True

    # 水浸传感器（只保留电压）
    if device_type in WATER_SENSOR_TYPES and sub_key == "V":
        return True

    # SL_SC_BB_V2 的 P2 是电量传感器
    if device_type == "SL_SC_BB_V2" and sub_key == "P2":
        return True

    # 车库门类型不创建传感器子设备
    if device_type in GARAGE_DOOR_TYPES:
        return False

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

    # 回退到传统逻辑
    subdevices = []

    # 特殊处理：温控版的超能面板
    if device_type == "SL_NATURE":
        # helpers中的is_sensor已经验证了P5=3的条件
        if "P4" in device_data:
            subdevices.append("P4")
        return subdevices

    # 其他设备使用子设备判断逻辑
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
    基于IO口功能精确判断一个设备的子IO口是否为开关控制点。

    根据const.py中每个设备类型的详细IO口注释进行逐一匹配。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。

    Returns:
        如果该IO口是此类型设备的开关控制点，则返回 True。
    """
    sub_key_upper = sub_key.upper()

    # ==================== 专门的开关控制器 ====================

    # 开关智控器 - P2是开关控制口
    if device_type == "SL_S":
        return sub_key_upper == "P2"

    # 九路开关控制器 - P1~P9都是开关控制口，支持点动模式
    if device_type == "SL_P_SW":
        return sub_key_upper in {f"P{i}" for i in range(1, 10)}

    # 星玉情景开关(六路) - P1~P6是情景开关控制
    if device_type == "SL_SW_NS6":
        return sub_key_upper in {f"P{i}" for i in range(1, 7)}

    # ==================== 流光开关系列 ====================

    # 流光开关/辰星开关 - L1/L2/L3是开关控制，dark/bright是指示灯控制(非开关)
    if device_type in {"SL_SW_IF1", "SL_SW_FE1", "SL_SF_IF1", "SL_SW_RC1", "SL_SW_CP1"}:
        return sub_key_upper == "L1"
    if device_type in {"SL_SW_IF2", "SL_SW_FE2", "SL_SF_IF2", "SL_SW_RC2", "SL_SW_CP2"}:
        return sub_key_upper in {"L1", "L2"}
    if device_type in {"SL_SW_IF3", "SL_SF_IF3", "SL_SW_RC3", "SL_SW_CP3"}:
        return sub_key_upper in {"L1", "L2", "L3"}

    # 触摸开关/极星开关(零火版) - L1/L2/L3是开关控制
    if device_type in {"SL_SW_RC", "SL_SF_RC"}:
        return sub_key_upper in {"L1", "L2", "L3"}

    # ==================== 星玉开关系列 ====================

    # 星玉开关 - L1/L2/L3是开关控制，dark/bright是指示灯控制
    if device_type == "SL_SW_NS1":
        return sub_key_upper == "L1"
    if device_type == "SL_SW_NS2":
        return sub_key_upper in {"L1", "L2"}
    if device_type == "SL_SW_NS3":
        return sub_key_upper in {"L1", "L2", "L3"}

    # ==================== 极星开关(120零火版) ====================

    # 极星开关120零火版 - P1/P2/P3是开关控制
    if device_type == "SL_SW_BS1":
        return sub_key_upper == "P1"
    if device_type == "SL_SW_BS2":
        return sub_key_upper in {"P1", "P2"}
    if device_type == "SL_SW_BS3":
        return sub_key_upper in {"P1", "P2", "P3"}

    # ==================== 恒星/辰星/极星系列(带电压监测) ====================

    # 单键版本: P1是开关，P2是电量监测(非开关控制)
    if device_type in {"SL_SW_ND1", "SL_MC_ND1"}:
        return sub_key_upper == "P1"

    # 双键版本: P1/P2是开关，P3是电量监测(非开关控制)
    if device_type in {"SL_SW_ND2", "SL_MC_ND2"}:
        return sub_key_upper in {"P1", "P2"}

    # 三键版本: P1/P2/P3是开关，P4是电量监测(非开关控制)
    if device_type in {"SL_SW_ND3", "SL_MC_ND3"}:
        return sub_key_upper in {"P1", "P2", "P3"}

    # ==================== 奇点开关模块 ====================

    # 奇点开关模块 - P1/P2/P3是开关控制
    if device_type == "SL_SW_MJ1":
        return sub_key_upper == "P1"
    if device_type == "SL_SW_MJ2":
        return sub_key_upper in {"P1", "P2"}
    if device_type == "SL_SW_MJ3":
        return sub_key_upper in {"P1", "P2", "P3"}

    # ==================== 超能面板 ====================

    # 超能面板 - P1/P2/P3是开关控制(仅开关版P5=1时有效)
    if device_type == "SL_NATURE":
        return sub_key_upper in {"P1", "P2", "P3"}

    # ==================== 插座系列 ====================

    # 智能插座系列 - O口是开关控制
    if device_type in {
        "SL_OL",
        "SL_OL_3C",
        "SL_OL_DE",
        "SL_OL_UK",
        "SL_OL_UL",
        "OD_WE_OT1",
    }:
        return sub_key_upper == "O"

    # 入墙插座 - L1是开关控制，dark/bright是指示灯控制
    if device_type == "SL_OL_W":
        return sub_key_upper == "L1"

    # 计量插座系列 - P1是开关控制，P4是功率门限控制(也算开关功能)
    if device_type in {"SL_OE_DE", "SL_OE_3C", "SL_OE_W"}:
        return sub_key_upper in {"P1", "P4"}

    # ==================== 特殊设备排除 ====================

    # 车库门控制器 - P1是灯光控制(由light平台处理，不是开关)
    if device_type in {"SL_ETDOOR"}:
        return False

    # 按钮开关 - 不是开关控制，是按键检测(由binary_sensor平台处理)
    if device_type in {"SL_SC_BB", "SL_SC_BB_V2"}:
        return False

    # 虚拟开关 - 根据配置动态生成，暂时返回False
    if device_type == "V_IND_S":
        return False

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

    # 回退到传统逻辑
    subdevices = []

    # 特殊处理：通用控制器
    if device_type in GENERIC_CONTROLLER_TYPES:
        # 通用控制器的工作模式已经在is_switch中验证
        for sub_key in ("P2", "P3", "P4"):
            if safe_get(device_data, sub_key) is not None:
                subdevices.append(sub_key)
        return subdevices

    # 特殊处理：超能面板 - 只有开关版才创建开关实体
    if device_type == "SL_NATURE":
        p5_val = safe_get(device, DEVICE_DATA_KEY, "P5", "val", default=0) & 0xFF
        if p5_val != 1:  # 只有P5=1才是开关版
            return []

    # 其他所有开关设备 - 使用子设备判断逻辑
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
