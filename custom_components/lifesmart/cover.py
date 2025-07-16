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

from . import generate_entity_id
from .const import (
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    NON_POSITIONAL_COVER_CONFIG,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    ALL_COVER_TYPES,
    GARAGE_DOOR_TYPES,
    DOOYA_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart covers from a config entry, following the standard pattern."""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices = hass.data[DOMAIN][entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][entry_id]["exclude_hubs"]

    covers = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        if device_type in ALL_COVER_TYPES:
            covers.append(
                LifeSmartCover(
                    raw_device=device,
                    client=client,
                    entry_id=entry_id,
                )
            )

    async_add_entities(covers)


class LifeSmartCover(CoverEntity):
    """LifeSmart cover entity with full state management."""

    _attr_has_entity_name = True

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """Initialize the cover."""
        self._raw_device = raw_device
        self._client = client
        self._entry_id = entry_id
        self.device_type = raw_device[DEVICE_TYPE_KEY]
        self._hub_id = raw_device[HUB_ID_KEY]
        self._device_id = raw_device[DEVICE_ID_KEY]

        self._attr_unique_id = generate_entity_id(
            self.device_type, self._hub_id, self._device_id, "cover"
        )
        self._attr_name = raw_device.get(DEVICE_NAME_KEY, "Unknown Cover")

        self._initialize_features()
        self._update_state(raw_device.get(DEVICE_DATA_KEY, {}))

    @callback
    def _initialize_features(self) -> None:
        """Initialize features based on device type using constants."""
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )
        self._attr_device_class = (
            CoverDeviceClass.GARAGE
            if self.device_type in GARAGE_DOOR_TYPES
            else CoverDeviceClass.CURTAIN
        )
        if self.device_type in DOOYA_TYPES or self.device_type in GARAGE_DOOR_TYPES:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION

    @callback
    def _update_state(self, data: dict) -> None:
        """Parse and update the entity's state from device data."""
        # --- 位置型设备 ---
        if self.device_type in GARAGE_DOOR_TYPES or self.device_type in DOOYA_TYPES:
            status_data = data.get(
                "P2" if self.device_type in GARAGE_DOOR_TYPES else "P1", {}
            )
            val = status_data.get("val", 0)
            self._attr_current_cover_position = val & 0x7F
            is_moving = status_data.get("type", 0) % 2 == 1
            is_opening_direction = val & 0x80 == 0x80

            self._attr_is_opening = is_moving and is_opening_direction
            self._attr_is_closing = is_moving and not is_opening_direction
            self._attr_is_closed = self.current_cover_position == 0

        # --- 命令型设备 ---
        elif self.device_type in NON_POSITIONAL_COVER_CONFIG:
            self._attr_current_cover_position = None
            config = NON_POSITIONAL_COVER_CONFIG[self.device_type]

            is_opening = data.get(config["open"], {}).get("type", 0) % 2 == 1
            is_closing = data.get(config["close"], {}).get("type", 0) % 2 == 1

            self._attr_is_opening = is_opening
            self._attr_is_closing = is_closing

            # 只有在明确收到“关闭”信号后停止，我们才乐观地认为它是关闭的。
            # 在其他情况下（如打开后停止），我们认为它是打开的（is_closed = False）。
            if not is_opening and not is_closing:
                # 如果上一个动作是关闭，现在停止了，我们假设它关闭了
                if self._attr_is_closing:
                    self._attr_is_closed = True
                else:  # 否则，我们假设它是打开的（或部分打开）
                    self._attr_is_closed = False
            else:
                # 只要在移动，就不是关闭状态
                self._attr_is_closed = False
        else:
            # 未知设备类型，采取最保守的状态
            self._attr_is_opening = False
            self._attr_is_closing = False
            self._attr_is_closed = None  # 状态未知
            self._attr_current_cover_position = None

        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._hub_id, self._device_id)},
            name=self._raw_device[DEVICE_NAME_KEY],
            manufacturer=MANUFACTURER,
            model=self.device_type,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self._hub_id),
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self.unique_id}",
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
        if new_data:
            self._update_state(new_data)

    @callback
    def _handle_global_refresh(self) -> None:
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (d for d in devices if d[DEVICE_ID_KEY] == self._device_id), None
            )
            if current_device:
                self._update_state(current_device.get(DEVICE_DATA_KEY, {}))
        except (KeyError, StopIteration):
            _LOGGER.warning(
                "Could not find device %s during global refresh.", self.unique_id
            )

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._client.open_cover_async(
            self._hub_id, self._device_id, self.device_type
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._client.close_cover_async(
            self._hub_id, self._device_id, self.device_type
        )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._client.stop_cover_async(
            self._hub_id, self._device_id, self.device_type
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position = kwargs[ATTR_POSITION]
        await self._client.set_cover_position_async(
            self._hub_id, self._device_id, position, self.device_type
        )
