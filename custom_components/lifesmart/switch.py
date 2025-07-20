"""Support for LifeSmart switch by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, generate_entity_id
from .const import (
    # --- 核心常量 ---
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    SUBDEVICE_INDEX_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
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
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices = hass.data[DOMAIN][entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][entry_id]["exclude_hubs"]

    switches = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]

        # 增加对 SL_NATURE 的特殊处理
        if device_type == "SL_NATURE":
            # 只处理开关版 SL_NATURE
            p5_val = device.get(DEVICE_DATA_KEY, {}).get("P5", {}).get("val", 1) & 0xFF
            if p5_val != 1:
                continue

        # 使用聚合列表判断是否为开关设备
        if device_type not in ALL_SWITCH_TYPES:
            continue

        ha_device = LifeSmartDevice(device, client)

        for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
            # 使用辅助函数判断子设备是否为开关
            if _is_switch_subdevice(device_type, sub_key):
                switches.append(
                    LifeSmartSwitch(
                        device=ha_device,
                        raw_device=device,
                        sub_device_key=sub_key,
                        sub_device_data=sub_data,
                        client=client,
                        entry_id=entry_id,
                    )
                )

    async_add_entities(switches)


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


class LifeSmartSwitch(SwitchEntity):
    """LifeSmart switch entity with full state management."""

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
        """Initialize the switch."""
        self._device = device
        self._raw_device = raw_device
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._client = client
        self._entry_id = entry_id

        # --- 设置核心属性 ---
        self._attr_unique_id = generate_entity_id(
            raw_device[DEVICE_TYPE_KEY],
            raw_device[HUB_ID_KEY],
            raw_device[DEVICE_ID_KEY],
            sub_device_key,
        )
        self._attr_name = self._generate_switch_name()
        self._attr_device_class = self._determine_device_class()
        self._attr_extra_state_attributes = {
            HUB_ID_KEY: raw_device[HUB_ID_KEY],
            DEVICE_ID_KEY: raw_device[DEVICE_ID_KEY],
            SUBDEVICE_INDEX_KEY: self._sub_key,
        }

        # --- 初始化状态 ---
        self._attr_is_on = self._parse_state(sub_device_data)

    @callback
    def _generate_switch_name(self) -> str:
        """Generate user-friendly switch name."""
        base_name = self._raw_device.get(DEVICE_NAME_KEY, "Unknown Switch")
        # 如果子设备有自己的名字 (如多联开关的按键名)，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} {self._sub_key.upper()}"

    @callback
    def _determine_device_class(self) -> SwitchDeviceClass:
        """Determine device class for better UI representation."""
        if self._raw_device[DEVICE_TYPE_KEY] in (
            SMART_PLUG_TYPES + POWER_METER_PLUG_TYPES
        ):
            return SwitchDeviceClass.OUTLET
        return SwitchDeviceClass.SWITCH

    @callback
    def _parse_state(self, data: dict) -> bool:
        """Parse the on/off state from device data, aligning with the knowledge base."""
        # 知识库明确指出: type%2==1 或 type&0x01==1 表示开启
        return data.get("type", 0) & 0x01 == 1

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息以链接实体到单个设备。"""
        # 从 self._raw_device 中安全地获取 hub_id 和 device_id
        hub_id = self._raw_device.get(HUB_ID_KEY)
        device_id = self._raw_device.get(DEVICE_ID_KEY)

        # 确保 identifiers 即使在 hub_id 或 device_id 为 None 的情况下也不会出错
        identifiers = set()
        if hub_id and device_id:
            identifiers.add((DOMAIN, hub_id, device_id))

        return DeviceInfo(
            identifiers=identifiers,
            name=self._raw_device.get(
                DEVICE_NAME_KEY, "Unnamed Device"
            ),  # 安全获取名称
            manufacturer=MANUFACTURER,
            model=self._raw_device.get(DEVICE_TYPE_KEY),  # 安全获取型号
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=((DOMAIN, hub_id) if hub_id else None),
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        # 监听特定实体的实时更新
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )
        # 监听全局数据刷新，确保状态最终一致
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    @callback
    def _handle_update(self, new_data: dict) -> None:
        """Handle real-time updates from the WebSocket."""
        if new_data:
            self._attr_is_on = self._parse_state(new_data)
            self.async_write_ha_state()

    @callback
    def _handle_global_refresh(self) -> None:
        """Handle global data refresh to sync state."""
        try:
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
                sub_data = current_device.get(DEVICE_DATA_KEY, {}).get(self._sub_key)
                if sub_data:
                    self._attr_is_on = self._parse_state(sub_data)
                    self.async_write_ha_state()
        except (KeyError, StopIteration):
            _LOGGER.warning(
                "Could not find device %s during global refresh.", self._attr_unique_id
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        result = await self._client.turn_on_light_switch_async(
            self._sub_key, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY]
        )
        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()
        else:
            _LOGGER.warning(
                "Failed to turn on switch %s (dev: %s, sub: %s)",
                self._attr_name,
                self._raw_device[DEVICE_ID_KEY],
                self._sub_key,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        result = await self._client.turn_off_light_switch_async(
            self._sub_key, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY]
        )
        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()
        else:
            _LOGGER.warning(
                "Failed to turn off switch %s (dev: %s, sub: %s)",
                self._attr_name,
                self._raw_device[DEVICE_ID_KEY],
                self._sub_key,
            )
