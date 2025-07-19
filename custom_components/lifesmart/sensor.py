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
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, LifeSmartEntity, generate_entity_id, async_setup_entities
from .const import (
    # 核心常量
    DEVICE_DATA_KEY,
    # --- 设备类型常量导入 ---
    ALL_SENSOR_TYPES,
    EV_SENSOR_TYPES,
    ENVIRONMENT_SENSOR_TYPES,
    GAS_SENSOR_TYPES,
    NOISE_SENSOR_TYPES,
    POWER_METER_PLUG_TYPES,
    SMART_PLUG_TYPES,
    POWER_METER_TYPES,
    LOCK_TYPES,
    COVER_TYPES,
    DEFED_SENSOR_TYPES,
    WATER_SENSOR_TYPES,
    SUPPORTED_SWITCH_TYPES,
    GARAGE_DOOR_TYPES,
    CLIMATE_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart sensors from a config entry."""
    
    # Define device type to entity class mapping for sensors
    SENSOR_ENTITY_MAP = {}
    
    # Add all sensor types to the mapping
    for device_type in ALL_SENSOR_TYPES:
        SENSOR_ENTITY_MAP[device_type] = LifeSmartSensor
    
    # Define device filter function for sensors including special SL_NATURE handling
    def device_filter(device_type: str, device: dict) -> bool:
        """Filter devices that should be handled by sensor platform."""
        if device_type == "SL_NATURE":
            # Only include SL_NATURE temperature control panels
            p5_val = device.get(DEVICE_DATA_KEY, {}).get("P5", {}).get("val", 1) & 0xFF
            return p5_val == 3
        
        return device_type in ALL_SENSOR_TYPES
    
    # Define sub-device filter with special SL_NATURE handling
    def sub_device_filter(device_type: str, sub_key: str) -> bool:
        """Filter sub-devices for sensors."""
        if device_type == "SL_NATURE":
            # For SL_NATURE, only P4 is the current temperature sensor
            return sub_key == "P4"
        
        return _is_sensor_subdevice(device_type, sub_key)
    
    # Use the generic setup helper
    await async_setup_entities(
        hass=hass,
        config_entry=config_entry,
        async_add_entities=async_add_entities,
        platform=Platform.SENSOR,
        entity_class_map=SENSOR_ENTITY_MAP,
        device_filter_func=device_filter,
        sub_device_filter_func=sub_device_filter,
    )


def _is_sensor_subdevice(device_type: str, sub_key: str) -> bool:
    """判断一个子设备是否为有效的数值传感器。"""
    if device_type in CLIMATE_TYPES:
        # 温控设备的温度/阀门等状态由 climate 实体内部管理
        if device_type == "SL_CP_DN" and sub_key == "P5":
            return True
        if device_type == "SL_CP_VL" and sub_key == "P6":
            return True
        if device_type == "SL_TR_ACIPM" and sub_key in ["P4", "P5"]:
            return True
        return False

    # 环境感应器（包括温度、湿度、光照、电压）
    if device_type in EV_SENSOR_TYPES and sub_key in {
        "T",
        "H",
        "Z",
        "V",
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
    }:
        return True

    # TVOC, CO2, CH2O 传感器
    if device_type in ENVIRONMENT_SENSOR_TYPES and sub_key in {"P1", "P3", "P4"}:
        return True

    # 气体感应器
    if device_type in GAS_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    # 门锁电量
    if device_type in LOCK_TYPES and sub_key == "BAT":
        return True

    # 窗帘位置
    if device_type in COVER_TYPES and sub_key == "P8":
        return True

    # 智能插座
    if device_type in POWER_METER_PLUG_TYPES and sub_key in {"P2", "P3", "P4"}:
        return True

    # 智能插座 (非计量版，但也可能带计量功能)
    if device_type in SMART_PLUG_TYPES and sub_key in {"EV", "EI", "EP", "EPA"}:
        return True

    # 噪音感应器
    if device_type in NOISE_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    # ELIQ电量计量器
    if device_type in POWER_METER_TYPES and sub_key in {"EPA", "EE", "EP"}:
        return True

    # 云防系列传感器
    if device_type in DEFED_SENSOR_TYPES and sub_key in {"T", "V"}:
        return True

    # 水浸传感器（只保留电压）
    if device_type in WATER_SENSOR_TYPES and sub_key == "V":
        return True

    # SL_SW* 和 SL_MC* 系列的 P4 是电量传感器
    if device_type in SUPPORTED_SWITCH_TYPES and sub_key == "P4":
        return True

    # SL_SC_BB_V2 的 P2 是电量传感器
    if device_type == "SL_SC_BB_V2" and sub_key == "P2":
        return True

    if device_type in GARAGE_DOOR_TYPES:
        return False

    return False


class LifeSmartSensor(LifeSmartEntity, SensorEntity):
    """LifeSmart sensor entity with enhanced compatibility."""

    def __init__(
        self,
        device: LifeSmartDevice,
        raw_device: dict[str, Any],
        sub_device_key: str,
        sub_device_data: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        # Call parent constructor
        super().__init__(device, raw_device, client, entry_id, sub_device_key)
        
        # Store sub_device_data for sensor-specific use
        self._sub_data = sub_device_data
        
        # Set sensor-specific attributes
        self._attr_device_class = self._determine_device_class()
        self._attr_state_class = self._determine_state_class()
        self._attr_native_unit_of_measurement = self._determine_unit()
        self._attr_native_value = self._extract_initial_value()
        self._attr_extra_state_attributes = self._get_extra_attributes()

    @callback
    def _determine_device_class(self) -> SensorDeviceClass | None:
        """Automatically determine device class based on sub-device."""
        device_type = self._devtype
        sub_key = self._sub_key

        # 气体传感器优先判断
        if device_type in GAS_SENSOR_TYPES and sub_key in {"P1", "P2"}:
            return SensorDeviceClass.GAS

        # 温控设备特殊处理
        if device_type in CLIMATE_TYPES:
            if sub_key == "P5":
                return (
                    SensorDeviceClass.TEMPERATURE
                    if device_type == "SL_CP_DN"
                    else SensorDeviceClass.PM25
                )
            if sub_key == "P6":
                return SensorDeviceClass.BATTERY
            if sub_key == "P4":
                return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
            return None

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

        # TVOC 传感器的设备
        if device_type in ENVIRONMENT_SENSOR_TYPES:
            if device_type == "SL_SC_CQ":
                return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
            if device_type == "SL_SC_CA":
                return SensorDeviceClass.CO2
            if device_type == "SL_SC_CH":
                return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS  # 甲醛也属于VOC

        # 智能插座特殊处理
        if device_type in POWER_METER_PLUG_TYPES:
            if sub_key == "P2":
                return SensorDeviceClass.ENERGY
            if sub_key == "P3":
                return SensorDeviceClass.POWER
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

        # 环境感应器（EV系列）
        if device_type in EV_SENSOR_TYPES:
            if sub_key == "T":
                return SensorDeviceClass.TEMPERATURE
            if sub_key == "H":
                return SensorDeviceClass.HUMIDITY
            if sub_key == "V":
                return SensorDeviceClass.VOLTAGE
            if sub_key == "Z":
                return SensorDeviceClass.ILLUMINANCE
            if device_type in ENVIRONMENT_SENSOR_TYPES and device_type != "SL_SC_CH":
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
        device_type = self._devtype
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
        if self.device_class in [
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
        ]:
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
            return value

        # 使用原始值并进行必要的转换
        raw_value = self._sub_data.get("val")
        if raw_value is not None:
            return self._convert_raw_value(raw_value)

        return None

    @callback
    def _convert_raw_value(self, raw_value: int) -> float | int:
        """Convert raw value to actual value based on device type."""
        device_type = self._devtype

        # 温度值通常需要除以10
        if (
            self._sub_key in {"T", "P1"}
            and self.device_class == SensorDeviceClass.TEMPERATURE
        ):
            return raw_value / 10.0

        # 湿度值需要除以10
        if (
            self._sub_key in {"H", "P2"}
            and self.device_class == SensorDeviceClass.HUMIDITY
        ):
            return raw_value / 10.0

        # CO2传感器的P1(温度)和P2(湿度)也需要除以10
        if device_type in EV_SENSOR_TYPES:
            if self._sub_key == "P1":  # 温度
                return raw_value / 10.0
            if self._sub_key == "P2":  # 湿度
                return raw_value / 10.0

        if device_type in CLIMATE_TYPES:
            # 地暖底板温度和新风VOC都需要除以10
            if (device_type == "SL_CP_DN" and self._sub_key == "P5") or (
                device_type == "SL_TR_ACIPM" and self._sub_key == "P4"
            ):
                return raw_value / 10.0
            # 其他值（如电量、PM2.5）直接使用
            return raw_value

        # 电量百分比值直接使用
        if self._sub_key in {"BAT", "V", "P4", "P5"}:
            return raw_value

        # 其他值直接返回
        return raw_value

    @callback
    def _get_extra_attributes(self) -> dict[str, Any] | None:
        """Get extra state attributes."""
        device_type = self._devtype

        # CO2传感器的空气质量等级
        if device_type == "SL_SC_CA" and self._sub_key == "P3":
            val = self._sub_data.get("val", 0)
            return {"air_quality": val}

        # 水浸传感器的导电率等级
        if device_type in WATER_SENSOR_TYPES and self._sub_key == "WA":
            val = self._sub_data.get("val", 0)
            return {"conductivity_level": val}

        return None

    @callback
    def _handle_update(self, new_data: dict) -> None:
        """Handle real-time updates."""
        try:
            # 处理WebSocket推送的数据格式
            if "msg" in new_data:
                sub_data = new_data.get("msg", {}).get(self._sub_key, {})
                val = sub_data.get("v") or sub_data.get("val")
            else:
                val = new_data.get("v") or new_data.get("val")

            if val is not None:
                self._attr_native_value = (
                    self._convert_raw_value(val) if "v" not in new_data else val
                )
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self.entity_id, e)

    def _update_from_sub_data(self, sub_data: dict) -> None:
        """Update sensor state from sub-device data during global refresh."""
        val = sub_data.get("v") or sub_data.get("val")
        if val is not None:
            self._attr_native_value = self._convert_raw_value(val)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self._attr_native_value
