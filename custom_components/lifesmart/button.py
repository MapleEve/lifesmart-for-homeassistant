"""
LifeSmart 按钮平台支持模块

由 @MapleEve 创建和维护

本模块为LifeSmart平台提供按钮设备支持，实现了对各种智能按钮的
控制和状态管理。

支持的按钮类型：
- 物理按钮：墙面开关、控制面板按钮
- 虚拟按钮：场景触发、功能按钮
- 系统按钮：复位、配对等特殊功能

技术特性：
- 配置驱动的按钮检测和创建
- 支持多种按钮设备类别
- 统一的按钮按下命令处理
- 与设备状态的同步更新
"""

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.const import (
    # 核心常量
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    # 按钮平台相关
    # 命令常量
    CMD_TYPE_PRESS,
)
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_button_subdevices, safe_get

_LOGGER = logging.getLogger(__name__)


def _get_enhanced_io_config(device: dict, sub_key: str) -> dict | None:
    """
    Get button IO port configuration information using the mapping engine.

    Args:
        device: Device dictionary
        sub_key: IO port key name

    Returns:
        IO port configuration dictionary, or None if not found
    """
    # Phase 2: 使用DeviceResolver统一接口 - 简化8行为3行
    from .core.resolver import get_device_resolver

    resolver = get_device_resolver()
    platform_config = resolver.get_platform_config(device, "button")

    if not platform_config:
        return None

    # 检查IO配置是否存在
    io_config = platform_config.ios.get(sub_key)
    if io_config and io_config.description:
        return {
            "description": io_config.description,
            "data_type": io_config.data_type,
            "rw": io_config.rw,
            "device_class": getattr(io_config, "device_class", None),
        }

    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目设置 LifeSmart 按钮设备。

    此函数负责遍历所有设备，识别支持按钮功能的设备，并为每个
    按钮子设备创建相应的Home Assistant实体。

    Args:
        hass: Home Assistant核心实例
        config_entry: 集成配置条目
        async_add_entities: 实体添加回调函数

    Returns:
        无返回值，通过async_add_entities添加实体
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    buttons = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 检查是否支持按钮平台
        button_subdevices = get_button_subdevices(device)

        # 为每个按钮子设备创建实体
        for btn_key in button_subdevices:
            # Use helper function to get IO configuration
            io_config = _get_enhanced_io_config(device, btn_key)
            if not io_config:
                continue

            btn_data = safe_get(device, DEVICE_DATA_KEY, btn_key, default={})
            if btn_data:  # Only create entity when button data exists
                button = LifeSmartButton(
                    raw_device=device,
                    client=hub.get_client(),
                    entry_id=config_entry.entry_id,
                    sub_device_key=btn_key,
                    sub_device_data=btn_data,
                )
                buttons.append(button)
                _LOGGER.debug(
                    "Added button %s for device %s",
                    btn_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if buttons:
        async_add_entities(buttons)
        _LOGGER.info("Added %d LifeSmart buttons", len(buttons))


class LifeSmartButton(LifeSmartEntity, ButtonEntity):
    """
    LifeSmart 按钮设备实现类。

    继承自LifeSmartEntity和ButtonEntity，提供完整的按钮功能。
    支持多种按钮类型和设备类别。

    主要功能:
    - 按钮按下事件处理
    - 设备类别自动识别
    - 状态同步和更新
    """

    def __init__(
        self,
        raw_device: dict[str, Any],
        client,
        entry_id: str,
        sub_device_key: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """
        初始化按钮设备。

        Args:
            raw_device: 原始设备数据字典
            client: LifeSmart 客户端实例
            entry_id: 配置条目 ID
            sub_device_key: 子设备键名
            sub_device_data: 子设备数据字典
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._btn_config = sub_device_data
        self._entry_id = entry_id

        # Generate button name and ID
        self._attr_name = self._generate_button_name()
        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )

        self._attr_device_class = ButtonDeviceClass.GENERIC

        # Get device class from configuration
        if "device_class" in sub_device_data:
            try:
                self._attr_device_class = ButtonDeviceClass(
                    sub_device_data["device_class"]
                )
            except ValueError:
                _LOGGER.warning(
                    "Invalid button device class: %s", sub_device_data["device_class"]
                )

    @callback
    def _generate_button_name(self) -> str | None:
        """
        返回按钮的唯一ID。

        Returns:
            基于设备类型和子设备键的唯一标识符
        """
        base_name = self._name
        # If sub-device has its own name, use it
        sub_name = self._btn_config.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # Otherwise, use base name + IO port index
        return f"{base_name} Button {self._sub_key.upper()}"

    @property
    def available(self) -> bool:
        """
        返回实体是否可用。

        Returns:
            如果设备有数据则返回True
        """
        return bool(self._raw_device.get(DEVICE_DATA_KEY, {}))

    async def async_press(self) -> None:
        """
        按下按钮。

        向设备发送按钮按下命令。
        """
        try:
            # 发送按钮按下命令
            await self._client.async_send_single_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_PRESS,
                1,  # 按下状态
            )

            _LOGGER.debug(
                "Pressed button %s on device %s",
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to press button %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        处理来自协调器的更新数据。

        按钮不需要状态更新，但保持连接以确保设备在线状态正确。
        """
        # 按钮不需要状态更新，但保持连接以确保设备在线状态正确
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """
        订阅状态更新。

        设置全局更新的事件监听器。
        """
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_coordinator_update,
            )
        )

    @property
    def device_info(self) -> DeviceInfo:
        """
        返回设备信息。

        Returns:
            包含设备标识和属性信息的DeviceInfo对象
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            via_device=(DOMAIN, self.agt),
        )
