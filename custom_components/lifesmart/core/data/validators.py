"""
Data Validation Module - 数据验证模块

负责验证从客户端接收的数据格式和有效性。
由 @MapleEve 初始创建和维护
"""

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def validate_io_data(io_data: dict[str, Any]) -> bool:
    """
    验证IO口数据的有效性。

    Args:
        io_data: IO口数据字典，包含type和val字段

    Returns:
        如果数据有效则返回True，否则返回False
    """
    if not isinstance(io_data, dict):
        return False

    # 检查必要字段
    if "type" not in io_data or "val" not in io_data:
        return False

    # 检查字段类型
    if not isinstance(io_data["type"], int):
        return False

    return True


def validate_device_data(device: dict[str, Any]) -> bool:
    """
    验证设备数据的完整性。

    Args:
        device: 设备数据字典

    Returns:
        如果设备数据有效则返回True，否则返回False
    """
    if not isinstance(device, dict):
        return False

    # 检查必需字段
    required_fields = ["devtype", "me", "agt", "data"]
    for field in required_fields:
        if field not in device:
            _LOGGER.warning("Device missing required field: %s", field)
            return False

    # 检查data字段
    device_data = device.get("data")
    if not isinstance(device_data, dict):
        _LOGGER.warning("Device data field is not a dictionary")
        return False

    return True


def validate_hub_data(hub: dict[str, Any]) -> bool:
    """
    验证智慧中心数据的有效性。

    Args:
        hub: 智慧中心数据字典

    Returns:
        如果数据有效则返回True，否则返回False
    """
    if not isinstance(hub, dict):
        return False

    # 检查必需字段
    required_fields = ["agt", "devices"]
    for field in required_fields:
        if field not in hub:
            _LOGGER.warning("Hub missing required field: %s", field)
            return False

    return True
