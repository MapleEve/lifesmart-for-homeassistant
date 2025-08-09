"""Support for LifeSmart locks by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
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
    # 门锁平台相关
    LOCK_STATE_LOCKED,
    LOCK_STATE_UNLOCKED,
    UNLOCK_METHOD,
    # 命令常量
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
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
    """Set up LifeSmart locks from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    locks = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 检查是否支持门锁平台
        platform_mapping = get_device_platform_mapping(device)
        if "lock" not in platform_mapping:
            continue

        lock_config = platform_mapping.get("lock", {})

        # 为每个支持的门锁子设备创建实体
        for lock_key, lock_cfg in lock_config.items():
            if isinstance(lock_cfg, dict) and lock_cfg.get("enabled", True):
                lock = LifeSmartLock(
                    device,
                    lock_key,
                    lock_cfg,
                    hub,
                )
                locks.append(lock)
                _LOGGER.debug(
                    "Added lock %s for device %s",
                    lock_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if locks:
        async_add_entities(locks)
        _LOGGER.info("Added %d LifeSmart locks", len(locks))


class LifeSmartLock(LifeSmartEntity, LockEntity):
    """LifeSmart lock implementation."""

    def __init__(
        self,
        device: dict,
        sub_key: str,
        lock_config: dict,
        hub,
    ) -> None:
        """Initialize the lock."""
        super().__init__(device, sub_key, hub)
        self._lock_config = lock_config
        self._attr_supported_features = LockEntityFeature.OPEN

        self._attr_is_locked = None
        self._attr_is_locking = False
        self._attr_is_unlocking = False
        self._attr_is_jammed = False

        # 额外属性
        self._unlock_method = None
        self._battery_level = None

    @property
    def unique_id(self) -> str:
        """Return unique id for the lock."""
        return generate_unique_id(
            self._device.get(DEVICE_TYPE_KEY, ""),
            self._device.get(HUB_ID_KEY, ""),
            self._device.get(DEVICE_ID_KEY, ""),
            self._sub_key,
        )

    @property
    def name(self) -> str:
        """Return the name of the lock."""
        device_name = self._device.get(DEVICE_NAME_KEY, "Unknown Device")
        lock_name = self._lock_config.get("name", self._sub_key)
        return f"{device_name} {lock_name}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._device.get(DEVICE_DATA_KEY, {}))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attributes = {}

        if self._unlock_method is not None:
            method_name = UNLOCK_METHOD.get(self._unlock_method, "Unknown")
            attributes["unlock_method"] = method_name

        if self._battery_level is not None:
            attributes["battery_level"] = self._battery_level

        return attributes

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        try:
            self._attr_is_locking = True
            self.async_write_ha_state()

            await self._send_lock_command(CMD_TYPE_ON, LOCK_STATE_LOCKED)

            _LOGGER.debug(
                "Locked lock %s on device %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to lock %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )
        finally:
            self._attr_is_locking = False
            self.async_write_ha_state()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        try:
            self._attr_is_unlocking = True
            self.async_write_ha_state()

            await self._send_lock_command(CMD_TYPE_OFF, LOCK_STATE_UNLOCKED)

            _LOGGER.debug(
                "Unlocked lock %s on device %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to unlock %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )
        finally:
            self._attr_is_unlocking = False
            self.async_write_ha_state()

    async def async_open(self, **kwargs: Any) -> None:
        """Open (unlatch) the lock."""
        if not (self.supported_features & LockEntityFeature.OPEN):
            return

        try:
            # 发送开门命令（通常与解锁命令不同）
            await self._send_lock_command(CMD_TYPE_OFF, 2)  # 开门状态值

            _LOGGER.debug(
                "Opened lock %s on device %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to open %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    async def _send_lock_command(self, cmd_type: int, value: Any) -> None:
        """Send command to lock."""
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

        # 检查门锁状态数据
        lock_data = device_data.get(self._sub_key)
        if lock_data is None:
            return

        # 处理IO数据
        processed_value = process_io_data(lock_data, self._lock_config)

        if isinstance(processed_value, dict):
            # 复杂状态数据
            self._attr_is_locked = processed_value.get("is_locked")
            self._attr_is_jammed = processed_value.get("is_jammed", False)
            self._unlock_method = processed_value.get("unlock_method")
            self._battery_level = processed_value.get("battery_level")
        else:
            # 简单布尔值 - 上锁状态
            self._attr_is_locked = bool(processed_value)

        # 检查电池电量数据
        battery_data = device_data.get("BAT")
        if battery_data:
            battery_processed = process_io_data(battery_data, {"type": "percentage"})
            if isinstance(battery_processed, (int, float)):
                self._battery_level = int(battery_processed)

        # 检查解锁方式数据 (部分门锁提供)
        unlock_data = device_data.get("UMD")
        if unlock_data:
            unlock_processed = process_io_data(unlock_data, {"type": "unlock_method"})
            if isinstance(unlock_processed, int):
                self._unlock_method = unlock_processed

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
