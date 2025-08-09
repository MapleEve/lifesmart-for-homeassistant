"""Support for LifeSmart valves by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.valve import ValveEntity, ValveEntityFeature
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
    # 阀门平台相关
    # 命令常量
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
)
from .core.data.processors import process_io_data
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_valve_subdevices
from .core.platform.platform_detection import safe_get

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart valves from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    valves = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 使用平台检测函数获取valve子设备
        valve_subdevices = get_valve_subdevices(device)

        # 为每个支持的valve子设备创建实体
        for sub_key in valve_subdevices:
            sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
            if sub_device_data:  # 只有当存在实际数据时才创建实体
                valve = LifeSmartValve(
                    raw_device=device,
                    client=hub.get_client(),
                    entry_id=config_entry.entry_id,
                    sub_device_key=sub_key,
                    sub_device_data=sub_device_data,
                )
                valves.append(valve)
                _LOGGER.debug(
                    "Added valve %s for device %s",
                    sub_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if valves:
        async_add_entities(valves)
        _LOGGER.info("Added %d LifeSmart valves", len(valves))


class LifeSmartValve(LifeSmartEntity, ValveEntity):
    """LifeSmart valve implementation."""

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """Initialize the valve."""
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        # 生成阀门名称和ID
        self._attr_name = self._generate_valve_name()
        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )

        # 阀门特性支持
        self._attr_supported_features = (
            ValveEntityFeature.OPEN
            | ValveEntityFeature.CLOSE
            | ValveEntityFeature.SET_POSITION
        )

        # 从子设备数据获取初始状态
        self._attr_is_closed = self._extract_initial_state()
        self._attr_current_valve_position = self._extract_position()

    @callback
    def _generate_valve_name(self) -> str | None:
        """Generate user-friendly valve name."""
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} Valve {self._sub_key.upper()}"

    @callback
    def _extract_initial_state(self) -> bool:
        """Extract initial valve state from device data."""
        # 检查type字段的最低位确定开关状态，0=关闭，1=打开
        valve_type = self._sub_data.get("type", 0)
        is_open = bool(valve_type & 1)
        return not is_open  # is_closed 与 is_open 相反

    @callback
    def _extract_position(self) -> int | None:
        """Extract valve position from device data."""
        # 尝试使用数据处理器获取位置值
        position_config = self._get_io_config("position")
        if position_config:
            position_value = process_io_data(
                self.devtype, self._sub_key, position_config, self._sub_data
            )
            if position_value is not None:
                # 确保位置在0-100范围内
                return max(0, min(100, int(position_value)))

        # 如果没有配置，从val字段获取位置
        position = self._sub_data.get("val")
        if position is not None:
            try:
                # 假设val字段表示百分比位置
                position = max(0, min(100, int(position)))
                return position
            except (ValueError, TypeError):
                pass

        # 根据开关状态推断位置
        if hasattr(self, "_attr_is_closed"):
            return 0 if self._attr_is_closed else 100

        return None

    def _get_io_config(self, metric: str) -> dict | None:
        """从DEVICE_MAPPING中获取阀门指标的配置。"""
        from .core.config.mapping import DEVICE_MAPPING

        device_type = self._raw_device.get(DEVICE_TYPE_KEY)
        if not device_type or device_type not in DEVICE_MAPPING:
            return None

        mapping = DEVICE_MAPPING[device_type]
        valve_config = mapping.get("valve", {})

        # 查找特定指标的配置
        for io_key, io_config in valve_config.items():
            if isinstance(io_config, dict) and io_config.get("metric") == metric:
                return io_config

        return None

    @property
    def is_closed(self) -> bool:
        """Return True if the valve is closed."""
        return self._attr_is_closed

    @property
    def current_valve_position(self) -> int | None:
        """Return the current position of the valve."""
        return self._attr_current_valve_position

    async def async_open_valve(self, **kwargs) -> None:
        """Open the valve."""
        try:
            await self._client.async_send_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_ON,
                1,
            )

            self._attr_is_closed = False
            self._attr_current_valve_position = 100
            self.async_write_ha_state()

            _LOGGER.debug(
                "Opened valve %s on device %s",
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to open valve %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def async_close_valve(self, **kwargs) -> None:
        """Close the valve."""
        try:
            await self._client.async_send_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_OFF,
                0,
            )

            self._attr_is_closed = True
            self._attr_current_valve_position = 0
            self.async_write_ha_state()

            _LOGGER.debug(
                "Closed valve %s on device %s",
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to close valve %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def async_set_valve_position(self, position: int, **kwargs) -> None:
        """Set the valve position."""
        try:
            # 确保位置在有效范围内
            position = max(0, min(100, position))

            await self._client.async_send_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_SET_VAL,
                position,
            )

            self._attr_current_valve_position = position
            self._attr_is_closed = position == 0
            self.async_write_ha_state()

            _LOGGER.debug(
                "Set valve position to %s%% for valve %s on device %s",
                position,
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to set valve position for valve %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for this valve."""
        # Get base attributes from parent class
        base_attrs = super().extra_state_attributes or {}

        # Add valve-specific attributes
        valve_attrs = {}

        if self._attr_current_valve_position is not None:
            valve_attrs["position"] = self._attr_current_valve_position
            valve_attrs["position_percentage"] = self._attr_current_valve_position

        valve_attrs["valve_state"] = "closed" if self._attr_is_closed else "open"

        # Merge attributes
        return {**base_attrs, **valve_attrs}

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

            # 更新阀门状态
            if "type" in io_data:
                is_open = bool(io_data["type"] & 1)
                new_is_closed = not is_open
                if self._attr_is_closed != new_is_closed:
                    self._attr_is_closed = new_is_closed
                    state_changed = True

            # 更新位置
            if "val" in io_data:
                try:
                    new_position = max(0, min(100, int(io_data["val"])))
                    if self._attr_current_valve_position != new_position:
                        self._attr_current_valve_position = new_position
                        # 根据位置更新关闭状态
                        self._attr_is_closed = new_position == 0
                        state_changed = True
                except (ValueError, TypeError):
                    pass

            if state_changed:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error handling valve update for %s: %s", self._attr_unique_id, e
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
                        "Valve device %s not found during global refresh, "
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
                        "Valve sub-device %s for %s not found, marking as unavailable.",
                        self._sub_key,
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            if not self.available:
                self._attr_available = True

            # 保存旧值用于比较
            old_is_closed = self._attr_is_closed
            old_position = self._attr_current_valve_position

            # 更新数据并重新提取状态和位置
            self._sub_data = new_sub_data
            new_is_closed = self._extract_initial_state()
            new_position = self._extract_position()

            state_changed = False
            if old_is_closed != new_is_closed:
                self._attr_is_closed = new_is_closed
                state_changed = True

            if old_position != new_position:
                self._attr_current_valve_position = new_position
                state_changed = True

            if state_changed:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during valve global refresh for %s: %s", self.unique_id, e
            )
