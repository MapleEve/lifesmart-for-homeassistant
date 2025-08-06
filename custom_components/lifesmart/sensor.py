"""Support for LifeSmart sensors by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    LIGHT_LUX,
    PERCENTAGE,
    Platform,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfSoundPressure,
    UnitOfElectricCurrent,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
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
    # --- 设备类型常量导入 ---
    BASIC_ENV_SENSOR_TYPES,
    AIR_QUALITY_SENSOR_TYPES,
    GAS_SENSOR_TYPES,
    NOISE_SENSOR_TYPES,
    POWER_METER_PLUG_TYPES,
    SMART_PLUG_TYPES,
    POWER_METER_TYPES,
    DEFED_SENSOR_TYPES,
    SMOKE_SENSOR_TYPES,
    WATER_SENSOR_TYPES,
    SUPPORTED_SWITCH_TYPES,
    CLIMATE_TYPES,
)
from .entity import LifeSmartEntity
from .helpers import (
    generate_unique_id,
    get_device_platform_mapping,
    safe_get,
    get_io_friendly_val,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    sensors = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用新的IO映射系统获取设备支持的平台
        platform_mapping = get_device_platform_mapping(device)
        sensor_subdevices = platform_mapping.get(Platform.SENSOR, [])

        # 为每个sensor子设备创建实体
        for sub_key in sensor_subdevices:
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
    """LifeSmart sensor entity with enhanced compatibility."""

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
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
        """Generate user-friendly sensor name."""
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} {self._sub_key.upper()}"

    @callback
    def _determine_device_class(self) -> SensorDeviceClass | None:
        """Automatically determine device class based on sub-device."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]
        sub_key = self._sub_key

        # 气体传感器优先判断
        if device_type in GAS_SENSOR_TYPES and sub_key in {"P1", "P2"}:
            return SensorDeviceClass.GAS

        # 温控设备特殊处理
        if device_type in CLIMATE_TYPES:
            if sub_key == "P5":
                return (
                    SensorDeviceClass.TEMPERATURE
                    if device_type in ("SL_CP_DN", "SL_NATURE")
                    else SensorDeviceClass.PM25
                )
            if sub_key == "P6":
                return SensorDeviceClass.BATTERY
            if sub_key == "P4":
                return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
            # 继续到通用子设备键判断，不返回None

        # 根据子设备键判断
        if sub_key == "BAT":
            return SensorDeviceClass.BATTERY
        if sub_key == "T":
            return SensorDeviceClass.TEMPERATURE
        if sub_key == "H":
            return SensorDeviceClass.HUMIDITY
        if sub_key == "Z":
            return SensorDeviceClass.ILLUMINANCE
        if sub_key == "V":
            return SensorDeviceClass.VOLTAGE

        # 空气质量传感器的设备
        if device_type in AIR_QUALITY_SENSOR_TYPES:
            if device_type == "SL_SC_CQ":
                if sub_key == "P4":
                    return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
                if sub_key == "P3":
                    return SensorDeviceClass.CO2
            if device_type == "SL_SC_CA":
                if sub_key == "P3":
                    return SensorDeviceClass.CO2
            if device_type == "SL_SC_CH":
                return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS  # 甲醛也属于VOC

        # 计量插座特殊处理
        if device_type in POWER_METER_PLUG_TYPES:
            if sub_key == "P2":
                return SensorDeviceClass.ENERGY
            if sub_key == "P3":
                return SensorDeviceClass.POWER

        # 智能插座的电压、电流、功率等传感器
        if device_type in SMART_PLUG_TYPES:
            if sub_key == "EV":
                return SensorDeviceClass.VOLTAGE
            if sub_key == "EI":
                return SensorDeviceClass.CURRENT
            if sub_key == "EP":
                return SensorDeviceClass.POWER
            if sub_key == "EPA":
                return SensorDeviceClass.ENERGY

        # 噪音感应器
        if device_type in NOISE_SENSOR_TYPES and sub_key == "P1":
            return SensorDeviceClass.SOUND_PRESSURE  # 噪音等级

        # 电量计量器
        if device_type in POWER_METER_TYPES:
            if sub_key in {"EPA", "EP"}:
                return SensorDeviceClass.POWER
            if sub_key == "EE":
                return SensorDeviceClass.ENERGY

        # 云防系列的温度传感器
        if device_type in DEFED_SENSOR_TYPES and sub_key == "T":
            return SensorDeviceClass.TEMPERATURE

        # 烟雾传感器的电量
        if device_type in SMOKE_SENSOR_TYPES and sub_key == "P2":
            return SensorDeviceClass.BATTERY

        # 基础环境感应器 (SL_SC_THL等)
        if device_type in BASIC_ENV_SENSOR_TYPES:
            if sub_key == "T":
                return SensorDeviceClass.TEMPERATURE
            if sub_key == "H":
                return SensorDeviceClass.HUMIDITY
            if sub_key == "V":
                return SensorDeviceClass.VOLTAGE
            if sub_key == "Z":
                return SensorDeviceClass.ILLUMINANCE

        # 空气质量传感器 (温湿度数据用于环境补偿)
        if device_type in AIR_QUALITY_SENSOR_TYPES and device_type != "SL_SC_CH":
            if sub_key == "P1":
                return SensorDeviceClass.TEMPERATURE
            if sub_key == "P2":
                return SensorDeviceClass.HUMIDITY

        # 插座开关等电量传感器
        if (device_type in SUPPORTED_SWITCH_TYPES and sub_key == "P4") or (
            device_type == "SL_SC_BB_V2" and sub_key == "P2"
        ):
            return SensorDeviceClass.BATTERY

        return None

    @callback
    def _determine_unit(self) -> str | None:
        """Map sub-device to unit."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]
        sub_key = self._sub_key

        if self.device_class == SensorDeviceClass.BATTERY:
            return PERCENTAGE
        if self.device_class == SensorDeviceClass.TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        if self.device_class == SensorDeviceClass.HUMIDITY:
            return PERCENTAGE
        if self.device_class == SensorDeviceClass.ILLUMINANCE:
            return LIGHT_LUX
        if self.device_class == SensorDeviceClass.VOLTAGE:
            return UnitOfElectricPotential.VOLT
        if self.device_class == SensorDeviceClass.CURRENT:
            return UnitOfElectricCurrent.AMPERE
        if self.device_class == SensorDeviceClass.POWER:
            return UnitOfPower.WATT
        if self.device_class == SensorDeviceClass.ENERGY:
            return UnitOfEnergy.KILO_WATT_HOUR
        if self.device_class == SensorDeviceClass.PM25:
            return CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        if self.device_class == SensorDeviceClass.CO2:
            return CONCENTRATION_PARTS_PER_MILLION
        if self.device_class == SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS:
            return CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        if self.device_class == SensorDeviceClass.SOUND_PRESSURE:
            return UnitOfSoundPressure.DECIBEL

        # 燃气浓度单位
        if device_type in GAS_SENSOR_TYPES and sub_key == "P1":
            return CONCENTRATION_PARTS_PER_MILLION  # 一般为甲烷等气体

        return None

    @callback
    def _determine_state_class(self) -> SensorStateClass | None:
        """Determine state class for long-term statistics."""
        # 为传感器设置状态类别，以支持历史图表
        if self.device_class in {
            SensorDeviceClass.TEMPERATURE,
            SensorDeviceClass.HUMIDITY,
            SensorDeviceClass.ILLUMINANCE,
            SensorDeviceClass.POWER,
            SensorDeviceClass.CO2,
            SensorDeviceClass.PM25,
            SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
            SensorDeviceClass.SOUND_PRESSURE,
            SensorDeviceClass.BATTERY,
            SensorDeviceClass.VOLTAGE,
        }:
            return SensorStateClass.MEASUREMENT
        if self.device_class == SensorDeviceClass.ENERGY:
            return SensorStateClass.TOTAL_INCREASING
        return None

    @callback
    def _extract_initial_value(self) -> float | int | None:
        """Extract initial value from device data."""
        # 优先使用友好值
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
                return None

        # 使用原始值并进行必要的转换
        raw_value = self._sub_data.get("val")
        if raw_value is not None:
            return self._convert_raw_value(raw_value)

        return None

    @callback
    def _convert_raw_value(self, raw_value: Any) -> float | int | None:
        """Convert raw value to actual value based on device type."""
        if raw_value is None:
            return None

        numeric_raw_value: float | int
        try:
            numeric_raw_value = float(raw_value)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid non-numeric 'val' received for %s: %s",
                self.unique_id,
                raw_value,
            )
            return None

        # 首先尝试使用type字段进行IEEE754转换
        if hasattr(self, "_sub_data") and "type" in self._sub_data:
            io_type = self._sub_data.get("type")
            if io_type is not None:
                try:
                    converted_val = get_io_friendly_val(io_type, int(numeric_raw_value))
                    if converted_val is not None:
                        return converted_val
                except (ValueError, TypeError, OverflowError) as e:
                    _LOGGER.debug(
                        "IEEE754 conversion failed for %s (type=%s, val=%s): %s",
                        self.unique_id,
                        io_type,
                        numeric_raw_value,
                        e,
                    )

        device_type = self._raw_device[DEVICE_TYPE_KEY]

        # 仅当设备类别是温度或湿度时，才应用此启发式规则
        if self.device_class in {
            SensorDeviceClass.TEMPERATURE,
            SensorDeviceClass.HUMIDITY,
        }:
            # 假设原始值（如 260）通常会大于一个阈值（如100），
            # 而最终值（如 26）则小于它。这是一个处理API不一致性的策略。
            # 这样可以避免将已经是最终值的 26 错误地处理成 2.6。
            if numeric_raw_value > 100:
                return numeric_raw_value / 10.0
            else:
                return numeric_raw_value

        # CO2传感器的特殊转换逻辑
        if self.device_class == SensorDeviceClass.CO2:
            # 只对明显过小的值进行转换，合理范围的值保持不变
            if numeric_raw_value < 10:
                return numeric_raw_value * 100
            elif 10 <= numeric_raw_value < 100:
                return numeric_raw_value * 10
            else:
                # 大于等于100的值认为已经是正确的ppm值，不转换
                return numeric_raw_value

        # 对于其他类型的传感器，保持原有逻辑
        if device_type in CLIMATE_TYPES:
            if (
                device_type in ("SL_CP_DN", "SL_NATURE")
                and self._sub_key in ("P5", "P4")
            ) or (device_type == "SL_TR_ACIPM" and self._sub_key == "P4"):
                return numeric_raw_value / 10.0
            return numeric_raw_value

        # 电量百分比值直接使用
        if self._sub_key in {"BAT", "V", "P4", "P5"}:
            return numeric_raw_value

        # 其他值直接返回
        return numeric_raw_value

    @callback
    def _get_extra_attributes(self) -> dict[str, Any] | None:
        """Get extra state attributes."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]

        # CO2传感器的空气质量等级
        if device_type == "SL_SC_CA" and self._sub_key == "P3":
            val = self._sub_data.get("val", 0)
            return {"air_quality": val}

        # 水浸传感器的导电率等级
        if device_type in WATER_SENSOR_TYPES and self._sub_key == "WA":
            val = self._sub_data.get("val", 0)
            return {"conductivity_level": val}

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for this sensor."""
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
        """Register update listeners."""
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
        """Handle real-time updates."""
        try:
            if not new_data:
                _LOGGER.warning(
                    "Received empty new_data in _handle_update; "
                    "possible upstream issue."
                )
                return
            # 统一处理数据来源
            sub_data = {}
            if "msg" in new_data:
                sub_data = new_data.get("msg", {}).get(self._sub_key, {})
            elif self._sub_key in new_data:
                sub_data = new_data.get(self._sub_key, {})
            else:
                # 兼容直接推送子键值对的格式，例如 {'v': 26.0} 或 {'val': 260}
                sub_data = new_data

            if not sub_data:
                return

            new_value = None
            # 优先使用 'v' (最终值), 否则使用 'val' (原始值)
            if "v" in new_data:
                try:
                    new_value = float(new_data["v"])
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Invalid non-numeric 'v' value received for %s: %s",
                        self.unique_id,
                        new_data["v"],
                    )
                    return
            elif "val" in sub_data:
                new_value = self._convert_raw_value(sub_data["val"])

            if new_value is None:
                # 如果收到无效数据仅打印日志（已在convert中完成）
                return

            self._attr_native_value = new_value
            self._attr_available = True  # 收到有效数据，确保实体是可用的
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self._attr_unique_id, e)

    async def _handle_global_refresh(self) -> None:
        """Handle periodic full data refresh with availability check."""
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
                        "Sub-device %s for %s not found, marking as unavailable.",
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
