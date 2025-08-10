"""
LifeSmart 传感器平台实现。

本模块实现LifeSmart智能家居系统的传感器实体，支持：
- 映射驱动的设备检测和配置
- 通配符IO口展开处理
- 增强型数据转换和状态处理
- 实时状态更新和全局数据刷新

创建者：@MapleEve
技术架构：基于DEVICE_MAPPING的统一配置管理
"""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.config.mapping import (
    # 设备映射结构
    DEVICE_MAPPING,
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
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
)
from .core.data.processors import process_io_data
from .core.entity import LifeSmartEntity
from .core.helpers import (
    generate_unique_id,
)
from .core.platform.platform_detection import (
    safe_get,
    expand_wildcard_ios,
    get_sensor_subdevices,
)

_LOGGER = logging.getLogger(__name__)


def _get_enhanced_io_config(device: dict, sub_key: str) -> dict | None:
    """
    从DEVICE_MAPPING中获取IO口的配置信息。

    Args:
        device: 设备字典
        sub_key: IO口键名

    Returns:
        IO口的配置信息字典，如果不存在则返回None
    """
    device_type = device.get(DEVICE_TYPE_KEY)
    if not device_type or device_type not in DEVICE_MAPPING:
        return None

    mapping = DEVICE_MAPPING[device_type]

    # 处理版本化设备
    if mapping.get("versioned"):
        from .core.helpers import get_device_version

        device_version = get_device_version(device)
        if device_version and device_version in mapping:
            mapping = mapping[device_version]
        else:
            return None

    # 在sensor平台中查找IO配置
    sensor_config = mapping.get("sensor")
    if not sensor_config:
        return None

    # 检查是否为增强结构
    if isinstance(sensor_config, dict) and sub_key in sensor_config:
        io_config = sensor_config[sub_key]
        if isinstance(io_config, dict) and "description" in io_config:
            return io_config

    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    设置LifeSmart传感器平台。

    从配置条目初始化传感器实体，使用映射驱动的设备检测。
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    sensors = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用工具函数获取设备的sensor子设备列表
        sensor_subdevices = get_sensor_subdevices(device)

        # 展开通配符模式的IO口并为每个sensor子设备创建实体
        device_data = device.get(DEVICE_DATA_KEY, {})

        for sub_key in sensor_subdevices:
            # 检查是否为通配符模式
            if "*" in sub_key or "x" in sub_key:
                # 展开通配符，获取实际的IO口列表
                expanded_ios = expand_wildcard_ios(sub_key, device_data)
                for expanded_io in expanded_ios:
                    sub_device_data = safe_get(
                        device, DEVICE_DATA_KEY, expanded_io, default={}
                    )
                    if sub_device_data:  # 只有当存在实际数据时才创建实体
                        sensors.append(
                            LifeSmartSensor(
                                raw_device=device,
                                client=hub.get_client(),
                                entry_id=config_entry.entry_id,
                                sub_device_key=expanded_io,
                                sub_device_data=sub_device_data,
                            )
                        )
            else:
                # 非通配符模式，正常处理
                sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
                sensors.append(
                    LifeSmartSensor(
                        raw_device=device,
                        client=hub.get_client(),
                        entry_id=config_entry.entry_id,
                        sub_device_key=sub_key,
                        sub_device_data=sub_device_data,
                    )
                )

    async_add_entities(sensors)


class LifeSmartSensor(LifeSmartEntity, SensorEntity):
    """
    LifeSmart传感器实体，具有增强的兼容性支持。

    主要功能：
    - 基于DEVICE_MAPPING的设备类别和单位检测
    - 映射驱动的数值转换和状态处理
    - 实时更新和全局刷新支持
    - 设备在线状态管理
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
        初始化传感器实体。

        Args:
            raw_device: 原始设备数据
            client: 客户端连接对象
            entry_id: 配置条目ID
            sub_device_key: 子设备键名
            sub_device_data: 子设备数据
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        self._attr_name = self._generate_sensor_name()
        device_name_slug = self._name.lower().replace(" ", "_")
        sub_key_slug = self._sub_key.lower()
        self._attr_object_id = f"{device_name_slug}_{sub_key_slug}"

        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )
        self._attr_device_class = self._determine_device_class()
        self._attr_state_class = self._determine_state_class()
        self._attr_native_unit_of_measurement = self._determine_unit()
        self._attr_native_value = self._extract_initial_value()

    @callback
    def _generate_sensor_name(self) -> str | None:
        """
        生成用户友好的传感器名称。

        优先使用子设备的自定义名称，否则使用基础名称+IO口索引。
        """
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} {self._sub_key.upper()}"

    @callback
    def _determine_device_class(self) -> SensorDeviceClass | None:
        """
        使用映射驱动方法确定设备类别。

        完全依赖DEVICE_MAPPING中的配置获取设备类别。
        """
        # 完全依赖映射获取设备类别
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if io_config and "device_class" in io_config:
            return io_config["device_class"]

        return None

    @callback
    def _determine_unit(self) -> str | None:
        """
        使用映射驱动方法确定测量单位。

        完全依赖DEVICE_MAPPING中的配置获取单位信息。
        """
        # 完全依赖映射获取单位
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if io_config and "unit_of_measurement" in io_config:
            return io_config["unit_of_measurement"]

        return None

    @callback
    def _determine_state_class(self) -> SensorStateClass | None:
        """从DEVICE_MAPPING获取状态类别。"""
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        return io_config.get("state_class") if io_config else None

    @callback
    def _extract_initial_value(self) -> float | int | None:
        """使用DEVICE_MAPPING提取初始值。"""
        # 完全依赖映射的转换逻辑，工具函数内部已处理v/val优先级
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if io_config:
            return process_io_data(io_config, self._sub_data)

        # 如果映射中没有转换配置，尝试直接使用v字段
        value = self._sub_data.get("v")
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Invalid non-numeric 'v' value received for %s: %s",
                    self.unique_id,
                    value,
                )

        # 最后尝试val字段
        raw_value = self._sub_data.get("val")
        if raw_value is not None:
            try:
                return float(raw_value)
            except (ValueError, TypeError):
                return None

        return None

    @callback
    def _convert_raw_value(self, raw_value: Any) -> float | int | None:
        """
        使用映射驱动方法转换原始数值。

        仅依赖DEVICE_MAPPING中的转换配置进行数值转换。
        """
        if raw_value is None:
            return None

        try:
            numeric_raw_value = float(raw_value)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid non-numeric 'val' received for %s: %s",
                self.unique_id,
                raw_value,
            )
            return None

        # 完全依赖映射的转换逻辑，工具函数内部已处理IEEE754转换
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if io_config:
            enhanced_value = process_io_data(io_config, self._sub_data)
            if enhanced_value is not None:
                return enhanced_value

        # 如果映射中没有转换配置，直接返回原始值
        return numeric_raw_value

    @callback
    def _get_extra_attributes(self) -> dict[str, Any] | None:
        """从DEVICE_MAPPING获取额外状态属性。"""
        # 从DEVICE_MAPPING获取IO配置
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if not io_config:
            return None

        # 获取extra_attributes配置
        extra_attributes = io_config.get("extra_attributes")
        if not extra_attributes:
            return None

        # 处理静态和动态属性
        result = {}
        for attr_name, attr_value in extra_attributes.items():
            if isinstance(attr_value, str) and attr_value in self._sub_data:
                # 动态属性：引用IO数据字段
                result[attr_name] = self._sub_data.get(attr_value)
            else:
                # 静态属性：直接使用配置值
                result[attr_name] = attr_value

        return result if result else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """
        返回此传感器的额外状态属性。

        合并基础属性和传感器特定属性。
        """
        # Get base attributes from parent class
        base_attrs = super().extra_state_attributes
        # Get sensor-specific extra attributes
        sensor_attrs = self._get_extra_attributes()

        if sensor_attrs:
            # Merge base attributes with sensor-specific ones
            if base_attrs:
                return {**base_attrs, **sensor_attrs}
            return sensor_attrs

        return base_attrs

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

    async def async_added_to_hass(self) -> None:
        """
        注册更新监听器。

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

    async def _handle_update(self, new_data: dict) -> None:
        """
        处理实时更新数据。

        使用映射驱动的转换逻辑处理收到的实时状态更新。
        """
        try:
            if not new_data:
                _LOGGER.warning(
                    "Received empty new_data in _handle_update; "
                    "possible upstream issue."
                )
                return
            # 统一处理数据来源，提取IO数据
            io_data = {}
            if "msg" in new_data and isinstance(new_data["msg"], dict):
                io_data = new_data["msg"].get(self._sub_key, {})
            elif self._sub_key in new_data:
                io_data = new_data[self._sub_key]
            else:
                # 直接推送子键值对格式
                io_data = new_data

            if not io_data:
                return

            # 使用新的业务逻辑处理器进行映射驱动的数值转换
            io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
            if io_config:
                new_value = process_io_data(io_config, io_data)
            else:
                new_value = None

            if new_value is None:
                # 如果收到无效数据仅打印日志（已在convert中完成）
                return

            self._attr_native_value = new_value
            self._attr_available = True  # 收到有效数据，确保实体是可用的
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self._attr_unique_id, e)

    async def _handle_global_refresh(self) -> None:
        """
        处理周期性全量数据刷新，包含可用性检查。

        检查设备和子设备的存在性，更新可用性状态。
        """
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
                        "Device %s not found during global refresh, "
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
                        "Sub-devices %s for %s not found, marking as unavailable.",
                        self._sub_key,
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            if not self.available:
                self._attr_available = True

            self._sub_data = new_sub_data
            new_value = self._extract_initial_value()

            if self._attr_native_value != new_value:
                self._attr_native_value = new_value
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error during global refresh for %s: %s", self.unique_id, e)
