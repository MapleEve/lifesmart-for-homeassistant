"""
LifeSmart 动态映射解析引擎 - 增强版

此引擎负责解析包含复杂业务逻辑的设备映射，
支持从纯数据层到HA规范的转换，动态分类、复杂IO口解析等功能。

主要功能:
- 纯数据层到HA规范的转换
- 动态分类设备解析
- 复杂IO口多功能解析
- 业务逻辑执行
- HA标准常量应用
- 命令类型常量映射
"""

from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.button import ButtonDeviceClass
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

# 从const.py导入命令常量
from ..const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_RAW_ON,
    CMD_TYPE_SET_RAW_OFF,
    CMD_TYPE_SET_TEMP_DECIMAL,
)

# 处理ButtonDeviceClass.IDENTIFY的兼容性
try:
    # 在HA 2024.2.0+版本中，ButtonDeviceClass.IDENTIFY存在
    _BUTTON_IDENTIFY = ButtonDeviceClass.IDENTIFY
except AttributeError:
    # 在HA 2023.6.0版本中，ButtonDeviceClass.IDENTIFY不存在，使用None
    _BUTTON_IDENTIFY = None


class EnhancedMappingEngine:
    """增强的动态映射解析引擎，支持纯数据层转换"""

    def __init__(self):
        # HA标准常量映射
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

        # 从原始代码提取的业务逻辑函数
        self.business_logic_functions = {
            # 门锁事件解析逻辑
            "lock_event": self._parse_lock_event,
            # 门窗感应器解析逻辑
            "door_sensor": self._parse_door_sensor,
            # 动态感应器解析逻辑
            "motion_sensor": self._parse_motion_sensor,
            # 云防设备解析逻辑
            "defed_device": self._parse_defed_device,
            # 水浸传感器解析逻辑
            "water_sensor": self._parse_water_sensor,
            # 烟雾感应器解析逻辑
            "smoke_sensor": self._parse_smoke_sensor,
            # 人体存在感应器解析逻辑
            "radar_sensor": self._parse_radar_sensor,
            # 温控设备解析逻辑
            "climate_device": self._parse_climate_device,
        }

    def convert_data_to_ha_mapping(self, raw_data: Dict) -> Dict:
        """
        将纯数据层的配置转换为HA规范的映射配置

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

    def resolve_device_mapping_from_data(
        self, device: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从纯数据层解析设备映射，返回HA规范的配置

        Args:
            device: 设备字典，包含设备信息和数据

        Returns:
            HA规范的设备配置字典
        """
        device_type = device.get("devtype")

        # 从mapping_data导入纯数据
        from .raw_data import DEVICE_SPECS_DATA

        raw_config = DEVICE_SPECS_DATA.get(device_type, {})

        if not raw_config:
            return {}

        # 将纯数据转换为HA规范配置
        ha_config = self.convert_data_to_ha_mapping(raw_config)

        # 检查是否需要动态处理
        if "dynamic_classification" in ha_config:
            return self._resolve_dynamic_classification(
                ha_config, device.get("data", {})
            )

        # 检查是否是版本化设备
        if "versioned" in ha_config:
            return self._resolve_versioned_device(ha_config, device)

        return ha_config

    def apply_ha_constants_to_mapping(self, mapping_config: Dict) -> Dict:
        """
        将HA标准常量应用到mapping配置中（兼容性方法）

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

    def resolve_device_mapping(self, device: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        解析设备映射，返回平台到IO口的映射（兼容性方法）

        Args:
            device: 设备字典，包含设备信息和数据

        Returns:
            平台映射字典，如 {"switch": ["P1"], "sensor": ["P2"]}
        """
        # 优先使用纯数据层
        ha_config = self.resolve_device_mapping_from_data(device)

        if ha_config:
            return self._extract_platform_mapping(ha_config, device.get("data", {}))

        # 降级到原有方法（向后兼容）
        device_type = device.get("devtype")
        device_data = device.get("data", {})

        # 从DEVICE_MAPPING中获取设备配置
        try:
            from .mapping import DEVICE_MAPPING

            device_config = DEVICE_MAPPING.get(device_type, {})
        except ImportError:
            return {}

        # 应用HA常量到配置
        device_config = self.apply_ha_constants_to_mapping(device_config)

        # 检查是否是动态分类设备
        if "dynamic_classification" in device_config:
            return self._resolve_dynamic_classification(device_config, device_data)

        # 检查是否是版本化设备
        if "versioned" in device_config:
            return self._resolve_versioned_device(device_config, device)

        # 静态设备映射
        return self._resolve_static_mapping(device_config, device_data)

    def _extract_platform_mapping(
        self, ha_config: Dict, device_data: Dict
    ) -> Dict[str, List[str]]:
        """
        从HA配置中提取平台到IO口的映射

        Args:
            ha_config: HA规范的设备配置
            device_data: 设备数据

        Returns:
            平台映射字典
        """
        platform_mapping = {}

        for platform, ios in ha_config.items():
            if platform == "name" or not isinstance(ios, dict):
                continue

            # 提取该平台的IO口列表
            io_ports = []
            for io_port, io_config in ios.items():
                if isinstance(io_config, dict) and io_port in device_data:
                    io_ports.append(io_port)

            if io_ports:
                platform_mapping[platform] = io_ports

        return platform_mapping

    def _resolve_dynamic_classification(
        self, device_config: Dict, device_data: Dict
    ) -> Dict[str, List[str]]:
        """解析动态分类设备"""
        dynamic_config = device_config["dynamic_classification"]
        classification_type = dynamic_config.get("type")

        if classification_type == "conditional":
            return self._resolve_conditional_classification(dynamic_config, device_data)
        elif classification_type == "bitwise":
            return self._resolve_bitwise_classification(dynamic_config, device_data)

        return {}

    def _resolve_conditional_classification(
        self, dynamic_config: Dict, device_data: Dict
    ) -> Dict[str, List[str]]:
        """解析条件分类设备"""
        condition_field = dynamic_config.get("condition_field")
        condition_expression = dynamic_config.get("condition_expression")
        modes = dynamic_config.get("modes", {})

        if not condition_field or condition_field not in device_data:
            return {}

        # 获取条件值
        field_data = device_data[condition_field]
        val = field_data.get("val", 0)

        # 执行条件表达式
        condition_result = self._evaluate_expression(condition_expression, {"val": val})

        if condition_result is None:
            return {}

        # 选择对应的模式配置
        selected_mode = modes.get(str(condition_result), {})
        return self._resolve_static_mapping(selected_mode, device_data)

    def _resolve_bitwise_classification(
        self, dynamic_config: Dict, device_data: Dict
    ) -> Dict[str, List[str]]:
        """解析位操作分类设备"""
        source_field = dynamic_config.get("source_field")
        bit_patterns = dynamic_config.get("bit_patterns", {})

        if not source_field or source_field not in device_data:
            return {}

        # 获取位值
        field_data = device_data[source_field]
        bit_value = field_data.get("val", 0)

        result_mapping = {}

        # 遍历位模式
        for pattern_name, pattern_config in bit_patterns.items():
            bit_mask = pattern_config.get("mask", 0)
            expected_value = pattern_config.get("value", 0)
            platform_mapping = pattern_config.get("mapping", {})

            # 检查位模式是否匹配
            if (bit_value & bit_mask) == expected_value:
                for platform, io_ports in platform_mapping.items():
                    if platform not in result_mapping:
                        result_mapping[platform] = []
                    result_mapping[platform].extend(io_ports)

        return result_mapping

    def _resolve_versioned_device(
        self, device_config: Dict, device: Dict
    ) -> Dict[str, List[str]]:
        """解析版本化设备"""
        versioned_config = device_config["versioned"]
        version_field = versioned_config.get("version_field", "version")
        versions = versioned_config.get("versions", {})

        # 从设备信息中获取版本
        device_version = device.get(version_field, "default")
        selected_config = versions.get(str(device_version), versions.get("default", {}))

        return self._resolve_static_mapping(selected_config, device.get("data", {}))

    def _resolve_static_mapping(
        self, device_config: Dict, device_data: Dict
    ) -> Dict[str, List[str]]:
        """解析静态设备映射"""
        platform_mapping = {}

        for platform, ios in device_config.items():
            if platform == "name" or not isinstance(ios, dict):
                continue

            # 提取该平台的IO口列表
            io_ports = []
            for io_port, io_config in ios.items():
                if isinstance(io_config, dict) and io_port in device_data:
                    io_ports.append(io_port)

            if io_ports:
                platform_mapping[platform] = io_ports

        return platform_mapping

    def _evaluate_expression(self, expression: str, variables: Dict) -> Optional[Any]:
        """
        安全评估表达式

        Args:
            expression: 表达式字符串
            variables: 变量字典

        Returns:
            评估结果或None（如果出错）
        """
        try:
            # 简单的表达式评估，仅支持基本操作
            if "val" in expression and "val" in variables:
                val = variables["val"]
                # 替换变量
                safe_expression = expression.replace("val", str(val))
                # 简单的条件判断
                if ">" in safe_expression:
                    parts = safe_expression.split(">")
                    return float(parts[0].strip()) > float(parts[1].strip())
                elif "<" in safe_expression:
                    parts = safe_expression.split("<")
                    return float(parts[0].strip()) < float(parts[1].strip())
                elif "==" in safe_expression:
                    parts = safe_expression.split("==")
                    return parts[0].strip() == parts[1].strip()
            return None
        except (ValueError, IndexError, AttributeError):
            return None

    # 业务逻辑方法占位符
    def _parse_lock_event(self, data: Dict) -> Dict:
        """解析门锁事件"""
        return {}

    def _parse_door_sensor(self, data: Dict) -> Dict:
        """解析门窗传感器"""
        return {}

    def _parse_motion_sensor(self, data: Dict) -> Dict:
        """解析运动传感器"""
        return {}

    def _parse_defed_device(self, data: Dict) -> Dict:
        """解析云防设备"""
        return {}

    def _parse_water_sensor(self, data: Dict) -> Dict:
        """解析水浸传感器"""
        return {}

    def _parse_smoke_sensor(self, data: Dict) -> Dict:
        """解析烟雾传感器"""
        return {}

    def _parse_radar_sensor(self, data: Dict) -> Dict:
        """解析人体存在传感器"""
        return {}

    def _parse_climate_device(self, data: Dict) -> Dict:
        """解析温控设备"""
        return {}


# 创建全局引擎实例
mapping_engine = EnhancedMappingEngine()
