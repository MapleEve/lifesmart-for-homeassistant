"""Support for LifeSmart Gateway Light by @MapleEve

未实现的灯光：
- 插座面板自身的 RGB/RGBW
- 窗帘电机自身的动态灯光 RGB灯光
"""

import binascii
import logging
import struct
from typing import Any

import homeassistant.util.color as color_util
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, generate_entity_id
from .const import (
    # 导入命令常量
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_RAW,
    CMD_TYPE_SET_VAL,
    # 导入其他常量
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
    BRIGHTNESS_LIGHT_TYPES,
    ALL_LIGHT_TYPES,
    GARAGE_DOOR_TYPES,
    # 导入DYN动态效果列表
    DYN_EFFECT_MAP,
    DYN_EFFECT_LIST,
    ALL_EFFECT_LIST,
    ALL_EFFECT_MAP,
)

_LOGGER = logging.getLogger(__name__)

# 色温范围
MAX_MIREDS = int(1000000 / 2700)
MIN_MIREDS = int(1000000 / 6500)


# 提取的公共颜色解析函数
def _parse_color_value(value: int, has_white: bool) -> tuple:
    """
    Parses a 32-bit integer color value into an RGB or RGBW tuple.

    The color format is assumed to be:
    - bits 0-7: Blue
    - bits 8-15: Green
    - bits 16-23: Red
    - bits 24-31: White (if has_white is True)
    """
    blue = value & 0xFF
    green = (value >> 8) & 0xFF
    red = (value >> 16) & 0xFF

    if has_white:
        white = (value >> 24) & 0xFF
        return (red, green, blue, white)

    return (red, green, blue)


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
        ha_device = LifeSmartDevice(device, client)

        # --- 优先处理特殊的超级碗SPOT设备 ---
        if device_type in SPOT_TYPES:
            # 根据文档，不同型号的SPOT设备灯光IO不同
            if device_type == "MSL_IRCTL":
                if "RGBW" in device:
                    lights.append(
                        LifeSmartSPOTRGBWLight(
                            device=ha_device,
                            raw_device=device,
                            client=client,
                            entry_id=entry_id,
                        )
                    )
            elif device_type in ["OD_WE_IRCTL", "SL_SPOT"]:
                if "RGB" in device:
                    lights.append(
                        LifeSmartSPOTRGBLight(
                            device=ha_device,
                            raw_device=device,
                            client=client,
                            entry_id=entry_id,
                        )
                    )
            # SL_P_IR 和 SL_P_IR_V2 没有灯，不创建实体
            continue  # 处理完SPOT后跳过后续逻辑

        # --- 常规灯光设备处理逻辑 ---
        if not _is_light_device(device_type):
            continue

        if device_type in GARAGE_DOOR_TYPES:
            for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
                if sub_key == "P1":
                    lights.append(
                        LifeSmartCoverLight(
                            device=ha_device,
                            raw_device=device,
                            sub_device_key=sub_key,
                            sub_device_data=sub_data,
                            client=client,
                            entry_id=entry_id,
                        )
                    )
            continue

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
        elif device_type in QUANTUM_TYPES:
            for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
                if sub_key == "P2":
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
        elif device_type in RGBW_LIGHT_TYPES and "RGBW" in device and "DYN" in device:
            lights.append(
                LifeSmartDualIORGBWLight(
                    ha_device, device, client, entry_id, "RGBW", "DYN"
                )
            )
        elif device_type in RGB_LIGHT_TYPES and "RGB" in device:
            lights.append(
                LifeSmartSingleIORGBWLight(ha_device, device, client, entry_id, "RGB")
            )
        elif device_type in OUTDOOR_LIGHT_TYPES and "P1" in device:
            lights.append(
                LifeSmartSingleIORGBWLight(ha_device, device, client, entry_id, "P1")
            )
        elif device_type in BRIGHTNESS_LIGHT_TYPES and "P1" in device:
            lights.append(
                LifeSmartBrightnessLight(
                    ha_device,
                    device,
                    "P1",
                    device.get(DEVICE_DATA_KEY, {}).get("P1", {}),
                    client,
                    entry_id,
                )
            )
        else:
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
        # 如果子设备有自己的名字 (如多联开关的按键名)，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} {self._sub_key.upper()}"

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
    """LifeSmart量子灯 (OD_WE_QUAN)."""

    @callback
    def _initialize_state(self) -> None:
        """初始化量子灯状态."""
        # 获取P1(亮度/开关)和P2(颜色)的数据
        p1_data = self._raw_device.get(DEVICE_DATA_KEY, {}).get("P1", {})
        p2_data = self._raw_device.get(DEVICE_DATA_KEY, {}).get("P2", {})

        # P1 控制开关状态和亮度
        self._attr_is_on = p1_data.get("type", 0) % 2 == 1
        self._attr_brightness = p1_data.get("val", 0)

        # P2 控制颜色和动态效果
        self._attr_color_mode = ColorMode.RGBW
        self._attr_supported_color_modes = {ColorMode.RGBW}
        self._attr_effect_list = ALL_EFFECT_LIST  # 支持所有动态效果

        color_val = p2_data.get("val", 0)
        white_byte = (color_val >> 24) & 0xFF

        if white_byte > 0:
            # 动态效果模式
            self._attr_effect = next(
                (k for k, v in ALL_EFFECT_MAP.items() if v == color_val), None
            )
        else:
            # 静态颜色模式
            self._attr_effect = None

        self._attr_rgbw_color = _parse_color_value(color_val, has_white=True)

    async def _handle_update(self, new_data: dict) -> None:
        """处理量子灯状态更新."""
        # 量子灯的更新涉及多个IO，需要从完整的设备信息中刷新
        devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
        current_device = next(
            (d for d in devices if d[DEVICE_ID_KEY] == self._raw_device[DEVICE_ID_KEY]),
            None,
        )
        if current_device:
            self._raw_device = current_device
            self._initialize_state()
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """开启量子灯."""
        io_commands = []

        # 优先处理效果
        if ATTR_EFFECT in kwargs:
            effect_name = kwargs[ATTR_EFFECT]
            if effect_name in ALL_EFFECT_MAP:
                effect_val = ALL_EFFECT_MAP[effect_name]
                # 设置效果时，需要同时确保灯是亮的
                io_commands.append({"idx": "P1", "type": CMD_TYPE_ON, "val": 1})
                io_commands.append(
                    {"idx": "P2", "type": CMD_TYPE_SET_RAW, "val": effect_val}
                )

        # 其次处理颜色和亮度
        else:
            # 确保灯是开的
            io_commands.append({"idx": "P1", "type": CMD_TYPE_ON, "val": 1})

            if ATTR_RGBW_COLOR in kwargs:
                r, g, b, w = kwargs[ATTR_RGBW_COLOR]
                color_val = (w << 24) | (r << 16) | (g << 8) | b
                io_commands.append(
                    {"idx": "P2", "type": CMD_TYPE_SET_RAW, "val": color_val}
                )

            if ATTR_BRIGHTNESS in kwargs:
                brightness = kwargs[ATTR_BRIGHTNESS]
                # P1的type为0xcf时设置亮度
                io_commands.append(
                    {"idx": "P1", "type": CMD_TYPE_SET_VAL, "val": brightness}
                )

        if io_commands:
            await self._client.async_set_multi_ep_async(
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
                io_commands,
            )
        else:
            # 如果没有其他参数，就是单纯的开灯
            await self._client.turn_on_light_switch_async(
                "P1", self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY]
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭量子灯."""
        # 根据文档，通过P1口关闭
        await self._client.turn_off_light_switch_async(
            "P1", self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY]
        )


class LifeSmartBrightnessLight(LifeSmartBaseLight):
    """LifeSmart户外灯光（调光壁灯、花园地灯）.亮度控制器"""

    @callback
    def _initialize_state(self) -> None:
        """初始化亮度灯状态."""
        if self._sub_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_brightness = self._sub_data.get("val", 0)

    async def _handle_update(self, new_data: dict) -> None:
        """处理亮度灯状态更新."""
        if not new_data:
            return

        if new_data.get("type", 0) & 0x01 == 1:
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        self._attr_brightness = new_data.get("val", 0)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """开启亮度灯."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            result = await self._client.send_epset_async(
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
                self._sub_key,
                CMD_TYPE_SET_VAL,
                brightness,
            )
            if result == 0:
                self._attr_brightness = brightness
        else:
            result = await self._client.turn_on_light_switch_async(
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭亮度灯."""
        result = await self._client.turn_off_light_switch_async(
            self._sub_key,
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )

        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()


class LifeSmartSingleIORGBWLight(LifeSmartBaseLight):
    """
    通用类，用于处理通过单个IO口控制颜色、白光和动态效果的灯。
    例如: SL_SC_RGB, SL_LI_UG1, OD_WE_IRCTL.
    """

    def __init__(
        self,
        device: LifeSmartDevice,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        io_key: str,
    ):
        super().__init__(
            device, raw_device, io_key, raw_device.get(io_key, {}), client, entry_id
        )
        self._attr_supported_color_modes = {ColorMode.RGBW}
        self._attr_effect_list = DYN_EFFECT_LIST

    @callback
    def _initialize_state(self) -> None:
        self._attr_is_on = self._sub_data.get("type", 0) % 2 == 1
        val = self._sub_data.get("val", 0)
        r, g, b, w = _parse_color_value(val, has_white=True)

        if w >= 128:  # 动态效果模式
            self._attr_effect = next(
                (k for k, v in DYN_EFFECT_MAP.items() if v == val), None
            )
            # 效果模式下，亮度是满的，颜色是效果本身决定的
            self._attr_brightness = 255 if self._attr_is_on else 0
            self._attr_rgbw_color = (r, g, b, 0)  # 效果模式下，W通道不代表白光
        elif w > 0:  # 白光模式 (W在1-100之间)
            self._attr_effect = None
            self._attr_brightness = int(w / 100 * 255)
            self._attr_rgbw_color = (r, g, b, w)  # 此时W代表白光
        else:  # 静态颜色模式
            self._attr_effect = None
            self._attr_brightness = (
                255 if self._attr_is_on else 0
            )  # 假设RGB模式下亮度满
            self._attr_rgbw_color = (r, g, b, 0)

    async def _handle_update(self, new_data: dict) -> None:
        self._sub_data = new_data
        self._initialize_state()
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        cmd_val = None
        if ATTR_EFFECT in kwargs:
            cmd_val = DYN_EFFECT_MAP.get(kwargs[ATTR_EFFECT])
        elif ATTR_RGBW_COLOR in kwargs:
            r, g, b, w = kwargs[ATTR_RGBW_COLOR]
            # 根据文档，白光值范围是0-100
            w_val = min(100, int(w / 255 * 100)) if w > 0 else 0
            cmd_val = (w_val << 24) | (r << 16) | (g << 8) | b
        elif ATTR_BRIGHTNESS in kwargs and self._attr_rgbw_color:
            # 调整白光亮度
            r, g, b, _ = self._attr_rgbw_color
            w_val = min(100, int(kwargs[ATTR_BRIGHTNESS] / 255 * 100))
            cmd_val = (w_val << 24) | (r << 16) | (g << 8) | b

        if cmd_val is not None:
            await self._client.send_epset_async(
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
                self._sub_key,
                CMD_TYPE_SET_RAW,
                cmd_val,
            )
        else:
            await self._client.turn_on_light_switch_async(
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.turn_off_light_switch_async(
            self._sub_key, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY]
        )


class LifeSmartDualIORGBWLight(LifeSmartBaseLight):
    """
    通用类，用于处理通过独立 'RGBW' 和 'DYN' IO口控制的灯。
    例如: SL_CT_RGBW, MSL_IRCTL.
    """

    def __init__(
        self,
        device: LifeSmartDevice,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        color_io: str,
        effect_io: str,
    ):
        super().__init__(
            device, raw_device, color_io, raw_device.get(color_io, {}), client, entry_id
        )
        self._color_io = color_io
        self._effect_io = effect_io
        self._attr_supported_color_modes = {ColorMode.RGBW}
        self._attr_effect_list = DYN_EFFECT_LIST

    @callback
    def _initialize_state(self) -> None:
        color_data = self._raw_device.get(self._color_io, {})
        dyn_data = self._raw_device.get(self._effect_io, {})

        self._attr_is_on = color_data.get("type", 0) % 2 == 1
        self._attr_brightness = 255 if self._attr_is_on else 0

        if dyn_data.get("type", 0) % 2 == 1:
            dyn_val = dyn_data.get("val", 0)
            self._attr_effect = next(
                (k for k, v in DYN_EFFECT_MAP.items() if v == dyn_val), None
            )
        else:
            self._attr_effect = None

        self._attr_rgbw_color = _parse_color_value(
            color_data.get("val", 0), has_white=True
        )

    async def _handle_update(self, new_data: dict) -> None:
        # 这种设备更新需要刷新整个设备对象
        devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
        current_device = next(
            (d for d in devices if d[DEVICE_ID_KEY] == self._raw_device[DEVICE_ID_KEY]),
            None,
        )
        if current_device:
            self._raw_device = current_device
            self._initialize_state()
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        io_list = []
        if ATTR_EFFECT in kwargs:
            effect_val = DYN_EFFECT_MAP.get(kwargs[ATTR_EFFECT])
            if effect_val is not None:
                io_list = [
                    {"idx": self._color_io, "type": CMD_TYPE_ON, "val": 1},
                    {
                        "idx": self._effect_io,
                        "type": CMD_TYPE_SET_RAW,
                        "val": effect_val,
                    },
                ]
        elif ATTR_RGBW_COLOR in kwargs:
            r, g, b, w = kwargs[ATTR_RGBW_COLOR]
            color_val = (w << 24) | (r << 16) | (g << 8) | b
            io_list = [
                {"idx": self._color_io, "type": CMD_TYPE_SET_RAW, "val": color_val},
                {"idx": self._effect_io, "type": CMD_TYPE_OFF, "val": 0},
            ]

        if io_list:
            await self._client.async_set_multi_ep_async(
                self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY], io_list
            )
        else:
            await self._client.turn_on_light_switch_async(
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        io_list = [
            {"idx": self._color_io, "type": CMD_TYPE_OFF, "val": 0},
            {"idx": self._effect_io, "type": CMD_TYPE_OFF, "val": 0},
        ]
        await self._client.async_set_multi_ep_async(
            self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY], io_list
        )


class LifeSmartSPOTRGBLight(LifeSmartBaseLight):
    """LifeSmart SPOT Light with RGB and Effects controlled by a single IO."""

    def __init__(
        self,
        device: LifeSmartDevice,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """初始化SPOT RGB灯。"""
        super().__init__(
            device, raw_device, "RGB", raw_device.get("RGB", {}), client, entry_id
        )

    @callback
    def _initialize_state(self) -> None:
        """初始化SPOT RGB灯状态。"""
        self._attr_is_on = self._sub_data.get("type", 0) % 2 == 1
        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {ColorMode.RGB}
        self._attr_effect_list = DYN_EFFECT_LIST
        self._attr_brightness = 255 if self._attr_is_on else 0

        val = self._sub_data.get("val", 0)
        # 根据文档，检查最高字节是否大于0，以判断是否为动态效果模式
        white_byte = (val >> 24) & 0xFF
        if white_byte > 0:
            self._attr_effect = next(
                (k for k, v in DYN_EFFECT_MAP.items() if v == val), None
            )
        else:
            self._attr_effect = None

        # 无论是否在效果模式下，都解析其基础RGB颜色值
        self._attr_rgb_color = _parse_color_value(val, has_white=False)

    async def _handle_update(self, new_data: dict) -> None:
        """处理SPOT RGB灯状态更新。"""
        self._sub_data = new_data
        self._initialize_state()
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """开启SPOT RGB灯。"""
        cmd_type = CMD_TYPE_SET_RAW
        cmd_val = None

        if ATTR_EFFECT in kwargs:
            effect_name = kwargs[ATTR_EFFECT]
            if effect_name in DYN_EFFECT_MAP:
                cmd_val = DYN_EFFECT_MAP[effect_name]
        elif ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            cmd_val = (r << 16) | (g << 8) | b
        else:
            cmd_type = CMD_TYPE_ON
            cmd_val = 1

        await self._client.send_epset_async(
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
            self._sub_key,
            cmd_type,
            cmd_val,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭SPOT RGB灯。"""
        await self._client.turn_off_light_switch_async(
            self._sub_key, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY]
        )


class LifeSmartSPOTRGBWLight(LifeSmartBaseLight):
    """LifeSmart SPOT Light with separate RGBW and DYN IOs."""

    def __init__(
        self,
        device: LifeSmartDevice,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """初始化SPOT RGBW灯。"""
        super().__init__(
            device, raw_device, "RGBW", raw_device.get("RGBW", {}), client, entry_id
        )

    @callback
    def _initialize_state(self) -> None:
        """初始化SPOT RGBW灯状态。"""
        rgbw_data = self._raw_device.get("RGBW", {})
        dyn_data = self._raw_device.get("DYN", {})

        self._attr_is_on = rgbw_data.get("type", 0) % 2 == 1
        self._attr_color_mode = ColorMode.RGBW
        self._attr_supported_color_modes = {ColorMode.RGBW}
        self._attr_effect_list = DYN_EFFECT_LIST
        self._attr_brightness = 255 if self._attr_is_on else 0

        if dyn_data.get("type", 0) % 2 == 1:
            dyn_val = dyn_data.get("val", 0)
            self._attr_effect = next(
                (k for k, v in DYN_EFFECT_MAP.items() if v == dyn_val), None
            )
        else:
            self._attr_effect = None

        self._attr_rgbw_color = _parse_color_value(
            rgbw_data.get("val", 0), has_white=True
        )

    async def _handle_update(self, new_data: dict) -> None:
        """处理SPOT RGBW灯状态更新。"""
        # SPOT灯的更新可能涉及多个IO，需要从完整的设备信息中刷新
        devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
        current_device = next(
            (d for d in devices if d[DEVICE_ID_KEY] == self._raw_device[DEVICE_ID_KEY]),
            None,
        )
        if current_device:
            self._raw_device = current_device
            self._initialize_state()
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """开启SPOT RGBW灯。"""
        io_list = []
        if ATTR_EFFECT in kwargs:
            effect_name = kwargs[ATTR_EFFECT]
            if effect_name in DYN_EFFECT_MAP:
                effect_val = DYN_EFFECT_MAP[effect_name]
                io_list = [
                    {"idx": "RGBW", "type": CMD_TYPE_ON, "val": 1},
                    {"idx": "DYN", "type": CMD_TYPE_SET_RAW, "val": effect_val},
                ]
        elif ATTR_RGBW_COLOR in kwargs:
            r, g, b, w = kwargs[ATTR_RGBW_COLOR]
            color_val = (w << 24) | (r << 16) | (g << 8) | b
            io_list = [
                {"idx": "RGBW", "type": CMD_TYPE_SET_RAW, "val": color_val},
                {"idx": "DYN", "type": CMD_TYPE_OFF, "val": 0},
            ]

        if io_list:
            await self._client.async_set_multi_ep_async(
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
                io_list,
            )
        else:
            await self._client.turn_on_light_switch_async(
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭SPOT RGBW灯。"""
        io_list = [
            {"idx": "RGBW", "type": CMD_TYPE_OFF, "val": 0},
            {"idx": "DYN", "type": CMD_TYPE_OFF, "val": 0},
        ]
        await self._client.async_set_multi_ep_async(
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
            io_list,
        )


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
                CMD_TYPE_SET_VAL,
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
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
                "P2",
                CMD_TYPE_SET_VAL,
                val,
            )
            if result == 0:
                self._attr_color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]

        # 确保在调整完参数后，灯是开启状态
        result = await self._client.turn_on_light_switch_async(
            "P1",
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )
        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭调光灯."""
        result = await self._client.turn_off_light_switch_async(
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
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
                self._sub_key,
                CMD_TYPE_SET_RAW,
                rgbhex,
            )
        elif self._attr_color_mode == ColorMode.RGBW:
            if ATTR_RGBW_COLOR in kwargs:
                self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]
                # 转换rgbw到wrgb元组
                rgbhex = (self._attr_rgbw_color[-1],) + self._attr_rgbw_color[:-1]
                rgbhex = binascii.hexlify(struct.pack("BBBB", *rgbhex)).decode("ASCII")
                rgbhex = int(rgbhex, 16)

                result = await self._client.send_epset_async(
                    self._raw_device[HUB_ID_KEY],
                    self._raw_device[DEVICE_ID_KEY],
                    self._sub_key,
                    CMD_TYPE_SET_RAW,
                    rgbhex,
                )
            else:
                result = await self._client.turn_on_light_switch_async(
                    self._sub_key,
                    self._raw_device[HUB_ID_KEY],
                    self._raw_device[DEVICE_ID_KEY],
                )
        else:
            result = await self._client.turn_on_light_switch_async(
                self._sub_key,
                self._raw_device[HUB_ID_KEY],
                self._raw_device[DEVICE_ID_KEY],
            )

        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """关闭通用灯."""
        result = await self._client.turn_off_light_switch_async(
            self._sub_key,
            self._raw_device[HUB_ID_KEY],
            self._raw_device[DEVICE_ID_KEY],
        )
        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()


class LifeSmartCoverLight(LifeSmartBaseLight):
    """Represents a light attached to a LifeSmart cover device (e.g., garage door light)."""

    @callback
    def _generate_light_name(self) -> str:
        base_name = self._raw_device.get(DEVICE_NAME_KEY, "Unknown Switch")
        # 如果子设备有自己的名字 (如多联开关的按键名)，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} {self._sub_key.upper()}"

    @callback
    def _initialize_state(self) -> None:
        self._attr_is_on = self._sub_data.get("type", 0) % 2 == 1
        self._attr_color_mode = ColorMode.ONOFF
        self._attr_supported_color_modes = {ColorMode.ONOFF}

    async def _handle_update(self, new_data: dict) -> None:
        if not new_data:
            return
        self._attr_is_on = new_data.get("type", 0) % 2 == 1
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        result = await self._client.turn_on_light_switch_async(
            self._sub_key, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY]
        )
        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        result = await self._client.turn_off_light_switch_async(
            self._sub_key, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY]
        )
        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()
