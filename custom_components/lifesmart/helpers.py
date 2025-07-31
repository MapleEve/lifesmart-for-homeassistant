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
    DEVICE_ID_KEY,
    GENERIC_CONTROLLER_TYPES,
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
        and "_chd" in dev_dict["_chd"]["m"]
    ):
        sub_devices = dev_dict["_chd"]["m"]["_chd"]
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


def is_switch(device: dict) -> bool:
    """判断一个设备是否应被创建为开关实体。"""
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


def is_light(device: dict) -> bool:
    """判断一个设备是否应被创建为灯光实体。"""
    return device.get("devtype") in ALL_LIGHT_TYPES


def is_cover(device: dict) -> bool:
    """判断一个设备是否应被创建为覆盖物实体。"""
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


def is_binary_sensor(device: dict) -> bool:
    """判断一个设备是否应被创建为二元传感器实体。"""
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


def is_sensor(device: dict) -> bool:
    """判断一个设备是否应被创建为数值传感器实体。"""
    device_type = device.get("devtype")
    # 温控版的超能面板会产生一个温度传感器
    if device_type == "SL_NATURE":
        p5_val = safe_get(device, DEVICE_DATA_KEY, "P5", "val", default=1) & 0xFF
        return p5_val == 3  # 3 代表温控版

    return device_type in ALL_SENSOR_TYPES


def is_climate(device: dict) -> bool:
    """判断一个设备是否应被创建为温控实体。"""
    device_type = device.get("devtype")
    if device_type not in CLIMATE_TYPES:
        return False

    # 超能面板需要特殊判断其工作模式
    if device_type == "SL_NATURE":
        p5_val = safe_get(device, DEVICE_DATA_KEY, "P5", "val", default=1) & 0xFF
        return p5_val == 3  # 3 代表温控版

    return True


# ====================================================================
# 测试专用辅助函数
# 注意：不要把测试函数导入正常模块中，这些函数仅用于测试
# ====================================================================


def find_test_device(devices: list, me: str):
    """
    /**
     * find_test_device - 一个测试专用辅助函数，用于从模拟设备列表中通过 'me' ID 查找设备。
     *
     * @devices: 包含模拟设备字典的列表。
     * @me: 要查找的设备的 'me' 标识符。
     *
     * 返回:
     *   找到的设备字典，或在未找到时返回 None。
     */
    """
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)
