"""
Support for LifeSmart binary sensors by @MapleEve
LifeSmart 二元传感器平台实现

此模块负责将 LifeSmart 的各种感应器（如门磁、动态感应器、水浸、门锁事件等）
注册为 Home Assistant 中的二元传感器实体。

"""

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .core.const import (
    # --- 核心常量导入 ---
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
)
from .core.entity import LifeSmartEntity
from .core.helpers import (
    generate_unique_id,
)
from .core.utils import (
    get_device_platform_mapping,
    get_binary_sensor_io_config,
    convert_binary_sensor_state,
    get_binary_sensor_attributes,
    is_momentary_button_device,
    safe_get,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart binary sensors from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    binary_sensors = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用新的IO映射系统获取设备支持的平台
        platform_mapping = get_device_platform_mapping(device)
        binary_sensor_subdevices = platform_mapping.get(Platform.BINARY_SENSOR, [])

        # 为每个binary_sensor子设备创建实体
        for sub_key in binary_sensor_subdevices:
            sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
            binary_sensors.append(
                LifeSmartBinarySensor(
                    raw_device=device,
                    client=hub.get_client(),
                    entry_id=config_entry.entry_id,
                    sub_device_key=sub_key,
                    sub_device_data=sub_device_data,
                )
            )

    async_add_entities(binary_sensors)


class LifeSmartBinarySensor(LifeSmartEntity, BinarySensorEntity):
    """LifeSmart binary sensor entity with enhanced compatibility."""

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        self._attr_name = f"{self._name} {self._sub_key.upper()}"
        device_name_slug = self._name.lower().replace(" ", "_")
        sub_key_slug = self._sub_key.lower()
        self._attr_object_id = f"{device_name_slug}_{sub_key_slug}"

        self._attr_unique_id = generate_unique_id(
            self.devtype, self.agt, self.me, sub_device_key
        )
        self._update_state(self._sub_data)

    @callback
    def _update_state(self, data: dict) -> None:
        """解析并根据数据更新所有实体状态和属性。"""
        self._sub_data = data
        device_class = self._determine_device_class()
        if device_class:
            self._attr_device_class = device_class

        # 首先，使用通用的 _parse_state 来确定当前事件是否应该为 'on'
        is_currently_on = self._parse_state()
        self._attr_is_on = is_currently_on

        # 然后，更新所有属性。_get_attributes 可能会用到 self._attr_is_on 的最新值
        self._attrs = self._get_attributes()

        # 最后，处理瞬时按钮的特殊重置逻辑 - 使用映射驱动判断
        if self._is_momentary_button_device() and is_currently_on:
            # 更新事件相关的属性
            val = data.get("val", 0)
            event_map = {1: "single_click", 2: "double_click", 255: "long_press"}
            self._attrs["last_event"] = event_map.get(val, "unknown")
            self._attrs["last_event_time"] = dt_util.utcnow().isoformat()

            # 使用 Home Assistant 的调度器在短暂延迟后将状态重置为 "off"
            @callback
            def reset_state_callback(_now):
                """Reset state to off."""
                self._attr_is_on = False
                self.async_write_ha_state()

            async_call_later(self.hass, 0.5, reset_state_callback)

    @callback
    def _determine_device_class(self) -> BinarySensorDeviceClass | None:
        """从DEVICE_MAPPING获取设备类别。"""
        io_config = get_binary_sensor_io_config(self._raw_device, self._sub_key)
        return io_config.get("device_class") if io_config else None

    @callback
    def _is_momentary_button_device(self) -> bool:
        """从DEVICE_MAPPING判断是否为瞬时按钮设备。"""
        return is_momentary_button_device(self.devtype, self._sub_key)

    @callback
    def _parse_state(self) -> bool:
        """使用工具函数解析设备状态。"""
        return convert_binary_sensor_state(self.devtype, self._sub_key, self._sub_data)

    @callback
    def _get_attributes(self) -> dict[str, Any]:
        """使用工具函数获取传感器属性。"""
        # 按钮开关类型初始化事件属性 - 使用映射驱动判断
        if self._is_momentary_button_device():
            return {"last_event": None, "last_event_time": None}

        # 使用工具函数获取设备特定属性
        return get_binary_sensor_attributes(
            self.devtype, self._sub_key, self._sub_data, self._attr_is_on
        )

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息以链接实体到单个设备。"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return self._attr_unique_id

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._attrs

    async def async_added_to_hass(self) -> None:
        """Register update listeners."""
        # 实时更新事件
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )
        # 全局数据刷新事件
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    async def _handle_update(self, data: dict) -> None:
        """Handle real-time updates."""
        try:
            if data is None:
                return

            self._update_state(data)
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self._attr_unique_id, e)

    async def _handle_global_refresh(self) -> None:
        """Handle periodic full data refresh."""
        try:
            # 从hass.data获取最新设备列表
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]

            # 查找当前设备
            current_device = next(
                (
                    d
                    for d in devices
                    if d[HUB_ID_KEY] == self.agt and d[DEVICE_ID_KEY] == self.me
                ),
                None,
            )

            if current_device:
                sub_data = safe_get(
                    current_device, DEVICE_DATA_KEY, self._sub_key, default={}
                )
                if sub_data:
                    self._update_state(sub_data)
                    self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during global refresh for %s: %s", self._attr_unique_id, e
            )
