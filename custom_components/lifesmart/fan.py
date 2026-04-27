"""
LifeSmart 风扇平台支持模块

由 @MapleEve 创建和维护

本模块为LifeSmart平台提供风扇设备支持，实现了对各种智能风扇的
全面控制和状态管理。

支持的风扇功能：
- 开关控制：基础的开启和关闭功能
- 速度调节：多级速度控制和百分比设置
- 预设模式：自动、睡眠、自然风等模式
- 摆动功能：水平摆动和垂直摆动
- 方向控制：正向和反向旋转

技术特性：
- 配置驱动的IO口检测
- 使用mapping_engine统一配置管理
- 统一的状态更新和错误处理
- 符合四层架构原则
"""

import logging
from typing import Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
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
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
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
from .core.error_handling import (
    handle_global_refresh,
    log_device_unavailable,
    log_subdevice_unavailable,
)
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_fan_subdevices, safe_get

_LOGGER = logging.getLogger(__name__)


def _get_enhanced_io_config(device: dict, sub_key: str) -> dict | None:
    """
    使用映射引擎获取fan IO口的配置信息。

    Args:
        device: 设备字典
        sub_key: IO口键名

    Returns:
        IO口的配置信息字典，如果不存在则返回None
    """
    # Phase 2: 使用DeviceResolver统一接口 - 简化8行为3行
    from .core.resolver import get_device_resolver

    resolver = get_device_resolver()
    platform_config = resolver.get_platform_config(device, "fan")

    if not platform_config:
        return None

    # 检查IO配置是否存在
    io_config = platform_config.ios.get(sub_key)
    if io_config and io_config.description:
        return {
            "description": io_config.description,
            "data_type": io_config.data_type,
            "rw": io_config.rw,
            "device_class": getattr(io_config, "device_class", None),
        }

    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目设置 LifeSmart 风扇设备。

    Args:
        hass: Home Assistant核心实例
        config_entry: 集成配置条目
        async_add_entities: 实体添加回调函数
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    fans = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用工具函数获取设备的fan子设备列表
        fan_subdevices = get_fan_subdevices(device)

        # 为每个fan子设备创建实体
        for sub_key in fan_subdevices:
            # 使用工具函数获取IO配置
            io_config = _get_enhanced_io_config(device, sub_key)
            if not io_config:
                continue

            # 根据IO配置创建相应的风扇实体
            fan = LifeSmartFan(
                raw_device=device,
                client=hub.get_client(),
                entry_id=config_entry.entry_id,
                sub_device_key=sub_key,
                sub_device_data=safe_get(device, DEVICE_DATA_KEY, sub_key, default={}),
            )
            fans.append(fan)
            _LOGGER.debug(
                "Added fan %s for device %s",
                sub_key,
                device.get(DEVICE_NAME_KEY),
            )

    if fans:
        async_add_entities(fans)
        _LOGGER.info("Added %d LifeSmart fans", len(fans))


class LifeSmartFan(LifeSmartEntity, FanEntity):
    """
    LifeSmart 风扇设备实现类。

    继承自LifeSmartEntity和FanEntity，提供完整的风扇控制功能。
    支持速度调节、预设模式、摆动和方向控制。
    """

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """
        初始化风扇设备。

        Args:
            raw_device: 原始设备数据字典
            client: LifeSmart 客户端实例
            entry_id: 配置条目ID
            sub_device_key: 子设备键名
            sub_device_data: 子设备数据字典
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        # 生成风扇名称和ID
        self._attr_name = self._generate_fan_name()
        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )

        # 从配置获取支持的功能
        self._attr_supported_features = FanEntityFeature.SET_SPEED

        # 获取IO配置以确定支持的功能
        io_config = _get_enhanced_io_config(raw_device, sub_device_key)
        if io_config:
            if io_config.get("supports_preset_modes", False):
                self._attr_supported_features |= FanEntityFeature.PRESET_MODE

            if io_config.get("supports_oscillate", False):
                self._attr_supported_features |= FanEntityFeature.OSCILLATE

            if io_config.get("supports_direction", False):
                self._attr_supported_features |= FanEntityFeature.DIRECTION

        # 设置速度级别和预设模式
        self._attr_speed_count = len(FAN_SPEED_LEVELS)
        self._attr_preset_modes = (
            FAN_PRESET_MODES
            if self.supported_features & FanEntityFeature.PRESET_MODE
            else None
        )

        # 初始化状态
        self._initialize_state()

    @callback
    def _generate_fan_name(self) -> str | None:
        """
        生成用户友好的风扇名称。
        """
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} Fan {self._sub_key.upper()}"

    @callback
    def _initialize_state(self) -> None:
        """从子设备数据初始化风扇状态。"""
        # 获取增强的IO配置
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)

        if io_config:
            # 使用配置的处理器
            processed_data = process_io_data(io_config, self._sub_data)
            if isinstance(processed_data, dict):
                self._attr_is_on = processed_data.get("is_on", False)

                # 更新速度百分比
                if "speed_level" in processed_data:
                    speed_level = processed_data["speed_level"]
                    if speed_level in FAN_SPEED_LEVELS:
                        self._attr_percentage = ordered_list_item_to_percentage(
                            FAN_SPEED_LEVELS, speed_level
                        )
                    else:
                        self._attr_percentage = 0

                # 更新预设模式
                self._attr_preset_mode = processed_data.get("preset_mode")

                # 更新摆动状态
                self._attr_oscillating = processed_data.get("oscillating", False)

                # 更新方向
                self._attr_current_direction = processed_data.get(
                    "direction", "forward"
                )
            else:
                # 简单布尔值处理
                self._attr_is_on = bool(processed_data)
                self._attr_percentage = 50 if self._attr_is_on else 0
        else:
            # 降级处理：直接解析type字段
            fan_type = self._sub_data.get("type", 0)
            self._attr_is_on = bool(fan_type & 1)
            self._attr_percentage = 50 if self._attr_is_on else 0

        # 默认值设置
        if not hasattr(self, "_attr_preset_mode"):
            self._attr_preset_mode = None
        if not hasattr(self, "_attr_oscillating"):
            self._attr_oscillating = False
        if not hasattr(self, "_attr_current_direction"):
            self._attr_current_direction = "forward"

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        开启风扇。

        Args:
            percentage: 目标速度百分比
            preset_mode: 预设模式
            **kwargs: 其他参数
        """
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
                self._name,
                err,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """
        关闭风扇。

        Args:
            **kwargs: 其他参数
        """
        try:
            await self._send_fan_command(CMD_TYPE_OFF, 0)
        except Exception as err:
            _LOGGER.error(
                "Failed to turn off fan %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def async_set_percentage(self, percentage: int) -> None:
        """
        设置风扇速度百分比。

        Args:
            percentage: 速度百分比 (0-100)
        """
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
                self._name,
                err,
            )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """
        设置风扇的预设模式。

        Args:
            preset_mode: 预设模式名称
        """
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
                self._name,
                err,
            )

    async def async_oscillate(self, oscillating: bool) -> None:
        """
        设置风扇摆动。

        Args:
            oscillating: 是否摆动
        """
        if not (self.supported_features & FanEntityFeature.OSCILLATE):
            return

        try:
            value = 1 if oscillating else 0
            await self._send_fan_command(CMD_TYPE_SET_CONFIG, value)

        except Exception as err:
            _LOGGER.error(
                "Failed to set fan oscillation %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def async_set_direction(self, direction: str) -> None:
        """
        设置风扇旋转方向。

        Args:
            direction: 旋转方向 ("forward" 或 "reverse")
        """
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
                self._name,
                err,
            )

    async def _send_fan_command(self, cmd_type: int, value: Any) -> None:
        """
        向风扇发送控制命令。

        Args:
            cmd_type: 命令类型
            value: 命令数值
        """
        await self._client.async_send_single_command(
            self.agt,
            self.me,
            self._sub_key,
            cmd_type,
            value,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """
        返回设备信息。
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """
        订阅状态更新。
        """
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
        """
        处理来自设备的实时状态更新。
        """
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

            # 更新子设备数据
            self._sub_data.update(io_data)

            # 重新初始化状态
            old_state = {
                "is_on": self._attr_is_on,
                "percentage": self._attr_percentage,
                "preset_mode": self._attr_preset_mode,
                "oscillating": self._attr_oscillating,
                "direction": self._attr_current_direction,
            }

            self._initialize_state()

            new_state = {
                "is_on": self._attr_is_on,
                "percentage": self._attr_percentage,
                "preset_mode": self._attr_preset_mode,
                "oscillating": self._attr_oscillating,
                "direction": self._attr_current_direction,
            }

            # 如果状态有变化，更新HA状态
            if old_state != new_state:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error handling fan update for %s: %s", self._attr_unique_id, e
            )

    @handle_global_refresh()
    async def _handle_global_refresh(self) -> None:
        """
        处理周期性的全数据刷新。
        """
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
                log_device_unavailable(self.unique_id, "global refresh")
                self._attr_available = False
                self.async_write_ha_state()
            return

        new_sub_data = safe_get(current_device, DEVICE_DATA_KEY, self._sub_key)
        if new_sub_data is None:
            if self.available:
                log_subdevice_unavailable(self.unique_id, self._sub_key)
                self._attr_available = False
                self.async_write_ha_state()
            return

        if not self.available:
            self._attr_available = True

        # 保存旧状态用于比较
        old_state = {
            "is_on": self._attr_is_on,
            "percentage": self._attr_percentage,
            "preset_mode": self._attr_preset_mode,
            "oscillating": self._attr_oscillating,
            "direction": self._attr_current_direction,
        }

        # 更新数据并重新初始化状态
        self._sub_data = new_sub_data
        self._initialize_state()

        new_state = {
            "is_on": self._attr_is_on,
            "percentage": self._attr_percentage,
            "preset_mode": self._attr_preset_mode,
            "oscillating": self._attr_oscillating,
            "direction": self._attr_current_direction,
        }

        # 如果状态有变化，更新HA状态
        if old_state != new_state:
            self.async_write_ha_state()
