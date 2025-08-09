"""Support for LifeSmart sirens by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.siren import SirenEntity, SirenEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
    # 警报平台相关
    SIREN_DURATION,
    SIREN_VOLUME_LEVELS,
    # 命令常量
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
)
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_siren_subdevices
from .core.platform.platform_detection import safe_get

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart sirens from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    sirens = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 使用平台检测函数获取siren子设备
        siren_subdevices = get_siren_subdevices(device)

        # 为每个支持的siren子设备创建实体
        for sub_key in siren_subdevices:
            sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
            if sub_device_data:  # 只有当存在实际数据时才创建实体
                siren = LifeSmartSiren(
                    raw_device=device,
                    client=hub.get_client(),
                    entry_id=config_entry.entry_id,
                    sub_device_key=sub_key,
                    sub_device_data=sub_device_data,
                )
                sirens.append(siren)
                _LOGGER.debug(
                    "Added siren %s for device %s",
                    sub_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if sirens:
        async_add_entities(sirens)
        _LOGGER.info("Added %d LifeSmart sirens", len(sirens))


class LifeSmartSiren(LifeSmartEntity, SirenEntity):
    """LifeSmart siren implementation."""

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """Initialize the siren."""
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        # 生成警报器名称和ID
        self._attr_name = self._generate_siren_name()
        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )

        # 警报器特性支持
        self._attr_supported_features = (
            SirenEntityFeature.TURN_ON
            | SirenEntityFeature.TURN_OFF
            | SirenEntityFeature.DURATION
            | SirenEntityFeature.VOLUME_SET
        )

        # 可用的音量级别
        self._attr_available_volume_levels = SIREN_VOLUME_LEVELS

        # 从子设备数据获取初始状态
        self._attr_is_on = self._extract_initial_state()
        self._attr_volume_level = self._extract_volume_level()

    @callback
    def _generate_siren_name(self) -> str | None:
        """Generate user-friendly siren name."""
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} Siren {self._sub_key.upper()}"

    @callback
    def _extract_initial_state(self) -> bool:
        """Extract initial siren state from device data."""
        # 检查type字段的最低位确定开关状态
        siren_type = self._sub_data.get("type", 0)
        return bool(siren_type & 1)

    @callback
    def _extract_volume_level(self) -> int | None:
        """Extract volume level from device data."""
        # 从val字段提取音量级别
        volume = self._sub_data.get("val")
        if volume is not None:
            # 确保音量在有效范围内
            volume = max(1, min(len(SIREN_VOLUME_LEVELS), int(volume)))
            return volume
        return None

    @property
    def is_on(self) -> bool:
        """Return True if the siren is on."""
        return self._attr_is_on

    @property
    def volume_level(self) -> int | None:
        """Return the volume level of the siren."""
        return self._attr_volume_level

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the siren."""
        try:
            # 获取参数
            duration = kwargs.get("duration", SIREN_DURATION)
            volume_level = kwargs.get("volume_level", self._attr_volume_level or 3)

            # 首先设置音量（如果指定）
            if volume_level != self._attr_volume_level:
                await self._client.async_send_command(
                    self.agt,
                    self.me,
                    self._sub_key,
                    CMD_TYPE_SET_VAL,
                    volume_level,
                )
                self._attr_volume_level = volume_level

            # 开启警报
            await self._client.async_send_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_ON,
                1,
            )

            self._attr_is_on = True
            self.async_write_ha_state()

            _LOGGER.debug(
                "Turned on siren %s on device %s with volume %s for %s seconds",
                self._sub_key,
                self._name,
                volume_level,
                duration,
            )

            # 如果指定了持续时间，则设置自动关闭
            if duration and duration > 0:
                self.hass.async_create_task(self._auto_turn_off(duration))

        except Exception as err:
            _LOGGER.error(
                "Failed to turn on siren %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the siren."""
        try:
            await self._client.async_send_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_OFF,
                0,
            )
            self._attr_is_on = False
            self.async_write_ha_state()

            _LOGGER.debug(
                "Turned off siren %s on device %s",
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to turn off siren %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def async_set_volume_level(self, volume_level: int) -> None:
        """Set the volume level of the siren."""
        try:
            # 确保音量在有效范围内
            volume_level = max(1, min(len(SIREN_VOLUME_LEVELS), volume_level))

            await self._client.async_send_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_SET_VAL,
                volume_level,
            )

            self._attr_volume_level = volume_level
            self.async_write_ha_state()

            _LOGGER.debug(
                "Set volume level to %s for siren %s on device %s",
                volume_level,
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to set volume level for siren %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def _auto_turn_off(self, duration: int) -> None:
        """Auto turn off the siren after specified duration."""
        import asyncio

        try:
            await asyncio.sleep(duration)
            if self._attr_is_on:
                await self.async_turn_off()
                _LOGGER.debug(
                    "Auto turned off siren %s after %s seconds",
                    self._sub_key,
                    duration,
                )
        except Exception as err:
            _LOGGER.error(
                "Error in auto turn off for siren %s: %s",
                self._sub_key,
                err,
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to updates."""
        await super().async_added_to_hass()

        # 实体特定更新
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )

        # 全局更新
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    async def _handle_update(self, new_data: dict) -> None:
        """Handle real-time updates."""
        try:
            if not new_data:
                return

            # 提取IO数据
            io_data = {}
            if "msg" in new_data and isinstance(new_data["msg"], dict):
                io_data = new_data["msg"].get(self._sub_key, {})
            elif self._sub_key in new_data:
                io_data = new_data[self._sub_key]
            else:
                io_data = new_data

            if not io_data:
                return

            state_changed = False

            # 更新警报状态
            if "type" in io_data:
                new_state = bool(io_data["type"] & 1)
                if self._attr_is_on != new_state:
                    self._attr_is_on = new_state
                    state_changed = True

            # 更新音量级别
            if "val" in io_data:
                new_volume = max(1, min(len(SIREN_VOLUME_LEVELS), int(io_data["val"])))
                if self._attr_volume_level != new_volume:
                    self._attr_volume_level = new_volume
                    state_changed = True

            if state_changed:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error handling siren update for %s: %s", self._attr_unique_id, e
            )

    async def _handle_global_refresh(self) -> None:
        """Handle periodic full data refresh."""
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (
                    d
                    for d in devices
                    if d[HUB_ID_KEY] == self.agt and d[DEVICE_ID_KEY] == self.me
                ),
                None,
            )

            if current_device is None:
                if self.available:
                    _LOGGER.warning(
                        "Siren device %s not found during global refresh, "
                        "marking as unavailable.",
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            new_sub_data = safe_get(current_device, DEVICE_DATA_KEY, self._sub_key)
            if new_sub_data is None:
                if self.available:
                    _LOGGER.warning(
                        "Siren sub-device %s for %s not found, marking as unavailable.",
                        self._sub_key,
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            if not self.available:
                self._attr_available = True

            self._sub_data = new_sub_data
            new_state = self._extract_initial_state()
            new_volume = self._extract_volume_level()

            state_changed = False
            if self._attr_is_on != new_state:
                self._attr_is_on = new_state
                state_changed = True

            if self._attr_volume_level != new_volume:
                self._attr_volume_level = new_volume
                state_changed = True

            if state_changed:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during siren global refresh for %s: %s", self.unique_id, e
            )
