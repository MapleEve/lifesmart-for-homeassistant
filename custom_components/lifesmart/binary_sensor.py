"""
Support for LifeSmart binary sensors by @MapleEve
LifeSmart 二元传感器平台实现

此模块负责将 LifeSmart 的各种感应器（如门磁、动态感应器、水浸、门锁事件等）
注册为 Home Assistant 中的二元传感器实体。

"""

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .core.const import (
    # --- 核心常量导入 ---
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    BINARY_SENSOR_BUTTON_RESET_DELAY,  # 新增常量
)
from .core.entity import LifeSmartEntity
from .core.helpers import (
    generate_unique_id,
)
from .core.platform.platform_detection import (
    get_device_platform_mapping,
    get_binary_sensor_io_config,
    is_momentary_button_device,
    safe_get,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目异步设置 LifeSmart 二元传感器设备。

    此函数负责遍历所有设备，识别二元传感器类型设备，并为每个设备创建
    相应的Home Assistant实体。支持设备排除配置和bitmask多设备生成。

    Args:
        hass: Home Assistant核心实例，提供数据存储和事件调度
        config_entry: 集成配置条目，包含用户配置和运行时数据
        async_add_entities: HA实体添加回调函数，用于注册新实体

    Returns:
        无返回值，通过async_add_entities回调添加实体

    注意事项:
        - 会自动跳过排除列表中的设备
        - 支持bitmask虚拟子设备生成
        - 支持瞬时按钮设备的自动复位机制
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    binary_sensors = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用新的IO映射系统获取设备支持的平台
        platform_mapping = get_device_platform_mapping(device)
        binary_sensor_subdevices = platform_mapping.get(Platform.BINARY_SENSOR, [])

        # 为每个binary_sensor子设备创建实体
        for sub_key in binary_sensor_subdevices:
            sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
            binary_sensors.append(
                LifeSmartBinarySensor(
                    raw_device=device,
                    client=hub.get_client(),
                    entry_id=config_entry.entry_id,
                    sub_device_key=sub_key,
                    sub_device_data=sub_device_data,
                )
            )

    async_add_entities(binary_sensors)


class LifeSmartBinarySensor(LifeSmartEntity, BinarySensorEntity):
    """
    LifeSmart 二元传感器设备实体类。

    继承自LifeSmartEntity和BinarySensorEntity，负责二元传感器的状态管理
    和数据处理逻辑。实现了增强的兼容性和完整的设备控制功能。

    主要职责:
    - 解析和处理各种二元传感器状态
    - 实现瞬时按钮设备的自动复位机制
    - 支持bitmask虚拟子设备的状态管理
    - 提供实时状态更新和设备类别识别

    技术特点:
    - 配置驱动的设备类别检测
    - 智能的状态处理和转换
    - 完整的错误处理和日志记录
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
        初始化二元传感器设备。

        Args:
            raw_device: 原始设备数据字典
            client: LifeSmart API客户端实例
            entry_id: 配置条目ID
            sub_device_key: 子设备键名，用于多IO设备
            sub_device_data: 子设备数据，包含IO口状态信息
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        # 为bitmask虚拟子设备生成更友好的名称
        if self._is_bitmask_virtual_subdevice():
            friendly_name = self._get_bitmask_friendly_name()
            self._attr_name = f"{self._name} {friendly_name}"
            device_name_slug = self._name.lower().replace(" ", "_")
            sub_key_slug = sub_device_key.lower().replace("_bit", "_")
            self._attr_object_id = f"{device_name_slug}_{sub_key_slug}"
        else:
            self._attr_name = f"{self._name} {self._sub_key.upper()}"
            device_name_slug = self._name.lower().replace(" ", "_")
            sub_key_slug = self._sub_key.lower()
            self._attr_object_id = f"{device_name_slug}_{sub_key_slug}"

        self._attr_unique_id = generate_unique_id(
            self.devtype, self.agt, self.me, sub_device_key
        )
        self._update_state(self._sub_data)

    def _get_bitmask_friendly_name(self) -> str:
        """
        获取bitmask虚拟子设备的友好名称。

        Returns:
            友好的设备名称
        """
        io_config = get_binary_sensor_io_config(self._raw_device, self._sub_key)
        friendly_name = io_config.get("friendly_name")

        if friendly_name:
            return friendly_name

        # Fallback: 使用默认格式
        return self._sub_key.upper()

    @callback
    def _update_state(self, data: dict) -> None:
        """
        解析并根据数据更新所有实体状态和属性。

        增强版本：支持bitmask虚拟子设备的数据处理。
        """
        # 对于虚拟子设备，需要特殊处理
        if self._is_bitmask_virtual_subdevice():
            # 虚拟子设备不直接使用传入的data，而是从原始IO口获取数据
            source_io_port = self._sub_key.split("_bit")[0]
            source_io_data = safe_get(
                self._raw_device, DEVICE_DATA_KEY, source_io_port, default={}
            )
            self._sub_data = source_io_data  # 使用原始IO口数据
        else:
            self._sub_data = data

        device_class = self._determine_device_class()
        if device_class:
            self._attr_device_class = device_class

        # 首先，使用通用的 _parse_state 来确定当前事件是否应该为 'on'
        is_currently_on = self._parse_state()
        self._attr_is_on = is_currently_on

        # 然后，更新所有属性。_get_attributes 可能会用到 self._attr_is_on 的最新值
        self._attrs = self._get_attributes()

        # 最后，处理瞬时按钮的特殊重置逻辑 - 使用映射驱动判断
        if self._is_momentary_button_device() and is_currently_on:
            # 更新事件相关的属性
            val = data.get("val", 0)
            event_map = {1: "single_click", 2: "double_click", 255: "long_press"}
            self._attrs["last_event"] = event_map.get(val, "unknown")
            self._attrs["last_event_time"] = dt_util.utcnow().isoformat()

            # 使用 Home Assistant 的调度器在短暂延迟后将状态重置为 "off"
            @callback
            def reset_state_callback(_now):
                """
                将瞬时按钮状态重置为关闭。

                用于模拟按钮按下后的自动复位行为。
                """
                self._attr_is_on = False
                self.async_write_ha_state()

            async_call_later(
                self.hass, BINARY_SENSOR_BUTTON_RESET_DELAY, reset_state_callback
            )

    @callback
    def _determine_device_class(self) -> BinarySensorDeviceClass | None:
        """从DEVICE_MAPPING获取设备类别。"""
        io_config = get_binary_sensor_io_config(self._raw_device, self._sub_key)
        return io_config.get("device_class") if io_config else None

    @callback
    def _is_momentary_button_device(self) -> bool:
        """从DEVICE_MAPPING判断是否为瞬时按钮设备。"""
        return is_momentary_button_device(self.devtype, self._sub_key)

    @callback
    def _parse_state(self) -> bool:
        """使用新的逻辑处理器系统解析设备状态。

        增强版本：支持bitmask虚拟子设备状态解析。
        """
        # 检查是否为bitmask虚拟子设备
        if self._is_bitmask_virtual_subdevice():
            return self._parse_bitmask_bit_state()

        # 原有逻辑
        from .core.data.processors.io_processors import process_io_data

        io_config = get_binary_sensor_io_config(self._raw_device, self._sub_key)
        if not io_config:
            # If no config found, return a basic val != 0 check
            return self._sub_data.get("val", 0) != 0

        # Use new logic processor system
        return process_io_data(io_config, self._sub_data)

    @callback
    def _is_bitmask_virtual_subdevice(self) -> bool:
        """判断是否为bitmask虚拟子设备。"""
        from .core.platform.platform_detection import is_bitmask_virtual_subdevice

        return is_bitmask_virtual_subdevice(self._sub_key)

    @callback
    def _parse_bitmask_bit_state(self) -> bool:
        """
        解析ALM虚拟子设备的bit状态。

        使用新的ALM数据处理器架构，从原始IO口数据中提取特定bit位的状态。
        """
        from .core.data.processors.data_processors import (
            alm_data_processor,
            is_alm_io_port,
        )

        # 解析虚拟键格式: {IO口}_bit{位号}
        if "_bit" not in self._sub_key:
            return False

        source_io_port = self._sub_key.split("_bit")[0]
        bit_position_str = self._sub_key.split("_bit")[1]

        # 检查是否为ALM IO口
        if not is_alm_io_port(source_io_port):
            return False

        try:
            bit_position = int(bit_position_str)
        except ValueError:
            return False

        # 获取原始IO口数据
        source_io_data = safe_get(
            self._raw_device, DEVICE_DATA_KEY, source_io_port, default={}
        )
        raw_value = source_io_data.get("val", 0)

        # 使用ALM数据处理器提取bit状态
        return alm_data_processor.extract_bit_value(raw_value, bit_position)

        # Fallback: 基础位操作
        try:
            return bool((raw_value >> bit_position) & 1)
        except (TypeError, ValueError):
            return False

    @callback
    def _get_attributes(self) -> dict[str, Any]:
        """使用新的逻辑处理器系统获取传感器属性。"""
        # 按钮开关类型初始化事件属性 - 使用映射驱动判断
        if self._is_momentary_button_device():
            return {"last_event": None, "last_event_time": None}

        # 使用新的逻辑处理器获取设备特定属性
        from .core.data.processors.io_processors import process_io_attributes

        io_config = get_binary_sensor_io_config(self._raw_device, self._sub_key)
        if io_config:
            try:
                return process_io_attributes(
                    self.devtype,
                    self._sub_key,
                    io_config,
                    self._sub_data,
                    self._attr_is_on,
                )
            except Exception:
                pass

        # Fallback to basic attributes
        return dict(self._sub_data)

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息以链接实体到单个设备。"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    @property
    def unique_id(self) -> str:
        """
        返回此实体的唯一标识符。

        Returns:
            基于设备类型、网关ID、设备ID和子设备键的唯一标识符
        """
        return self._attr_unique_id

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        返回实体的状态属性。

        Returns:
            包含设备状态信息的属性字典
        """
        return self._attrs

    async def async_added_to_hass(self) -> None:
        """
        注册状态更新监听器。

        设置实时更新和全局刷新的事件监听器。
        """
        # 实时更新事件
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )
        # 全局数据刷新事件
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    async def _handle_update(self, data: dict) -> None:
        """Handle real-time updates."""
        try:
            if data is None:
                return

            self._update_state(data)
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self._attr_unique_id, e)

    async def _handle_global_refresh(self) -> None:
        """Handle periodic full data refresh."""
        try:
            # 从hass.data获取最新设备列表
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]

            # 查找当前设备
            current_device = next(
                (
                    d
                    for d in devices
                    if d[HUB_ID_KEY] == self.agt and d[DEVICE_ID_KEY] == self.me
                ),
                None,
            )

            if current_device:
                sub_data = safe_get(
                    current_device, DEVICE_DATA_KEY, self._sub_key, default={}
                )
                if sub_data:
                    self._update_state(sub_data)
                    self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during global refresh for %s: %s", self._attr_unique_id, e
            )
