"""Support for LifeSmart switch by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    SUBDEVICE_INDEX_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    SMART_PLUG_TYPES,
    POWER_METER_PLUG_TYPES,
)
from .entity import LifeSmartEntity
from .helpers import generate_unique_id, get_switch_subdevices

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart switches from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    switches = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用helpers中的统一逻辑获取所有有效的开关子设备
        subdevice_keys = get_switch_subdevices(device)
        for sub_key in subdevice_keys:
            switches.append(
                LifeSmartSwitch(
                    device, sub_key, hub.get_client(), config_entry.entry_id
                )
            )

    async_add_entities(switches)


class LifeSmartSwitch(LifeSmartEntity, SwitchEntity):
    """LifeSmart switch entity with full state management."""

    _attr_has_entity_name = False

    def __init__(
        self,
        raw_device: dict[str, Any],
        sub_device_key: str,
        client: Any,
        entry_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._entry_id = entry_id

        self._sub_data = self._raw_device.get(DEVICE_DATA_KEY, {}).get(
            self._sub_key, {}
        )

        self._attr_unique_id = generate_unique_id(
            self.devtype, self.agt, self.me, sub_device_key
        )
        self._attr_name = self._generate_switch_name()
        self._attr_device_class = self._determine_device_class()
        self._attr_extra_state_attributes = {
            HUB_ID_KEY: self.agt,
            DEVICE_ID_KEY: self.me,
            SUBDEVICE_INDEX_KEY: self._sub_key,
        }
        self._attr_is_on = self._parse_state(self._sub_data)

    @callback
    def _generate_switch_name(self) -> str:
        """Generate user-friendly switch name."""
        base_name = self._name
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        return f"{base_name} {self._sub_key.upper()}"

    @callback
    def _determine_device_class(self) -> SwitchDeviceClass:
        """Determine device class for better UI representation."""
        if self.devtype in (SMART_PLUG_TYPES | POWER_METER_PLUG_TYPES):
            return SwitchDeviceClass.OUTLET
        return SwitchDeviceClass.SWITCH

    @callback
    def _parse_state(self, data: dict) -> bool:
        """Parse the on/off state from device data."""
        return data.get("type", 0) & 0x01 == 1

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link the entity to a single device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    @callback
    def _handle_update(self, new_data: dict) -> None:
        """Handle real-time updates from the WebSocket."""
        if new_data:
            self._attr_is_on = self._parse_state(new_data)
            self.async_write_ha_state()

    @callback
    def _handle_global_refresh(self) -> None:
        """Handle global data refresh to sync state."""
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (d for d in devices if d[DEVICE_ID_KEY] == self.me), None
            )
            if current_device:
                self._raw_device = current_device
                sub_data = current_device.get(DEVICE_DATA_KEY, {}).get(self._sub_key)
                if sub_data:
                    self._attr_is_on = self._parse_state(sub_data)
                    self.async_write_ha_state()
        except (KeyError, StopIteration):
            _LOGGER.warning(
                "Could not find device %s during global refresh.", self._attr_unique_id
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        result = await self._client.turn_on_light_switch_async(
            self._sub_key, self.agt, self.me
        )
        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        result = await self._client.turn_off_light_switch_async(
            self._sub_key, self.agt, self.me
        )
        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()
