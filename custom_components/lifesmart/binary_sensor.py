"""
Support for LifeSmart binary sensors by @MapleEve
LifeSmart 二元传感器平台实现

此模块负责将 LifeSmart 的各种感应器（如门磁、动态感应器、水浸、门锁事件等）
注册为 Home Assistant 中的二元传感器实体。

"""

import asyncio
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
from homeassistant.util import dt as dt_util

from . import generate_unique_id, LifeSmartDevice
from .const import (
    # --- 核心常量导入 ---
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    UNLOCK_METHOD,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    # --- 设备类型常量导入 ---
    ALL_BINARY_SENSOR_TYPES,
    BINARY_SENSOR_TYPES,
    GENERIC_CONTROLLER_TYPES,
    GUARD_SENSOR_TYPES,
    MOTION_SENSOR_TYPES,
    LOCK_TYPES,
    WATER_SENSOR_TYPES,
    SMOKE_SENSOR_TYPES,
    RADAR_SENSOR_TYPES,
    DEFED_SENSOR_TYPES,
    CLIMATE_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart binary sensors from a config entry."""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    exclude_devices_str = config_entry.options.get(CONF_EXCLUDE_ITEMS, "")
    exclude_hubs_str = config_entry.options.get(CONF_EXCLUDE_AGTS, "")

    exclude_devices = {
        dev.strip() for dev in exclude_devices_str.split(",") if dev.strip()
    }
    exclude_hubs = {hub.strip() for hub in exclude_hubs_str.split(",") if hub.strip()}
    client = hass.data[DOMAIN][entry_id]["client"]

    binary_sensors = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        device_data = device.get(DEVICE_DATA_KEY, {})

        if device_type in GENERIC_CONTROLLER_TYPES:
            p1_val = device_data.get("P1", {}).get("val", 0)
            work_mode = (p1_val >> 24) & 0xE
            # 只有在“自由模式”下，P5/P6/P7 才可能是二元传感器
            if work_mode == 0:
                for sub_key in ("P5", "P6", "P7"):
                    if sub_key in device_data:
                        binary_sensors.append(
                            LifeSmartBinarySensor(device, sub_key, client, entry_id)
                        )
            continue

        if device_type not in ALL_BINARY_SENSOR_TYPES:
            continue

        for sub_device_key in device[DEVICE_DATA_KEY]:
            sub_device_data = device[DEVICE_DATA_KEY][sub_device_key]

            if not _is_binary_sensor_subdevice(device_type, sub_device_key):
                continue

            binary_sensors.append(
                LifeSmartBinarySensor(
                    raw_device=device,
                    client=client,
                    entry_id=entry_id,
                    sub_device_key=sub_device_key,
                    sub_device_data=sub_device_data,
                )
            )

    async_add_entities(binary_sensors)


def _is_binary_sensor_subdevice(device_type: str, sub_key: str) -> bool:
    """判断一个子设备是否为有效的二元传感器。"""
    if device_type in CLIMATE_TYPES:
        # 为特定温控器的附属功能创建实体
        if device_type == "SL_CP_DN" and sub_key == "P2":
            return True
        if device_type == "SL_CP_AIR" and sub_key == "P2":
            return True
        if device_type == "SL_CP_VL" and sub_key == "P5":
            return True
        if device_type in {"SL_NATURE", "SL_FCU"} and sub_key in {"P2", "P3"}:
            return True
        return False  # 默认不为温控设备创建其他二元传感器

    # 通用控制器 (SL_P) 的 P5/P6/P7 在自由模式下是二元传感器
    if device_type in GENERIC_CONTROLLER_TYPES and sub_key in {
        "P5",
        "P6",
        "P7",
    }:
        return True

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


class LifeSmartBinarySensor(LifeSmartDevice, BinarySensorEntity):
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
        if self.devtype == "SL_SC_BB_V2" and is_currently_on:
            # 更新事件相关的属性
            val = data.get("val", 0)
            event_map = {1: "single_click", 2: "double_click", 255: "long_press"}
            self._attrs["last_event"] = event_map.get(val, "unknown")
            self._attrs["last_event_time"] = dt_util.utcnow().isoformat()

            # 创建一个异步任务，在短暂延迟后将状态重置为 "off"
            async def reset_state():
                await asyncio.sleep(0.5)
                self._attr_is_on = False
                self.async_write_ha_state()

            self.hass.loop.create_task(reset_state())

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
            if sub_key == "G":
                return BinarySensorDeviceClass.DOOR
            if sub_key == "AXS":
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
            return val == 0 if sub_key == "G" else val != 0

        # 云防系列设备特殊处理
        if device_type in DEFED_SENSOR_TYPES:
            return type_val % 2 == 1

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
            return type_val % 2 == 1

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
            # 其他所有温控器的附属开关/阀门都遵循 type%2==1 为开启的规则
            return type_val % 2 == 1

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

        # SL_SC_BB_V2 初始化事件属性
        if device_type == "SL_SC_BB_V2":
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
                sub_data = current_device.get(DEVICE_DATA_KEY, {}).get(
                    self._sub_key, {}
                )
                if sub_data:
                    self._update_state(sub_data)
                    self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during global refresh for %s: %s", self._attr_unique_id, e
            )
