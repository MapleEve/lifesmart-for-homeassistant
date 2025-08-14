"""
HAConstantStrategy - HA常量转换工具策略

提取自mapping_engine的HA常量转换逻辑，作为工具策略供其他策略使用。
解决原始代码中常量转换逻辑分散重复的问题。

从原始mapping_engine.py的84-305行提取，包括：
- HA设备类常量映射
- 单位常量映射
- 状态类常量映射
- HVAC模式常量映射
- 命令类型常量映射

由 @MapleEve 创建，基于Phase 2.5关键重构任务
"""

from typing import Dict, Any
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    HVACMode,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfSoundPressure,
    UnitOfTime,
    PERCENTAGE,
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
    LIGHT_LUX,
)

from ..const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_RAW_ON,
    CMD_TYPE_SET_RAW_OFF,
    CMD_TYPE_SET_TEMP_DECIMAL,
)

from .base_strategy import BaseDeviceStrategy


class HAConstantStrategy(BaseDeviceStrategy):
    """
    HA常量转换工具策略

    提供统一的HA常量转换功能，被其他策略类使用。
    解决原始mapping_engine中常量转换逻辑重复的问题。
    """

    def __init__(self):
        """初始化HA常量映射表"""
        self.ha_constants = {
            # 设备类常量
            "device_class": {
                "temperature": SensorDeviceClass.TEMPERATURE,
                "humidity": SensorDeviceClass.HUMIDITY,
                "battery": SensorDeviceClass.BATTERY,
                "power": SensorDeviceClass.POWER,
                "energy": SensorDeviceClass.ENERGY,
                "voltage": SensorDeviceClass.VOLTAGE,
                "current": SensorDeviceClass.CURRENT,
                "pm25": SensorDeviceClass.PM25,
                "pm10": SensorDeviceClass.PM10,
                "co2": SensorDeviceClass.CO2,
                "co": SensorDeviceClass.CO,
                "illuminance": SensorDeviceClass.ILLUMINANCE,
                "motion": BinarySensorDeviceClass.MOTION,
                "door": BinarySensorDeviceClass.DOOR,
                "window": BinarySensorDeviceClass.WINDOW,
                "lock": BinarySensorDeviceClass.LOCK,
                "tamper": BinarySensorDeviceClass.TAMPER,
                "moisture": SensorDeviceClass.MOISTURE,
                "gas": SensorDeviceClass.GAS,
                "smoke": BinarySensorDeviceClass.SMOKE,
                "sound": BinarySensorDeviceClass.SOUND,
                "vibration": BinarySensorDeviceClass.VIBRATION,
                "opening": BinarySensorDeviceClass.OPENING,
                "problem": BinarySensorDeviceClass.PROBLEM,
                "moving": BinarySensorDeviceClass.MOVING,
                "volatile_organic_compounds": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "sound_pressure": SensorDeviceClass.SOUND_PRESSURE,
                "power_factor": SensorDeviceClass.POWER_FACTOR,
                "frequency": SensorDeviceClass.FREQUENCY,
            },
            # 单位常量
            "unit_of_measurement": {
                "celsius": UnitOfTemperature.CELSIUS,
                "percentage": PERCENTAGE,
                "watt": UnitOfPower.WATT,
                "kwh": UnitOfEnergy.KILO_WATT_HOUR,
                "volt": UnitOfElectricPotential.VOLT,
                "ampere": UnitOfElectricCurrent.AMPERE,
                "ppm": CONCENTRATION_PARTS_PER_MILLION,
                "lux": LIGHT_LUX,
                "decibel": UnitOfSoundPressure.DECIBEL,
                "mg_m3": CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
                "ug_m3": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "us_cm": None,  # HA没有微西门每厘米的标准常量
                "h": UnitOfTime.HOURS,
            },
            # 状态类常量
            "state_class": {
                "measurement": SensorStateClass.MEASUREMENT,
                "total_increasing": SensorStateClass.TOTAL_INCREASING,
            },
            # HVAC模式常量
            "hvac_mode": {
                "auto": HVACMode.AUTO,
                "heat": HVACMode.HEAT,
                "cool": HVACMode.COOL,
                "heat_cool": HVACMode.HEAT_COOL,
                "dry": HVACMode.DRY,
                "fan_only": HVACMode.FAN_ONLY,
            },
            # 风扇速度常量
            "fan_speed": {
                "auto": FAN_AUTO,
                "low": FAN_LOW,
                "medium": FAN_MEDIUM,
                "high": FAN_HIGH,
            },
        }

        # 命令类型常量映射
        self.command_types = {
            "CMD_TYPE_ON": CMD_TYPE_ON,
            "CMD_TYPE_OFF": CMD_TYPE_OFF,
            "CMD_TYPE_SET_VAL": CMD_TYPE_SET_VAL,
            "CMD_TYPE_SET_CONFIG": CMD_TYPE_SET_CONFIG,
            "CMD_TYPE_SET_RAW_ON": CMD_TYPE_SET_RAW_ON,
            "CMD_TYPE_SET_RAW_OFF": CMD_TYPE_SET_RAW_OFF,
            "CMD_TYPE_SET_TEMP_DECIMAL": CMD_TYPE_SET_TEMP_DECIMAL,
        }

    def can_handle(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> bool:
        """HA常量策略是工具类，不直接处理设备"""
        return False

    def resolve_device_mapping(
        self, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """HA常量策略是工具类，不直接解析设备"""
        return self.convert_data_to_ha_mapping(raw_config)

    def get_strategy_name(self) -> str:
        return "HAConstantStrategy"

    @property
    def priority(self) -> int:
        return 999  # 工具策略，优先级最低

    def convert_data_to_ha_mapping(self, raw_data: Dict) -> Dict:
        """
        将纯数据层的配置转换为HA规范的映射配置

        从原始mapping_engine.convert_data_to_ha_mapping方法提取

        Args:
            raw_data: 来自mapping_data的原始数据

        Returns:
            应用了HA常量的mapping配置
        """
        if not isinstance(raw_data, dict):
            return raw_data

        result = {}

        for key, value in raw_data.items():
            if isinstance(key, str) and key.endswith("_key") and isinstance(value, str):
                # 将字符串键转换为HA常量
                actual_key = key[:-4]  # 移除"_key"后缀
                result[actual_key] = self._resolve_constant(actual_key, value)
            elif (
                isinstance(key, str) and key == "command_key" and isinstance(value, str)
            ):
                # 转换命令类型
                result["type"] = self.command_types.get(value, value)
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                result[key] = self.convert_data_to_ha_mapping(value)
            elif isinstance(value, (list, tuple)):
                # 处理列表或元组
                result[key] = [
                    (
                        self.convert_data_to_ha_mapping(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _resolve_constant(self, constant_type: str, key: str) -> Any:
        """
        解析常量键值到HA常量

        从原始mapping_engine._resolve_constant方法提取

        Args:
            constant_type: 常量类型 (device_class, unit_of_measurement等)
            key: 常量键值

        Returns:
            对应的HA常量
        """
        if constant_type == "device_class":
            return self.ha_constants["device_class"].get(key, key)
        elif constant_type == "unit_of_measurement":
            return self.ha_constants["unit_of_measurement"].get(key, key)
        elif constant_type == "state_class":
            return self.ha_constants["state_class"].get(key, key)
        elif constant_type == "hvac_mode":
            return self.ha_constants["hvac_mode"].get(key, key)
        elif constant_type == "fan_speed":
            return self.ha_constants["fan_speed"].get(key, key)
        else:
            return key

    def apply_ha_constants_to_mapping(self, mapping_config: Dict) -> Dict:
        """
        将HA标准常量应用到mapping配置中（兼容性方法）

        从原始mapping_engine.apply_ha_constants_to_mapping方法提取

        Args:
            mapping_config: 原始的mapping配置

        Returns:
            应用了HA常量的mapping配置
        """
        if not isinstance(mapping_config, dict):
            return mapping_config

        result = {}

        for key, value in mapping_config.items():
            if key == "device_class" and isinstance(value, str):
                # 将字符串设备类转换为HA常量
                result[key] = self.ha_constants["device_class"].get(value, value)
            elif key == "unit_of_measurement" and isinstance(value, str):
                # 将字符串单位转换为HA常量
                result[key] = self.ha_constants["unit_of_measurement"].get(value, value)
            elif key == "state_class" and isinstance(value, str):
                # 将字符串状态类转换为HA常量
                result[key] = self.ha_constants["state_class"].get(value, value)
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                result[key] = self.apply_ha_constants_to_mapping(value)
            elif isinstance(value, (list, tuple)):
                # 处理列表或元组
                result[key] = [
                    (
                        self.apply_ha_constants_to_mapping(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                result[key] = value

        return result
