"""
LifeSmart 集成的通用辅助函数模块。

此模块包含所有与协议或客户端状态无关的、可在多个地方复用的纯函数。
这包括实体ID生成、设备类型检查、数据安全获取和名称规范化等。
"""

import re
from typing import Any

from .const import (
    ALL_BINARY_SENSOR_TYPES,
    ALL_COVER_TYPES,
    ALL_LIGHT_TYPES,
    ALL_SENSOR_TYPES,
    ALL_SWITCH_TYPES,
    CLIMATE_TYPES,
    DEVICE_DATA_KEY,
    GENERIC_CONTROLLER_TYPES,
    GARAGE_DOOR_TYPES,
    SUPPORTED_SWITCH_TYPES,
    SMART_PLUG_TYPES,
    POWER_METER_PLUG_TYPES,
)


# ====================================================================
# 通用辅助函数
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

    此函数包含特殊业务逻辑：
    - 对于通用控制器 (GENERIC_CONTROLLER_TYPES)，它们是多功能设备，需要通过检查
      其 'P1' IO口的工作模式来区分具体功能。只有工作模式为 0 (自由模式) 时，
      其P5/P6/P7等IO口才会作为二元传感器输入。
    - 对于其他设备，直接检查其 devtype 是否在 ALL_BINARY_SENSOR_TYPES 集合中。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为二元传感器实体，则返回 True，否则返回 False。
    """
    device_type = device.get("devtype")
    if device_type not in ALL_BINARY_SENSOR_TYPES:
        return False

    # 通用控制器需要特殊判断其工作模式
    if device_type in GENERIC_CONTROLLER_TYPES:
        p1_val = safe_get(device, DEVICE_DATA_KEY, "P1", "val", default=0)
        work_mode = (p1_val >> 24) & 0xE
        # 0: 自由模式，此时P5/P6/P7为二元传感器输入
        return work_mode == 0

    return True


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

    # SL_SC_BB_V2 的 P1 是按钮事件触发器
    if device_type == "SL_SC_BB_V2" and sub_key == "P1":
        return True

    return False


def get_binary_sensor_subdevices(device: dict) -> list[str]:
    """
    获取设备中所有有效的二元传感器子设备键。

    此函数包含所有二元传感器设备的特殊处理逻辑：
    - 对于通用控制器 (GENERIC_CONTROLLER_TYPES)，只有在工作模式为0（自由模式）时，
      P5/P6/P7才是有效的二元传感器输入。
    - 对于温控设备，某些IO口有特殊的二元传感器功能（如窗户开关检测）。
    - 对于其他设备，使用通用的子设备判断逻辑。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效二元传感器子设备键的列表。
    """
    if not is_binary_sensor(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    subdevices = []

    # 对于通用控制器，helpers中的is_binary_sensor已经验证了工作模式，这里直接处理子设备
    if device_type in GENERIC_CONTROLLER_TYPES:
        for sub_key in ("P5", "P6", "P7"):
            if sub_key in device_data:
                subdevices.append(sub_key)
    else:
        # 其他设备使用子设备判断逻辑
        for sub_key in device_data:
            if is_binary_sensor_subdevice(device_type, sub_key):
                subdevices.append(sub_key)

    return subdevices


def is_climate(device: dict) -> bool:
    """
    判断一个设备是否应被创建为温控实体。

    此函数包含特殊业务逻辑：
    - 对于 'SL_NATURE' (超能面板)，它不仅仅是一个温控设备，也可能是开关面板。
      必须通过检查其 'P5' IO口的值来区分。如果 P5 的低8位值为3，则为温控版。
    - 对于其他设备，直接检查其 devtype 是否在 CLIMATE_TYPES 集合中。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为温控实体，则返回 True，否则返回 False。
    """
    device_type = device.get("devtype")
    if device_type not in CLIMATE_TYPES:
        return False

    # 超能面板需要特殊判断其工作模式
    if device_type == "SL_NATURE":
        # 温控版 SL_NATURE 必须存在 P5 且值为 3
        # 使用位与操作 `& 0xFF` 确保只比较低8位，增加代码健壮性
        p5_val = safe_get(device, DEVICE_DATA_KEY, "P5", "val", default=0) & 0xFF
        return p5_val == 3  # 3 代表温控版

    return True


def is_cover(device: dict) -> bool:
    """
    判断一个设备是否应被创建为覆盖物(窗帘)实体。

    此函数包含特殊业务逻辑：
    - 对于通用控制器 (GENERIC_CONTROLLER_TYPES)，它们是多功能设备，需要通过检查
      其 'P1' IO口的工作模式来区分具体功能。只有工作模式为 2 或 4 时才是窗帘控制。
    - 对于其他设备，直接检查其 devtype 是否在 ALL_COVER_TYPES 集合中。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为覆盖物实体，则返回 True，否则返回 False。
    """
    device_type = device.get("devtype")
    if device_type not in ALL_COVER_TYPES:
        return False

    # 通用控制器需要特殊判断其工作模式
    if device_type in GENERIC_CONTROLLER_TYPES:
        p1_val = safe_get(device, DEVICE_DATA_KEY, "P1", "val", default=0)
        work_mode = (p1_val >> 24) & 0xE
        # 2: 二线窗帘, 4: 三线窗帘
        return work_mode in {2, 4}

    return True


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

    此函数包含所有窗帘设备的特殊处理逻辑：
    - 对于通用控制器 (GENERIC_CONTROLLER_TYPES)，只有在工作模式为2或4时，
      P2/P3才是有效的窗帘控制点。
    - 对于非定位窗帘，只为其"开"操作的IO口创建一个实体，以避免重复。
    - 对于其他设备，使用通用的子设备判断逻辑。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效窗帘子设备键的列表。
    """
    if not is_cover(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    subdevices = []

    # 对于通用控制器，helpers中的is_cover已经验证了工作模式，这里直接处理子设备
    if device_type in GENERIC_CONTROLLER_TYPES:
        for sub_key in ("P2", "P3"):
            if sub_key in device_data:
                # 对于非定位窗帘，只为"开"操作的IO口创建实体
                from .const import NON_POSITIONAL_COVER_CONFIG

                config = NON_POSITIONAL_COVER_CONFIG.get("SL_P", {})
                rep_key = config.get("open")
                if rep_key and sub_key == rep_key:
                    subdevices.append(sub_key)
                # 对于定位窗帘，都添加
                elif not NON_POSITIONAL_COVER_CONFIG.get("SL_P"):
                    subdevices.append(sub_key)
    else:
        # 其他设备使用子设备判断逻辑
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

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为灯光实体，则返回 True，否则返回 False。
    """
    return device.get("devtype") in ALL_LIGHT_TYPES


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

    此函数包含所有灯光设备的特殊处理逻辑：
    - 对于 SPOT 类型设备，根据具体的 IO 口返回相应的子设备键。
    - 对于车库门类型，只检查 P1 是否存在。
    - 对于特殊的灯光类型（调光、量子灯、RGB等），不返回子设备键，因为它们会创建特殊的实体类。
    - 对于其他设备，使用通用的子设备判断逻辑。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效灯光子设备键的列表。每个键对应一个需要创建的灯光实体。
    """
    if not is_light(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    subdevices = []

    # 特殊处理：SPOT 类型设备
    if device_type in {"MSL_IRCTL", "OD_WE_IRCTL", "SL_SPOT"}:
        if device_type == "MSL_IRCTL" and "RGBW" in device_data:
            subdevices.append("RGBW")  # 特殊标记，表示需要创建 SPOT RGBW 灯
        elif device_type in {"OD_WE_IRCTL", "SL_SPOT"} and "RGB" in device_data:
            subdevices.append("RGB")  # 特殊标记，表示需要创建 SPOT RGB 灯
        return subdevices

    # 特殊处理：车库门类型，只检查 P1
    if device_type in GARAGE_DOOR_TYPES:  # GARAGE_DOOR_TYPES
        if "P1" in device_data:
            subdevices.append("P1")
        return subdevices

    # 特殊处理：这些设备类型会创建特殊的灯光实体，不需要子设备遍历
    from .const import (
        LIGHT_DIMMER_TYPES,
        QUANTUM_TYPES,
        RGBW_LIGHT_TYPES,
        RGB_LIGHT_TYPES,
        OUTDOOR_LIGHT_TYPES,
        BRIGHTNESS_LIGHT_TYPES,
    )

    if device_type in LIGHT_DIMMER_TYPES:
        subdevices.append("_DIMMER")  # 特殊标记，表示需要创建调光灯
        return subdevices

    if device_type in QUANTUM_TYPES:
        subdevices.append("_QUANTUM")  # 特殊标记，表示需要创建量子灯
        return subdevices

    if (
        device_type in RGBW_LIGHT_TYPES
        and "RGBW" in device_data
        and "DYN" in device_data
    ):
        subdevices.append("_DUAL_RGBW")  # 特殊标记，表示需要创建双IO RGBW灯
        return subdevices

    if device_type in RGB_LIGHT_TYPES and "RGB" in device_data:
        subdevices.append("RGB")  # 使用实际的子设备键
        return subdevices

    if device_type in OUTDOOR_LIGHT_TYPES and "P1" in device_data:
        subdevices.append("P1")  # 使用实际的子设备键
        return subdevices

    if device_type in BRIGHTNESS_LIGHT_TYPES and "P1" in device_data:
        subdevices.append("P1")  # 使用实际的子设备键，但会创建亮度灯
        return subdevices

    # 通用处理：其他灯光设备，遍历所有子设备
    for sub_key in device_data:
        if is_light_subdevice(device_type, sub_key):
            subdevices.append(sub_key)

    return subdevices


def is_sensor(device: dict) -> bool:
    """
    判断一个设备是否应被创建为数值传感器实体。

    此函数包含特殊业务逻辑：
    - 对于 'SL_NATURE' (超能面板)，它不仅仅是一个开关设备，在温控模式下还会
      产生温度传感器。必须通过检查其 'P5' IO口的值来区分。如果 P5 的低8位值为3，
      则为温控版，会产生一个温度传感器实体。
    - 对于其他设备，直接检查其 devtype 是否在 ALL_SENSOR_TYPES 集合中。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为数值传感器实体，则返回 True，否则返回 False。
    """
    device_type = device.get("devtype")
    # 温控版的超能面板会产生一个温度传感器
    if device_type == "SL_NATURE":
        p5_val = safe_get(device, DEVICE_DATA_KEY, "P5", "val", default=0) & 0xFF
        return p5_val == 3  # 3 代表温控版

    return device_type in ALL_SENSOR_TYPES


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
        EV_SENSOR_TYPES,
        ENVIRONMENT_SENSOR_TYPES,
        GAS_SENSOR_TYPES,
        NOISE_SENSOR_TYPES,
        POWER_METER_PLUG_TYPES,
        SMART_PLUG_TYPES,
        POWER_METER_TYPES,
        LOCK_TYPES,
        COVER_TYPES,
        DEFED_SENSOR_TYPES,
        SMOKE_SENSOR_TYPES,
        WATER_SENSOR_TYPES,
        GARAGE_DOOR_TYPES,
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

    # 环境感应器（包括温度、湿度、光照、电压）
    if device_type in EV_SENSOR_TYPES and sub_key in {
        "T",  # 温度
        "H",  # 湿度
        "Z",  # 光照
        "V",  # 电压
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",  # 各种传感器端口
    }:
        return True

    # TVOC, CO2, CH2O 传感器
    if device_type in ENVIRONMENT_SENSOR_TYPES and sub_key in {"P1", "P3", "P4"}:
        return True

    # 气体感应器
    if device_type in GAS_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    # 门锁电量
    if device_type in LOCK_TYPES and sub_key == "BAT":
        return True

    # 窗帘位置
    if device_type in COVER_TYPES and sub_key == "P8":
        return True

    # 智能插座（计量版）
    if device_type in POWER_METER_PLUG_TYPES and sub_key in {"P2", "P3", "P4"}:
        return True

    # 智能插座 (非计量版，但也可能带计量功能)
    if device_type in SMART_PLUG_TYPES and sub_key in {"EV", "EI", "EP", "EPA"}:
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

    此函数包含所有传感器设备的特殊处理逻辑：
    - 对于 'SL_NATURE' (超能面板)，只有在温控版（P5=3）时才创建P4温度传感器。
    - 对于其他设备，使用通用的子设备判断逻辑。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效传感器子设备键的列表。
    """
    if not is_sensor(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
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

    此函数包含特殊业务逻辑：
    - 对于通用控制器 (GENERIC_CONTROLLER_TYPES)，它们是多功能设备，需要通过检查
      其 'P1' IO口的工作模式来区分具体功能。只有工作模式为 8 或 10 时才是开关。
    - 对于其他设备，直接检查其 devtype 是否在 ALL_SWITCH_TYPES 集合中。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        如果该设备应该被创建为开关实体，则返回 True，否则返回 False。
    """
    device_type = device.get("devtype")
    if device_type not in ALL_SWITCH_TYPES:
        return False

    # 通用控制器需要特殊判断其工作模式
    if device_type in GENERIC_CONTROLLER_TYPES:
        p1_val = safe_get(device, DEVICE_DATA_KEY, "P1", "val", default=0)
        work_mode = (p1_val >> 24) & 0xE
        # 8: 三路开关, 10: 三路开关(新)
        return work_mode in {8, 10}

    return True


def is_switch_subdevice(device_type: str, sub_key: str) -> bool:
    """
    判断一个设备的子IO口是否为开关控制点。

    Args:
        device_type: 设备的类型代码。
        sub_key: 子设备或IO口的索引键。

    Returns:
        如果该IO口是此类型设备的开关控制点，则返回 True。
    """
    sub_key_upper = sub_key.upper()

    if device_type == "SL_P_SW":
        return sub_key_upper in {f"P{i}" for i in range(1, 10)}

    if device_type in GARAGE_DOOR_TYPES:
        return False
    if device_type == "SL_SC_BB_V2":
        return False
    if device_type in SUPPORTED_SWITCH_TYPES and sub_key_upper == "P4":
        return False

    if device_type in SMART_PLUG_TYPES:
        return sub_key_upper == "O"

    if device_type in POWER_METER_PLUG_TYPES:
        return sub_key_upper in {"P1", "P4"}

    if sub_key_upper in {"L1", "L2", "L3", "P1", "P2", "P3"}:
        return True

    return False


def get_switch_subdevices(device: dict) -> list[str]:
    """
    获取设备中所有有效的开关子设备键。

    此函数包含所有开关设备的特殊处理逻辑：
    - 对于通用控制器 (GENERIC_CONTROLLER_TYPES)，只有在工作模式为8或10时，
      P2/P3/P4才是有效的开关控制点。
    - 对于超能面板 (SL_NATURE)，只有在开关版（P5=1）时才创建开关实体。
    - 对于其他设备，使用通用的子设备判断逻辑。

    Args:
        device: 设备字典，包含设备的基本信息和数据。

    Returns:
        包含所有有效开关子设备键的列表。
    """
    if not is_switch(device):
        return []

    device_type = device.get("devtype")
    device_data = safe_get(device, DEVICE_DATA_KEY, default={})
    subdevices = []

    # 特殊处理：通用控制器
    if device_type in GENERIC_CONTROLLER_TYPES:
        # 通用控制器的工作模式已经在is_switch中验证，这里直接返回子设备键
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
