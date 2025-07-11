"""Support for LifeSmart Gateway Light by @MapleEve"""

import binascii
import logging
import struct
from typing import Any

import homeassistant.util.color as color_util
from homeassistant.components.light import (
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGB_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, generate_entity_id
from .const import (
    DEVICE_DATA_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_VERSION_KEY,
    DOMAIN,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    MANUFACTURER,
    # 导入所有灯的常量设备类型
    QUANTUM_TYPES,
    SPOT_TYPES,
    LIGHT_DIMMER_TYPES,
    RGBW_LIGHT_TYPES,
    RGB_LIGHT_TYPES,
    OUTDOOR_LIGHT_TYPES,
    ALL_LIGHT_TYPES,
)

_LOGGER = logging.getLogger(__name__)

# 色温范围
MAX_MIREDS = int(1000000 / 2700)
MIN_MIREDS = int(1000000 / 6500)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart lights from a config entry."""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices = hass.data[DOMAIN][entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][entry_id]["exclude_hubs"]

    lights = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        if not _is_light_device(device_type):
            continue

        ha_device = LifeSmartDevice(device, client)

        # 根据设备类型创建对应的灯实体
        if device_type in LIGHT_DIMMER_TYPES:
            lights.append(
                LifeSmartDimmerLight(
                    device=ha_device,
                    raw_device=device,
                    sub_device_key="P1P2",
                    sub_device_data=device[DEVICE_DATA_KEY],
                    client=client,
                    entry_id=entry_id,
                )
            )
        elif device_type in SPOT_TYPES:
            # SPOT设备专用处理
            for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
                if sub_key == "RGB":
                    lights.append(
                        LifeSmartSPOTLight(
                            device=ha_device,
                            raw_device=device,
                            sub_device_key=sub_key,
                            sub_device_data=sub_data,
                            client=client,
                            entry_id=entry_id,
                        )
                    )
        elif device_type in QUANTUM_TYPES:
            # 量子灯特殊处理
            for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
                if sub_key == "P2":  # 量子灯的颜色控制
                    lights.append(
                        LifeSmartQuantumLight(
                            device=ha_device,
                            raw_device=device,
                            sub_device_key=sub_key,
                            sub_device_data=sub_data,
                            client=client,
                            entry_id=entry_id,
                        )
                    )
        elif device_type in RGBW_LIGHT_TYPES:
            # RGBW灯带/设备
            for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
                if sub_key == "RGBW":
                    lights.append(
                        LifeSmartRGBWLight(
                            device=ha_device,
                            raw_device=device,
                            sub_device_key=sub_key,
                            sub_device_data=sub_data,
                            client=client,
                            entry_id=entry_id,
                        )
                    )
        elif device_type in RGB_LIGHT_TYPES:
            # RGB灯带
            for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
                if sub_key == "RGB":
                    lights.append(
                        LifeSmartRGBLight(
                            device=ha_device,
                            raw_device=device,
                            sub_device_key=sub_key,
                            sub_device_data=sub_data,
                            client=client,
                            entry_id=entry_id,
                        )
                    )
        elif device_type in OUTDOOR_LIGHT_TYPES:
            # 户外灯光（调光壁灯、花园地灯）
            for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
                if sub_key == "P1":  # 主要控制口
                    lights.append(
                        LifeSmartOutdoorLight(
                            device=ha_device,
                            raw_device=device,
                            sub_device_key=sub_key,
                            sub_device_data=sub_data,
                            client=client,
                            entry_id=entry_id,
                        )
                    )
        else:
            # 通用灯设备
            for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
                if _is_light_subdevice(device_type, sub_key):
                    lights.append(
                        LifeSmartLight(
                            device=ha_device,
                            raw_device=device,
                            sub_device_key=sub_key,
                            sub_device_data=sub_data,
                            client=client,
                            entry_id=entry_id,
                        )
                    )

    async_add_entities(lights)


def _is_light_device(device_type: str) -> bool:
    """判断是否为灯设备."""
    return device_type in ALL_LIGHT_TYPES


def _is_light_subdevice(device_type: str, sub_key: str) -> bool:
    """判断子设备是否为灯."""
    light_sub_keys = [
        "RGB",
        "RGBW",
        "HS",
        "P1",
        "P2",
        "P3",
        "P4",
        "dark",
        "dark1",
        "dark2",
        "dark3",
        "bright",
        "bright1",
        "bright2",
        "bright3",
    ]
    return sub_key in light_sub_keys


class LifeSmartBaseLight(LightEntity):
    """LifeSmart灯基类."""

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
        """初始化灯."""
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
        self._attr_name = self._generate_light_name()
        self._initialize_state()

    @callback
    def _generate_light_name(self) -> str:
        """生成灯名称."""
        base_name = self._raw_device.get(DEVICE_NAME_KEY, "Unknown Light")
        if self._sub_key not in ["RGB", "RGBW", "P1", "P2"]:
            return f"{base_name} {self._sub_key}"
        return f"{base_name} Light"

    @callback
    def _initialize_state(self) -> None:
        """初始化状态 - 由子类实现."""
        pass

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY])
            },
            name=self._raw_device[DEVICE_NAME_KEY],
            manufacturer=MANUFACTURER,
            model=self._raw_device[DEVICE_TYPE_KEY],
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(
                (DOMAIN, self._raw_device[HUB_ID_KEY])
                if self._raw_device[HUB_ID_KEY]
                else None
            ),
        )

    async def async_added_to_hass(self) -> None:
        """注册更新监听器."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self.unique_id}",
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

    async def _handle_update(self, new_data: dict) -> None:
        """处理实时更新 - 由子类实现."""
        pass

    async def _handle_global_refresh(self) -> None:
        """处理全局刷新."""
        devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
        current_device = next(
            (
                d
                for d in devices
                if d[HUB_ID_KEY] == self._raw_device[HUB_ID_KEY]
                and d[DEVICE_ID_KEY] == self._raw_device[DEVICE_ID_KEY]
            ),
            None,
        )
        if current_device:
            sub_data = current_device.get(DEVICE_DATA_KEY, {}).get(self._sub_key, {})
            await self._handle_update(sub_data)


class LifeSmartQuantumLight(LifeSmartBaseLight):
    """LifeSmart量子灯."""

    @callback
    def _initialize_state(self) -> None:
        """初始化量子灯状态."""
        # 量子灯通过P2口控制颜色，没有明确的开关状态
        self._attr_is_on = True  # 默认开启
        self._attr_color_mode = ColorMode.RGBW
        self._attr_supported_color_modes = {ColorMode.RGBW}

        # 解析颜色值
        color_val = self._sub_data.get("val", 0)
        self._attr_rgbw_color = self._parse_quantum_color(color_val)

    def _parse_quantum_color(self, value: int) -> tuple:
        """解析量子灯颜色值."""
        # 根据文档：bit0~7:Blue, bit8~15:Green, bit16~23:Red, bit24~31:White
        blue = value & 0xFF
        green = (value >> 8) & 0xFF
        red = (value >> 16) & 0xFF
        white = (value >> 24) & 0xFF
        return (red, green, blue, white)

    def _encode_quantum_color(self, rgbw: tuple) -> int:
        """编码量子灯颜色值."""
        r, g, b, w = rgbw
        return (w << 24) | (r << 16) | (g << 8) | b

    async def _handle_update(self, new_data: dict) -> None:
        """处理量子灯状态更新."""
        if not new_data:
            return

        color_val = new_data.get("val", 0)
        self._attr_rgbw_color = self._parse_quantum_color(color_val)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """开启量子灯."""
        if ATTR_RGBW_COLOR in kwargs:
            self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]

        color_val = self._encode_quantum_color(self._attr_rgbw_color)
        result = await self._client.send_epset_async(
            "0xff",
            color_val,
            self._sub_key,
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )

        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭量子灯."""
        # 量子灯关闭设置为黑色
        result = await self._client.send_epset_async(
            "0xff",
            0,  # 全黑
            self._sub_key,
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )

        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()


class LifeSmartRGBWLight(LifeSmartBaseLight):
    """LifeSmart RGBW灯带."""

    @callback
    def _initialize_state(self) -> None:
        """初始化RGBW灯状态."""
        if self._sub_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        self._attr_color_mode = ColorMode.RGBW
        self._attr_supported_color_modes = {ColorMode.RGBW}

        # 解析RGBW颜色值
        color_val = self._sub_data.get("val", 0)
        self._attr_rgbw_color = self._parse_rgbw_color(color_val)

    def _parse_rgbw_color(self, value: int) -> tuple:
        """解析RGBW颜色值."""
        # bit0~7:Blue, bit8~15:Green, bit16~23:Red, bit24~31:White
        blue = value & 0xFF
        green = (value >> 8) & 0xFF
        red = (value >> 16) & 0xFF
        white = (value >> 24) & 0xFF
        return (red, green, blue, white)

    def _encode_rgbw_color(self, rgbw: tuple) -> int:
        """编码RGBW颜色值."""
        r, g, b, w = rgbw
        return (w << 24) | (r << 16) | (g << 8) | b

    async def _handle_update(self, new_data: dict) -> None:
        """处理RGBW灯状态更新."""
        if not new_data:
            return

        if new_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        color_val = new_data.get("val", 0)
        self._attr_rgbw_color = self._parse_rgbw_color(color_val)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """开启RGBW灯."""
        if ATTR_RGBW_COLOR in kwargs:
            self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]
            color_val = self._encode_rgbw_color(self._attr_rgbw_color)
            result = await self._client.send_epset_async(
                "0xff",
                color_val,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
        else:
            result = await self._client.send_epset_async(
                "0x81",
                1,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭RGBW灯."""
        if ATTR_RGBW_COLOR in kwargs:
            self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]
            color_val = self._encode_rgbw_color(self._attr_rgbw_color)
            result = await self._client.send_epset_async(
                "0xfe",
                color_val,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
        else:
            result = await self._client.send_epset_async(
                "0x80",
                0,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()


class LifeSmartRGBLight(LifeSmartBaseLight):
    """LifeSmart RGB灯带（不带白光）."""

    @callback
    def _initialize_state(self) -> None:
        """初始化RGB灯状态."""
        if self._sub_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {ColorMode.RGB}

        # 解析RGB颜色值
        color_val = self._sub_data.get("val", 0)
        self._attr_rgb_color = self._parse_rgb_color(color_val)

    def _parse_rgb_color(self, value: int) -> tuple:
        """解析RGB颜色值."""
        blue = value & 0xFF
        green = (value >> 8) & 0xFF
        red = (value >> 16) & 0xFF
        return (red, green, blue)

    def _encode_rgb_color(self, rgb: tuple) -> int:
        """编码RGB颜色值."""
        r, g, b = rgb
        return (r << 16) | (g << 8) | b

    async def _handle_update(self, new_data: dict) -> None:
        """处理RGB灯状态更新."""
        if not new_data:
            return

        if new_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        color_val = new_data.get("val", 0)
        self._attr_rgb_color = self._parse_rgb_color(color_val)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """开启RGB灯."""
        if ATTR_RGB_COLOR in kwargs:
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]
            color_val = self._encode_rgb_color(self._attr_rgb_color)
            result = await self._client.send_epset_async(
                "0xff",
                color_val,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
        else:
            result = await self._client.send_epset_async(
                "0x81",
                1,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭RGB灯."""
        result = await self._client.send_epset_async(
            "0x80",
            0,
            self._sub_key,
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )

        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()


class LifeSmartOutdoorLight(LifeSmartBaseLight):
    """LifeSmart户外灯光（调光壁灯、花园地灯）."""

    @callback
    def _initialize_state(self) -> None:
        """初始化户外灯状态."""
        if self._sub_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_brightness = self._sub_data.get("val", 0)

    async def _handle_update(self, new_data: dict) -> None:
        """处理户外灯状态更新."""
        if not new_data:
            return

        if new_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        self._attr_brightness = new_data.get("val", 0)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """开启户外灯."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            result = await self._client.send_epset_async(
                "0xcf",
                brightness,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
            if result == 0:
                self._attr_brightness = brightness
        else:
            result = await self._client.send_epset_async(
                "0x81",
                1,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭户外灯."""
        result = await self._client.send_epset_async(
            "0x80",
            0,
            self._sub_key,
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )

        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()


# 继续包含之前的其他类...
class LifeSmartSPOTLight(LifeSmartBaseLight):
    """LifeSmart SPOT灯."""

    @callback
    def _initialize_state(self) -> None:
        """初始化SPOT灯状态."""
        if self._sub_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
            self._attr_brightness = 255
        else:
            self._attr_is_on = False

        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {ColorMode.RGB}

        # 转换颜色值
        self._attr_rgb_color = self._convert_ls_wrgb_to_ha_rgb(
            self._sub_data.get("val", 0)
        )

    def _convert_ha_rgb_to_ls_wrgb(self, rgb_color: tuple) -> int:
        """转换HA RGB到LS wrgb格式."""
        rgbhex = (0,) + rgb_color
        rgbhex = binascii.hexlify(struct.pack("BBBB", *rgbhex)).decode("ASCII")
        return int(rgbhex, 16)

    def _convert_ls_wrgb_to_ha_rgb(self, value: int) -> tuple:
        """转换LS wrgb到HA RGB格式."""
        rgbhexstr = f"{value:x}".zfill(8)
        rgbhex = bytes.fromhex(rgbhexstr[2:])
        return struct.unpack("BBB", rgbhex)

    async def async_added_to_hass(self) -> None:
        """添加到HA时加载遥控器列表."""
        await super().async_added_to_hass()

        # 加载遥控器列表
        try:
            rmdata = {}
            rmlist = await self._client.get_ir_remote_list_async(
                self._raw_device[HUB_ID_KEY]
            )
            for device_id in rmlist:
                if self._raw_device[DEVICE_ID_KEY] in device_id:
                    rms = await self._client.get_ir_remote_async(
                        self._raw_device[HUB_ID_KEY], device_id
                    )
                    rms["category"] = rmlist[device_id]["category"]
                    rms["brand"] = rmlist[device_id]["brand"]
                    rms["idx"] = rmlist[device_id]["idx"]
                    rmdata[device_id] = rms
            self._attr_extra_state_attributes = {"remotelist": rmdata}
            _LOGGER.debug("SPOT remote list loaded: %s", rmdata)
        except Exception as e:
            _LOGGER.warning("Failed to load SPOT remote list: %s", e)

    async def _handle_update(self, new_data: dict) -> None:
        """处理SPOT灯状态更新."""
        if not new_data:
            return

        if new_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
            self._attr_brightness = 255
        else:
            self._attr_is_on = False

        self._attr_rgb_color = self._convert_ls_wrgb_to_ha_rgb(new_data.get("val", 0))
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """开启SPOT灯."""
        if ATTR_RGB_COLOR in kwargs:
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]
            rgbhex = self._convert_ha_rgb_to_ls_wrgb(self._attr_rgb_color)

            result = await self._client.send_epset_async(
                "0xff",
                rgbhex,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
        else:
            result = await self._client.turn_on_light_swith_async(
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭SPOT灯."""
        if ATTR_RGB_COLOR in kwargs:
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]
            rgbhex = self._convert_ha_rgb_to_ls_wrgb(self._attr_rgb_color)

            result = await self._client.send_epset_async(
                "0xfe",
                rgbhex,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
        else:
            result = await self._client.turn_off_light_swith_async(
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()


class LifeSmartDimmerLight(LifeSmartBaseLight):
    """LifeSmart调光灯."""

    @callback
    def _initialize_state(self) -> None:
        """初始化调光灯状态."""
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}
        self._attr_max_mireds = MAX_MIREDS
        self._attr_min_mireds = MIN_MIREDS

        for data_idx, data_val in self._sub_data.items():
            if data_idx == "P1":
                # 设置开关状态和亮度
                if data_val.get("type", 0) & 0x01 == 1:
                    self._attr_is_on = True
                else:
                    self._attr_is_on = False
                self._attr_brightness = data_val.get("val", 0)
            elif data_idx == "P2":
                # 设置色温
                ratio = 1 - (data_val.get("val", 0) / 255)
                self._attr_color_temp = (
                    int((self._attr_max_mireds - self._attr_min_mireds) * ratio)
                    + self._attr_min_mireds
                )

    async def _handle_update(self, new_data: dict) -> None:
        """处理调光灯状态更新."""
        if not new_data:
            return

        for data_idx, data_val in new_data.items():
            if data_idx == "P1":
                if data_val.get("type", 0) & 0x01 == 1:
                    self._attr_is_on = True
                else:
                    self._attr_is_on = False
                self._attr_brightness = data_val.get("val", 0)
            elif data_idx == "P2":
                ratio = 1 - (data_val.get("val", 0) / 255)
                self._attr_color_temp = (
                    int((self._attr_max_mireds - self._attr_min_mireds) * ratio)
                    + self._attr_min_mireds
                )

        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """开启调光灯."""
        if ATTR_BRIGHTNESS in kwargs:
            result = await self._client.send_epset_async(
                "0xcf",
                kwargs[ATTR_BRIGHTNESS],
                "P1",
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
            if result == 0:
                self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            ratio = (kwargs[ATTR_COLOR_TEMP_KELVIN] - self._attr_min_mireds) / (
                self._attr_max_mireds - self._attr_min_mireds
            )
            val = int((-ratio + 1) * 255)
            result = await self._client.send_epset_async(
                "0xcf",
                val,
                "P2",
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
            if result == 0:
                self._attr_color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]

        result = await self._client.send_epset_async(
            "0x81",
            1,
            "P1",
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )
        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭调光灯."""
        result = await self._client.send_epset_async(
            "0x80",
            0,
            "P1",
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )
        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()


class LifeSmartLight(LifeSmartBaseLight):
    """LifeSmart通用灯."""

    @callback
    def _initialize_state(self) -> None:
        """初始化通用灯状态."""
        if self._sub_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        # 根据子设备类型确定颜色模式
        self._attr_color_mode = self._determine_color_mode()
        self._attr_supported_color_modes = {self._attr_color_mode}

        # 初始化颜色值
        self._initialize_color_values()

    @callback
    def _determine_color_mode(self) -> ColorMode:
        """确定颜色模式."""
        if self._sub_key == "P1":
            return ColorMode.COLOR_TEMP
        elif self._sub_key in ["HS"]:
            return ColorMode.HS
        elif self._sub_key in ["RGBW", "RGB"]:
            return ColorMode.RGBW
        else:
            return ColorMode.ONOFF

    @callback
    def _initialize_color_values(self) -> None:
        """初始化颜色值."""
        value = self._sub_data.get("val", 0)

        if self._sub_key in ["HS"]:
            if value == 0:
                self._attr_hs_color = None
            else:
                rgbhexstr = f"{value:x}".zfill(8)
                rgbhex = bytes.fromhex(rgbhexstr)
                rgba = struct.unpack("BBBB", rgbhex)
                rgb = rgba[1:]
                self._attr_hs_color = color_util.color_RGB_to_hs(*rgb)
        elif self._sub_key in ["RGB_0"]:
            if value == 0:
                self._attr_rgb_color = None
            else:
                rgbhexstr = f"{value:x}".zfill(8)
                rgbhex = bytes.fromhex(rgbhexstr)
                rgba = struct.unpack("BBBB", rgbhex)
                self._attr_rgb_color = rgba[1:]
        elif self._sub_key in ["RGBW", "RGB"]:
            rgbhexstr = f"{value:x}".zfill(8)
            rgbhex = bytes.fromhex(rgbhexstr)
            rgbhex = struct.unpack("BBBB", rgbhex)
            # 转换从wrgb到rgbw元组
            self._attr_rgbw_color = rgbhex[1:] + (rgbhex[0],)

    async def _handle_update(self, new_data: dict) -> None:
        """处理通用灯状态更新."""
        if not new_data:
            return

        if new_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        # 更新颜色值
        value = new_data.get("val", 0)
        if self._sub_key in ["HS"] and value != 0:
            rgbhexstr = f"{value:x}".zfill(8)
            rgbhex = bytes.fromhex(rgbhexstr)
            rgba = struct.unpack("BBBB", rgbhex)
            rgb = rgba[1:]
            self._attr_hs_color = color_util.color_RGB_to_hs(*rgb)
        elif self._sub_key in ["RGBW", "RGB"]:
            rgbhexstr = f"{value:x}".zfill(8)
            rgbhex = bytes.fromhex(rgbhexstr)
            rgbhex = struct.unpack("BBBB", rgbhex)
            self._attr_rgbw_color = rgbhex[1:] + (rgbhex[0],)

        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """开启通用灯."""
        if self._attr_color_mode == ColorMode.HS:
            if ATTR_HS_COLOR in kwargs:
                self._attr_hs_color = kwargs[ATTR_HS_COLOR]

            rgb = color_util.color_hs_to_RGB(*self._attr_hs_color)
            rgba = (0,) + rgb
            rgbhex = binascii.hexlify(struct.pack("BBBB", *rgba)).decode("ASCII")
            rgbhex = int(rgbhex, 16)

            result = await self._client.send_epset_async(
                "0xff",
                rgbhex,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )
        elif self._attr_color_mode == ColorMode.RGBW:
            if ATTR_RGBW_COLOR in kwargs:
                self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]
                # 转换rgbw到wrgb元组
                rgbhex = (self._attr_rgbw_color[-1],) + self._attr_rgbw_color[:-1]
                rgbhex = binascii.hexlify(struct.pack("BBBB", *rgbhex)).decode("ASCII")
                rgbhex = int(rgbhex, 16)

                result = await self._client.send_epset_async(
                    "0xff",
                    rgbhex,
                    self._sub_key,
                    self._raw_device[HUB_ID_KEY],
                    self._raw_device[DEVICE_ID_KEY],
                )
            else:
                result = await self._client.send_epset_async(
                    "0x81",
                    1,
                    self._sub_key,
                    self._raw_device[HUB_ID_KEY],
                    self._raw_device[DEVICE_ID_KEY],
                )
        else:
            result = await self._client.send_epset_async(
                "0x81",
                1,
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭通用灯."""
        result = await self._client.send_epset_async(
            "0x80",
            0,
            self._sub_key,
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )
        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()
