"""
LifeSmart 数值控制器平台支持模块

由 @MapleEve 创建和维护

本模块为LifeSmart平台提供数值控制器设备支持，实现了对各种
数值型控制参数的调节和管理。

支持的数值控制类型：
- 温度设定：空调、地暖等温度控制
- 亮度调节：可调光LED灯亮度控制
- 音量控制：音响设备音量调节
- 参数设定：各种设备的数值参数配置

技术特性：
- 灵活的数值范围和步长配置
- 多种数值转换模式
- 支持滑块和数字输入模式
- 实时数值同步和更新
"""

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberDeviceClass, NumberMode
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
    # 数值平台相关
    NUMBER_MIN_VALUE,
    NUMBER_MAX_VALUE,
    NUMBER_STEP,
    # 命令常量
    CMD_TYPE_SET_VAL,
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
    """
    从配置条目设置 LifeSmart 数值控制器。
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    numbers = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 检查是否支持数值平台
        platform_mapping = get_device_platform_mapping(device)
        if "number" not in platform_mapping:
            continue

        number_config = platform_mapping.get("number", {})

        # 为每个支持的数值控制器创建实体
        for number_key, number_cfg in number_config.items():
            if isinstance(number_cfg, dict) and number_cfg.get("enabled", True):
                number = LifeSmartNumber(
                    device,
                    number_key,
                    number_cfg,
                    hub,
                )
                numbers.append(number)
                _LOGGER.debug(
                    "Added number %s for device %s",
                    number_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if numbers:
        async_add_entities(numbers)
        _LOGGER.info("Added %d LifeSmart numbers", len(numbers))


class LifeSmartNumber(LifeSmartEntity, NumberEntity):
    """
    LifeSmart 数值控制器实现类。
    """

    def __init__(
        self,
        device: dict,
        sub_key: str,
        number_config: dict,
        hub,
    ) -> None:
        """
        初始化数值实体。
        """
        super().__init__(device, sub_key, hub)
        self._number_config = number_config

        # 从配置获取数值范围和步长
        self._attr_native_min_value = number_config.get("min_value", NUMBER_MIN_VALUE)
        self._attr_native_max_value = number_config.get("max_value", NUMBER_MAX_VALUE)
        self._attr_native_step = number_config.get("step", NUMBER_STEP)

        # 设置数值模式
        mode = number_config.get("mode", "slider")
        try:
            self._attr_mode = NumberMode(mode)
        except ValueError:
            self._attr_mode = NumberMode.SLIDER
            _LOGGER.warning("Invalid number mode: %s", mode)

        # 设置设备类别
        device_class = number_config.get("device_class")
        if device_class:
            try:
                self._attr_device_class = NumberDeviceClass(device_class)
            except ValueError:
                _LOGGER.warning("Invalid number device class: %s", device_class)

        # 设置单位
        self._attr_native_unit_of_measurement = number_config.get("unit_of_measurement")

        self._attr_native_value = None

    @property
    def unique_id(self) -> str:
        """
        返回数值控制器的唯一ID。

        Returns:
            基于设备和子设备信息的唯一标识符
        """
        return generate_unique_id(
            self._device.get(DEVICE_TYPE_KEY, ""),
            self._device.get(HUB_ID_KEY, ""),
            self._device.get(DEVICE_ID_KEY, ""),
            self._sub_key,
        )

    @property
    def name(self) -> str:
        """
        返回数值实体的名称。

        Returns:
            组合设备名称和数值控制器名称的字符串
        """
        device_name = self._device.get(DEVICE_NAME_KEY, "Unknown Device")
        number_name = self._number_config.get("name", self._sub_key)
        return f"{device_name} {number_name}"

    @property
    def available(self) -> bool:
        """
        返回实体是否可用。

        Returns:
            如果设备有数据则返回True
        """
        return bool(self._device.get(DEVICE_DATA_KEY, {}))

    async def async_set_native_value(self, value: float) -> None:
        """
        设置数值。
        """
        try:
            # 确保值在有效范围内
            value = max(self.native_min_value, min(self.native_max_value, value))

            # 根据配置转换值
            device_value = self._convert_to_device_value(value)

            await self._send_number_command(CMD_TYPE_SET_VAL, device_value)

            _LOGGER.debug(
                "Set number %s to %s (device value: %s) on device %s",
                self._sub_key,
                value,
                device_value,
                self._device.get(DEVICE_NAME_KEY),
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to set number %s to %s on device %s: %s",
                self._sub_key,
                value,
                self._device.get(DEVICE_NAME_KEY),
                err,
            )

    def _convert_to_device_value(self, ha_value: float) -> Any:
        """将HA值转换为设备值。"""
        conversion = self._number_config.get("conversion", "direct")

        if conversion == "percentage":
            # 转换为0-100的百分比
            return int(
                (ha_value - self.native_min_value)
                / (self.native_max_value - self.native_min_value)
                * 100
            )
        elif conversion == "scale":
            # 使用自定义缩放因子
            scale = self._number_config.get("scale", 1)
            return int(ha_value * scale)
        elif conversion == "inverse":
            # 反向值
            return self.native_max_value - ha_value + self.native_min_value
        else:
            # 直接值
            return ha_value

    def _convert_from_device_value(self, device_value: Any) -> float | None:
        """将设备值转换为HA值。"""
        if device_value is None:
            return None

        conversion = self._number_config.get("conversion", "direct")

        try:
            if conversion == "percentage":
                # 从0-100的百分比转换
                percentage = float(device_value)
                return self.native_min_value + (
                    percentage / 100 * (self.native_max_value - self.native_min_value)
                )
            elif conversion == "scale":
                # 使用自定义缩放因子
                scale = self._number_config.get("scale", 1)
                return float(device_value) / scale
            elif conversion == "inverse":
                # 反向值
                return (
                    self.native_max_value - float(device_value) + self.native_min_value
                )
            else:
                # 直接值
                return float(device_value)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Failed to convert device value %s for %s",
                device_value,
                self._sub_key,
            )
            return None

    async def _send_number_command(self, cmd_type: int, value: Any) -> None:
        """
        向数值控制器发送命令。
        """
        await self._hub.async_send_command(
            self._device[HUB_ID_KEY],
            self._device[DEVICE_ID_KEY],
            self._sub_key,
            cmd_type,
            value,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        处理来自协调器的更新数据。
        """
        device_data = self._device.get(DEVICE_DATA_KEY, {})
        io_data = device_data.get(self._sub_key)

        if io_data is None:
            return

        # 处理IO数据
        processed_value = process_io_data(io_data, self._number_config)

        # 转换为HA值
        self._attr_native_value = self._convert_from_device_value(processed_value)

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """
        订阅状态更新。
        """
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
        """
        返回设备信息。
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.get(DEVICE_ID_KEY))},
            name=self._device.get(DEVICE_NAME_KEY),
            manufacturer=MANUFACTURER,
            model=self._device.get(DEVICE_TYPE_KEY),
            via_device=(DOMAIN, self._device.get(HUB_ID_KEY)),
        )
