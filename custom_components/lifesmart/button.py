"""Support for LifeSmart buttons by @MapleEve"""

import logging

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
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
    # 按钮平台相关
    # 命令常量
    CMD_TYPE_PRESS,
)
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_device_platform_mapping

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart buttons from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    buttons = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 检查是否支持按钮平台
        platform_mapping = get_device_platform_mapping(device)
        if "button" not in platform_mapping:
            continue

        button_config = platform_mapping.get("button", {})

        # 为每个支持的按钮子设备创建实体
        for btn_key, btn_config in button_config.items():
            if isinstance(btn_config, dict) and btn_config.get("enabled", True):
                button = LifeSmartButton(
                    device,
                    btn_key,
                    btn_config,
                    hub,
                )
                buttons.append(button)
                _LOGGER.debug(
                    "Added button %s for device %s",
                    btn_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if buttons:
        async_add_entities(buttons)
        _LOGGER.info("Added %d LifeSmart buttons", len(buttons))


class LifeSmartButton(LifeSmartEntity, ButtonEntity):
    """LifeSmart button implementation."""

    def __init__(
        self,
        device: dict,
        sub_key: str,
        btn_config: dict,
        hub,
    ) -> None:
        """Initialize the button."""
        super().__init__(device, sub_key, hub)
        self._btn_config = btn_config
        self._attr_device_class = ButtonDeviceClass.GENERIC

        # 从配置中获取设备类别
        if "device_class" in btn_config:
            try:
                self._attr_device_class = ButtonDeviceClass(btn_config["device_class"])
            except ValueError:
                _LOGGER.warning(
                    "Invalid button device class: %s", btn_config["device_class"]
                )

    @property
    def unique_id(self) -> str:
        """Return unique id for the button."""
        return generate_unique_id(
            self._device.get(DEVICE_TYPE_KEY, ""),
            self._device.get(HUB_ID_KEY, ""),
            self._device.get(DEVICE_ID_KEY, ""),
            self._sub_key,
        )

    @property
    def name(self) -> str:
        """Return the name of the button."""
        device_name = self._device.get(DEVICE_NAME_KEY, "Unknown Device")
        btn_name = self._btn_config.get("name", self._sub_key)
        return f"{device_name} {btn_name}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._device.get(DEVICE_DATA_KEY, {}))

    async def async_press(self) -> None:
        """Press the button."""
        try:
            # 发送按钮按下命令
            await self._hub.async_send_command(
                self._device[HUB_ID_KEY],
                self._device[DEVICE_ID_KEY],
                self._sub_key,
                CMD_TYPE_PRESS,
                1,  # 按下状态
            )

            _LOGGER.debug(
                "Pressed button %s on device %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to press button %s on device %s: %s",
                self._sub_key,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # 按钮不需要状态更新，但保持连接以确保设备在线状态正确
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
