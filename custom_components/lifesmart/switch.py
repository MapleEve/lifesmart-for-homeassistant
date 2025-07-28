"""Support for LifeSmart switch by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, generate_unique_id
from .const import (
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    SUBDEVICE_INDEX_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    CONF_EXCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    ALL_SWITCH_TYPES,
    SMART_PLUG_TYPES,
    POWER_METER_PLUG_TYPES,
    GARAGE_DOOR_TYPES,
    SUPPORTED_SWITCH_TYPES,
    GENERIC_CONTROLLER_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart switches from a config entry."""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices_str = config_entry.options.get(CONF_EXCLUDE_ITEMS, "")
    exclude_hubs_str = config_entry.options.get(CONF_EXCLUDE_AGTS, "")
    exclude_devices = {
        dev.strip() for dev in exclude_devices_str.split(",") if dev.strip()
    }
    exclude_hubs = {hub.strip() for hub in exclude_hubs_str.split(",") if hub.strip()}

    switches = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        device_data = device.get(DEVICE_DATA_KEY, {})

        if device_type not in ALL_SWITCH_TYPES:
            continue

        # 特殊处理：通用控制器 (SL_P)
        if device_type in GENERIC_CONTROLLER_TYPES:
            p1_val = device_data.get("P1", {}).get("val", 0)
            work_mode = (p1_val >> 24) & 0xE
            # 只有在三路开关模式下，P2/P3/P4 才是开关
            if work_mode in {8, 10}:
                for sub_key in ("P2", "P3", "P4"):
                    if sub_key in device_data:
                        switches.append(
                            LifeSmartSwitch(device, sub_key, client, entry_id)
                        )
            continue  # 处理完通用控制器后跳过，避免进入下面的通用逻辑

        # 特殊处理：超能面板 (SL_NATURE)
        if device_type == "SL_NATURE":
            p5_val = device_data.get("P5", {}).get("val", 1) & 0xFF
            if p5_val != 1:  # 仅处理开关版
                continue

        # 其他所有开关设备
        for sub_key in device_data:
            if _is_switch_subdevice(device_type, sub_key):
                switches.append(LifeSmartSwitch(device, sub_key, client, entry_id))

    async_add_entities(switches)


def _is_switch_subdevice(device_type: str, sub_key: str) -> bool:
    """
    Determine if a sub-device is a valid switch based on device type.
    NOTE: This function does NOT handle GENERIC_CONTROLLER_TYPES, as their
    logic is handled dynamically within async_setup_entry.
    """
    sub_key_upper = sub_key.upper()

    if device_type == "SL_P_SW":
        return sub_key_upper in {f"P{i}" for i in range(1, 10)}

    if device_type in GARAGE_DOOR_TYPES:
        return False
    if device_type == "SL_SC_BB_V2":
        return False
    if device_type in SUPPORTED_SWITCH_TYPES and sub_key_upper == "P4":
        return False

    if device_type in SMART_PLUG_TYPES:
        return sub_key_upper == "O"

    if device_type in POWER_METER_PLUG_TYPES:
        return sub_key_upper in {"P1", "P4"}

    if sub_key_upper in {"L1", "L2", "L3", "P1", "P2", "P3"}:
        return True

    return False


class LifeSmartSwitch(LifeSmartDevice, SwitchEntity):
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
