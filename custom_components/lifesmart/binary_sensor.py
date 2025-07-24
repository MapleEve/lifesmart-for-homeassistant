"""Support for LifeSmart binary sensors by @MapleEve"""

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
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    UNLOCK_METHOD,
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
    exclude_devices = hass.data[DOMAIN][entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][entry_id]["exclude_hubs"]
    client = hass.data[DOMAIN][entry_id]["client"]

    binary_sensors = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]

        if device_type not in ALL_BINARY_SENSOR_TYPES:
            continue

        for sub_device_key in device[DEVICE_DATA_KEY]:
            sub_device_data = device[DEVICE_DATA_KEY][sub_device_key]

            if not _is_binary_sensor_subdevice(device_type, sub_device_key):
                continue

            binary_sensors.append(
                LifeSmartBinarySensor(
                    raw_device=device,
                    sub_device_key=sub_device_key,
                    sub_device_data=sub_device_data,
                    client=client,
                    entry_id=entry_id,
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

    # 通用控制器
    if device_type in GENERIC_CONTROLLER_TYPES and sub_key in {
        "P2",
        "P3",
        "P4",
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

    _attr_has_entity_name = False

    def __init__(
        self,
        raw_device: dict[str, Any],
        sub_device_key: str,
        sub_device_data: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        self._attr_name = self._generate_sensor_name()
        self._attr_unique_id = generate_unique_id(
            self.devtype, self.agt, self.me, sub_device_key
        )

        # 初始化设备类别和状态
        device_class = self._determine_device_class()
        if device_class:
            self._attr_device_class = device_class
        self._attr_is_on = self._parse_initial_state()
        self._attrs = self._get_initial_attributes()

    @callback
    def _generate_sensor_name(self) -> str:
        """
        Generate a user-friendly name for the binary sensor.

        The naming strategy combines the base device name with the sub-device name or key:
        - If the sub-device has a specific name (and it differs from the sub-device key),
          the name is formatted as "{base_name} {sub_name}".
        - Otherwise, the name is formatted as "{base_name} {sub_key.upper()}".

        Parameters:
        - self._raw_device: A dictionary containing the raw device data, including the base name.
        - self._sub_data: A dictionary containing the sub-device data, including the sub-device name.
        - self._sub_key: A string representing the sub-device key (e.g., an I/O port index).

        Returns:
        - A string representing the user-friendly name of the sensor.

        Examples:
        - Base name: "Living Room Sensor", Sub-device name: "Motion Detector"
          -> "Living Room Sensor Motion Detector"
        - Base name: "Living Room Sensor", Sub-device key: "io1"
          -> "Living Room Sensor IO1"
        """
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} {self._sub_key.upper()}"

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
    def _parse_initial_state(self, data: dict | None = None) -> bool:
        """Parse the state based on device type and sub-device data."""
        source_data = data if data is not None else self._sub_data
        device_type = self.devtype
        sub_key = self._sub_key
        val = source_data.get("val", 0)
        type_val = source_data.get("type", 0)

        # 门窗感应器特殊处理
        if device_type in GUARD_SENSOR_TYPES:
            if sub_key == "G":
                return val == 0  # 门窗传感器：0=开，1=关
            else:
                return val != 0  # 其他传感器：非0=触发

        # 云防系列设备特殊处理
        if device_type in DEFED_SENSOR_TYPES:
            # 所有云防设备都应使用 type 判断
            return type_val % 2 == 1

        # 动态感应器
        if device_type in MOTION_SENSOR_TYPES:
            return val != 0

        # 门锁事件
        if device_type in LOCK_TYPES and sub_key == "EVTLO":
            return self._parse_lock_event()

        # 门锁报警
        if device_type in LOCK_TYPES and sub_key == "ALM":
            return val > 0

        # 通用控制器
        if device_type in GENERIC_CONTROLLER_TYPES:
            return val == 0  # 0=开，1=关

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

        # SL_SC_BB_V2 的状态是瞬时的, 默认为 off
        if device_type == "SL_SC_BB_V2":
            return False  # 初始状态总是 off

        if device_type in CLIMATE_TYPES:
            if sub_key == "P5":  # 温控阀门告警 (val 是 bitmask)
                return val > 0
            # 其他所有温控器的附属开关/阀门都遵循 type%2==1 为开启的规则
            return type_val % 2 == 1

        # 其他传感器默认处理
        return val != 0

    @callback
    def _parse_lock_event(self) -> bool:
        """Parse lock event state."""
        val = self._sub_data.get("val", 0)
        unlock_type = self._sub_data.get("type", 0)
        unlock_user = val & 0xFFF

        if val == 0:
            return False

        return unlock_type & 0x01 == 1 and unlock_user != 0 and val >> 12 != 15

    @callback
    def _get_initial_attributes(self, data: dict | None = None) -> dict[str, Any]:
        """Get attributes for the sensor."""
        source_data = data if data is not None else self._sub_data
        device_type = self.devtype
        sub_key = self._sub_key

        # 门锁事件的特殊属性
        if device_type in LOCK_TYPES and sub_key == "EVTLO":
            val = source_data.get("val", 0)
            unlock_method = UNLOCK_METHOD.get(val >> 12, "Unknown")
            unlock_user = val & 0xFFF

            return {
                "unlocking_method": unlock_method,
                "unlocking_user": unlock_user,
                "device_type": device_type,
                "unlocking_success": self._attr_is_on,
                "last_updated": datetime.datetime.fromtimestamp(
                    source_data.get("valts", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }

        # 门锁报警的属性
        if device_type in LOCK_TYPES and sub_key == "ALM":
            return {"alarm_type": source_data.get("val", 0)}

        # 水浸传感器的属性
        if device_type in WATER_SENSOR_TYPES and sub_key == "WA":
            val = source_data.get("val", 0)
            return {"conductivity_level": val, "water_detected": val != 0}

        # SL_SC_BB_V2 初始化事件属性
        if device_type == "SL_SC_BB_V2":
            return {
                "last_event": None,
                "last_event_time": None,
            }

        # 为温控阀门的告警传感器添加详细属性
        if device_type == "SL_CP_VL" and sub_key == "P5":
            val = source_data.get("val", 0)
            return {
                "high_temp_protection": bool(val & 0b1),
                "low_temp_protection": bool(val & 0b10),
                "internal_sensor_fault": bool(val & 0b100),
                "external_sensor_fault": bool(val & 0b1000),
                "low_battery": bool(val & 0b10000),
                "device_offline": bool(val & 0b100000),
            }
        # 默认返回原始数据
        return dict(source_data)

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

            # 处理WebSocket推送的数据格式
            if "msg" in data:
                sub_data = data.get("msg", {}).get(self._sub_key, {})
                val = sub_data.get("val")
            else:
                val = data.get("val")

            if val is None:
                return

            # 根据设备类型更新状态
            self._update_state_by_device_type(data)
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self._attr_unique_id, e)

    @callback
    def _update_state_by_device_type(self, data: dict) -> None:
        """Update state based on device type."""
        device_type = self.devtype
        sub_key = self._sub_key
        val = data.get("val", 0)
        type_val = data.get("type", 0)  # 获取 type 值

        if device_type in LOCK_TYPES and sub_key == "EVTLO":
            self._update_lock_event_state(data)
        elif device_type in MOTION_SENSOR_TYPES:
            self._attr_is_on = val != 0
        elif device_type in DEFED_SENSOR_TYPES:
            # 所有云防设备都应使用 type 判断
            self._attr_is_on = type_val % 2 == 1
        elif device_type in GUARD_SENSOR_TYPES and sub_key == "G":
            self._attr_is_on = val == 0
        elif device_type in WATER_SENSOR_TYPES and sub_key == "WA":
            self._attr_is_on = val != 0
            # 更新水浸传感器属性
            self._attrs.update({"conductivity_level": val, "water_detected": val != 0})
        elif device_type in SMOKE_SENSOR_TYPES and sub_key == "P1":
            self._attr_is_on = val != 0
        elif device_type in RADAR_SENSOR_TYPES and sub_key == "P1":
            self._attr_is_on = val != 0
        elif device_type == "SL_SC_BB_V2":  # 特殊处理 SL_SC_BB_V2 的事件更新
            type_val = data.get("type", 0)
            if type_val % 2 == 1:  # 事件发生
                self._attr_is_on = True
                val = data.get("val", 0)
                event_map = {1: "single_click", 2: "double_click", 255: "long_press"}
                event = event_map.get(val, "unknown")

                self._attrs["last_event"] = event
                self._attrs["last_event_time"] = dt_util.utcnow().isoformat()

                # 触发后立即安排一个任务来将其状态重置为 off
                async def reset_state():
                    await asyncio.sleep(0.5)  # 保持 on 状态 0.5 秒
                    self._attr_is_on = False
                    self.async_write_ha_state()

                self.hass.loop.create_task(reset_state())
            else:  # 事件消失
                self._attr_is_on = False
        elif device_type in CLIMATE_TYPES:
            self._attr_is_on = self._parse_initial_state(data)
            if device_type == "SL_CP_VL" and sub_key == "P5":
                self._attrs = self._get_initial_attributes(data)
            self.async_write_ha_state()
        else:
            self._attr_is_on = val != 0

    @callback
    def _update_lock_event_state(self, data: dict) -> None:
        """Update lock event state and attributes."""
        val = data.get("val", 0)
        unlock_type = data.get("type", 0)

        if val == 0:
            self._attr_is_on = False
        else:
            unlock_user = val & 0xFFF
            self._attr_is_on = (
                unlock_type & 0x01 == 1 and unlock_user != 0 and val >> 12 != 15
            )

        # 更新属性
        self._attrs.update(
            {
                "unlocking_method": UNLOCK_METHOD.get(val >> 12, "Unknown"),
                "unlocking_user": val & 0xFFF,
                "device_type": self.devtype,
                "unlocking_success": self._attr_is_on,
                "last_updated": datetime.datetime.fromtimestamp(
                    data.get("ts", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

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

            if current_device is None:
                _LOGGER.warning(
                    "LifeSmartBinarySensor: Device not found during global refresh: %s",
                    self._attr_unique_id,
                )
                return

            sub_data = current_device.get(DEVICE_DATA_KEY, {}).get(self._sub_key, {})
            if not sub_data:
                _LOGGER.debug(
                    "LifeSmartBinarySensor: No sub-device data found for '%s' during global refresh",
                    self._sub_key,
                )
                return

            # 更新状态
            self._update_state_by_device_type(sub_data)
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during global refresh for %s: %s", self._attr_unique_id, e
            )
