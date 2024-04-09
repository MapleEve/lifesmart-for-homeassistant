"""Support for LifeSmart covers."""
from homeassistant.components.cover import (
    ENTITY_ID_FORMAT,
    ATTR_POSITION,
    CoverEntity,
)

from . import LifeSmartDevice


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up lifesmart dooya cover devices."""
    if discovery_info is None:
        return
    dev = discovery_info.get("dev")
    param = discovery_info.get("param")
    devices = []
    idx = "P1"
    devices.append(LifeSmartCover(dev, idx, dev["data"][idx], param))
    async_add_entities(devices)


class LifeSmartCover(LifeSmartDevice, CoverEntity):
    """LifeSmart cover devices."""

    def __init__(self, dev, idx, val, param):
        """Init LifeSmart cover device."""
        super().__init__(dev, idx, val, param)
        self._name = dev["name"]
        self.entity_id = ENTITY_ID_FORMAT.format(
            (dev["devtype"] + "_" + dev["agt"][:-3] + "_" + dev["me"]).lower()
        )
        self._pos = val["val"]
        self._device_class = "curtain"

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self._pos

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self.current_cover_position <= 0

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        await super().async_lifesmart_epset("0xCF", 0, "P2")

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await super().async_lifesmart_epset("0xCF", 100, "P2")

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await super().async_lifesmart_epset("0xCE", 0x80, "P2")

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        await super().async_lifesmart_epset("0xCE", position, "P2")

    @property
    def device_class(self):
        """Return the class of binary sensor."""
        return self._device_class

    @property
    def unique_id(self):
        """A unique identifier for this entity."""
        return self.entity_id
