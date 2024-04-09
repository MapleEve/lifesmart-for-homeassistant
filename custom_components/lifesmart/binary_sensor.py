"""Support for LifeSmart binary sensors."""
import datetime
import logging
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from homeassistant.helpers.entity import DeviceInfo
from .const import (
    BINARY_SENSOR_TYPES,
    DEVICE_DATA_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DOMAIN,
    GENERIC_CONTROLLER_TYPES,
    GUARD_SENSOR_TYPES,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    LOCK_TYPES,
    MANUFACTURER,
    MOTION_SENSOR_TYPES,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    ENTITY_ID_FORMAT,
)

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

        if device_type not in BINARY_SENSOR_TYPES + LOCK_TYPES:
            continue

        ha_device = LifeSmartDevice(
            device,
            client,
        )
        for sub_device_key in device[DEVICE_DATA_KEY]:
            sub_device_data = device[DEVICE_DATA_KEY][sub_device_key]
            if device_type in GENERIC_CONTROLLER_TYPES:
                if sub_device_key in [
                    "P5",
                    "P6",
                    "P7",
                ]:
                    sensor_devices.append(
                        LifeSmartBinarySensor(
                            ha_device,
                            device,
                            sub_device_key,
                            sub_device_data,
                            client,
                        )
                    )
            elif device_type in LOCK_TYPES and sub_device_key == "EVTLO":
                sensor_devices.append(
                    LifeSmartBinarySensor(
                        ha_device,
                        device,
                        sub_device_key,
                        sub_device_data,
                        client,
                    )
                )
            elif device_type in BINARY_SENSOR_TYPES and sub_device_key in [
                "M",
                "G",
                "B",
                "AXS",
                "P1",
            ]:
                sensor_devices.append(
                    LifeSmartBinarySensor(
                        ha_device,
                        device,
                        sub_device_key,
                        sub_device_data,
                        client,
                    )
                )
    async_add_entities(sensor_devices)


class LifeSmartBinarySensor(BinarySensorEntity):
    """Representation of LifeSmartBinarySensor."""

    def __init__(
        self, device, raw_device_data, sub_device_key, sub_device_data, client
    ) -> None:
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
        self.sensor_device_name = raw_device_data[DEVICE_NAME_KEY]
        self.device_name = device_name
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
        self._attrs = sub_device_data

        if device_type in GUARD_SENSOR_TYPES:
            if sub_device_key in ["G"]:
                self._device_class = BinarySensorDeviceClass.DOOR
                if sub_device_data["val"] == 0:
                    self._state = True
                else:
                    self._state = False
            if sub_device_key in ["AXS"]:
                self._device_class = BinarySensorDeviceClass.VIBRATION
                if sub_device_data["val"] == 0:
                    self._state = False
                else:
                    self._state = True
            if sub_device_key in ["B"]:
                self._device_class = None
                if sub_device_data["val"] == 0:
                    self._state = False
                else:
                    self._state = True
        elif device_type in MOTION_SENSOR_TYPES:
            self._device_class = BinarySensorDeviceClass.MOTION
            if sub_device_data["val"] == 0:
                self._state = False
            else:
                self._state = True
        elif device_type in LOCK_TYPES:
            self._device_class = BinarySensorDeviceClass.LOCK
            # On means open (unlocked), Off means closed (locked)
            val = sub_device_data["val"]
            unlock_method = val >> 12
            unlock_user = val & 0xFFF
            is_unlock_success = False
            if (
                sub_device_data["type"] % 2 == 1
                and unlock_user != 0
                and unlock_method != 15
            ):
                is_unlock_success = True
            if sub_device_data["type"] % 2 == 1:
                self._state = True
            else:
                self._state = False
            self._attrs = {
                "unlocking_method": unlock_method,
                "unlocking_user": unlock_user,
                "device_type": device_type,
                "unlocking_success": is_unlock_success,
            }
        elif device_type in GENERIC_CONTROLLER_TYPES:
            self._device_class = BinarySensorDeviceClass.LOCK
            # On means open (unlocked), Off means closed (locked)
            if sub_device_data["val"] == 0:
                self._state = True
            else:
                self._state = False
        else:
            self._device_class = BinarySensorDeviceClass.SMOKE
            if sub_device_data["val"] == 0:
                self._state = False
            else:
                self._state = True

    @property
    def name(self):
        """Name of the entity."""
        return self.device_name

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
    def is_on(self):
        """Return true if sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the class of binary sensor."""
        return self._device_class

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
                self._update_state,
            )
        )

    async def _update_state(self, data) -> None:
        if data is not None:
            if data["val"] == 0:
                self._state = True
            else:
                self._state = False
            self.schedule_update_ha_state()
