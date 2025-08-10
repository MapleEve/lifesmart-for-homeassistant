"""
LifeSmart 动态映射解析引擎 - 增强版

此引擎负责解析包含复杂业务逻辑的设备映射，
支持从纯数据层到HA规范的转换，动态分类、复杂IO口解析等功能。
由 @MapleEve 初始创建和维护

主要功能:
- 纯数据层到HA规范的转换
- 动态分类设备解析
- 复杂IO口多功能解析
- 业务逻辑执行
- HA标准常量应用
- 命令类型常量映射
"""

from typing import Any, Optional, Dict

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

# 导入数据处理器
try:
    from ..data.processors.data_processors import (
        is_alm_io_port,
        get_alm_subdevices,
        is_evtlo_io_port,
        get_evtlo_subdevices,
    )

    DATA_PROCESSORS_AVAILABLE = True
except ImportError:
    DATA_PROCESSORS_AVAILABLE = False

# 导入逻辑处理器
from ..data.processors.logic_processors import (
    get_processor_registry,
)


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
                "volatile_organic_compounds": (
                    SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
                ),
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

        # 集成业务逻辑处理器
        self.logic_registry = get_processor_registry()

        # 导入设备分类器
        try:
            from ..data.processors.device_classifier import device_classifier

            self.device_classifier = device_classifier
        except ImportError:
            self.device_classifier = None

        # 初始化运行时管理器（延迟初始化）
        self.runtime_manager = None

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

    def get_runtime_manager(self, hass=None):
        """
        获取或初始化运行时管理器

        Args:
            hass: Home Assistant实例（可选）

        Returns:
            运行时管理器实例
        """
        if self.runtime_manager is None:
            try:
                from ..data.processors.dynamic_runtime_manager import (
                    DynamicDeviceRuntimeManager,
                )

                self.runtime_manager = DynamicDeviceRuntimeManager(self, hass)
            except ImportError:
                return None
        return self.runtime_manager

    def register_dynamic_device(self, device: dict[str, Any], hass=None) -> bool:
        """
        注册动态设备到运行时管理器

        Args:
            device: 设备信息
            hass: Home Assistant实例（可选）

        Returns:
            注册成功返回True
        """
        runtime_manager = self.get_runtime_manager(hass)
        if runtime_manager:
            return runtime_manager.register_device(device)
        return False

    def convert_data_to_ha_mapping(self, raw_data: dict) -> dict:
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
        self, device: dict[str, Any]
    ) -> dict[str, Any]:
        """
        从纯数据层解析设备映射，返回HA规范的配置
        增强版本：集成业务逻辑处理器

        Args:
            device: 设备字典，包含设备信息和数据

        Returns:
            HA规范的设备配置字典
        """
        device_type = device.get("devtype")

        # 从mapping_data导入纯数据
        from .device_specs import DEVICE_SPECS_DATA

        raw_config = DEVICE_SPECS_DATA.get(device_type, {})

        if not raw_config:
            return {}

        # 检查是否是动态分类设备
        if raw_config.get("dynamic", False):
            return self._resolve_dynamic_device_with_logic(raw_config, device)

        # 检查是否是版本化设备
        if "versioned" in raw_config:
            # 对于版本化设备，先获取正确的版本配置，然后转换为HA格式
            versioned_config = raw_config["versioned"]

            if (
                isinstance(versioned_config, bool)
                and versioned_config
                and "version_modes" in raw_config
            ):
                # 提取版本信息
                device_version = self._extract_version_from_fullcls(device)
                if not device_version:
                    device_version = device.get("version", "default")

                # 获取版本对应的配置
                versions = raw_config["version_modes"]
                selected_config = versions.get(
                    str(device_version), versions.get("default", {})
                )

                # 将版本配置转换为HA规范并应用业务逻辑处理
                return self.convert_data_to_ha_mapping_with_logic(
                    selected_config, device
                )

        # 将纯数据转换为HA规范配置，并应用业务逻辑处理
        ha_config = self.convert_data_to_ha_mapping_with_logic(raw_config, device)

        # 检查是否需要动态处理
        if "dynamic_classification" in ha_config:
            return self._resolve_dynamic_classification(
                ha_config, device.get("data", {})
            )

        return ha_config

    def convert_data_to_ha_mapping_with_logic(
        self, raw_data: dict, device: dict[str, Any]
    ) -> dict:
        """
        将纯数据层的配置转换为HA规范的映射配置
        增强版本：集成业务逻辑处理

        Args:
            raw_data: 来自mapping_data的原始数据
            device: 完整设备信息，包含数据

        Returns:
            应用了HA常量和业务逻辑的mapping配置
        """
        if not isinstance(raw_data, dict):
            return raw_data

        result = {}
        device_data = device.get("data", {})

        for key, value in raw_data.items():
            if key == "name" or key == "dynamic":
                result[key] = value
                continue

            # 处理平台配置
            if isinstance(value, dict) and any(
                platform_key in value
                for platform_key in [
                    "description",
                    "rw",
                    "data_type",
                    "conversion",
                    "detailed_description",
                ]
            ):
                # 这是单个IO口配置
                result[key] = self._process_io_config_with_logic(
                    value, device_data.get(key, {}), device.get("devtype", "")
                )
            elif isinstance(value, dict):
                # 这是平台或嵌套配置
                platform_result = {}
                for io_key, io_value in value.items():
                    if isinstance(io_value, dict):
                        platform_result[io_key] = self._process_io_config_with_logic(
                            io_value,
                            device_data.get(io_key, {}),
                            device.get("devtype", ""),
                        )
                    else:
                        platform_result[io_key] = io_value
                result[key] = platform_result
            elif isinstance(value, (list, tuple)):
                # 处理列表或元组
                result[key] = [
                    (
                        self.convert_data_to_ha_mapping_with_logic(item, device)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _process_io_config_with_logic(
        self, io_config: dict[str, Any], io_data: dict[str, Any], device_type: str
    ) -> dict[str, Any]:
        """
        处理单个IO口配置，应用业务逻辑处理器

        Args:
            io_config: IO口原始配置
            io_data: IO口实际数据
            device_type: 设备类型

        Returns:
            处理后的IO口配置
        """
        # 防护检查：如果io_config不是字典，返回简化配置
        if not isinstance(io_config, dict):
            return {
                "description": str(io_config) if io_config else "Unknown",
                "rw": "RW",
                "data_type": "generic",
                "conversion": "val_direct",
                "_logic_processor": "none",
                "_can_process_value": False,
            }

        # 先进行基本的HA常量转换
        processed_config = self.convert_data_to_ha_mapping(io_config)

        # 查找合适的逻辑处理器
        processor = None
        processor_type = processed_config.get("processor_type")
        if processor_type and self.logic_registry:
            processor = self.logic_registry.get_processor(processor_type)

        if processor:
            # 应用业务逻辑处理器的元数据
            processed_config["_logic_processor"] = processor.get_processor_type()
            processed_config["_can_process_value"] = True

            # 如果有实际数据，也处理一下作为示例
            if io_data:
                try:
                    processed_value = processor.process_value(
                        io_data.get("val"), io_data.get("type", 0)
                    )
                    processed_config["_example_processed_value"] = processed_value
                except Exception as e:
                    processed_config["_processing_error"] = str(e)
        else:
            processed_config["_logic_processor"] = "none"
            processed_config["_can_process_value"] = False

        return processed_config

    def _resolve_dynamic_device_with_logic(
        self, raw_config: dict[str, Any], device: dict[str, Any]
    ) -> dict[str, Any]:
        """
        解析动态设备配置，使用逻辑处理器

        Args:
            raw_config: 原始动态设备配置
            device: 设备完整信息

        Returns:
            解析后的设备配置
        """
        device_data = device.get("data", {})

        # 使用设备分类器确定设备模式
        device_mode = (
            self.device_classifier.classify_device(raw_config, device_data)
            if self.device_classifier
            else None
        )

        # 根据分类结果选择对应的配置
        if device_mode == "switch_mode":
            # 处理开关模式 - 支持两种配置结构
            switch_config = None

            # 方法1: 从顶层直接获取 (SL_NATURE风格)
            if "switch_mode" in raw_config:
                switch_config = raw_config["switch_mode"]
            # 方法2: 从control_modes中获取 (SL_P风格)
            elif (
                "control_modes" in raw_config
                and "switch_mode" in raw_config["control_modes"]
            ):
                switch_config = raw_config["control_modes"]["switch_mode"]

            if not switch_config:
                return {
                    "_device_mode": device_mode,
                    "_error": "switch_mode configuration not found",
                }

            result = {"_device_mode": device_mode}

            # 方法1: SL_NATURE风格 - 使用io列表
            if "io" in switch_config:
                io_list = switch_config.get("io", [])
                sensor_io_list = switch_config.get("sensor_io", [])

                # 添加开关平台 - 为所有io端口创建开关配置（即使设备数据中不存在）
                if io_list:
                    result["switch"] = {}
                    for io_port in io_list:
                        # 使用默认开关逻辑
                        result["switch"][io_port] = {
                            "description": f"开关{io_port}",
                            "rw": "RW",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "detailed_description": (
                                "`type&1==1` 表示打开；`type&1==0` 表示关闭"
                            ),
                            "_logic_processor": "type_bit_0_switch",
                        }

                # 添加传感器平台 - 仅为存在于设备数据中的sensor_io端口
                # 对于SL_NATURE，排除P5端口（只是设备类型标识符，不是传感器数据）
                if sensor_io_list:
                    result["sensor"] = {}
                    for io_port in sensor_io_list:
                        # 对于SL_NATURE的switch_mode，P5只是设备类型标识符，不是传感器数据
                        if (
                            io_port == "P5"
                            and device.get("devtype") == "SL_NATURE"
                            and device_mode == "switch_mode"
                        ):
                            continue

                        if io_port in device_data:
                            result["sensor"][io_port] = {
                                "description": f"传感器{io_port}",
                                "rw": "R",
                                "data_type": "sensor",
                                "conversion": "val_direct",
                                "_logic_processor": "direct_value_passthrough",
                            }

            # 方法2: SL_P风格 - 直接包含平台配置
            else:
                # 直接从 switch_config 中提取平台配置
                for platform_name in [
                    "switch",
                    "sensor",
                    "binary_sensor",
                    "light",
                    "cover",
                    "climate",
                ]:
                    if platform_name in switch_config:
                        result[platform_name] = {}
                        platform_config = switch_config[platform_name]
                        for io_port, io_config in platform_config.items():
                            if isinstance(io_config, dict):
                                result[platform_name][io_port] = (
                                    self._process_io_config_with_logic(
                                        io_config,
                                        device_data.get(io_port, {}),
                                        device.get("devtype", ""),
                                    )
                                )

            return result

        elif device_mode == "climate_mode" and "climate_mode" in raw_config:
            # 处理温控模式 - 直接使用raw_config中定义的climate配置
            climate_config = raw_config["climate_mode"].get("climate", {})
            result = {"_device_mode": device_mode}

            # climate_config直接包含IO端口配置，而不是平台嵌套
            # 结构: {"P1": {...}, "P4": {...}, "P5": {...}}
            if climate_config:
                result["climate"] = {}

                # 同时检查是否有传感器IO口需要生成传感器平台
                sensor_ios = {}

                for io_port, io_config in climate_config.items():
                    if isinstance(io_config, dict):
                        processed_config = self._process_io_config_with_logic(
                            io_config,
                            device_data.get(io_port, {}),
                            device.get("devtype", ""),
                        )

                        result["climate"][io_port] = processed_config

                        # 检查是否是传感器IO口（有device_class、unit_of_measurement等传感器特征）
                        if self._is_sensor_io_config(io_config):
                            sensor_ios[io_port] = processed_config

                # 如果有传感器IO口，生成传感器平台
                if sensor_ios:
                    result["sensor"] = sensor_ios

            return result

        elif device_mode == "cover_mode":
            # 处理窗帘模式 - 支持两种配置结构
            cover_config = None

            # 方法1: 从顶层直接获取 (SL_NATURE风格)
            if "cover_mode" in raw_config:
                cover_config = raw_config["cover_mode"]
            # 方法2: 从control_modes中获取 (SL_P风格)
            elif (
                "control_modes" in raw_config
                and "cover_mode" in raw_config["control_modes"]
            ):
                cover_config = raw_config["control_modes"]["cover_mode"]

            if not cover_config:
                return {
                    "_device_mode": device_mode,
                    "_error": "cover_mode configuration not found",
                }

            result = {"_device_mode": device_mode}

            # 直接从 cover_config 中提取平台配置
            for platform_name in [
                "cover",
                "sensor",
                "binary_sensor",
                "light",
                "switch",
            ]:
                if platform_name in cover_config:
                    result[platform_name] = {}
                    platform_config = cover_config[platform_name]
                    for io_port, io_config in platform_config.items():
                        if isinstance(io_config, dict):
                            result[platform_name][io_port] = (
                                self._process_io_config_with_logic(
                                    io_config,
                                    device_data.get(io_port, {}),
                                    device.get("devtype", ""),
                                )
                            )

            return result

        elif device_mode == "free_mode":
            # 处理自由模式 - SL_P设备的默认模式
            free_config = None

            # 从 control_modes 中获取 free_mode 配置
            if (
                "control_modes" in raw_config
                and "free_mode" in raw_config["control_modes"]
            ):
                free_config = raw_config["control_modes"]["free_mode"]
            elif "free_mode" in raw_config:
                free_config = raw_config["free_mode"]

            if not free_config:
                return {
                    "_device_mode": device_mode,
                    "_error": "free_mode configuration not found",
                }

            result = {"_device_mode": device_mode}

            # 直接从 free_config 中提取平台配置
            for platform_name in [
                "binary_sensor",
                "sensor",
                "switch",
                "light",
                "cover",
                "climate",
            ]:
                if platform_name in free_config:
                    result[platform_name] = free_config[platform_name]

            return result

        else:
            # 未知模式，返回基础配置
            return {
                "_device_mode": device_mode,
                "_error": f"Unknown device mode: {device_mode}",
            }

    def process_device_io_value(
        self,
        device_type: str,
        io_port: str,
        io_config: dict[str, Any],
        raw_data: dict[str, Any],
    ) -> Any:
        """
        处理设备IO口的实际数据值

        Args:
            device_type: 设备类型
            io_port: IO口名称
            io_config: IO口配置
            raw_data: 原始数据

        Returns:
            处理后的值
        """
        # return process_device_io(device_type, io_port, io_config, raw_data)
        # 暂时返回原始数据，后续实现具体的IO处理逻辑
        return raw_data.get("val", raw_data.get("v"))

    def apply_ha_constants_to_mapping(self, mapping_config: dict) -> dict:
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

    def resolve_device_mapping(self, device: dict[str, Any]) -> dict[str, list[str]]:
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

        # 从raw_data获取设备配置并转换为HA格式
        try:
            from .device_specs import DEVICE_SPECS_DATA

            raw_config = DEVICE_SPECS_DATA.get(device_type, {})
            device_config = (
                self.convert_data_to_ha_mapping(raw_config) if raw_config else {}
            )
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
        self, ha_config: dict, device_data: dict
    ) -> dict[str, list[str]]:
        """
        从HA配置中提取平台到IO口的映射

        增强版本：支持bitmask多设备生成和多平台虚拟设备生成

        Args:
            ha_config: HA规范的设备配置
            device_data: 设备数据

        Returns:
            平台映射字典，包含bitmask扩展和多平台虚拟设备
        """
        platform_mapping = {}

        # 第一步：处理传统的单平台映射
        for platform, ios in ha_config.items():
            if platform == "name" or not isinstance(ios, dict):
                continue

            # 提取该平台的IO口列表
            io_ports = []
            for io_port, io_config in ios.items():
                if isinstance(io_config, dict):
                    io_ports.append(io_port)

                    # 检查是否需要bitmask扩展（仅对binary_sensor）
                    if platform == "binary_sensor" and io_port in device_data:
                        expanded_subdevices = self._expand_bitmask_for_io(
                            io_port, io_config, device_data.get(io_port, {})
                        )
                        io_ports.extend(expanded_subdevices)

            if io_ports:
                platform_mapping[platform] = io_ports

        # 第二步：处理多平台虚拟设备生成
        # 注意：多平台虚拟设备功能当前未实现，跳过此步骤
        # TODO: 实现多平台虚拟设备生成功能

        return platform_mapping

    def _expand_bitmask_for_io(
        self, io_port: str, io_config: dict, io_data: dict
    ) -> list[str]:
        """
        为单个IO口扩展ALM虚拟子设备

        使用新的ALM数据处理器架构，基于配置驱动的原则。

        Args:
            io_port: IO口名称
            io_config: IO口配置
            io_data: IO口数据

        Returns:
            虚拟子设备键列表
        """
        # 检查是否为ALM IO口
        if not is_alm_io_port(io_port):
            return []

        # 生成ALM虚拟子设备
        virtual_subdevices = get_alm_subdevices()

        return list(virtual_subdevices.keys())

    def _generate_multi_platform_virtual_devices(
        self, ha_config: dict, device_data: dict
    ) -> dict[str, list[str]]:
        """
        生成多平台虚拟设备

        Args:
            ha_config: HA规范的设备配置
            device_data: 设备数据

        Returns:
            按平台分组的虚拟设备键列表
        """
        multi_platform_devices = {}

        # 遍历所有平台和IO口，查找需要多平台处理的字段
        for platform, ios in ha_config.items():
            if platform == "name" or not isinstance(ios, dict):
                continue

            for io_port, io_config in ios.items():
                if not isinstance(io_config, dict) or io_port not in device_data:
                    continue

                # 查找适合的多平台处理器
                # 注意：多平台处理器当前未实现，返回空结果
                platform_devices = {}

                # 合并结果
                for target_platform, virtual_devices in platform_devices.items():
                    if target_platform not in multi_platform_devices:
                        multi_platform_devices[target_platform] = []

                    # 提取虚拟设备的键
                    device_keys = [device.key for device in virtual_devices]
                    multi_platform_devices[target_platform].extend(device_keys)

        return multi_platform_devices

    def _resolve_dynamic_classification(
        self, device_config: dict, device_data: dict
    ) -> dict[str, list[str]]:
        """解析动态分类设备"""
        dynamic_config = device_config["dynamic_classification"]
        classification_type = dynamic_config.get("type")

        if classification_type == "conditional":
            return self._resolve_conditional_classification(dynamic_config, device_data)
        elif classification_type == "bitwise":
            return self._resolve_bitwise_classification(dynamic_config, device_data)

        return {}

    def _resolve_conditional_classification(
        self, dynamic_config: dict, device_data: dict
    ) -> dict[str, list[str]]:
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
        self, dynamic_config: dict, device_data: dict
    ) -> dict[str, list[str]]:
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
        self, device_config: dict, device: dict
    ) -> dict[str, list[str]]:
        """解析版本化设备"""
        versioned_config = device_config["versioned"]

        # 处理不同的versioned配置格式
        if isinstance(versioned_config, bool):
            # 布尔值格式，使用version_modes
            if versioned_config and "version_modes" in device_config:
                # 修复: 对于LifeSmart设备，版本信息从fullCls字段提取
                versions = device_config["version_modes"]

                # 从fullCls字段提取版本信息
                device_version = self._extract_version_from_fullcls(device)

                # 如果没有提取到版本，尝试直接从version字段获取
                if not device_version:
                    device_version = device.get("version", "default")

            else:
                return {}
        elif isinstance(versioned_config, dict):
            # 字典格式，使用标准结构
            version_field = versioned_config.get("version_field", "version")
            versions = versioned_config.get("versions", {})

            # 对于LifeSmart设备，优先从fullCls字段提取版本
            if version_field == "version" and device.get("fullCls"):
                device_version = self._extract_version_from_fullcls(device)
            else:
                device_version = device.get(version_field, "default")
        else:
            return {}

        # 选择对应的版本配置
        selected_config = versions.get(str(device_version), versions.get("default", {}))
        return self._resolve_static_mapping(selected_config, device.get("data", {}))

    def _extract_version_from_fullcls(self, device: dict) -> str:
        """
        从fullCls字段中提取版本信息

        Args:
            device: 设备字典

        Returns:
            版本字符串，如"V1", "V2"等，未找到时返回空字符串
        """
        full_cls = device.get("fullCls", "")
        device_type = device.get("devtype", "")

        if not full_cls or not device_type:
            return ""

        # 提取版本号，例如：SL_SW_DM1_V1 -> V1
        if f"{device_type}_V1" in full_cls:
            return "V1"
        elif f"{device_type}_V2" in full_cls:
            return "V2"
        elif f"{device_type}_V3" in full_cls:
            return "V3"

        return ""

    def _resolve_static_mapping(
        self, device_config: dict, device_data: dict
    ) -> dict[str, list[str]]:
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
        安全评估表达式 - 增强版本，支持复杂位运算

        Args:
            expression: 表达式字符串，如 "(P1>>24)&0xe == 0", "P5&0xFF in [3,6]"
            variables: 变量字典，如 {"P1": 123456, "P5": 1}

        Returns:
            评估结果或None（如果出错）
        """
        try:
            # 使用设备分类器的安全评估器
            if self.device_classifier and hasattr(self.device_classifier, "evaluator"):
                return self.device_classifier.evaluator.evaluate(expression, variables)

            # 降级到简单评估（向后兼容）
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
        except (ValueError, IndexError, AttributeError, Exception) as e:
            import logging

            _LOGGER = logging.getLogger(__name__)
            _LOGGER.debug(f"Expression evaluation failed: {expression}, error: {e}")
            return None

    def get_bitmask_virtual_config(
        self, device_type: str, virtual_key: str
    ) -> dict[str, Any]:
        """
        获取ALM虚拟子设备的配置。

        使用新的ALM数据处理器架构，基于配置驱动的原则。

        Args:
            device_type: 设备类型
            virtual_key: 虚拟子设备键，如"ALM_bit0"

        Returns:
            虚拟子设备的配置字典
        """
        # 解析虚拟键格式: {IO口}_bit{位号}
        if "_bit" not in virtual_key:
            return {}

        source_io_port = virtual_key.split("_bit")[0]

        # 检查是否为ALM IO口
        if not is_alm_io_port(source_io_port):
            return {}

        # 获取ALM虚拟子设备配置
        virtual_subdevices = get_alm_subdevices()
        raw_config = virtual_subdevices.get(virtual_key, {})

        if raw_config:
            # 转换为HA规范的配置
            return self.convert_data_to_ha_mapping(raw_config)

        return {}

    def get_multi_platform_virtual_config(
        self, device_type: str, virtual_key: str
    ) -> dict[str, Any]:
        """
        获取多平台虚拟设备的配置。

        Args:
            device_type: 设备类型
            virtual_key: 虚拟设备键，如"EVTLO_lock_status", "P1_red_value"

        Returns:
            虚拟设备的配置字典
        """
        # 多平台虚拟设备功能当前未实现
        return {}

        from .device_specs import DEVICE_SPECS_DATA

        # 解析虚拟键格式: {IO口}_{virtual_suffix}
        if "_" not in virtual_key:
            return {}

        # 查找原始IO口：尝试不同的分割方式
        parts = virtual_key.split("_")
        source_io_port = None
        source_io_config = None

        # 尝试从短到长的组合
        for i in range(1, len(parts)):
            potential_io_port = "_".join(parts[:i])

            # 在device_specs中查找这个IO口
            device_specs = DEVICE_SPECS_DATA.get(device_type, {})

            # 在所有平台中查找原始IO口配置
            for platform_config in device_specs.values():
                if (
                    isinstance(platform_config, dict)
                    and potential_io_port in platform_config
                ):
                    source_io_port = potential_io_port
                    source_io_config = platform_config[potential_io_port]
                    break

            if source_io_config:
                break

        if not source_io_port or not source_io_config:
            return {}

        # 使用多平台处理器生成虚拟设备
        # 注意：多平台处理器当前未实现，返回空结果
        platform_devices = {}

        # 查找匹配的虚拟设备
        for virtual_devices in platform_devices.values():
            for virtual_device in virtual_devices:
                if virtual_device.key == virtual_key:
                    # 转换为HA规范的配置
                    config = {
                        "description": virtual_device.description,
                        "rw": "R",  # 虚拟设备默认只读
                        "data_type": self._infer_data_type_from_platform(
                            virtual_device.platform
                        ),
                        "conversion": virtual_device.extraction_logic or "val_direct",
                        "detailed_description": virtual_device.description,
                        "friendly_name": virtual_device.friendly_name,
                        # HA属性
                        "device_class_key": self._get_device_class_key(
                            virtual_device.device_class
                        ),
                        "unit_of_measurement": virtual_device.unit_of_measurement,
                        "state_class_key": self._get_state_class_key(
                            virtual_device.state_class
                        ),
                        # 虚拟设备元数据
                        "_is_virtual_device": True,
                        "_virtual_device_type": "multi_platform",
                        "_source_io_port": virtual_device.source_io_port,
                        "_extraction_logic": virtual_device.extraction_logic,
                        "_extraction_params": virtual_device.extraction_params,
                        "_platform": virtual_device.platform.value,
                        "_metadata": virtual_device.metadata,
                    }

                    # 转换HA常量
                    return self.convert_data_to_ha_mapping(config)

        return {}

    def _get_device_class_key(self, device_class) -> Optional[str]:
        """
        获取设备类别的字符串键

        Args:
            device_class: HA设备类别常量

        Returns:
            字符串键或None
        """
        if device_class is None:
            return None

        # 反向查找device_class的字符串键
        for key, value in self.ha_constants["device_class"].items():
            if value == device_class:
                return key

        return None

    def _get_state_class_key(self, state_class) -> Optional[str]:
        """
        获取状态类别的字符串键

        Args:
            state_class: HA状态类别常量

        Returns:
            字符串键或None
        """
        if state_class is None:
            return None

        # 反向查找state_class的字符串键
        for key, value in self.ha_constants["state_class"].items():
            if value == state_class:
                return key

        return None

    # 业务逻辑方法占位符
    def _parse_lock_event(self, data: dict) -> dict:
        """解析门锁事件"""
        return {}

    def _parse_door_sensor(self, data: dict) -> dict:
        """解析门窗传感器"""
        return {}

    def _parse_motion_sensor(self, data: dict) -> dict:
        """解析运动传感器"""
        return {}

    def _parse_defed_device(self, data: dict) -> dict:
        """解析云防设备"""
        return {}

    def _parse_water_sensor(self, data: dict) -> dict:
        """解析水浸传感器"""
        return {}

    def _parse_smoke_sensor(self, data: dict) -> dict:
        """解析烟雾传感器"""
        return {}

    def _parse_radar_sensor(self, data: dict) -> dict:
        """解析人体存在传感器"""
        return {}

    def _parse_climate_device(self, data: dict) -> dict:
        """解析温控设备"""
        return {}

    def _is_sensor_io_config(self, io_config: dict) -> bool:
        """
        判断一个IO配置是否是传感器配置

        传感器IO配置通常包含以下特征之一：
        - device_class: 传感器设备类别
        - unit_of_measurement: 测量单位
        - state_class: 状态类别（measurement, total_increasing等）
        - data_type: 数据类型为temperature、humidity等传感器类型

        Args:
            io_config: IO配置字典

        Returns:
            是否是传感器配置
        """
        if not isinstance(io_config, dict):
            return False

        # 检查是否有传感器特征
        sensor_features = ["device_class", "unit_of_measurement", "state_class"]

        # 如果有任何传感器特征，则认为是传感器
        if any(feature in io_config for feature in sensor_features):
            return True

        # 检查data_type是否是传感器类型
        data_type = io_config.get("data_type", "")
        sensor_data_types = [
            "temperature",
            "humidity",
            "pressure",
            "voltage",
            "current",
            "power",
            "energy",
            "sensor",  # 通用传感器类型
        ]

        if data_type in sensor_data_types:
            return True

        # 检查rw特征，只读的通常是传感器（但不绝对）
        rw = io_config.get("rw", "")
        if rw == "R" and data_type not in [
            "device_type",
            "config_bitmask",
            "hvac_mode",
            "fan_speed",
        ]:
            return True

        return False


# 创建全局引擎实例
mapping_engine = EnhancedMappingEngine()
