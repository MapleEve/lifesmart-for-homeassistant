"""Support for LifeSmart Covers by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, generate_unique_id
from .const import (
    ALL_COVER_TYPES,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    DEVICE_DATA_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_VERSION_KEY,
    DOMAIN,
    DOOYA_TYPES,
    GARAGE_DOOR_TYPES,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    MANUFACTURER,
    NON_POSITIONAL_COVER_CONFIG,
)

_LOGGER = logging.getLogger(__name__)


def _is_cover_subdevice(device_type: str, sub_key: str) -> bool:
    """Check if a sub-device is a valid cover control point."""
    if device_type in GARAGE_DOOR_TYPES:
        return sub_key in {"P2", "HS"}
    if device_type in DOOYA_TYPES:
        return sub_key == "P1"
    if device_type in NON_POSITIONAL_COVER_CONFIG:
        # For non-positional, any of its defined control keys is a valid sub-device
        config = NON_POSITIONAL_COVER_CONFIG[device_type]
        return sub_key in {config["open"], config["close"], config["stop"]}
    return False


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart covers from a config entry."""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices_str = config_entry.options.get(CONF_EXCLUDE_ITEMS, "")
    exclude_hubs_str = config_entry.options.get(CONF_EXCLUDE_AGTS, "")
    exclude_devices = {
        dev.strip() for dev in exclude_devices_str.split(",") if dev.strip()
    }
    exclude_hubs = {hub.strip() for hub in exclude_hubs_str.split(",") if hub.strip()}

    covers = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if device_type not in ALL_COVER_TYPES:
            continue

        device_data = device.get(DEVICE_DATA_KEY, {})
        for sub_key in device_data:
            if not _is_cover_subdevice(device_type, sub_key):
                continue

            # For non-positional covers, multiple keys might point to the same entity.
            # We only create one entity per device.
            # We use the 'open' key as the representative sub_key.
            if device_type in NON_POSITIONAL_COVER_CONFIG:
                rep_key = NON_POSITIONAL_COVER_CONFIG[device_type]["open"]
                if sub_key != rep_key:
                    continue

            if device_type in GARAGE_DOOR_TYPES or device_type in DOOYA_TYPES:
                covers.append(
                    LifeSmartPositionalCover(
                        raw_device=device,
                        client=client,
                        entry_id=entry_id,
                        sub_device_key=sub_key,
                    )
                )
            elif device_type in NON_POSITIONAL_COVER_CONFIG:
                covers.append(
                    LifeSmartNonPositionalCover(
                        raw_device=device,
                        client=client,
                        entry_id=entry_id,
                        sub_device_key=sub_key,
                    )
                )

    async_add_entities(covers)


class LifeSmartBaseCover(LifeSmartDevice, CoverEntity):
    """Base class for LifeSmart covers, mirroring LifeSmartBaseLight."""

    _attr_has_entity_name = False

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
    ) -> None:
        """Initialize the base cover."""
        super().__init__(raw_device, client)
        self._entry_id = entry_id
        self._sub_key = sub_device_key

        base_name = self._name
        sub_name_from_data = (
            raw_device.get(DEVICE_DATA_KEY, {})
            .get(self._sub_key, {})
            .get(DEVICE_NAME_KEY)
        )
        suffix = (
            sub_name_from_data
            if sub_name_from_data and sub_name_from_data != self._sub_key
            else self._sub_key.upper()
        )
        self._attr_name = f"{base_name} {suffix}"

        device_name_slug = self._name.lower().replace(" ", "_")
        sub_key_slug = self._sub_key.lower()
        self._attr_object_id = f"{device_name_slug}_{sub_key_slug}"

        self._attr_unique_id = generate_unique_id(
            self.devtype, self.agt, self.me, self._sub_key
        )

        self._sub_data = raw_device.get(DEVICE_DATA_KEY, {}).get(sub_device_key, {})
        self._initialize_state()

    @callback
    def _initialize_state(self) -> None:
        """Initialize state - to be implemented by subclasses."""
        raise NotImplementedError

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link entities to a single device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """Register update listeners."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, LIFESMART_SIGNAL_UPDATE_ENTITY, self._handle_global_refresh
            )
        )

    @callback
    def _handle_update(self, new_data: dict) -> None:
        """Handle real-time updates by re-initializing state."""
        if new_data:
            self._raw_device[DEVICE_DATA_KEY] = new_data
            self._initialize_state()
            self.async_write_ha_state()

    @callback
    def _handle_global_refresh(self) -> None:
        """Handle global refresh."""
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (d for d in devices if d[DEVICE_ID_KEY] == self.me), None
            )
            if current_device:
                self._raw_device = current_device
                self._initialize_state()
                self.async_write_ha_state()
        except (KeyError, StopIteration):
            _LOGGER.warning(
                "Could not find device %s during global refresh.", self._attr_unique_id
            )

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._client.open_cover_async(self.agt, self.me, self.devtype)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._client.close_cover_async(self.agt, self.me, self.devtype)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._client.stop_cover_async(self.agt, self.me, self.devtype)


class LifeSmartPositionalCover(LifeSmartBaseCover):
    """Represents a LifeSmart cover that supports positions."""

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
    ) -> None:
        """Initialize the positional cover."""
        super().__init__(raw_device, client, entry_id, sub_device_key)
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        self._attr_device_class = (
            CoverDeviceClass.GARAGE
            if self.devtype in GARAGE_DOOR_TYPES
            else CoverDeviceClass.CURTAIN
        )

    @callback
    def _initialize_state(self) -> None:
        """Parse and update the entity's state from device data."""
        status_data = self._raw_device.get(DEVICE_DATA_KEY, {}).get(self._sub_key, {})
        val = status_data.get("val", 0)
        self._attr_current_cover_position = val & 0x7F
        is_moving = status_data.get("type", 0) % 2 == 1
        is_opening_direction = val & 0x80 == 0x80

        self._attr_is_opening = is_moving and is_opening_direction
        self._attr_is_closing = is_moving and not is_opening_direction
        self._attr_is_closed = self.current_cover_position == 0

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover position."""
        position = kwargs[ATTR_POSITION]
        await self._client.set_cover_position_async(
            self.agt, self.me, position, self.devtype
        )


class LifeSmartNonPositionalCover(LifeSmartBaseCover):
    """Represents a LifeSmart cover that only supports open/close/stop."""

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
    ) -> None:
        """Initialize the non-positional cover."""
        super().__init__(raw_device, client, entry_id, sub_device_key)
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )
        self._attr_device_class = CoverDeviceClass.CURTAIN

    @callback
    def _initialize_state(self) -> None:
        """Parse and update the entity's state from device data."""
        self._attr_current_cover_position = None
        config = NON_POSITIONAL_COVER_CONFIG[self.devtype]
        data = self._raw_device.get(DEVICE_DATA_KEY, {})

        is_opening = data.get(config["open"], {}).get("type", 0) % 2 == 1
        is_closing = data.get(config["close"], {}).get("type", 0) % 2 == 1

        self._attr_is_opening = is_opening
        self._attr_is_closing = is_closing

        if not is_opening and not is_closing:
            if self._attr_is_closing:
                self._attr_is_closed = True
            else:
                self._attr_is_closed = False
        else:
            self._attr_is_closed = False
