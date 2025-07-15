"""Support for LifeSmart covers by @MapleEve"""

import asyncio

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from . import LifeSmartDevice, generate_entity_id
from .const import (
    DOMAIN,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_DATA_KEY,
    DEVICE_NAME_KEY,
    DEVICE_VERSION_KEY,
    HUB_ID_KEY,
    COVER_TYPES,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    MANUFACTURER,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    # 设置 LifeSmart 窗帘设备
    devices = hass.data[DOMAIN][config_entry.entry_id]["devices"]
    exclude_devices = hass.data[DOMAIN][config_entry.entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][config_entry.entry_id]["exclude_hubs"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    cover_devices = []

    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        if device_type in COVER_TYPES:
            ha_device = LifeSmartDevice(device, client)

            if device_type in ["SL_CN_IF", "SL_CN_FE"]:
                idx = ["P1", "P2", "P3"]
                val = {i: device[DEVICE_DATA_KEY][i] for i in idx}
            elif device_type == "SL_P_V2":
                idx = ["P2", "P3", "P4", "P8"]  # 增加了P8电量属性
                val = {i: device[DEVICE_DATA_KEY][i] for i in idx}
            elif device_type == "SL_SW_WIN":
                idx = ["OP", "CL", "ST"]
                val = {i: device[DEVICE_DATA_KEY][i] for i in idx}
            elif device_type == "SL_DOOYA":
                idx = "P1"
                val = device[DEVICE_DATA_KEY][idx]
            else:
                continue

            cover_devices.append(LifeSmartCover(ha_device, device, idx, val, client))

    async_add_entities(cover_devices)


class LifeSmartCover(LifeSmartDevice, CoverEntity):
    """LifeSmart cover devices."""

    def __init__(self, device, raw_device_data, idx, val, client):
        """Init LifeSmart cover device."""
        super().__init__(raw_device_data, client)

        device_name = raw_device_data[DEVICE_NAME_KEY]
        device_type = raw_device_data[DEVICE_TYPE_KEY]
        hub_id = raw_device_data[HUB_ID_KEY]
        device_id = raw_device_data[DEVICE_ID_KEY]

        self._attr_has_entity_name = True
        self.device_name = device_name
        self.sensor_device_name = raw_device_data[DEVICE_NAME_KEY]
        self.device_id = device_id
        self.hub_id = hub_id
        self.device_type = device_type
        self.raw_device_data = raw_device_data
        self._device = device
        self.entity_id = generate_entity_id(device_type, hub_id, device_id, idx)
        self._client = client

        self._attr_device_class = CoverDeviceClass.CURTAIN
        self._supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP  # 默认支持打开、关闭和停止
        )
        self._is_opening = False
        self._is_closing = False
        self._is_closed = False

        if device_type in COVER_TYPES:
            if device_type == "SL_DOOYA":
                self._pos = val["val"]
                self._open_cmd = {"type": "0xCF", "val": 100, "idx": "P2"}
                self._close_cmd = {"type": "0xCF", "val": 0, "idx": "P2"}
                self._stop_cmd = {"type": "0xCE", "val": 0x80, "idx": "P2"}
                self._position_cmd = {"type": "0xCF", "idx": "P2"}
                self._supported_features |= (
                    CoverEntityFeature.SET_POSITION
                )  # 额外支持设置位置
            elif device_type == "SL_P_V2":
                self._open_cmd = {"type": "0x81", "val": 1, "idx": "P2"}
                self._close_cmd = {"type": "0x81", "val": 1, "idx": "P3"}
                self._stop_cmd = {"type": "0x81", "val": 1, "idx": "P4"}
                self._attr_battery_level = val["P8"]["v"]
            elif device_type == "SL_SW_WIN":
                self._open_cmd = {"type": "0x81", "val": 1, "idx": "OP"}
                self._close_cmd = {"type": "0x81", "val": 1, "idx": "CL"}
                self._stop_cmd = {"type": "0x81", "val": 1, "idx": "ST"}
            elif device_type in ["SL_CN_IF", "SL_CN_FE"]:
                self._open_cmd = {"type": "0x81", "val": 1, "idx": "P1"}
                self._close_cmd = {"type": "0x81", "val": 1, "idx": "P2"}
                self._stop_cmd = {"type": "0x81", "val": 1, "idx": "P3"}

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        if CoverEntityFeature.SET_POSITION:
            return self._pos
        else:
            return None

    @property
    def device_info(self) -> DeviceInfo:
        # 支持 Hub 的 Device info
        return DeviceInfo(
            identifiers={(DOMAIN, self.hub_id, self.device_id)},
            name=self.sensor_device_name,
            manufacturer=MANUFACTURER,
            model=self.device_type,
            sw_version=self.raw_device_data.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.hub_id) if self.hub_id else None,
        )

    @property
    def device_class(self):
        """Return the class of binary sensor."""
        return self._attr_device_class

    @property
    def unique_id(self):
        """A unique identifier for this entity.py."""
        return self.entity_id

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.device_type == "SL_DOOYA":
            return self.current_cover_position <= 0
        else:
            return self._is_closed

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        await super().async_lifesmart_epset(
            self._close_cmd["type"], self._close_cmd["val"], self._close_cmd["idx"]
        )
        self.schedule_update_ha_state()
        await self.async_poll_status()

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await super().async_lifesmart_epset(
            self._open_cmd["type"], self._open_cmd["val"], self._open_cmd["idx"]
        )
        self.schedule_update_ha_state()
        await self.async_poll_status()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        if not self._supported_features & CoverEntityFeature.STOP:
            return
        await super().async_lifesmart_epset(
            self._stop_cmd["type"], self._stop_cmd["val"], self._stop_cmd["idx"]
        )
        self.schedule_update_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the entity.py."""
        if self.is_opening or self.is_closing:
            await self.async_stop_cover()
        elif self.is_closed:
            await self.async_open_cover()
        else:
            await self.async_close_cover()

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        if not self._supported_features & CoverEntityFeature.SET_POSITION:
            return
        position = kwargs.get(ATTR_POSITION)
        await super().async_lifesmart_epset(
            self._position_cmd["type"], position, self._position_cmd["idx"]
        )
        self.schedule_update_ha_state()
        await self.async_poll_status()

    async def async_poll_status(self):
        """Poll cover status until it stops moving."""
        max_polls = 40  # 最大轮询次数40
        poll_interval = 0.8  # 轮询间隔0.5秒

        for _ in range(max_polls):
            if not self._is_opening and not self._is_closing:
                break  # 如果已停止,跳出循环
            await asyncio.sleep(poll_interval)
            await self.async_lifesmart_epget()
            self.schedule_update_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()  # 添加父类调用
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self.entity_id}",
                self._update_state,
            )
        )
        self.async_schedule_update_ha_state(force_refresh=True)  # 添加强制刷新

    async def _update_state(self, data) -> None:
        """Update cover state."""
        if data is not None:
            if self.device_type == "SL_DOOYA":
                if isinstance(data, dict):  # 判断data是否为字典类型
                    pos = data["val"] & 0x7F
                    if pos <= 100:
                        self._pos = pos
                        self._state = self._pos
                    else:
                        self._pos = None
                        self._state = None

                    if data["type"] & 0x01 == 1:  # 正在运行
                        if data["val"] & 0x80 == 0x80:
                            self._is_opening = True
                            self._is_closing = False
                        else:
                            self._is_opening = False
                            self._is_closing = True
                    else:  # 没有运行
                        self._is_opening = False
                        self._is_closing = False
                        if self._pos == 100:
                            self._is_closed = False
                        elif self._pos == 0:
                            self._is_closed = True
                else:
                    self._pos = None
                    self._state = None
                    self._is_opening = False
                    self._is_closing = False
                    self._is_closed = None  # 无法判断窗帘状态

            elif self.device_type == "SL_P_V2":
                for idx in ["P2", "P3", "P4"]:
                    if data[idx]["type"] & 0x01 == 1:  # 正在运行
                        if idx == "P2":
                            self._is_opening = True
                        elif idx == "P3":
                            self._is_closing = True
                        elif idx == "P4":
                            self._is_opening = False
                            self._is_closing = False
                    else:
                        if idx == "P2":
                            self._is_opening = False
                        elif idx == "P3":
                            self._is_closing = False
                            self._is_closed = True
                        elif idx == "P4":
                            self._is_closed = self._is_closing
                self._attr_battery_level = data["P8"]["v"]

            elif self.device_type == "SL_SW_WIN":
                for idx in ["OP", "CL", "ST"]:
                    if data[idx]["type"] & 0x01 == 1:  # 正在运行
                        if idx == "OP":
                            self._is_opening = True
                        elif idx == "CL":
                            self._is_closing = True
                        elif idx == "ST":
                            self._is_opening = False
                            self._is_closing = False
                    else:
                        if idx == "OP":
                            self._is_opening = False
                        elif idx == "CL":
                            self._is_closing = False
                            self._is_closed = True
                        elif idx == "ST":
                            self._is_closed = self._is_closing

            elif self.device_type in ["SL_CN_IF", "SL_CN_FE"]:
                for idx in ["P1", "P2", "P3"]:
                    if data[idx]["type"] & 0x01 == 1:  # 正在运行
                        if idx == "P1":
                            self._is_opening = True
                        elif idx == "P2":
                            self._is_opening = False
                            self._is_closing = False
                        elif idx == "P3":
                            self._is_closing = True
                    else:
                        if idx == "P1":
                            self._is_opening = False
                        elif idx == "P2":
                            self._is_closed = self._is_closing
                        elif idx == "P3":
                            self._is_closing = False
                            self._is_closed = True

            self.schedule_update_ha_state()
