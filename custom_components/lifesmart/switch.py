import subprocess
import urllib.request
import json
import time
import hashlib
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from . import LifeSmartDevice, generate_entity_id

from .const import (
    DEVICE_DATA_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DOMAIN,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    MANUFACTURER,
    SMART_PLUG_TYPES,
    SPOT_TYPES,
    SUPPORTED_SUB_SWITCH_TYPES,
    SUPPORTED_SWTICH_TYPES,
)

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    ENTITY_ID_FORMAT,
)

_LOGGER = logging.getLogger(__name__)

CON_AI_TYPE_SCENE = "scene"
CON_AI_TYPE_AIB = "aib"
CON_AI_TYPE_GROUP = "grouphw"
CON_AI_TYPES = [
    CON_AI_TYPE_SCENE,
    CON_AI_TYPE_AIB,
    CON_AI_TYPE_GROUP,
]
AI_TYPES = ["ai"]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup Switch entities."""
    devices = hass.data[DOMAIN][config_entry.entry_id]["devices"]
    exclude_devices = hass.data[DOMAIN][config_entry.entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][config_entry.entry_id]["exclude_hubs"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    switch_devices = []
    for device in devices:
        if (
                device[DEVICE_ID_KEY] in exclude_devices
                or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        if device_type in SUPPORTED_SWTICH_TYPES + SMART_PLUG_TYPES + SPOT_TYPES:
            ha_device = LifeSmartDevice(
                device,
                client,
            )

            if device_type in AI_TYPES:
                switch_devices.append(LifeSmartSceneSwitch(ha_device, device, client))
            elif device_type in SMART_PLUG_TYPES:
                sub_device_key = "P1"
                switch_devices.append(
                    LifeSmartSwitch(
                        ha_device,
                        device,
                        sub_device_key,
                        device[DEVICE_DATA_KEY][sub_device_key],
                        client,
                    )
                )
            elif device_type in SPOT_TYPES:
                sub_device_key = "RGB"
            else:
                for sub_device_key in device[DEVICE_DATA_KEY]:
                    if sub_device_key in SUPPORTED_SUB_SWITCH_TYPES:
                        switch_devices.append(
                            LifeSmartSwitch(
                                ha_device,
                                device,
                                sub_device_key,
                                device[DEVICE_DATA_KEY][sub_device_key],
                                client,
                            )
                        )
    async_add_entities(switch_devices)


class LifeSmartSwitch(SwitchEntity):
    def __init__(
            self, device, raw_device_data, sub_device_key, sub_device_data, client
    ) -> None:
        """Initialize the switch."""

        device_name = raw_device_data[DEVICE_NAME_KEY]
        device_type = raw_device_data[DEVICE_TYPE_KEY]
        hub_id = raw_device_data[HUB_ID_KEY]
        device_id = raw_device_data[DEVICE_ID_KEY]

        if DEVICE_NAME_KEY in sub_device_data:
            device_name = sub_device_data[DEVICE_NAME_KEY]
        else:
            device_name = ""

        self._attr_has_entity_name = True
        self.device_name = device_name
        self.switch_name = raw_device_data[DEVICE_NAME_KEY]
        self.device_id = device_id
        self.hub_id = hub_id
        self.sub_device_key = sub_device_key
        self.device_type = device_type
        self.raw_device_data = raw_device_data
        self._device = device
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self.entity_id = generate_entity_id(
            device_type, hub_id, device_id, sub_device_key
        )
        self._client = client

        if sub_device_data["type"] % 2 == 1:
            self._state = True
        else:
            self._state = False

        super().__init__()

    @property
    def name(self):
        """Name of the entity."""
        return self.device_name

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.hub_id, self.device_id)},
            name=self.switch_name,
            manufacturer=MANUFACTURER,
            model=self.device_type,
            sw_version=self.raw_device_data["ver"],
            via_device=(DOMAIN, self.hub_id),
        )

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
            if data["type"] % 2 == 1:
                self._state = True
            else:
                self._state = False
            self.schedule_update_ha_state()

    def _get_state(self):
        """get lifesmart switch state."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        if (
                await self._client.turn_on_light_swith_async(
                    self.sub_device_key, self.hub_id, self.device_id
                )
                == 0
        ):
            self._state = True
            self.async_schedule_update_ha_state()
        else:
            _LOGGER.warning("Switch {self._me} - {self._idx} status changed failed")

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        if (
                await self._client.turn_off_light_swith_async(
                    self.sub_device_key, self.hub_id, self.device_id
                )
                == 0
        ):
            self._state = False
            self.async_schedule_update_ha_state()
        else:
            _LOGGER.warning("Switch {self._me} - {self._idx} status changed failed")

    @property
    def unique_id(self):
        """A unique identifier for this entity."""
        return self.entity_id


class LifeSmartSceneSwitch(LifeSmartDevice, SwitchEntity):
    def __init__(self, device, raw_device_data, client) -> None:
        """Initialize the switch."""
        device_name = raw_device_data[DEVICE_NAME_KEY]
        device_type = raw_device_data[DEVICE_TYPE_KEY]
        hub_id = raw_device_data[HUB_ID_KEY]
        device_id = raw_device_data[DEVICE_ID_KEY]

        self._device = device

        self._name = raw_device_data[DEVICE_NAME_KEY]

        self.entity_id = generate_entity_id(device_type, hub_id, device_id)
        self.hub_id = raw_device_data[HUB_ID_KEY]

        self._state = False
        super().__init__()

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.hub_id, self.device_id)
            },
            name=self.switch_name,
            manufacturer=MANUFACTURER,
            model=self.device_type,
            # sw_version=self.light.swversion,
            via_device=(DOMAIN, self.hub_id),
        )

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""

    def _get_state(self):
        """get lifesmart switch state."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Set scene."""
        if await super().async_lifesmart_sceneset(self, None, None) == 0:
            self._state = True
            self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """TODO: 手动关闭场景吗？"""
        self._state = False
        self.async_schedule_update_ha_state()

    @property
    def unique_id(self):
        """A unique identifier for this entity."""
        return self.entity_id
