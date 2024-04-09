"""Support for lifesmart sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from .const import (
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


# DOMAIN = "sensor"
# ENTITY_ID_FORMAT = DOMAIN + ".{}"

from . import LifeSmartDevice, generate_entity_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup Switch entities."""
    devices = hass.data[DOMAIN][config_entry.entry_id]["devices"]
    exclude_devices = hass.data[DOMAIN][config_entry.entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][config_entry.entry_id]["exclude_hubs"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    sensor_devices = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        supported_sensors = (
            OT_SENSOR_TYPES + GAS_SENSOR_TYPES + LOCK_TYPES + SMART_PLUG_TYPES
        )

        if device_type not in supported_sensors:
            continue

        ha_device = LifeSmartDevice(
            device,
            client,
        )
        for sub_device_key in device[DEVICE_DATA_KEY]:
            sub_device_data = device[DEVICE_DATA_KEY][sub_device_key]
            if device_type in OT_SENSOR_TYPES and sub_device_key in [
                "Z",
                "V",
                "P3",
                "P4",
            ]:
                sensor_devices.append(
                    LifeSmartSensor(
                        ha_device,
                        device,
                        sub_device_key,
                        sub_device_data,
                        client,
                    )
                )
            elif device_type in GAS_SENSOR_TYPES:
                sensor_devices.append(
                    LifeSmartSensor(
                        ha_device,
                        device,
                        sub_device_key,
                        sub_device_data,
                        client,
                    )
                )
            elif device_type in LOCK_TYPES and sub_device_key in ["BAT"]:
                sensor_devices.append(
                    LifeSmartSensor(
                        ha_device,
                        device,
                        sub_device_key,
                        sub_device_data,
                        client,
                    )
                )
            elif device_type in SMART_PLUG_TYPES and sub_device_key in ["P2", "P3"]:
                sensor_devices.append(
                    LifeSmartSensor(
                        ha_device,
                        device,
                        sub_device_key,
                        sub_device_data,
                        client,
                    )
                )
    async_add_entities(sensor_devices)


class LifeSmartSensor(SensorEntity):
    """Representation of a LifeSmartSensor."""

    # def __init__(self, dev, idx, val, param) -> None:
    def __init__(
        self, device, raw_device_data, sub_device_key, sub_device_data, client
    ) -> None:
        """Initialize the LifeSmartSensor."""

        super().__init__()

        device_name = raw_device_data[DEVICE_NAME_KEY]
        device_type = raw_device_data[DEVICE_TYPE_KEY]
        hub_id = raw_device_data[HUB_ID_KEY]
        device_id = raw_device_data[DEVICE_ID_KEY]

        if (
            DEVICE_NAME_KEY in sub_device_data
            and sub_device_data[DEVICE_NAME_KEY] != "none"
        ):
            device_name = sub_device_data[DEVICE_NAME_KEY]
        else:
            device_name = ""

        self._attr_has_entity_name = True
        self.device_name = device_name
        self.sensor_device_name = raw_device_data[DEVICE_NAME_KEY]
        self.device_id = device_id
        self.hub_id = hub_id
        self.sub_device_key = sub_device_key
        self.device_type = device_type
        self.raw_device_data = raw_device_data
        self._device = device
        self.entity_id = generate_entity_id(
            device_type, hub_id, device_id, sub_device_key
        )
        self._client = client

        # devtype = raw_device_data["devtype"]
        if device_type in GAS_SENSOR_TYPES:
            self._device_class = SensorDeviceClass.GAS
            self._unit = "None"
            self._state = sub_device_data["val"]
        elif device_type in SMART_PLUG_TYPES and sub_device_key == "P2":
            self._device_class = SensorDeviceClass.ENERGY
            self._unit = "kWh"
            self._state = sub_device_data["v"]
        elif device_type in SMART_PLUG_TYPES and sub_device_key == "P3":
            self._device_class = SensorDeviceClass.POWER
            self._unit = "W"
            self._state = sub_device_data["v"]
        else:
            if sub_device_key == "T" or sub_device_key == "P1":
                self._device_class = SensorDeviceClass.TEMPERATURE
                self._unit = UnitOfTemperature.CELSIUS
            elif sub_device_key == "H" or sub_device_key == "P2":
                self._device_class = SensorDeviceClass.HUMIDITY
                self._unit = "%"
            elif sub_device_key == "Z":
                self._device_class = SensorDeviceClass.ILLUMINANCE
                self._unit = "lx"
            elif sub_device_key == "V":
                self._device_class = SensorDeviceClass.BATTERY
                self._unit = "%"
            elif sub_device_key == "P3":
                self._device_class = "None"
                self._unit = "ppm"
            elif sub_device_key == "P4":
                self._device_class = "None"
                self._unit = "mg/m3"
            elif sub_device_key == "BAT":
                self._device_class = SensorDeviceClass.BATTERY
                self._unit = "%"
            else:
                self._unit = "None"
                self._device_class = "None"
            self._state = sub_device_data["v"]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.hub_id, self.device_id)},
            name=self.sensor_device_name,
            manufacturer=MANUFACTURER,
            model=self.device_type,
            sw_version=self.raw_device_data["ver"],
            via_device=(DOMAIN, self.hub_id),
        )

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return self._device_class

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unique_id(self):
        """A unique identifier for this entity."""
        return self.entity_id

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self.entity_id}",
                self._update_value,
            )
        )

    async def _update_value(self, data) -> None:
        if data is not None:
            self._state = data["v"]
            self.schedule_update_ha_state()
