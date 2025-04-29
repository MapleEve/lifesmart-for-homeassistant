"""Support for LifeSmart sensors."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
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
        if device_type not in (
            OT_SENSOR_TYPES + GAS_SENSOR_TYPES + LOCK_TYPES + SMART_PLUG_TYPES
        ):
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
    if device_type in OT_SENSOR_TYPES and sub_key in {"Z", "V", "P3", "P4"}:
        return True
    if device_type in GAS_SENSOR_TYPES:
        return True
    if device_type in LOCK_TYPES and sub_key == "BAT":
        return True
    if device_type in COVER_TYPES and sub_key == "P8":
        return True
    if device_type in SMART_PLUG_TYPES and sub_key in {"P2", "P3"}:
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

        if device_type in GAS_SENSOR_TYPES:
            return SensorDeviceClass.GAS
        if sub_key == "BAT":
            return SensorDeviceClass.BATTERY
        if sub_key == "T" or (device_type in SMART_PLUG_TYPES and sub_key == "P1"):
            return SensorDeviceClass.TEMPERATURE
        if sub_key == "H" or (device_type in SMART_PLUG_TYPES and sub_key == "P2"):
            return SensorDeviceClass.HUMIDITY
        if sub_key == "Z":
            return SensorDeviceClass.ILLUMINANCE
        if device_type in SMART_PLUG_TYPES and sub_key == "P3":
            return SensorDeviceClass.POWER
        if device_type in SMART_PLUG_TYPES and sub_key == "P4":
            return SensorDeviceClass.ENERGY
        return None

    @callback
    def _determine_unit(self) -> str | None:
        """Map sub-device to unit."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]
        sub_key = self._sub_key

        if self.device_class == SensorDeviceClass.BATTERY:
            return PERCENTAGE
        if self.device_class == SensorDeviceClass.TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        if self.device_class == SensorDeviceClass.HUMIDITY:
            return PERCENTAGE
        if self.device_class == SensorDeviceClass.ILLUMINANCE:
            return LIGHT_LUX
        if device_type in SMART_PLUG_TYPES:
            if sub_key == "P2":
                return UnitOfEnergy.KILO_WATT_HOUR
            if sub_key == "P3":
                return UnitOfPower.WATT
        if sub_key == "P3":
            return CONCENTRATION_PARTS_PER_MILLION
        if sub_key == "P4":
            return CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER
        return None

    @callback
    def _extract_initial_value(self) -> float | int | None:
        """Extract initial value from device data."""
        return self._sub_data.get("v") or self._sub_data.get("val")

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
            via_device=(DOMAIN, self._raw_device[HUB_ID_KEY]),
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
        val = new_data.get("v") or new_data.get("val")
        if val is not None:
            self._attr_native_value = val
            self.async_write_ha_state()

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
