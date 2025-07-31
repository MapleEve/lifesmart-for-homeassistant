"""
共用的测试辅助函数。

此模块包含在多个测试文件中重复使用的辅助函数，避免代码重复。
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from custom_components.lifesmart.const import DEVICE_ID_KEY


def get_entity_unique_id(hass: HomeAssistant, entity_id: str) -> str:
    """
    通过 entity_id 获取实体的 unique_id。

    Args:
        hass: Home Assistant 实例。
        entity_id: 实体的 ID。

    Returns:
        实体的 unique_id。

    Raises:
        AssertionError: 如果实体在注册表中未找到。
    """
    entity_registry = async_get_entity_registry(hass)
    entry = entity_registry.async_get(entity_id)
    assert entry is not None, f"实体 {entity_id} 未在注册表中找到"
    return entry.unique_id


def find_test_device(devices: list, me: str):
    """
    测试专用辅助函数，用于从模拟设备列表中通过 'me' ID 查找设备。

    Args:
        devices: 包含模拟设备字典的列表。
        me: 要查找的设备的 'me' 标识符。

    Returns:
        找到的设备字典，或在未找到时返回 None。
    """
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)
