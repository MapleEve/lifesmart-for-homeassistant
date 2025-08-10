"""
LifeSmart 事件平台实现。

本模块实现LifeSmart智能家居系统的事件实体，支持：
- 多类型事件处理（按钮、传感器、门窗等）
- 映射驱动的事件配置和检测
- 智能事件类型判断和数据处理
- 实时事件触发和状态同步

创建者：@MapleEve
技术架构：基于DEVICE_MAPPING的统一配置管理
"""

import logging
from typing import Any

from homeassistant.components.event import EventEntity, EventDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
    # 事件平台相关
    EVENT_TYPES,
)
from .core.data.processors import process_io_data
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_device_platform_mapping

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    设置LifeSmart事件平台。

    从配置条目初始化事件实体，根据设备类型自动检测支持的事件类型。
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    events = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 检查是否支持事件平台
        platform_mapping = get_device_platform_mapping(device)
        if "event" not in platform_mapping:
            continue

        event_config = platform_mapping.get("event", {})

        # 为每个支持的事件源创建实体
        for event_key, event_cfg in event_config.items():
            if isinstance(event_cfg, dict) and event_cfg.get("enabled", True):
                event = LifeSmartEvent(
                    device,
                    event_key,
                    event_cfg,
                    hub,
                )
                events.append(event)
                _LOGGER.debug(
                    "Added event %s for device %s",
                    event_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if events:
        async_add_entities(events)
        _LOGGER.info("Added %d LifeSmart events", len(events))


class LifeSmartEvent(LifeSmartEntity, EventEntity):
    """
    LifeSmart事件实现。

    支持多类型设备的事件处理，包括按钮、传感器、门窗感应器等。
    """

    def __init__(
        self,
        device: dict,
        sub_key: str,
        event_config: dict,
        hub,
    ) -> None:
        """
        初始化事件实体。

        Args:
            device: 设备信息字典
            sub_key: 子设备键名
            event_config: 事件配置信息
            hub: 集线器对象
        """
        super().__init__(device, sub_key, hub)
        self._event_config = event_config

        # 从配置获取支持的事件类型
        self._attr_event_types = event_config.get(
            "event_types", list(EVENT_TYPES.keys())
        )

        # 设置设备类别
        device_class = event_config.get("device_class", "generic")
        try:
            self._attr_device_class = EventDeviceClass(device_class)
        except ValueError:
            self._attr_device_class = EventDeviceClass.GENERIC
            _LOGGER.warning("Invalid event device class: %s", device_class)

        self._last_event_data = None

    @property
    def unique_id(self) -> str:
        """
        返回事件的唯一ID。
        """
        return generate_unique_id(
            self._device.get(DEVICE_TYPE_KEY, ""),
            self._device.get(HUB_ID_KEY, ""),
            self._device.get(DEVICE_ID_KEY, ""),
            self._sub_key,
        )

    @property
    def name(self) -> str:
        """
        返回事件实体的名称。
        """
        device_name = self._device.get(DEVICE_NAME_KEY, "Unknown Device")
        event_name = self._event_config.get("name", self._sub_key)
        return f"{device_name} {event_name}"

    @property
    def available(self) -> bool:
        """
        返回True如果实体可用。
        """
        return bool(self._device.get(DEVICE_DATA_KEY, {}))

    def _trigger_event(self, event_type: str, event_data: dict | None = None) -> None:
        """
        触发事件。

        Args:
            event_type: 事件类型
            event_data: 事件数据（可选）
        """
        if event_type not in self.event_types:
            _LOGGER.warning("Unsupported event type: %s", event_type)
            return

        # 触发事件
        self._trigger_event_with_data(event_type, event_data or {})

        _LOGGER.debug(
            "Triggered event %s for device %s with data: %s",
            event_type,
            self._device.get(DEVICE_NAME_KEY),
            event_data,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        处理来自协调器的更新数据。

        处理IO数据并根据数值变化触发相应事件。
        """
        device_data = self._device.get(DEVICE_DATA_KEY, {})
        io_data = device_data.get(self._sub_key)

        if io_data is None:
            return

        # 处理IO数据
        processed_value = process_io_data(io_data, self._event_config)

        # 检查是否有新的事件数据
        if processed_value != self._last_event_data:
            self._last_event_data = processed_value

            # 根据处理后的值确定事件类型
            event_type, event_data = self._determine_event(processed_value)
            if event_type:
                self._trigger_event(event_type, event_data)

        self.async_write_ha_state()

    def _determine_event(self, processed_value: Any) -> tuple[str | None, dict]:
        """
        根据处理后的值确定事件类型和数据。

        Args:
            processed_value: 经过处理的设备数据值

        Returns:
            tuple: (event_type, event_data) 事件类型和数据
        """
        event_data = {}

        if isinstance(processed_value, dict):
            # 复杂事件数据
            event_type = processed_value.get("event_type")
            event_data = processed_value.get("event_data", {})

            # 添加通用属性
            event_data["device_type"] = self._device.get(DEVICE_TYPE_KEY)
            event_data["sub_key"] = self._sub_key

        elif isinstance(processed_value, bool):
            # 布尔值：按钮按下/释放
            event_type = "button_press" if processed_value else None
            event_data = {
                "pressed": processed_value,
                "device_type": self._device.get(DEVICE_TYPE_KEY),
                "sub_key": self._sub_key,
            }

        elif isinstance(processed_value, (int, float)):
            # 数值：可能是传感器触发
            if processed_value > 0:
                # 根据设备类型判断事件类型
                device_type = self._device.get(DEVICE_TYPE_KEY, "")
                if "DOOR" in device_type or "WIN" in device_type:
                    event_type = (
                        "door_opened" if processed_value == 1 else "door_closed"
                    )
                elif "PIR" in device_type or "SC" in device_type:
                    event_type = "motion_detected"
                else:
                    event_type = "sensor_triggered"

                event_data = {
                    "value": processed_value,
                    "device_type": device_type,
                    "sub_key": self._sub_key,
                }
            else:
                event_type = None

        else:
            # 其他类型
            event_type = "data_updated"
            event_data = {
                "value": str(processed_value),
                "device_type": self._device.get(DEVICE_TYPE_KEY),
                "sub_key": self._sub_key,
            }

        return event_type, event_data

    async def async_added_to_hass(self) -> None:
        """
        订阅状态更新。
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
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.get(DEVICE_ID_KEY))},
            name=self._device.get(DEVICE_NAME_KEY),
            manufacturer=MANUFACTURER,
            model=self._device.get(DEVICE_TYPE_KEY),
            via_device=(DOMAIN, self._device.get(HUB_ID_KEY)),
        )
