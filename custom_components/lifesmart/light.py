"""
此模块为 LifeSmart 平台提供灯光设备 (Light) 支持。

由 @MapleEve 初始创建和维护。

未实现的灯光 PR Welcome：
- 插座面板自身的 RGB/RGBW
- 窗帘电机自身的动态灯光 RGB灯光

主要功能:
- 定义了多种 LifeSmart 灯光实体类，以适配不同功能的灯具，
  如普通开关灯、亮度灯、色温灯、RGB/RGBW 灯和量子灯等。
- 在 `async_setup_entry` 中，根据设备的类型 (devtype) 和其数据 (data) 中的
  IO口信息，智能地创建对应的灯光实体。
- 实现了乐观更新 (Optimistic Update) 机制，当用户在 Home Assistant 中
  操作灯光时，UI 会立即反馈变化，无需等待设备状态的下一次推送，提升了用户体验。
- 实现了健壮的状态更新逻辑，能够防御性地处理不完整的设备数据推送，
  避免因数据缺失导致实体状态被错误地重置。
- 遵循 Home Assistant 最新的开发实践。
"""

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, generate_unique_id
from .const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_RAW,
    CMD_TYPE_SET_VAL,
    DEVICE_DATA_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_VERSION_KEY,
    DOMAIN,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    MANUFACTURER,
    CONF_EXCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    QUANTUM_TYPES,
    SPOT_TYPES,
    LIGHT_DIMMER_TYPES,
    RGB_LIGHT_TYPES,
    RGBW_LIGHT_TYPES,
    OUTDOOR_LIGHT_TYPES,
    BRIGHTNESS_LIGHT_TYPES,
    ALL_LIGHT_TYPES,
    GARAGE_DOOR_TYPES,
    DYN_EFFECT_MAP,
    DYN_EFFECT_LIST,
    ALL_EFFECT_LIST,
    ALL_EFFECT_MAP,
)

_LOGGER = logging.getLogger(__name__)

# --- 遵循 HA 最佳实践：直接定义开尔文范围 ---
DEFAULT_MIN_KELVIN = 2700
DEFAULT_MAX_KELVIN = 6500


def _parse_color_value(value: int, has_white: bool) -> tuple:
    """
    将一个32位整数颜色值解析为RGB或RGBW元组。

    颜色格式假定为：
    - bits 0-7:   Blue
    - bits 8-15:  Green
    - bits 16-23: Red
    - bits 24-31: White (如果 has_white 为 True) 或 亮度/效果标志
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
    """从配置条目异步设置 LifeSmart 灯光设备。"""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices_str = config_entry.options.get(CONF_EXCLUDE_ITEMS, "")
    exclude_hubs_str = config_entry.options.get(CONF_EXCLUDE_AGTS, "")
    exclude_devices = {
        dev.strip() for dev in exclude_devices_str.split(",") if dev.strip()
    }
    exclude_hubs = {hub.strip() for hub in exclude_hubs_str.split(",") if hub.strip()}

    lights = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]
        device_data = device.get(DEVICE_DATA_KEY, {})

        if device_type in SPOT_TYPES:
            if device_type == "MSL_IRCTL" and "RGBW" in device_data:
                lights.append(LifeSmartSPOTRGBWLight(device, client, entry_id))
            elif device_type in {"OD_WE_IRCTL", "SL_SPOT"} and "RGB" in device_data:
                lights.append(LifeSmartSPOTRGBLight(device, client, entry_id))
            continue

        if not _is_light_device(device_type):
            continue

        if device_type in GARAGE_DOOR_TYPES:
            if "P1" in device_data:
                lights.append(LifeSmartCoverLight(device, client, entry_id, "P1"))
            continue  # 无论是否找到P1，处理完车库门类型后都应跳过

        if device_type in LIGHT_DIMMER_TYPES:
            lights.append(LifeSmartDimmerLight(device, client, entry_id))
        elif device_type in QUANTUM_TYPES:
            lights.append(LifeSmartQuantumLight(device, client, entry_id))
        elif (
            device_type in RGBW_LIGHT_TYPES
            and "RGBW" in device_data
            and "DYN" in device_data
        ):
            lights.append(
                LifeSmartDualIORGBWLight(device, client, entry_id, "RGBW", "DYN")
            )
        elif device_type in RGB_LIGHT_TYPES and "RGB" in device_data:
            lights.append(LifeSmartSingleIORGBWLight(device, client, entry_id, "RGB"))
        elif device_type in OUTDOOR_LIGHT_TYPES and "P1" in device_data:
            lights.append(LifeSmartSingleIORGBWLight(device, client, entry_id, "P1"))
        elif device_type in BRIGHTNESS_LIGHT_TYPES and "P1" in device_data:
            lights.append(LifeSmartBrightnessLight(device, client, entry_id, "P1"))
        else:
            for sub_key, sub_data in device_data.items():
                if _is_light_subdevice(device_type, sub_key):
                    lights.append(LifeSmartLight(device, client, entry_id, sub_key))

    async_add_entities(lights)


def _is_light_device(device_type: str) -> bool:
    """判断一个设备是否属于灯光类型。"""
    return device_type in ALL_LIGHT_TYPES


def _is_light_subdevice(device_type: str, sub_key: str) -> bool:
    """判断一个设备的子IO口是否为灯光控制点。"""
    return (sub_key.startswith(("P", "L")) or sub_key == "HS") and sub_key not in {
        "P5",
        "P6",
        "P7",
        "P8",
        "P9",
        "P10",
    }


class LifeSmartBaseLight(LifeSmartDevice, LightEntity):
    """
    LifeSmart 灯光设备的基类。

    实现了所有灯光设备共有的逻辑，如设备信息、实体命名、唯一ID生成、
    以及统一的状态更新处理机制。
    """

    _attr_should_poll = False

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str | None = None,
    ) -> None:
        """初始化灯光基类。"""
        super().__init__(raw_device, client)
        self._entry_id = entry_id
        self._sub_key = sub_device_key

        device_data = self._raw_device.get(DEVICE_DATA_KEY, {})
        if self._sub_key:
            self._sub_data = device_data.get(self._sub_key, {})
        else:
            self._sub_data = device_data

        base_name = self._name
        if self._sub_key:
            sub_name_from_data = self._sub_data.get(DEVICE_NAME_KEY)
            suffix = (
                sub_name_from_data
                if sub_name_from_data and sub_name_from_data != self._sub_key
                else self._sub_key.upper()
            )
            self._attr_name = f"{base_name} {suffix}"
            sub_key_slug = self._sub_key.lower()
            self._attr_object_id = (
                f"{base_name.lower().replace(' ', '_')}_{sub_key_slug}"
            )
        else:
            self._attr_name = base_name
            self._attr_object_id = base_name.lower().replace(" ", "_")

        self._attr_unique_id = generate_unique_id(
            self.devtype, self.agt, self.me, self._sub_key
        )

        self._initialize_state()

    @callback
    def _initialize_state(self) -> None:
        """初始化状态 - 由子类实现."""
        raise NotImplementedError

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息，用于在 Home Assistant UI 中将实体链接到物理设备。"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """当实体被添加到 Home Assistant 时，注册更新监听器。"""
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
        """
        统一处理来自 WebSocket 的实时状态更新。

        此方法是状态更新的核心入口。它会更新内部的设备数据，
        然后调用 `_initialize_state` 来重新解析状态，并通知 HA 更新前端。
        """
        if not new_data:
            return

        device_data = self._raw_device.get(DEVICE_DATA_KEY, {}).copy()

        first_key = next(iter(new_data), None)
        is_raw_io_update = first_key in ("type", "val", "v")

        if self._sub_key and is_raw_io_update:
            sub_device_data = device_data.get(self._sub_key, {})
            sub_device_data.update(new_data)
            device_data[self._sub_key] = sub_device_data
        else:
            device_data.update(new_data)

        self._raw_device[DEVICE_DATA_KEY] = device_data

        if self._sub_key:
            self._sub_data = device_data.get(self._sub_key, {})
        else:
            self._sub_data = device_data

        self._initialize_state()
        self.async_write_ha_state()

    @callback
    def _handle_global_refresh(self) -> None:
        """处理来自 API 轮询的全局设备列表刷新。"""
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (d for d in devices if d[DEVICE_ID_KEY] == self.me), None
            )
            if current_device:
                self._raw_device = current_device
                device_data = self._raw_device.get(DEVICE_DATA_KEY, {})
                if self._sub_key:
                    self._sub_data = device_data.get(self._sub_key, {})
                else:
                    self._sub_data = device_data
                self._initialize_state()
                self.async_write_ha_state()
        except (KeyError, StopIteration):
            _LOGGER.warning("在全局刷新期间未能找到设备 %s。", self._attr_unique_id)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light with robust optimistic update."""
        original_is_on = self._attr_is_on

        self._attr_is_on = True
        self.async_write_ha_state()

        try:
            await self._client.turn_on_light_switch_async(
                self._sub_key, self.agt, self.me
            )
        except Exception as e:
            _LOGGER.error(
                "Failed to turn on light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light with robust optimistic update."""
        original_is_on = self._attr_is_on

        self._attr_is_on = False
        self.async_write_ha_state()

        try:
            await self._client.turn_off_light_switch_async(
                self._sub_key, self.agt, self.me
            )
        except Exception as e:
            _LOGGER.error(
                "Failed to turn off light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self.async_write_ha_state()


class LifeSmartLight(LifeSmartBaseLight):
    """LifeSmart通用灯 (通常是开关面板上的一个通道)。"""

    @callback
    def _initialize_state(self) -> None:
        """初始化通用灯状态。"""
        self._attr_is_on = self._sub_data.get("type", 0) % 2 == 1
        self._attr_color_mode = ColorMode.ONOFF
        self._attr_supported_color_modes = {ColorMode.ONOFF}


class LifeSmartBrightnessLight(LifeSmartBaseLight):
    """亮度灯，仅支持亮度和开关。"""

    @callback
    def _initialize_state(self) -> None:
        """初始化亮度灯状态。"""
        self._attr_is_on = self._sub_data.get("type", 0) % 2 == 1
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        if (val := self._sub_data.get("val")) is not None:
            self._attr_brightness = val

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light with robust optimistic update."""
        original_is_on = self._attr_is_on
        original_brightness = self._attr_brightness

        self._attr_is_on = True
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
        self.async_write_ha_state()

        try:
            if ATTR_BRIGHTNESS in kwargs:
                await self._client.async_send_single_command(
                    self.agt,
                    self.me,
                    self._sub_key,
                    CMD_TYPE_SET_VAL,
                    self._attr_brightness,
                )
            else:
                await self._client.turn_on_light_switch_async(
                    self._sub_key, self.agt, self.me
                )
        except Exception as e:
            _LOGGER.error(
                "Failed to turn on light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self._attr_brightness = original_brightness
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light with robust optimistic update."""
        original_is_on = self._attr_is_on

        self._attr_is_on = False
        self.async_write_ha_state()

        try:
            await self._client.turn_off_light_switch_async(
                self._sub_key, self.agt, self.me
            )
        except Exception as e:
            _LOGGER.error(
                "Failed to turn off light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self.async_write_ha_state()


class LifeSmartDimmerLight(LifeSmartBaseLight):
    """色温灯，支持亮度、色温和开关。"""

    _attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
    _attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN

    def __init__(self, raw_device: dict, client: Any, entry_id: str) -> None:
        super().__init__(raw_device, client, entry_id)

    @callback
    def _initialize_state(self) -> None:
        """初始化色温灯状态。"""
        data = self._sub_data
        p1_data = data.get("P1", {})
        p2_data = data.get("P2", {})

        self._attr_is_on = p1_data.get("type", 0) % 2 == 1
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}

        if (val := p1_data.get("val")) is not None:
            self._attr_brightness = val
        if (val := p2_data.get("val")) is not None:
            ratio = (255 - val) / 255.0
            self._attr_color_temp_kelvin = self._attr_min_color_temp_kelvin + ratio * (
                self._attr_max_color_temp_kelvin - self._attr_min_color_temp_kelvin
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light with robust optimistic update."""
        original_is_on = self._attr_is_on
        original_brightness = self._attr_brightness
        original_color_temp = self._attr_color_temp_kelvin

        self._attr_is_on = True
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._attr_color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
        self.async_write_ha_state()

        try:
            io_commands = []
            # 只有在提供了相关参数时才构建命令
            if ATTR_BRIGHTNESS in kwargs or ATTR_COLOR_TEMP_KELVIN in kwargs:
                # 确保我们有值可以发送，即使只提供了其中一个参数
                brightness = (
                    self._attr_brightness if self._attr_brightness is not None else 255
                )
                kelvin = (
                    self._attr_color_temp_kelvin
                    if self._attr_color_temp_kelvin is not None
                    else self._attr_min_color_temp_kelvin
                )

                min_k, max_k = (
                    self._attr_min_color_temp_kelvin,
                    self._attr_max_color_temp_kelvin,
                )
                clamped_kelvin = max(min_k, min(kelvin, max_k))
                ratio = (
                    ((clamped_kelvin - min_k) / (max_k - min_k))
                    if (max_k - min_k) != 0
                    else 0
                )
                temp_val = round(255 - (ratio * 255))

                io_commands.extend(
                    [
                        {"idx": "P1", "type": CMD_TYPE_SET_VAL, "val": brightness},
                        {"idx": "P2", "type": CMD_TYPE_SET_VAL, "val": temp_val},
                    ]
                )

            if io_commands:
                await self._client.async_send_multi_command(
                    self.agt, self.me, io_commands
                )

            # 无论如何，最后都要确保灯是开启状态
            await self._client.turn_on_light_switch_async("P1", self.agt, self.me)

        except Exception as e:
            _LOGGER.error(
                "Failed to turn on light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self._attr_brightness = original_brightness
            self._attr_color_temp_kelvin = original_color_temp
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light with robust optimistic update."""
        original_is_on = self._attr_is_on

        self._attr_is_on = False
        self.async_write_ha_state()

        try:
            await self._client.turn_off_light_switch_async("P1", self.agt, self.me)
        except Exception as e:
            _LOGGER.error(
                "Failed to turn off light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self.async_write_ha_state()


class LifeSmartSPOTRGBLight(LifeSmartBaseLight):
    """SPOT灯 (RGB模式)。"""

    def __init__(self, raw_device: dict, client: Any, entry_id: str):
        super().__init__(raw_device, client, entry_id, "RGB")
        self._attr_supported_features = LightEntityFeature.EFFECT

    @callback
    def _initialize_state(self) -> None:
        """初始化SPOT RGB灯状态。"""
        sub_data = self._sub_data
        self._attr_is_on = sub_data.get("type", 0) % 2 == 1
        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {ColorMode.RGB}
        self._attr_effect_list = DYN_EFFECT_LIST
        self._attr_brightness = 255 if self._attr_is_on else 0

        if (val := sub_data.get("val")) is not None:
            if (val >> 24) & 0xFF > 0:
                self._attr_effect = next(
                    (k for k, v in DYN_EFFECT_MAP.items() if v == val), None
                )
            else:
                self._attr_effect = None
            self._attr_rgb_color = _parse_color_value(val, has_white=False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """开启SPOT RGB灯，支持颜色、亮度和效果，带乐观更新。"""
        # 1. 保存原始状态
        original_is_on = self._attr_is_on
        original_brightness = self._attr_brightness
        original_rgb_color = self._attr_rgb_color
        original_effect = self._attr_effect

        # 2. 执行乐观更新
        self._attr_is_on = True
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_RGB_COLOR in kwargs:
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]
            self._attr_effect = None
        if ATTR_EFFECT in kwargs:
            self._attr_effect = kwargs[ATTR_EFFECT]
            self._attr_rgb_color = None
            self._attr_brightness = 255  # 效果模式下，亮度设为全亮
        self.async_write_ha_state()

        # 3. 发送命令并处理异常
        try:
            cmd_type, cmd_val = CMD_TYPE_ON, 1

            if ATTR_EFFECT in kwargs:
                effect_val = DYN_EFFECT_MAP.get(self._attr_effect)
                if effect_val is not None:
                    cmd_type, cmd_val = CMD_TYPE_SET_RAW, effect_val
            elif ATTR_RGB_COLOR in kwargs or ATTR_BRIGHTNESS in kwargs:
                # 使用乐观更新后的状态来计算最终颜色
                rgb = self._attr_rgb_color if self._attr_rgb_color else (255, 255, 255)
                brightness = (
                    self._attr_brightness if self._attr_brightness is not None else 255
                )

                ratio = brightness / 255.0
                final_rgb = tuple(round(c * ratio) for c in rgb)

                r, g, b = final_rgb
                cmd_type, cmd_val = CMD_TYPE_SET_RAW, (r << 16) | (g << 8) | b

            if cmd_val is not None:
                await self._client.async_send_single_command(
                    self.agt, self.me, self._sub_key, cmd_type, cmd_val
                )
            else:
                # 如果没有颜色或效果参数，则执行默认的开灯操作
                await super().async_turn_on(**kwargs)
        except Exception as e:
            _LOGGER.error(
                "Failed to turn on light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            # 4. 失败则回滚状态
            self._attr_is_on = original_is_on
            self._attr_brightness = original_brightness
            self._attr_rgb_color = original_rgb_color
            self._attr_effect = original_effect
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light with robust optimistic update."""
        original_is_on = self._attr_is_on

        self._attr_is_on = False
        self.async_write_ha_state()

        try:
            await self._client.turn_off_light_switch_async(
                self._sub_key, self.agt, self.me
            )
        except Exception as e:
            _LOGGER.error(
                "Failed to turn off light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self.async_write_ha_state()


class LifeSmartQuantumLight(LifeSmartBaseLight):
    """LifeSmart量子灯 (OD_WE_QUAN)."""

    def __init__(self, raw_device: dict, client: Any, entry_id: str) -> None:
        super().__init__(raw_device, client, entry_id)
        self._attr_supported_features = LightEntityFeature.EFFECT

    @callback
    def _initialize_state(self) -> None:
        """初始化量子灯状态。"""
        data = self._sub_data
        p1_data = data.get("P1", {})
        p2_data = data.get("P2", {})

        self._attr_is_on = p1_data.get("type", 0) % 2 == 1
        if (val := p1_data.get("val")) is not None:
            self._attr_brightness = val

        self._attr_color_mode = ColorMode.RGBW
        self._attr_supported_color_modes = {ColorMode.RGBW}
        self._attr_effect_list = ALL_EFFECT_LIST

        if (color_val := p2_data.get("val")) is not None:
            white_byte = (color_val >> 24) & 0xFF
            if white_byte > 0:
                self._attr_effect = next(
                    (k for k, v in ALL_EFFECT_MAP.items() if v == color_val), None
                )
            else:
                self._attr_effect = None
            self._attr_rgbw_color = _parse_color_value(color_val, has_white=True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light with robust optimistic update."""
        original_is_on = self._attr_is_on
        original_brightness = self._attr_brightness
        original_rgbw_color = self._attr_rgbw_color
        original_effect = self._attr_effect

        self._attr_is_on = True
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_RGBW_COLOR in kwargs:
            self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]
            self._attr_effect = None
        if ATTR_EFFECT in kwargs:
            self._attr_effect = kwargs[ATTR_EFFECT]
            self._attr_rgbw_color = None
        self.async_write_ha_state()

        try:
            params = []
            if ATTR_BRIGHTNESS in kwargs:
                params.append(
                    {
                        "idx": "P1",
                        "type": CMD_TYPE_SET_VAL,
                        "val": self._attr_brightness,
                    }
                )
            if ATTR_RGBW_COLOR in kwargs:
                r, g, b, w = self._attr_rgbw_color
                color_val = (w << 24) | (r << 16) | (g << 8) | b
                params.append({"idx": "P2", "type": CMD_TYPE_SET_RAW, "val": color_val})
            if ATTR_EFFECT in kwargs:
                params.append(
                    {
                        "idx": "P2",
                        "type": CMD_TYPE_SET_RAW,
                        "val": ALL_EFFECT_MAP[self._attr_effect],
                    }
                )
            if params:
                await self._client.async_send_multi_command(self.agt, self.me, params)
            await self._client.turn_on_light_switch_async("P1", self.agt, self.me)
        except Exception as e:
            _LOGGER.error(
                "Failed to turn on light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self._attr_brightness = original_brightness
            self._attr_rgbw_color = original_rgbw_color
            self._attr_effect = original_effect
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light with robust optimistic update."""
        original_is_on = self._attr_is_on

        self._attr_is_on = False
        self.async_write_ha_state()

        try:
            await self._client.turn_off_light_switch_async("P1", self.agt, self.me)
        except Exception as e:
            _LOGGER.error(
                "Failed to turn off light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            self._attr_is_on = original_is_on
            self.async_write_ha_state()


class LifeSmartSingleIORGBWLight(LifeSmartBaseLight):
    """单IO口控制的RGBW灯。"""

    def __init__(self, raw_device: dict, client: Any, entry_id: str, io_key: str):
        super().__init__(raw_device, client, entry_id, io_key)
        self._attr_supported_features = LightEntityFeature.EFFECT

    @callback
    def _initialize_state(self) -> None:
        """初始化单IO RGBW灯状态。"""
        sub_data = self._sub_data
        self._attr_is_on = sub_data.get("type", 0) % 2 == 1
        self._attr_supported_color_modes = {ColorMode.RGBW}
        self._attr_color_mode = ColorMode.RGBW
        self._attr_effect_list = DYN_EFFECT_LIST

        if (val := sub_data.get("val")) is not None:
            r, g, b, w_flag = _parse_color_value(val, has_white=True)
            if w_flag >= 128:
                self._attr_effect = next(
                    (k for k, v in DYN_EFFECT_MAP.items() if v == val), None
                )
                self._attr_brightness = 255
                self._attr_rgbw_color = (r, g, b, 0)
            else:
                self._attr_effect = None
                self._attr_brightness = round(w_flag / 100 * 255)
                self._attr_rgbw_color = (r, g, b, 255 if w_flag > 0 else 0)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """
        开启单IO RGBW灯，严格遵循设备协议。
        协议: type=0xff, val=颜色/动态值; 或 type=0x81, val=1
        """
        # 保存原始状态，以备回滚
        original_is_on = self._attr_is_on
        original_brightness = self._attr_brightness
        original_rgbw_color = self._attr_rgbw_color
        original_effect = self._attr_effect

        cmd_type, cmd_val = CMD_TYPE_ON, 1  # 默认为普通开灯

        # 优先处理效果
        self._attr_is_on = True
        if ATTR_EFFECT in kwargs:
            self._attr_effect = kwargs[ATTR_EFFECT]
            self._attr_rgbw_color = None  # 效果模式下，静态颜色无意义
            self._attr_brightness = 255  # 效果模式下，亮度视为全亮

            effect_val = DYN_EFFECT_MAP.get(self._attr_effect)
            if effect_val is not None:
                cmd_type, cmd_val = CMD_TYPE_SET_RAW, effect_val

        # 其次处理颜色
        elif ATTR_RGBW_COLOR in kwargs:
            self._attr_effect = None
            self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]

            # 协议不支持同时设置颜色和亮度，优先保证颜色。
            # 亮度乐观更新为全亮。
            self._attr_brightness = 255

            r, g, b, w = self._attr_rgbw_color
            color_val = (w << 24) | (r << 16) | (g << 8) | b
            cmd_type, cmd_val = CMD_TYPE_SET_RAW, color_val

        # 如果只调节亮度，这通常意味着用户想要白光
        elif ATTR_BRIGHTNESS in kwargs:
            self._attr_effect = None
            brightness = kwargs[ATTR_BRIGHTNESS]
            self._attr_brightness = brightness

            # 将亮度转换为白光值 (W通道)
            # 注意：协议中没有明确定义如何用亮度设置白光，
            # 这里我们假设将亮度值编码到W通道，RGB为0。
            w = brightness
            r, g, b = 0, 0, 0
            self._attr_rgbw_color = (r, g, b, w)

            color_val = (w << 24) | (r << 16) | (g << 8) | b
            cmd_type, cmd_val = CMD_TYPE_SET_RAW, color_val

        self.async_write_ha_state()

        # 3. 发送命令并处理异常
        try:
            await self._client.async_send_single_command(
                self.agt, self.me, self._sub_key, cmd_type, cmd_val
            )
        except Exception as e:
            _LOGGER.error(
                "Failed to turn on light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            # 4. 失败则回滚状态
            self._attr_is_on = original_is_on
            self._attr_brightness = original_brightness
            self._attr_rgbw_color = original_rgbw_color
            self._attr_effect = original_effect
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """
        关闭单IO RGBW灯。
        协议: type=0x80, val=0
        """
        # 1. 保存原始状态
        original_is_on = self._attr_is_on

        # 2. 执行乐观更新
        self._attr_is_on = False
        self.async_write_ha_state()

        # 3. 发送命令并处理异常
        try:
            await self._client.async_send_single_command(
                self.agt, self.me, self._sub_key, CMD_TYPE_OFF, 0
            )
        except Exception as e:
            _LOGGER.error(
                "Failed to turn off light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            # 4. 失败则回滚状态
            self._attr_is_on = original_is_on
            self.async_write_ha_state()


class LifeSmartDualIORGBWLight(LifeSmartBaseLight):
    """
    双IO口控制的RGBW灯。

    严格遵循官方文档逻辑：
    1. DYN（效果）优先级高于 RGBW（颜色）。
    2. 设置颜色时，必须显式关闭DYN。
    3. 设置效果时，必须确保RGBW处于开启状态。
    """

    def __init__(
        self,
        raw_device: dict,
        client: Any,
        entry_id: str,
        color_io: str,
        effect_io: str,
    ):
        self._color_io = color_io
        self._effect_io = effect_io
        super().__init__(raw_device, client, entry_id)
        self._attr_supported_features = LightEntityFeature.EFFECT

    @callback
    def _initialize_state(self) -> None:
        """初始化双IO RGBW灯状态。"""
        data = self._sub_data
        color_data = data.get(self._color_io, {})
        dyn_data = data.get(self._effect_io, {})

        self._attr_is_on = color_data.get("type", 0) % 2 == 1
        self._attr_brightness = 255 if self._attr_is_on else 0
        self._attr_supported_color_modes = {ColorMode.RGBW}
        self._attr_color_mode = ColorMode.RGBW
        self._attr_effect_list = DYN_EFFECT_LIST

        if dyn_data.get("type", 0) % 2 == 1:
            self._attr_effect = next(
                (k for k, v in DYN_EFFECT_MAP.items() if v == dyn_data.get("val")), None
            )
        else:
            self._attr_effect = None

        self._attr_rgbw_color = _parse_color_value(
            color_data.get("val", 0), has_white=True
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """
        开启双IO RGBW灯，并根据参数设置颜色或效果。
        """
        # 1. 保存原始状态，以备回滚
        original_is_on = self._attr_is_on
        original_brightness = self._attr_brightness
        original_rgbw_color = self._attr_rgbw_color
        original_effect = self._attr_effect

        # 2. 执行乐观更新
        self._attr_is_on = True
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_RGBW_COLOR in kwargs:
            self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]
            self._attr_effect = None  # 设置颜色时，效果应被清除
        if ATTR_EFFECT in kwargs:
            self._attr_effect = kwargs[ATTR_EFFECT]
            self._attr_rgbw_color = None  # 设置效果时，颜色无意义
            self._attr_brightness = 255  # 效果模式下，亮度视为全亮
        self.async_write_ha_state()

        # 3. 发送命令并处理异常
        try:
            io_list = []
            # 场景1: 设置动态效果 (DYN 优先级最高)
            if ATTR_EFFECT in kwargs:
                effect_val = DYN_EFFECT_MAP.get(self._attr_effect)
                if effect_val is not None:
                    io_list = [
                        {"idx": self._color_io, "type": CMD_TYPE_ON, "val": 1},
                        {
                            "idx": self._effect_io,
                            "type": CMD_TYPE_SET_RAW,
                            "val": effect_val,
                        },
                    ]
            # 场景2: 设置静态颜色 (或仅亮度)
            elif ATTR_RGBW_COLOR in kwargs or ATTR_BRIGHTNESS in kwargs:
                rgbw = (
                    self._attr_rgbw_color
                    if self._attr_rgbw_color
                    else (255, 255, 255, 255)
                )
                ratio = self._attr_brightness / 255.0
                final_rgbw = tuple(round(c * ratio) for c in rgbw)

                r, g, b, w = final_rgbw
                color_val = (w << 24) | (r << 16) | (g << 8) | b

                io_list = [
                    {"idx": self._color_io, "type": CMD_TYPE_SET_RAW, "val": color_val},
                    {"idx": self._effect_io, "type": CMD_TYPE_OFF, "val": 0},
                ]

            if io_list:
                await self._client.async_send_multi_command(self.agt, self.me, io_list)
            else:
                # 如果只调用 turn_on 而没有颜色/效果参数，则默认打开
                await self._client.turn_on_light_switch_async(
                    self._color_io, self.agt, self.me
                )
        except Exception as e:
            _LOGGER.error(
                "Failed to turn on light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            # 4. 失败则回滚状态
            self._attr_is_on = original_is_on
            self._attr_brightness = original_brightness
            self._attr_rgbw_color = original_rgbw_color
            self._attr_effect = original_effect
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭双IO RGBW灯，同时关闭颜色和效果通道。"""
        # 1. 保存原始状态
        original_is_on = self._attr_is_on

        # 2. 执行乐观更新
        self._attr_is_on = False
        self.async_write_ha_state()

        # 3. 发送命令并处理异常
        try:
            io_list = [
                {"idx": self._color_io, "type": CMD_TYPE_OFF, "val": 0},
                {"idx": self._effect_io, "type": CMD_TYPE_OFF, "val": 0},
            ]
            await self._client.async_send_multi_command(self.agt, self.me, io_list)
        except Exception as e:
            _LOGGER.error(
                "Failed to turn off light %s. Reverting state. Error: %s",
                self.entity_id,
                e,
            )
            # 4. 失败则回滚状态
            self._attr_is_on = original_is_on
            self.async_write_ha_state()


class LifeSmartSPOTRGBWLight(LifeSmartDualIORGBWLight):
    """SPOT灯 (RGBW模式)，继承自双IO灯。"""

    def __init__(self, raw_device: dict, client: Any, entry_id: str):
        super().__init__(raw_device, client, entry_id, color_io="RGBW", effect_io="DYN")


class LifeSmartCoverLight(LifeSmartBaseLight):
    """车库门附属灯。"""

    def __init__(
        self, raw_device: dict, client: Any, entry_id: str, sub_device_key: str
    ):
        super().__init__(raw_device, client, entry_id, sub_device_key)

    @callback
    def _initialize_state(self) -> None:
        """初始化车库门灯状态。"""
        self._attr_is_on = self._sub_data.get("type", 0) % 2 == 1
        self._attr_color_mode = ColorMode.ONOFF
        self._attr_supported_color_modes = {ColorMode.ONOFF}
