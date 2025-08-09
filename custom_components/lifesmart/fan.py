"""Support for LifeSmart fans by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .core.const import (
    # 核心常量
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    # 风扇平台相关
    FAN_SPEED_LEVELS,
    FAN_PRESET_MODES,
    # 命令常量
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
)
from .core.data.processors import process_io_data
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_device_platform_mapping

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart fans from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    fans = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 检查是否支持风扇平台
        platform_mapping = get_device_platform_mapping(device)
        if "fan" not in platform_mapping:
            continue

        fan_config = platform_mapping.get("fan", {})

        # 为每个支持的风扇子设备创建实体
        for fan_key, fan_config in fan_config.items():
            if isinstance(fan_config, dict) and fan_config.get("enabled", True):
                fan = LifeSmartFan(
                    device,
                    fan_key,
                    fan_config,
                    hub,
                )
                fans.append(fan)
                _LOGGER.debug(
                    "Added fan %s for device %s",
                    fan_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if fans:
        async_add_entities(fans)
        _LOGGER.info("Added %d LifeSmart fans", len(fans))


class LifeSmartFan(LifeSmartEntity, FanEntity):
    """LifeSmart fan implementation."""

    def __init__(
        self,
        device: dict,
        sub_key: str,
        fan_config: dict,
        hub,
    ) -> None:
        """Initialize the fan."""
        super().__init__(device, sub_key, hub)
        self._fan_config = fan_config
        self._attr_supported_features = FanEntityFeature.SET_SPEED

        # 从配置获取支持的功能
        if fan_config.get("supports_preset_modes", False):
            self._attr_supported_features |= FanEntityFeature.PRESET_MODE

        if fan_config.get("supports_oscillate", False):
            self._attr_supported_features |= FanEntityFeature.OSCILLATE

        if fan_config.get("supports_direction", False):
            self._attr_supported_features |= FanEntityFeature.DIRECTION

        # 设置速度级别和预设模式
        self._attr_speed_count = len(FAN_SPEED_LEVELS)
        self._attr_preset_modes = (
            FAN_PRESET_MODES
            if self.supported_features & FanEntityFeature.PRESET_MODE
            else None
        )

        self._attr_is_on = False
        self._attr_percentage = 0
        self._attr_preset_mode = None
        self._attr_oscillating = False
        self._attr_current_direction = "forward"

    @property
    def unique_id(self) -> str:
        """Return unique id for the fan."""
        return generate_unique_id(
            self._device.get(DEVICE_TYPE_KEY, ""),
            self._device.get(HUB_ID_KEY, ""),
            self._device.get(DEVICE_ID_KEY, ""),
            self._sub_key,
        )

    @property
    def name(self) -> str:
        """Return the name of the fan."""
        device_name = self._device.get(DEVICE_NAME_KEY, "Unknown Device")
        fan_name = self._fan_config.get("name", self._sub_key)
        return f"{device_name} {fan_name}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._device.get(DEVICE_DATA_KEY, {}))

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the fan on."""
        try:
            if preset_mode:
                await self.async_set_preset_mode(preset_mode)
            elif percentage is not None:
                await self.async_set_percentage(percentage)
            else:
                # 默认开启到中等速度
                await self._send_fan_command(
                    CMD_TYPE_ON, FAN_SPEED_LEVELS[len(FAN_SPEED_LEVELS) // 2]
                )

        except Exception as err:
            _LOGGER.error(
                "Failed to turn on fan %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        try:
            await self._send_fan_command(CMD_TYPE_OFF, 0)
        except Exception as err:
            _LOGGER.error(
                "Failed to turn off fan %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
            return

        try:
            # 将百分比转换为速度级别
            speed_level = percentage_to_ordered_list_item(FAN_SPEED_LEVELS, percentage)
            await self._send_fan_command(CMD_TYPE_SET_VAL, speed_level)

        except Exception as err:
            _LOGGER.error(
                "Failed to set fan speed %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        if preset_mode not in (self.preset_modes or []):
            _LOGGER.warning("Invalid preset mode: %s", preset_mode)
            return

        try:
            # 将预设模式映射为命令值
            preset_values = {
                "auto": 101,
                "sleep": 102,
                "natural": 103,
            }
            value = preset_values.get(preset_mode, 101)
            await self._send_fan_command(CMD_TYPE_SET_CONFIG, value)

        except Exception as err:
            _LOGGER.error(
                "Failed to set fan preset mode %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation of the fan."""
        if not (self.supported_features & FanEntityFeature.OSCILLATE):
            return

        try:
            value = 1 if oscillating else 0
            await self._send_fan_command(CMD_TYPE_SET_CONFIG, value)

        except Exception as err:
            _LOGGER.error(
                "Failed to set fan oscillation %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        if not (self.supported_features & FanEntityFeature.DIRECTION):
            return

        try:
            direction_values = {"forward": 0, "reverse": 1}
            value = direction_values.get(direction, 0)
            await self._send_fan_command(CMD_TYPE_SET_CONFIG, value)

        except Exception as err:
            _LOGGER.error(
                "Failed to set fan direction %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    async def _send_fan_command(self, cmd_type: int, value: Any) -> None:
        """Send command to fan."""
        await self._hub.async_send_command(
            self._device[HUB_ID_KEY],
            self._device[DEVICE_ID_KEY],
            self._sub_key,
            cmd_type,
            value,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device_data = self._device.get(DEVICE_DATA_KEY, {})
        io_data = device_data.get(self._sub_key)

        if io_data is None:
            return

        # 处理IO数据
        processed_value = process_io_data(io_data, self._fan_config)

        # 更新状态
        if isinstance(processed_value, dict):
            self._attr_is_on = processed_value.get("is_on", False)

            # 更新速度百分比
            if "speed_level" in processed_value:
                speed_level = processed_value["speed_level"]
                if speed_level in FAN_SPEED_LEVELS:
                    self._attr_percentage = ordered_list_item_to_percentage(
                        FAN_SPEED_LEVELS, speed_level
                    )
                else:
                    self._attr_percentage = 0

            # 更新预设模式
            if "preset_mode" in processed_value:
                self._attr_preset_mode = processed_value["preset_mode"]

            # 更新摆动状态
            if "oscillating" in processed_value:
                self._attr_oscillating = processed_value["oscillating"]

            # 更新方向
            if "direction" in processed_value:
                self._attr_current_direction = processed_value["direction"]
        else:
            # 简单布尔值处理
            self._attr_is_on = bool(processed_value)
            self._attr_percentage = 50 if self._attr_is_on else 0

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_coordinator_update,
            )
        )
        # 初始状态更新
        self._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.get(DEVICE_ID_KEY))},
            name=self._device.get(DEVICE_NAME_KEY),
            manufacturer=MANUFACTURER,
            model=self._device.get(DEVICE_TYPE_KEY),
            via_device=(DOMAIN, self._device.get(HUB_ID_KEY)),
        )
