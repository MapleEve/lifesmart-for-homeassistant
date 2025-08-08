"""
LifeSmart 动态映射解析引擎。

此引擎负责解析包含复杂业务逻辑的设备映射，
支持动态分类、复杂IO口解析等功能。

主要功能:
- 动态分类设备解析
- 复杂IO口多功能解析
- 业务逻辑执行
- HA标准常量应用
"""

from typing import Any, Dict, List

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import HVACMode
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


# 从const.py导入需要的常量


class DynamicMappingEngine:
    """动态映射解析引擎"""

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
                "co2": SensorDeviceClass.CO2,
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
            },
            # 单位常量
            "unit_of_measurement": {
                "temperature": UnitOfTemperature.CELSIUS,
                "percentage": PERCENTAGE,
                "power": UnitOfPower.WATT,
                "energy": UnitOfEnergy.KILO_WATT_HOUR,
                "voltage": UnitOfElectricPotential.VOLT,
                "current": UnitOfElectricCurrent.AMPERE,
                "ppm": CONCENTRATION_PARTS_PER_MILLION,
                "lux": LIGHT_LUX,
                "db": UnitOfSoundPressure.DECIBEL,
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

    def apply_ha_constants_to_mapping(self, mapping_config: Dict) -> Dict:
        """
        将HA标准常量应用到mapping配置中

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
        解析设备映射，返回平台到IO口的映射

        Args:
            device: 设备字典，包含设备信息和数据

        Returns:
            平台映射字典，如 {"switch": ["P1"], "sensor": ["P2"]}
        """
        device_type = device.get("devtype")
        device_data = device.get("data", {})

        # 从DEVICE_MAPPING中获取设备配置
        from ..device.mapping import DEVICE_MAPPING

        device_config = DEVICE_MAPPING.get(device_type, {})

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

        # 查找匹配的模式
        for mode_condition, mode_config in modes.items():
            if self._match_condition(condition_result, mode_condition):
                return self._extract_platforms_from_mode(mode_config)

        return {}

    def _resolve_bitwise_classification(
        self, dynamic_config: Dict, device_data: Dict
    ) -> Dict[str, List[str]]:
        """解析位运算分类设备"""
        condition_field = dynamic_config.get("condition_field")
        condition_expression = dynamic_config.get("condition_expression")
        modes = dynamic_config.get("modes", {})

        if not condition_field or condition_field not in device_data:
            return {}

        # 获取条件值
        field_data = device_data[condition_field]
        val = field_data.get("val", 0)

        # 执行位运算表达式
        condition_result = self._evaluate_expression(condition_expression, {"val": val})

        if condition_result is None:
            return {}

        # 查找匹配的模式
        for mode_condition, mode_config in modes.items():
            if self._match_condition(condition_result, mode_condition):
                return self._extract_platforms_from_mode(mode_config)

        return {}

    def _resolve_versioned_device(
        self, device_config: Dict, device: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """解析版本化设备"""
        device_type = device.get("devtype", "")
        full_cls = device.get("fullCls", "")

        versioned_configs = device_config.get("versioned", {})

        # 检查版本化设备类型
        for version_key, version_config in versioned_configs.items():
            if version_key in full_cls or version_key == device_type:
                return self._resolve_static_mapping(
                    version_config, device.get("data", {})
                )

        return {}

    def _resolve_static_mapping(
        self, device_config: Dict, device_data: Dict
    ) -> Dict[str, List[str]]:
        """解析静态设备映射"""
        platforms = {}

        for platform, config in device_config.items():
            if platform in [
                "switch",
                "light",
                "sensor",
                "binary_sensor",
                "cover",
                "climate",
                "button",
                "lock",
                "fan",
            ]:
                if isinstance(config, dict):
                    # 检查是否是新的直接映射格式
                    if all(
                        isinstance(io_config, dict) and "description" in io_config
                        for io_config in config.values()
                    ):
                        # 新格式：直接IO口映射
                        ios = list(config.keys())
                        valid_ios = [io for io in ios if io in device_data]
                        if valid_ios:
                            platforms[platform] = valid_ios
                    else:
                        # ❌ 旧格式 TODO 必须重构掉：helper函数生成的复杂结构或嵌套结构
                        # 递归查找所有IO口
                        all_ios = self._extract_ios_from_config(config)
                        valid_ios = [io for io in all_ios if io in device_data]
                        if valid_ios:
                            platforms[platform] = valid_ios

        return platforms

    def _extract_ios_from_config(self, config: Dict) -> List[str]:
        """从配置中提取所有IO口"""
        ios = []

        # 常见的IO口模式
        io_patterns = [
            "P1",
            "P2",
            "P3",
            "P4",
            "P5",
            "P6",
            "P7",
            "P8",
            "P9",
            "P10",
            "L1",
            "L2",
            "L3",
            "O",
            "T",
            "H",
            "V",
            "M",
            "G",
            "A",
            "B",
            "C",
        ]

        for key, value in config.items():
            if key in io_patterns:
                ios.append(key)
            elif isinstance(value, dict):
                # 递归查找嵌套的IO口
                ios.extend(self._extract_ios_from_config(value))
            elif isinstance(value, (list, tuple)):
                # 处理列表或元组中的配置
                for item in value:
                    if isinstance(item, dict):
                        ios.extend(self._extract_ios_from_config(item))

        return ios

    def _evaluate_expression(self, expression: str, context: Dict[str, Any]) -> Any:
        """评估表达式"""
        try:
            # 简单的表达式评估
            # 支持基本的位运算和比较运算
            if "==" in expression:
                left, right = expression.split("==", 1)
                left_val = self._evaluate_operand(left.strip(), context)
                right_val = self._evaluate_operand(right.strip(), context)
                return left_val == right_val
            elif "&" in expression:
                left, right = expression.split("&", 1)
                left_val = self._evaluate_operand(left.strip(), context)
                right_val = self._evaluate_operand(right.strip(), context)
                return left_val & right_val
            elif ">>" in expression:
                left, right = expression.split(">>", 1)
                left_val = self._evaluate_operand(left.strip(), context)
                right_val = self._evaluate_operand(right.strip(), context)
                return left_val >> right_val
            elif "|" in expression:
                # 处理多个条件，如 "3|6"
                conditions = [c.strip() for c in expression.split("|")]
                return any(
                    self._evaluate_condition(context.get("val", 0), c)
                    for c in conditions
                )
            else:
                return self._evaluate_operand(expression, context)
        except Exception:
            return None

    def _evaluate_operand(self, operand: str, context: Dict[str, Any]) -> Any:
        """评估操作数"""
        operand = operand.strip()
        if operand in context:
            return context[operand]
        elif operand.isdigit():
            return int(operand)
        else:
            return operand

    def _match_condition(self, result: Any, condition: str) -> bool:
        """匹配条件"""
        try:
            if "|" in condition:
                # 处理或条件
                conditions = [c.strip() for c in condition.split("|")]
                return any(self._match_condition(result, c) for c in conditions)
            elif condition.isdigit():
                return result == int(condition)
            else:
                return str(result) == condition
        except Exception:
            return False

    def _extract_platforms_from_mode(self, mode_config: Dict) -> Dict[str, List[str]]:
        """从模式配置中提取平台映射"""
        platforms = {}
        platforms_config = mode_config.get("platforms", {})

        for platform, config in platforms_config.items():
            if "ios" in config:
                platforms[platform] = config["ios"]

        return platforms

    def _evaluate_condition(self, val: int, condition: str) -> bool:
        """评估条件"""
        try:
            if condition.isdigit():
                return val == int(condition)
            else:
                return False
        except Exception:
            return False

    # 业务逻辑函数 - 从原始代码中提取
    def _parse_lock_event(self, sub_data: Dict[str, Any]) -> bool:
        """解析门锁事件 - 从原始代码提取"""
        val = sub_data.get("val", 0)
        unlock_type = sub_data.get("type", 0)
        unlock_user = val & 0xFFF

        return (
            val != 0
            and unlock_type & 0x01 == 1
            and unlock_user != 0
            and val >> 12 != 15
        )

    def _parse_door_sensor(
        self, device_type: str, sub_key: str, sub_data: Dict[str, Any]
    ) -> bool:
        """解析门窗感应器 - 从原始代码提取"""
        val = sub_data.get("val", 0)
        type_val = sub_data.get("type", 0)

        if device_type in {"SL_SC_G", "SL_SC_BG", "SL_SC_GS"}:
            if device_type == "SL_SC_GS" and sub_key in {"P1", "P2"}:
                return type_val & 1 == 1
            if device_type == "SL_SC_BG" and sub_key == "AXS":
                return val != 0
            return val == 0 if sub_key == "G" else val != 0

        if device_type == "SL_DF_GG" and sub_key == "A":
            return val == 0  # 云防门窗：0=开，1=关

        return type_val & 1 == 1

    def _parse_motion_sensor(self, device_type: str, sub_data: Dict[str, Any]) -> bool:
        """解析动态感应器 - 从原始代码提取"""
        val = sub_data.get("val", 0)

        if device_type in {"SL_SC_MHW", "SL_SC_BM", "SL_SC_CM", "SL_BP_MZ"}:
            return val != 0

        if device_type == "SL_DF_MM":
            type_val = sub_data.get("type", 0)
            return type_val & 1 == 1

        return False

    def _parse_defed_device(self, sub_data: Dict[str, Any]) -> bool:
        """解析云防设备 - 从原始代码提取"""
        type_val = sub_data.get("type", 0)
        return type_val & 1 == 1

    def _parse_water_sensor(self, sub_data: Dict[str, Any]) -> bool:
        """解析水浸传感器 - 从原始代码提取"""
        val = sub_data.get("val", 0)
        return val != 0

    def _parse_smoke_sensor(self, sub_data: Dict[str, Any]) -> bool:
        """解析烟雾感应器 - 从原始代码提取"""
        val = sub_data.get("val", 0)
        return val != 0

    def _parse_radar_sensor(self, sub_data: Dict[str, Any]) -> bool:
        """解析人体存在感应器 - 从原始代码提取"""
        val = sub_data.get("val", 0)
        return val != 0

    def _parse_climate_device(self, device_type: str, sub_data: Dict[str, Any]) -> bool:
        """解析温控设备 - 从原始代码提取"""
        type_val = sub_data.get("type", 0)
        return type_val & 1 == 1


# 全局映射引擎实例
mapping_engine = DynamicMappingEngine()
