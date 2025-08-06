"""
Support for LifeSmart binary sensors by @MapleEve
LifeSmart 二元传感器平台实现

此模块负责将 LifeSmart 的各种感应器（如门磁、动态感应器、水浸、门锁事件等）
注册为 Home Assistant 中的二元传感器实体。

"""

import datetime
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .const import (
    # --- 核心常量导入 ---
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    UNLOCK_METHOD,
    # --- 设备类型常量导入 ---
    GENERIC_CONTROLLER_TYPES,
    GUARD_SENSOR_TYPES,
    MOTION_SENSOR_TYPES,
    LOCK_TYPES,
    WATER_SENSOR_TYPES,
    SMOKE_SENSOR_TYPES,
    RADAR_SENSOR_TYPES,
    DEFED_SENSOR_TYPES,
    CUBE_BUTTON_TYPES,
    CLIMATE_TYPES,
)
from .entity import LifeSmartEntity
from .helpers import generate_unique_id, get_binary_sensor_subdevices, safe_get

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

        # 使用helpers中的统一逻辑获取所有有效的二元传感器子设备
        subdevice_keys = get_binary_sensor_subdevices(device)
        for sub_key in subdevice_keys:
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

        # 最后，处理瞬时按钮的特殊重置逻辑
        if self.devtype in CUBE_BUTTON_TYPES and is_currently_on:
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
        """Determine device class based on device type and sub-device key."""
        device_type = self.devtype
        sub_key = self._sub_key

        if device_type in CLIMATE_TYPES:
            if sub_key == "P2":  # 地暖继电器, 风机盘管阀门
                return (
                    BinarySensorDeviceClass.POWER
                    if device_type == "SL_CP_DN"
                    else BinarySensorDeviceClass.OPENING
                )
            if sub_key == "P5":  # 温控阀门告警
                return BinarySensorDeviceClass.PROBLEM
            if sub_key in {"P2", "P3"}:  # 超能面板阀门
                return BinarySensorDeviceClass.OPENING

            return None

        # 门窗感应器
        if device_type in GUARD_SENSOR_TYPES:
            if sub_key in {"G", "P1"}:
                return BinarySensorDeviceClass.DOOR
            if sub_key in {"AXS", "P2"}:
                return BinarySensorDeviceClass.VIBRATION
            if sub_key == "B":
                return None  # 通用二元传感器

        # 动态感应器
        if device_type in MOTION_SENSOR_TYPES:
            return BinarySensorDeviceClass.MOTION

        # 门锁
        if device_type in LOCK_TYPES:
            if sub_key == "EVTLO":
                return BinarySensorDeviceClass.LOCK
            if sub_key == "ALM":
                return BinarySensorDeviceClass.PROBLEM

        # 通用控制器
        if device_type in GENERIC_CONTROLLER_TYPES:
            return BinarySensorDeviceClass.OPENING

        # 水浸传感器
        if device_type in WATER_SENSOR_TYPES and sub_key == "WA":
            return BinarySensorDeviceClass.MOISTURE

        # 烟雾感应器
        if device_type in SMOKE_SENSOR_TYPES and sub_key == "P1":
            return BinarySensorDeviceClass.SMOKE

        # 人体存在感应器
        if device_type in RADAR_SENSOR_TYPES and sub_key == "P1":
            return BinarySensorDeviceClass.OCCUPANCY

        # 云防系列设备类别
        if device_type in DEFED_SENSOR_TYPES:
            if device_type == "SL_DF_GG":
                return BinarySensorDeviceClass.DOOR
            if device_type == "SL_DF_MM":
                return BinarySensorDeviceClass.MOTION
            if device_type == "SL_DF_SR":
                return BinarySensorDeviceClass.SOUND
            # 遥控器没有标准类别，作为通用触发器
            return None

        return None

    @callback
    def _parse_state(self) -> bool:
        """Parse the state based on device type and sub-device data."""
        device_type = self.devtype
        sub_key = self._sub_key
        val = self._sub_data.get("val", 0)
        type_val = self._sub_data.get("type", 0)

        # 门窗感应器特殊处理
        if device_type in GUARD_SENSOR_TYPES:
            if device_type == "SL_SC_GS" and sub_key in {"P1", "P2"}:
                return type_val & 1 == 1
            if device_type == "SL_SC_BG" and sub_key == "AXS":
                return val != 0  # 非0表示检测到震动
            return val == 0 if sub_key == "G" else val != 0

        # 云防系列设备特殊处理
        if device_type in DEFED_SENSOR_TYPES:
            return type_val & 1 == 1

        # 动态感应器
        if device_type in MOTION_SENSOR_TYPES:
            return val != 0

        # 门锁事件
        if device_type in LOCK_TYPES:
            if sub_key == "EVTLO":
                unlock_type = self._sub_data.get("type", 0)
                unlock_user = val & 0xFFF
                return (
                    val != 0
                    and unlock_type & 0x01 == 1
                    and unlock_user != 0
                    and val >> 12 != 15
                )
            if sub_key == "ALM":
                return val > 0

        # 通用控制器
        if device_type in GENERIC_CONTROLLER_TYPES:
            return type_val & 1 == 1

        # 水浸传感器
        if device_type in WATER_SENSOR_TYPES and sub_key == "WA":
            return val != 0  # 非0表示检测到水

        # 烟雾感应器
        if device_type in SMOKE_SENSOR_TYPES and sub_key == "P1":
            return val != 0  # 非0表示检测到烟雾

        # 人体存在感应器
        if device_type in RADAR_SENSOR_TYPES and sub_key == "P1":
            return val != 0  # 非0表示检测到人体存在

        # 云防门窗感应器
        if device_type == "SL_DF_GG" and sub_key == "A":
            return val == 0  # 云防门窗：0=开，1=关

        if device_type in CLIMATE_TYPES:
            if sub_key == "P5":  # 温控阀门告警 (val 是 bitmask)
                return val > 0
            # 其他所有温控器的附属开关/阀门都遵循 type&1==1 为开启的规则
            return type_val & 1 == 1

        # 其他传感器默认处理
        return val != 0

    @callback
    def _get_attributes(self) -> dict[str, Any]:
        """Get attributes for the sensor."""
        device_type = self.devtype
        sub_key = self._sub_key
        val = self._sub_data.get("val", 0)

        # 门锁事件的特殊属性
        if device_type in LOCK_TYPES and sub_key == "EVTLO":
            return {
                "unlocking_method": UNLOCK_METHOD.get(val >> 12, "Unknown"),
                "unlocking_user": val & 0xFFF,
                "device_type": device_type,
                "unlocking_success": self._attr_is_on,
                "last_updated": datetime.datetime.fromtimestamp(
                    self._sub_data.get("valts", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }

        # 门锁报警的属性
        if device_type in LOCK_TYPES and sub_key == "ALM":
            return {"alarm_type": val}

        # 水浸传感器的属性
        if device_type in WATER_SENSOR_TYPES and sub_key == "WA":
            return {"conductivity_level": val, "water_detected": val != 0}

        # 按钮开关类型初始化事件属性
        if device_type in CUBE_BUTTON_TYPES:
            return {"last_event": None, "last_event_time": None}

        # 为温控阀门的告警传感器添加详细属性
        if device_type == "SL_CP_VL" and sub_key == "P5":
            return {
                "high_temp_protection": bool(val & 0b1),
                "low_temp_protection": bool(val & 0b10),
                "internal_sensor_fault": bool(val & 0b100),
                "external_sensor_fault": bool(val & 0b1000),
                "low_battery": bool(val & 0b10000),
                "device_offline": bool(val & 0b100000),
            }
        # 默认返回原始数据
        return dict(self._sub_data)

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
