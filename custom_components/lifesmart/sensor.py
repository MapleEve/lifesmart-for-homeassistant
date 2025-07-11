"""Support for LifeSmart sensors by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfSoundPressure,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, generate_entity_id
from .const import (
    COVER_TYPES,
    DEVICE_DATA_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DOMAIN,
    GAS_SENSOR_TYPES,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    LOCK_TYPES,
    MANUFACTURER,
    OT_SENSOR_TYPES,
    SMART_PLUG_TYPES,
    WATER_SENSOR_TYPES,
    NOISE_SENSOR_TYPES,
    POWER_METER_TYPES,
    DEFED_SENSOR_TYPES,
    EV_SENSOR_TYPES,
    ALL_SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart from a config entry."""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices = hass.data[DOMAIN][entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][entry_id]["exclude_hubs"]

    sensors = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        if device_type not in ALL_SENSOR_TYPES:
            continue

        ha_device = LifeSmartDevice(device, client)

        for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
            if not _is_sensor_subdevice(device_type, sub_key):
                continue

            sensors.append(
                LifeSmartSensor(
                    device=ha_device,
                    raw_device=device,
                    sub_device_key=sub_key,
                    sub_device_data=sub_data,
                    client=client,
                    entry_id=entry_id,
                )
            )

    async_add_entities(sensors)


def _is_sensor_subdevice(device_type: str, sub_key: str) -> bool:
    """Determine if a sub-device is a valid sensor."""
    # 环境感应器（包括温度、湿度、光照、电压）
    if device_type in OT_SENSOR_TYPES and sub_key in {"T", "H", "Z", "V", "P3", "P4"}:
        return True

    # 气体感应器
    if device_type in GAS_SENSOR_TYPES:
        return True

    # 门锁电量
    if device_type in LOCK_TYPES and sub_key == "BAT":
        return True

    # 窗帘位置
    if device_type in COVER_TYPES and sub_key == "P8":
        return True

    # 智能插座
    if device_type in SMART_PLUG_TYPES and sub_key in {"P1", "P2", "P3", "P4"}:
        return True

    # 噪音感应器
    if device_type in NOISE_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    # ELIQ电量计量器
    if device_type in POWER_METER_TYPES and sub_key in {"P1", "P2", "P3", "P4"}:
        return True

    # 云防系列传感器
    if device_type in DEFED_SENSOR_TYPES and sub_key in {"T", "V"}:
        return True

    # 水浸传感器（只保留电压）
    if device_type in WATER_SENSOR_TYPES and sub_key == "V":
        return True

    # 环境感应器（EV系列）
    if device_type in EV_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    return False


class LifeSmartSensor(SensorEntity):
    """LifeSmart sensor entity with enhanced compatibility."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: LifeSmartDevice,
        raw_device: dict[str, Any],
        sub_device_key: str,
        sub_device_data: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        self._device = device
        self._raw_device = raw_device
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._client = client
        self._entry_id = entry_id
        self._attr_unique_id = generate_entity_id(
            raw_device[DEVICE_TYPE_KEY],
            raw_device[HUB_ID_KEY],
            raw_device[DEVICE_ID_KEY],
            sub_device_key,
        )
        self._attr_name = self._generate_sensor_name()
        self._attr_device_class = self._determine_device_class()
        self._attr_native_unit_of_measurement = self._determine_unit()
        self._attr_native_value = self._extract_initial_value()
        self._attr_extra_state_attributes = self._get_extra_attributes()

    @callback
    def _generate_sensor_name(self) -> str | None:
        """Generate user-friendly sensor name."""
        base_name = self._raw_device.get(DEVICE_NAME_KEY, "Unknown Device")
        sub_key = self._sub_key.upper()
        return f"{base_name} {sub_key}"  # 生成传感器名称

    @callback
    def _determine_device_class(self) -> SensorDeviceClass | None:
        """Automatically determine device class based on sub-device."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]
        sub_key = self._sub_key

        # 气体传感器优先判断
        if device_type in GAS_SENSOR_TYPES:
            return SensorDeviceClass.GAS

        # 根据子设备键判断
        if sub_key == "BAT":
            return SensorDeviceClass.BATTERY
        if sub_key == "T":
            return SensorDeviceClass.TEMPERATURE
        if sub_key == "H":
            return SensorDeviceClass.HUMIDITY
        if sub_key == "Z":
            return SensorDeviceClass.ILLUMINANCE
        if sub_key == "V":
            return SensorDeviceClass.VOLTAGE

        # 智能插座特殊处理
        if device_type in SMART_PLUG_TYPES:
            if sub_key == "P1":
                return SensorDeviceClass.TEMPERATURE
            if sub_key == "P2":
                return SensorDeviceClass.HUMIDITY
            if sub_key == "P3":
                return SensorDeviceClass.POWER
            if sub_key == "P4":
                return SensorDeviceClass.ENERGY

        # OT传感器的P3/P4是气体浓度
        if device_type in OT_SENSOR_TYPES and sub_key in {"P3", "P4"}:
            return SensorDeviceClass.GAS

        # 噪音感应器
        if device_type in NOISE_SENSOR_TYPES:
            if sub_key == "P1":
                return SensorDeviceClass.SOUND_PRESSURE  # 噪音等级
            if sub_key == "P2":
                return None  # 可能是其他数据

        # ELIQ电量计量器
        if device_type in POWER_METER_TYPES:
            if sub_key in {"P1", "P3"}:
                return SensorDeviceClass.POWER
            if sub_key in {"P2", "P4"}:
                return SensorDeviceClass.ENERGY

        # 云防系列的温度传感器
        if device_type in DEFED_SENSOR_TYPES and sub_key == "T":
            return SensorDeviceClass.TEMPERATURE

        # 环境感应器（EV系列）
        if device_type in EV_SENSOR_TYPES:
            if sub_key == "P1":
                return SensorDeviceClass.TEMPERATURE
            if sub_key == "P2":
                return SensorDeviceClass.HUMIDITY

        return None

    @callback
    def _determine_unit(self) -> str | None:
        """Map sub-device to unit."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]
        sub_key = self._sub_key

        # 使用已确定的device_class来判断
        if self.device_class == SensorDeviceClass.BATTERY:
            return PERCENTAGE
        if self.device_class == SensorDeviceClass.TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        if self.device_class == SensorDeviceClass.HUMIDITY:
            return PERCENTAGE
        if self.device_class == SensorDeviceClass.ILLUMINANCE:
            return LIGHT_LUX
        if self.device_class == SensorDeviceClass.VOLTAGE:
            return UnitOfElectricPotential.VOLT

        # 特殊处理
        if device_type in SMART_PLUG_TYPES:
            if sub_key == "P3":
                return UnitOfPower.WATT
            if sub_key == "P4":
                return UnitOfEnergy.KILO_WATT_HOUR

        # OT传感器的气体浓度单位
        if device_type in OT_SENSOR_TYPES:
            if sub_key == "P3":
                return CONCENTRATION_PARTS_PER_MILLION
            if sub_key == "P4":
                return CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER

        # 噪音传感器单位
        if device_type in NOISE_SENSOR_TYPES and sub_key == "P1":
            return UnitOfSoundPressure.DECIBEL

        # ELIQ电量计量器单位
        if device_type in POWER_METER_TYPES:
            if sub_key in {"P1", "P3"}:
                return UnitOfPower.WATT
            if sub_key in {"P2", "P4"}:
                return UnitOfEnergy.KILO_WATT_HOUR

        return None

    @callback
    def _extract_initial_value(self) -> float | int | None:
        """Extract initial value from device data."""
        # 优先使用友好值
        value = self._sub_data.get("v")
        if value is not None:
            return value

        # 使用原始值并进行必要的转换
        raw_value = self._sub_data.get("val")
        if raw_value is not None:
            return self._convert_raw_value(raw_value)

        return None

    @callback
    def _convert_raw_value(self, raw_value: int) -> float | int:
        """Convert raw value to actual value based on device type."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]

        # 温度值通常需要除以10
        if (
            self._sub_key in {"T", "P1"}
            and self.device_class == SensorDeviceClass.TEMPERATURE
        ):
            return raw_value / 10.0

        # 湿度值需要除以10
        if (
            self._sub_key in {"H", "P2"}
            and self.device_class == SensorDeviceClass.HUMIDITY
        ):
            return raw_value / 10.0

        # CO2传感器的P1(温度)和P2(湿度)也需要除以10
        if device_type in EV_SENSOR_TYPES:
            if self._sub_key == "P1":  # 温度
                return raw_value / 10.0
            if self._sub_key == "P2":  # 湿度
                return raw_value / 10.0

        # 电量百分比值直接使用
        if self._sub_key in {"BAT", "V", "P4", "P5"}:
            return raw_value

        # 其他值直接返回
        return raw_value

    @callback
    def _get_extra_attributes(self) -> dict[str, Any] | None:
        """Get extra state attributes."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]

        # CO2传感器的空气质量等级
        if device_type == "SL_SC_CA" and self._sub_key == "P3":
            val = self._sub_data.get("val", 0)
            return {"air_quality": val}

        # 水浸传感器的导电率等级
        if device_type in WATER_SENSOR_TYPES and self._sub_key == "WA":
            val = self._sub_data.get("val", 0)
            return {"conductivity_level": val}

        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY])
            },
            name=self._raw_device[DEVICE_NAME_KEY],
            manufacturer=MANUFACTURER,
            model=self._raw_device[DEVICE_TYPE_KEY],
            sw_version=self._raw_device.get("ver", "unknown"),  # 添加版本信息
            via_device=(
                (DOMAIN, self._raw_device[HUB_ID_KEY])
                if self._raw_device[HUB_ID_KEY]
                else None
            ),
        )

    async def async_added_to_hass(self) -> None:
        """Register update listeners."""
        # 实时更新事件
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self.unique_id}",
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

    async def _handle_update(self, new_data: dict) -> None:
        """Handle real-time updates."""
        try:
            # 处理WebSocket推送的数据格式
            if "msg" in new_data:
                sub_data = new_data.get("msg", {}).get(self._sub_key, {})
                val = sub_data.get("v") or sub_data.get("val")
            else:
                val = new_data.get("v") or new_data.get("val")

            if val is not None:
                self._attr_native_value = (
                    self._convert_raw_value(val) if "v" not in new_data else val
                )
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self.entity_id, e)

    async def _handle_global_refresh(self) -> None:
        """Handle periodic full data refresh."""
        # 从hass.data获取最新设备列表
        devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
        # 查找当前设备
        current_device = next(
            (
                d
                for d in devices
                if d[HUB_ID_KEY] == self._raw_device[HUB_ID_KEY]
                and d[DEVICE_ID_KEY] == self._raw_device[DEVICE_ID_KEY]
            ),
            None,
        )
        if current_device is None:
            _LOGGER.warning(
                "LifeSmartSensor: Device not found during global refresh: %s",
                self.unique_id,
            )
            return

        sub_data = current_device.get(DEVICE_DATA_KEY, {}).get(self._sub_key, {})
        val = sub_data.get("v") or sub_data.get("val")
        if val is not None:
            self._attr_native_value = val
            self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "LifeSmartSensor: No value found for sub-device '%s' during global refresh",
                self._sub_key,
            )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self._attr_native_value
