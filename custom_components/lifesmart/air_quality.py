"""
LifeSmart 空气质量传感器平台支持模块

由 @MapleEve 创建和维护

本模块为LifeSmart平台提供空气质量传感器支持，实现了对各种空气质量指标的
全面监测和数据处理。

支持的空气质量指标：
- AQI (空气质量指数)
- PM2.5 (细颗粒物)
- PM10 (可吸入颗粒物)
- CO2 (二氧化碳浓度)
- VOC (挥发性有机化合物)

技术特性：
- 配置驱动的IO口检测
- 智能数据处理和转换
- 实时状态更新机制
- 符合Home Assistant标准的空气质量等级映射
"""

import logging
from typing import Any

from homeassistant.components.air_quality import AirQualityEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
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
    # 空气质量平台相关
    AIR_QUALITY_EXCELLENT,
    AIR_QUALITY_GOOD,
    AIR_QUALITY_FAIR,
    AIR_QUALITY_POOR,
    AIR_QUALITY_VERY_POOR,
)
from .core.data.processors import process_io_data
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_air_quality_subdevices
from .core.platform.platform_detection import safe_get

_LOGGER = logging.getLogger(__name__)

# LifeSmart空气质量等级映射到HA标准
AQI_LEVEL_MAPPING = {
    0: "excellent",  # 优
    1: "good",  # 良
    2: "fair",  # 中等
    3: "poor",  # 差
    4: "very_poor",  # 很差
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目异步设置 LifeSmart 空气质量传感器。

    此函数负责遍历所有设备，识别空气质量类型设备，并为每个设备创建
    相应的Home Assistant实体。支持设备排除配置和动态设备发现。

    Args:
        hass: Home Assistant核心实例，提供数据存储和事件调度
        config_entry: 集成配置条目，包含用户配置和运行时数据
        async_add_entities: HA实体添加回调函数，用于注册新实体

    Returns:
        无返回值，通过async_add_entities回调添加实体

    注意事项:
        - 会自动跳过排除列表中的设备
        - 只为存在实际数据的子设备创建实体
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    air_quality_sensors = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 使用平台检测函数获取air_quality子设备
        air_quality_subdevices = get_air_quality_subdevices(device)

        # 为每个支持的air_quality子设备创建实体
        for sub_key in air_quality_subdevices:
            sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
            if sub_device_data:  # 只有当存在实际数据时才创建实体
                air_quality_sensor = LifeSmartAirQuality(
                    raw_device=device,
                    client=hub.get_client(),
                    entry_id=config_entry.entry_id,
                    sub_device_key=sub_key,
                    sub_device_data=sub_device_data,
                )
                air_quality_sensors.append(air_quality_sensor)
                _LOGGER.debug(
                    "Added air quality sensor %s for device %s",
                    sub_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if air_quality_sensors:
        async_add_entities(air_quality_sensors)
        _LOGGER.info("Added %d LifeSmart air quality sensors", len(air_quality_sensors))


class LifeSmartAirQuality(LifeSmartEntity, AirQualityEntity):
    """
    LifeSmart 空气质量传感器实现类。

    继承自LifeSmartEntity和AirQualityEntity，负责空气质量传感器的状态管理
    和数据处理逻辑。实现了完整的空气质量监测功能。

    主要职责:
    - 解析和处理多种空气质量指标
    - 实现符合HA标准的空气质量等级映射
    - 提供实时状态更新和全局刷新
    - 自动生成友好的传感器名称
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
        初始化空气质量传感器。

        Args:
            raw_device: 原始设备数据字典
            client: LifeSmart API客户端实例
            entry_id: 配置条目ID
            sub_device_key: 子设备键名
            sub_device_data: 子设备数据
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        # 生成空气质量传感器名称和ID
        self._attr_name = self._generate_air_quality_name()
        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )

        # 从子设备数据提取空气质量指标
        self._update_air_quality_values()

    @callback
    def _generate_air_quality_name(self) -> str | None:
        """
        生成用户友好的空气质量传感器名称。

        Returns:
            生成的传感器显示名称字符串
        """
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} Air Quality {self._sub_key.upper()}"

    def _get_io_config(self, metric: str) -> dict | None:
        """
        使用映射引擎获取空气质量指标的配置。

        Args:
            metric: 要查找的指标类型，如'aqi', 'pm25'等

        Returns:
            包含处理器配置的字典，如果未找到则返回None
        """
        from .core.config.mapping_engine import mapping_engine

        device_config = mapping_engine.resolve_device_mapping_from_data(
            self._raw_device
        )
        if not device_config:
            _LOGGER.error("映射引擎无法解析设备配置: %s", self._raw_device)
            raise HomeAssistantError(
                f"Device configuration not found for "
                f"{self._raw_device.get('me', 'unknown')}"
            )

        air_quality_config = device_config.get("air_quality", {})

        # 查找特定指标的配置
        for io_key, io_config in air_quality_config.items():
            if isinstance(io_config, dict) and io_config.get("metric") == metric:
                return io_config

        return None

    @callback
    def _update_air_quality_values(self) -> None:
        """
        从设备数据更新空气质量数值。

        解析各种空气质量指标并设置相应的属性值。
        """
        # AQI (Air Quality Index)
        aqi_config = self._get_io_config("aqi")
        if aqi_config:
            aqi_value = process_io_data(
                self.devtype, self._sub_key, aqi_config, self._sub_data
            )
            if aqi_value is not None:
                self._attr_air_quality_index = int(aqi_value)
        else:
            # 直接从val字段获取AQI
            self._attr_air_quality_index = self._sub_data.get("val")

        # PM2.5
        pm25_config = self._get_io_config("pm25")
        if pm25_config:
            pm25_value = process_io_data(
                self.devtype, self._sub_key, pm25_config, self._sub_data
            )
            if pm25_value is not None:
                self._attr_particulate_matter_2_5 = float(pm25_value)
        else:
            # 尝试从其他字段获取PM2.5数据
            self._attr_particulate_matter_2_5 = self._sub_data.get("pm25")

        # PM10
        pm10_config = self._get_io_config("pm10")
        if pm10_config:
            pm10_value = process_io_data(
                self.devtype, self._sub_key, pm10_config, self._sub_data
            )
            if pm10_value is not None:
                self._attr_particulate_matter_10 = float(pm10_value)
        else:
            # 尝试从其他字段获取PM10数据
            self._attr_particulate_matter_10 = self._sub_data.get("pm10")

        # CO2
        co2_config = self._get_io_config("co2")
        if co2_config:
            co2_value = process_io_data(
                self.devtype, self._sub_key, co2_config, self._sub_data
            )
            if co2_value is not None:
                self._attr_carbon_dioxide = float(co2_value)
        else:
            # 尝试从其他字段获取CO2数据
            self._attr_carbon_dioxide = self._sub_data.get("co2")

        # VOC (挥发性有机化合物)
        voc_config = self._get_io_config("voc")
        if voc_config:
            voc_value = process_io_data(
                self.devtype, self._sub_key, voc_config, self._sub_data
            )
            if voc_value is not None:
                self._attr_volatile_organic_compounds = float(voc_value)
        else:
            # 尝试从其他字段获取VOC数据
            self._attr_volatile_organic_compounds = self._sub_data.get("voc")

        # 根据AQI值确定空气质量等级
        if (
            hasattr(self, "_attr_air_quality_index")
            and self._attr_air_quality_index is not None
        ):
            if self._attr_air_quality_index <= 50:
                level = AIR_QUALITY_EXCELLENT
            elif self._attr_air_quality_index <= 100:
                level = AIR_QUALITY_GOOD
            elif self._attr_air_quality_index <= 150:
                level = AIR_QUALITY_FAIR
            elif self._attr_air_quality_index <= 200:
                level = AIR_QUALITY_POOR
            else:
                level = AIR_QUALITY_VERY_POOR

            # 映射到HA标准
            self._attr_air_quality = AQI_LEVEL_MAPPING.get(level, "unknown")

    @property
    def device_info(self) -> DeviceInfo:
        """
        返回设备信息。

        Returns:
            包含设备标识、名称等信息的DeviceInfo对象
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """
        订阅状态更新。

        设置实时更新和全局刷新的事件监听器。
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
        处理实时状态更新。

        Args:
            new_data: 包含更新数据的字典
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

            # 重新计算空气质量指标
            old_aqi = getattr(self, "_attr_air_quality_index", None)
            self._update_air_quality_values()

            # 如果有变化，更新HA状态
            new_aqi = getattr(self, "_attr_air_quality_index", None)
            if old_aqi != new_aqi:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error handling air quality update for %s: %s", self._attr_unique_id, e
            )

    async def _handle_global_refresh(self) -> None:
        """
        处理周期性的全数据刷新。

        检查设备可用性并更新状态。
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
                        "Air quality device %s not found during global refresh, "
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
                        "Air quality sub-device %s for %s not found, "
                        "marking as unavailable.",
                        self._sub_key,
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            if not self.available:
                self._attr_available = True

            # 保存旧值用于比较
            old_aqi = getattr(self, "_attr_air_quality_index", None)

            # 更新数据并重新计算指标
            self._sub_data = new_sub_data
            self._update_air_quality_values()

            # 如果有变化，更新HA状态
            new_aqi = getattr(self, "_attr_air_quality_index", None)
            if old_aqi != new_aqi:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during air quality global refresh for %s: %s", self.unique_id, e
            )
