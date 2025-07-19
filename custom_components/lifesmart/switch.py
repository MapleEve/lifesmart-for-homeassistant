"""Support for LifeSmart switch by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, LifeSmartEntity, generate_entity_id, async_setup_entities
from .const import (
    # --- 核心常量 ---
    DEVICE_DATA_KEY,
    # --- 设备类型常量 ---
    SUPPORTED_SWITCH_TYPES,
    ALL_SWITCH_TYPES,
    SMART_PLUG_TYPES,
    POWER_METER_PLUG_TYPES,
    GARAGE_DOOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart switches from a config entry."""
    
    # Define device type to entity class mapping for switches
    SWITCH_ENTITY_MAP = {}
    
    # Add all switch types to the mapping
    for device_type in ALL_SWITCH_TYPES:
        SWITCH_ENTITY_MAP[device_type] = LifeSmartSwitch
    
    # Define device filter function for switches
    def device_filter(device_type: str, device: dict) -> bool:
        """Filter devices that should be handled by switch platform."""
        # Special handling for SL_NATURE - only include switch version
        if device_type == "SL_NATURE":
            p5_val = device.get(DEVICE_DATA_KEY, {}).get("P5", {}).get("val", 1) & 0xFF
            return p5_val == 1
        
        return device_type in ALL_SWITCH_TYPES
    
    # Use the generic setup helper
    await async_setup_entities(
        hass=hass,
        config_entry=config_entry,
        async_add_entities=async_add_entities,
        platform=Platform.SWITCH,
        entity_class_map=SWITCH_ENTITY_MAP,
        device_filter_func=device_filter,
        sub_device_filter_func=_is_switch_subdevice,
    )


def _is_switch_subdevice(device_type: str, sub_key: str) -> bool:
    """
    Determine if a sub-device is a valid switch based on device type.
    """
    sub_key_upper = sub_key.upper()

    # SL_P_SW (九路开关控制器) 的 P1-P9 都是开关
    if device_type == "SL_P_SW":
        return sub_key_upper in {f"P{i}" for i in range(1, 10)}

    # SL_SW* 和 SL_MC* 系列, P4 是电量, 明确排除
    if device_type in SUPPORTED_SWITCH_TYPES and sub_key_upper == "P4":
        return False

    # SL_SC_BB_V2 (随心按键) 的 P1 是事件触发器, 不是开关
    if device_type == "SL_SC_BB_V2":
        return False

    # 处理 SL_OL* 系列智慧插座，它们的开关 idx 是 'O'
    if device_type in {"SL_OL", "SL_OL_3C", "SL_OL_DE", "SL_OL_UK", "SL_OL_UL"}:
        return sub_key_upper == "O"

    # 处理 SL_OE* 系列计量插座
    if device_type in POWER_METER_PLUG_TYPES:
        # P1 是主开关, P4 是功率门限开关
        return sub_key_upper in {"P1", "P4"}

    # 处理其他所有标准开关和插座 (如多联开关, WiFi插座等)
    # 它们的开关 idx 通常是 L1-L3 或 P1-P3
    if sub_key_upper in {"L1", "L2", "L3", "P1", "P2", "P3"}:
        return True

    if device_type in GARAGE_DOOR_TYPES:
        return False

    return False


class LifeSmartSwitch(LifeSmartEntity, SwitchEntity):
    """LifeSmart switch entity with full state management."""

    def __init__(
        self,
        device: LifeSmartDevice,
        raw_device: dict[str, Any],
        sub_device_key: str,
        sub_device_data: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """Initialize the switch."""
        # Call parent constructor
        super().__init__(device, raw_device, client, entry_id, sub_device_key)
        
        # Store sub_device_data for switch-specific use
        self._sub_data = sub_device_data
        
        # Set switch-specific attributes
        self._attr_device_class = self._determine_device_class()
        
        # Initialize state
        self._attr_is_on = self._parse_state(sub_device_data)

    @callback
    def _determine_device_class(self) -> SwitchDeviceClass:
        """Determine device class for better UI representation."""
        if self._devtype in (SMART_PLUG_TYPES + POWER_METER_PLUG_TYPES):
            return SwitchDeviceClass.OUTLET
        return SwitchDeviceClass.SWITCH

    @callback
    def _parse_state(self, data: dict) -> bool:
        """Parse the on/off state from device data, aligning with the knowledge base."""
        # 知识库明确指出: type%2==1 或 type&0x01==1 表示开启
        return data.get("type", 0) & 0x01 == 1

    @callback
    def _handle_update(self, new_data: dict) -> None:
        """Handle real-time updates from the WebSocket."""
        if new_data:
            self._attr_is_on = self._parse_state(new_data)
            self.async_write_ha_state()

    def _update_from_sub_data(self, sub_data: dict) -> None:
        """Update switch state from sub-device data during global refresh."""
        self._attr_is_on = self._parse_state(sub_data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        result = await self._client.turn_on_light_switch_async(
            self._sub_key, self._agt, self._me
        )
        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()
        else:
            _LOGGER.warning(
                "Failed to turn on switch %s (dev: %s, sub: %s)",
                self.name,
                self._me,
                self._sub_key,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        result = await self._client.turn_off_light_switch_async(
            self._sub_key, self._agt, self._me
        )
        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()
        else:
            _LOGGER.warning(
                "Failed to turn off switch %s (dev: %s, sub: %s)",
                self.name,
                self._me,
                self._sub_key,
            )
