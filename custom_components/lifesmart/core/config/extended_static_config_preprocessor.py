"""
StaticConfigPreprocessor扩展 - 支持DEVICE_CENTRIC_CONFIG新格式
基于Phase 1.1分析，实现双格式兼容的配置预处理器扩展

核心功能:
- 检测并支持DEVICE_CENTRIC_CONFIG格式
- 保持与legacy格式100%兼容
- 处理嵌入的climate_config/bitmask_config/cover_config/fan_config
- 统一输出格式确保StaticDeviceResolver兼容性
"""

import logging
from typing import Dict, Any, List, Optional, Set

_LOGGER = logging.getLogger(__name__)


class DeviceCentricConfigProcessor:
    """DEVICE_CENTRIC_CONFIG格式处理器"""

    def __init__(self):
        """初始化处理器"""
        self.processing_stats = {
            "device_centric_configs": 0,
            "climate_configs": 0,
            "bitmask_configs": 0,
            "cover_configs": 0,
            "fan_configs": 0,
        }

    def is_device_centric_format(self, device_config: Dict[str, Any]) -> bool:
        """
        检测是否为DEVICE_CENTRIC_CONFIG格式

        Args:
            device_config: 设备配置

        Returns:
            是否为新格式
        """
        # 安全检查：确保device_config不为None且为字典类型
        if not device_config or not isinstance(device_config, dict):
            return False

        new_format_indicators = [
            "category",
            "climate_config",
            "bitmask_config",
            "cover_config",
            "fan_config",
            "_generation",
        ]
        return any(key in device_config for key in new_format_indicators)

    def process_device_centric_config(
        self, device_type: str, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理DEVICE_CENTRIC_CONFIG格式的设备配置

        Args:
            device_type: 设备类型
            raw_config: 原始配置

        Returns:
            处理后的静态配置
        """
        static_config = {
            "name": raw_config.get("name", device_type),
            "_features": self._extract_features_from_new_format(
                device_type, raw_config
            ),
            "platforms": self._process_platforms_from_new_format(raw_config),
        }

        # 处理特殊配置嵌入
        self._process_embedded_configs(device_type, raw_config, static_config)

        self.processing_stats["device_centric_configs"] += 1
        return static_config

    def _extract_features_from_new_format(
        self, device_type: str, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从DEVICE_CENTRIC_CONFIG格式提取设备特性

        Args:
            device_type: 设备类型
            raw_config: 原始配置

        Returns:
            设备特性字典
        """
        features = {
            "is_dynamic": False,  # 新格式都是静态配置
            "is_versioned": False,
            "category": raw_config.get("category"),
            "generation": raw_config.get("_generation", 2),  # 新格式标识
            "manufacturer": raw_config.get("manufacturer", "lifesmart"),
            "model": raw_config.get("model", device_type),
        }

        # 从capabilities字段提取能力
        if "capabilities" in raw_config:
            for capability in raw_config["capabilities"]:
                features[f"has_{capability}"] = True

        # 从嵌入配置提取特殊能力
        if "climate_config" in raw_config:
            features["has_climate_config"] = True
            climate_config = raw_config["climate_config"]

            if "hvac_modes" in climate_config:
                features["hvac_mode_count"] = len(
                    climate_config["hvac_modes"].get("modes", {})
                )
                features["hvac_io_field"] = climate_config["hvac_modes"].get("io_field")

            if "temperature" in climate_config:
                temp_config = climate_config["temperature"]
                features["temp_range"] = temp_config.get("range", [10, 35])
                features["temp_precision"] = temp_config.get("precision", 0.1)

            features["climate_template"] = climate_config.get("template", "standard")

        if "bitmask_config" in raw_config:
            features["has_bitmask_config"] = True
            # 统计bit数量和配置复杂度
            total_bits = 0
            io_fields = []
            for io_field, bitmask_config in raw_config["bitmask_config"].items():
                io_fields.append(io_field)
                if "bit_definitions" in bitmask_config:
                    total_bits += len(bitmask_config["bit_definitions"])
                elif "field_definitions" in bitmask_config:
                    total_bits += len(bitmask_config["field_definitions"])

            features["total_bitmask_bits"] = total_bits
            features["bitmask_io_fields"] = io_fields

        if "cover_config" in raw_config:
            features["has_cover_config"] = True
            cover_config = raw_config["cover_config"]
            features["has_positioning"] = cover_config.get("position_feedback", False)
            features["cover_device_class"] = cover_config.get("device_class", "curtain")
            features["cover_control_type"] = cover_config.get(
                "control_type", "optimistic"
            )

        if "fan_config" in raw_config:
            features["has_fan_config"] = True
            fan_config = raw_config["fan_config"]
            features["fan_speed_control"] = fan_config.get("speed_control", "discrete")
            features["supports_oscillation"] = fan_config.get(
                "supports_oscillation", False
            )
            features["fan_speed_count"] = len(fan_config.get("speed_modes", {}))

        return features

    def _process_platforms_from_new_format(
        self, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从新格式中处理平台配置

        Args:
            raw_config: 原始配置

        Returns:
            平台配置字典
        """
        platforms = {}

        if "platforms" in raw_config:
            for platform_type, platform_config in raw_config["platforms"].items():
                if "io_configs" in platform_config:
                    # 新格式: 直接使用io_configs
                    platforms[platform_type] = platform_config["io_configs"]
                else:
                    # 兼容格式: 直接使用platform_config
                    platforms[platform_type] = platform_config

        return platforms

    def _process_embedded_configs(
        self,
        device_type: str,
        raw_config: Dict[str, Any],
        static_config: Dict[str, Any],
    ):
        """
        处理嵌入的特殊配置 (climate_config, bitmask_config等)

        Args:
            device_type: 设备类型
            raw_config: 原始配置
            static_config: 静态配置（输出）
        """

        # Climate配置处理
        if "climate_config" in raw_config:
            static_config["_climate_config"] = self._process_climate_config(
                device_type, raw_config["climate_config"]
            )
            self.processing_stats["climate_configs"] += 1

        # Bitmask配置处理
        if "bitmask_config" in raw_config:
            static_config["_bitmask_config"] = self._process_bitmask_config(
                device_type, raw_config["bitmask_config"]
            )
            self.processing_stats["bitmask_configs"] += 1

        # Cover配置处理
        if "cover_config" in raw_config:
            static_config["_cover_config"] = self._process_cover_config(
                device_type, raw_config["cover_config"]
            )
            self.processing_stats["cover_configs"] += 1

        # Fan配置处理
        if "fan_config" in raw_config:
            static_config["_fan_config"] = self._process_fan_config(
                device_type, raw_config["fan_config"]
            )
            self.processing_stats["fan_configs"] += 1

    def _process_climate_config(
        self, device_type: str, climate_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理climate_config嵌入配置

        Args:
            device_type: 设备类型
            climate_config: climate配置

        Returns:
            处理后的climate配置
        """
        processed_config = {
            "template": climate_config.get("template", "standard_ac"),
            "capabilities": climate_config.get("capabilities", []),
        }

        # 处理HVAC模式映射
        if "hvac_modes" in climate_config:
            hvac_config = climate_config["hvac_modes"]
            processed_config["hvac_modes"] = {
                "io_field": hvac_config.get("io_field"),
                "modes": hvac_config.get("modes", {}),
                # 生成反向映射以支持set_hvac_mode
                "reverse_modes": {
                    v: k for k, v in hvac_config.get("modes", {}).items()
                },
            }

        # 处理温度配置
        if "temperature" in climate_config:
            temp_config = climate_config["temperature"]
            processed_config["temperature"] = {
                "target_io": temp_config.get("target_io"),
                "current_io": temp_config.get("current_io"),
                "range": temp_config.get("range", [10, 35]),
                "precision": temp_config.get("precision", 0.1),
                "conversion": temp_config.get("conversion", {"source": "v"}),
            }

        # 处理风扇模式配置
        if "fan_modes" in climate_config:
            fan_config = climate_config["fan_modes"]
            processed_config["fan_modes"] = {
                "io_field": fan_config.get("io_field"),
                "modes": fan_config.get("modes", {}),
                "reverse_modes": {v: k for k, v in fan_config.get("modes", {}).items()},
            }

        _LOGGER.debug(f"处理{device_type}的climate_config: {processed_config}")
        return processed_config

    def _process_bitmask_config(
        self, device_type: str, bitmask_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理bitmask_config嵌入配置

        Args:
            device_type: 设备类型
            bitmask_config: bitmask配置

        Returns:
            处理后的bitmask配置
        """
        processed_config = {}

        for io_field, field_config in bitmask_config.items():
            processed_field = {
                "type": field_config.get("type", "multi_bit_switch"),
                "virtual_device_template": field_config.get(
                    "virtual_device_template", f"{device_type}_{io_field}_{{name}}"
                ),
            }

            # 处理bit_definitions（SL_FCU类型）
            if "bit_definitions" in field_config:
                bit_defs = {}
                for bit_pos, bit_config in field_config["bit_definitions"].items():
                    bit_defs[int(bit_pos)] = {
                        "name": bit_config.get("name"),
                        "platform": bit_config.get("platform", "switch"),
                        "description": bit_config.get("description"),
                        "translation_key": bit_config.get("translation_key"),
                        "commands": bit_config.get("commands", {}),
                    }
                processed_field["bit_definitions"] = bit_defs

            # 处理field_definitions（SL_DN类型）
            if "field_definitions" in field_config:
                field_defs = {}
                for field_name, field_def in field_config["field_definitions"].items():
                    field_defs[field_name] = {
                        "platform": field_def.get("platform"),
                        "bit_range": field_def.get("bit_range"),
                        "transform": field_def.get("transform"),
                        "reverse_transform": field_def.get("reverse_transform"),
                        "options_mapping": field_def.get("options_mapping"),
                        "min_value": field_def.get("min_value"),
                        "max_value": field_def.get("max_value"),
                        "step": field_def.get("step"),
                        "commands": field_def.get("commands", {}),
                    }
                processed_field["field_definitions"] = field_defs

            # 处理secondary_platforms
            if "secondary_platforms" in field_config:
                processed_field["secondary_platforms"] = field_config[
                    "secondary_platforms"
                ]

            processed_config[io_field] = processed_field

        _LOGGER.debug(f"处理{device_type}的bitmask_config: {processed_config}")
        return processed_config

    def _process_cover_config(
        self, device_type: str, cover_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理cover_config嵌入配置

        Args:
            device_type: 设备类型
            cover_config: cover配置

        Returns:
            处理后的cover配置
        """
        processed_config = {
            "device_class": cover_config.get("device_class", "curtain"),
            "position_feedback": cover_config.get("position_feedback", False),
            "control_type": cover_config.get("control_type", "optimistic"),
            "capabilities": cover_config.get("capabilities", ["open", "close", "stop"]),
        }

        # 位置相关配置
        if processed_config["position_feedback"]:
            processed_config.update(
                {
                    "position_io": cover_config.get("position_io"),
                    "position_range": cover_config.get("position_range", [0, 100]),
                    "travel_time": cover_config.get("travel_time", 30),
                }
            )
        else:
            processed_config["travel_time"] = cover_config.get("travel_time", 30)

        # 命令配置
        if "commands" in cover_config:
            processed_config["commands"] = cover_config["commands"]

        _LOGGER.debug(f"处理{device_type}的cover_config: {processed_config}")
        return processed_config

    def _process_fan_config(
        self, device_type: str, fan_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理fan_config嵌入配置

        Args:
            device_type: 设备类型
            fan_config: fan配置

        Returns:
            处理后的fan配置
        """
        processed_config = {
            "speed_control": fan_config.get("speed_control", "discrete"),
            "supports_oscillation": fan_config.get("supports_oscillation", False),
            "capabilities": fan_config.get("capabilities", ["speed_control"]),
        }

        # 速度模式配置
        if "speed_modes" in fan_config:
            speed_modes = fan_config["speed_modes"]
            processed_config["speed_modes"] = speed_modes
            processed_config["reverse_speed_modes"] = {
                v: k for k, v in speed_modes.items()
            }

        # 预设模式配置
        if "preset_modes" in fan_config:
            processed_config["preset_modes"] = fan_config["preset_modes"]

        # 百分比控制配置
        if processed_config["speed_control"] == "percentage":
            processed_config["percentage_step"] = fan_config.get("percentage_step", 5)

        _LOGGER.debug(f"处理{device_type}的fan_config: {processed_config}")
        return processed_config

    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.processing_stats.copy()


# Legacy处理所需的常量数据（从StaticConfigPreprocessor迁移）
SPECIAL_DEVICE_FEATURES = {
    "SL_NATURE": {
        "default_mode": "switch_mode",
        "mode_switch_field": "P5",
        "temp_sensor_ios": ["P2", "P3"],
    },
    "SL_DOOYA": {
        "cover_type": "non_positional",
        "cover_operations": ["open", "close", "stop"],
        "control_ios": {"open": "P1", "close": "P2", "stop": "P3"},
    },
    "OD_WE_QUAN": {
        "light_type": "quantum",
        "effect_support": True,
        "effect_list": ["rainbow", "breath", "strobe"],
        "special_ios": ["_QUANTUM"],
    },
    "SL_LI_WW": {
        "light_type": "dimmer",
        "brightness_support": True,
        "dimmer_ios": ["_DIMMER"],
    },
    "SL_P": {
        "is_multi_mode": True,
        "default_mode": "free_mode",
        "mode_detection_field": "P1",
    },
    "SL_JEMA": {
        "is_multi_mode": True,
        "default_mode": "free_mode",
        "supports_curtain_mode": True,
    },
}

# 窗帘定位能力映射
COVER_POSITIONING_MAP = {
    "SL_SW_WIN": False,  # 无定位
    "SL_P_V2": False,  # 无定位
    "SL_CN_IF": False,  # 无定位
    "SL_DOOYA": True,  # 有定位
    "SL_CURTAIN": True,  # 有定位
}

# 版本化设备配置
VERSIONED_DEVICE_CONFIG = {
    "SL_LI_WW": {
        "V1": {"brightness_support": True},
        "V2": {"brightness_support": True, "color_temp_support": True},
    },
    "SL_OL": {
        "V1": {"power_monitoring": False},
        "V2": {"power_monitoring": True, "energy_tracking": True},
    },
}


class ExtendedStaticConfigPreprocessor:
    """
    扩展的静态配置预处理器 - 支持双格式（Legacy + DEVICE_CENTRIC_CONFIG）

    基于现有StaticConfigPreprocessor，添加对DEVICE_CENTRIC_CONFIG格式的支持
    """

    def __init__(self, raw_device_data: Dict[str, Any]):
        """
        初始化扩展预处理器

        Args:
            raw_device_data: 原始设备数据，支持混合格式
        """
        self.raw_data = raw_device_data
        self.static_configs = {}
        self.preprocessing_stats = {
            "total_devices": 0,
            "legacy_devices": 0,
            "device_centric_devices": 0,
            "dynamic_devices": 0,
            "versioned_devices": 0,
            "virtual_subdevices": 0,
            "special_devices": 0,
        }

        # 格式处理器
        self.device_centric_processor = DeviceCentricConfigProcessor()

        # Legacy处理所需的常量引用
        self._SPECIAL_DEVICE_FEATURES = SPECIAL_DEVICE_FEATURES
        self._COVER_POSITIONING_MAP = COVER_POSITIONING_MAP
        self._VERSIONED_DEVICE_CONFIG = VERSIONED_DEVICE_CONFIG

        # 检测配置格式
        self.config_format = self._detect_config_format()
        _LOGGER.info(f"检测到配置格式: {self.config_format}")

    def _detect_config_format(self) -> str:
        """
        检测配置格式类型

        Returns:
            "legacy" | "device_centric" | "mixed"
        """
        legacy_count = 0
        device_centric_count = 0

        for device_type, config in self.raw_data.items():
            if isinstance(config, dict):
                if self.device_centric_processor.is_device_centric_format(config):
                    device_centric_count += 1
                else:
                    legacy_count += 1

        if device_centric_count == 0:
            return "legacy"
        elif legacy_count == 0:
            return "device_centric"
        else:
            return "mixed"

    def generate_static_configs(self) -> Dict[str, Any]:
        """
        生成完整的静态配置（支持双格式）

        Returns:
            完整的静态设备配置字典
        """
        _LOGGER.info(f"开始生成静态配置... (格式: {self.config_format})")

        # 按格式分别处理设备
        for device_type, raw_config in self.raw_data.items():
            if self.device_centric_processor.is_device_centric_format(raw_config):
                # 新格式处理
                self.static_configs[device_type] = (
                    self.device_centric_processor.process_device_centric_config(
                        device_type, raw_config
                    )
                )
                self.preprocessing_stats["device_centric_devices"] += 1
            else:
                # Legacy格式处理 (导入原有StaticConfigPreprocessor逻辑)
                self.static_configs[device_type] = self._process_legacy_device(
                    device_type, raw_config
                )
                self.preprocessing_stats["legacy_devices"] += 1

            self.preprocessing_stats["total_devices"] += 1

        # 后续处理保持不变（原有逻辑）
        self._expand_versioned_devices()
        self._preprocess_special_devices()
        self._expand_virtual_subdevices()
        self._validate_all_configs()

        # 合并统计信息
        device_centric_stats = self.device_centric_processor.get_processing_stats()
        self.preprocessing_stats.update(device_centric_stats)

        _LOGGER.info(f"静态配置生成完成: {self.preprocessing_stats}")
        return self.static_configs

    def _process_legacy_device(
        self, device_type: str, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理Legacy格式设备配置（完整实现从StaticConfigPreprocessor迁移）

        Args:
            device_type: 设备类型
            raw_config: 原始配置

        Returns:
            处理后的静态配置
        """
        # 安全检查：确保raw_config不为None
        if not raw_config or not isinstance(raw_config, dict):
            return {
                "name": device_type,
                "_features": {"is_dynamic": False, "generation": 1},
                "platforms": {},
            }

        static_config = {
            "name": raw_config.get("name", device_type),
            "_features": self._extract_legacy_features(device_type, raw_config),
            "platforms": self._process_legacy_platforms(raw_config),
        }

        # 处理动态设备模式
        if raw_config.get("dynamic"):
            static_config["_mode_configs"] = self._process_legacy_dynamic_modes(
                raw_config
            )
            self.preprocessing_stats["dynamic_devices"] += 1

        return static_config

    def _extract_legacy_features(
        self, device_type: str, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取Legacy格式设备特性（完整实现）"""
        features = {
            "is_dynamic": bool(raw_config.get("dynamic")),
            "is_versioned": bool(raw_config.get("versioned")),
            "has_positioning": self._detect_positioning_capability(device_type),
            "has_dyn_color": self._detect_dynamic_color(raw_config),
            "cover_type": self._get_cover_type(device_type),
            "light_type": self._get_light_type(device_type),
            "virtual_subdevice_type": self._get_virtual_subdevice_type(raw_config),
            "generation": 1,  # Legacy格式标识
        }

        # 从特殊设备特性库添加
        if device_type in self._SPECIAL_DEVICE_FEATURES:
            features.update(self._SPECIAL_DEVICE_FEATURES[device_type])
            self.preprocessing_stats["special_devices"] += 1

        return features

    def _process_legacy_platforms(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """处理Legacy格式平台配置（简化版本）"""
        platforms = {}
        platform_types = [
            "switch",
            "sensor",
            "binary_sensor",
            "light",
            "cover",
            "climate",
            "camera",
        ]

        for platform_type in platform_types:
            if platform_type in raw_config:
                platforms[platform_type] = raw_config[platform_type]

        return platforms

    def _process_legacy_dynamic_modes(
        self, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理Legacy格式动态模式（完整实现）"""
        mode_configs = {}

        # SL_NATURE风格：从顶层直接获取
        for mode_name in ["switch_mode", "climate_mode"]:
            if mode_name in raw_config:
                mode_config = raw_config[mode_name]

                # 转换动态条件为静态条件
                condition = self._extract_static_condition(mode_name, mode_config)
                platforms = self._process_mode_platforms(mode_config)

                mode_configs[mode_name] = {
                    "condition": condition,
                    "platforms": platforms,
                }

        # SL_P风格：从control_modes中获取
        if "control_modes" in raw_config:
            control_modes = raw_config["control_modes"]
            for mode_name, mode_config in control_modes.items():
                condition = self._extract_static_condition(mode_name, mode_config)
                platforms = self._process_mode_platforms(mode_config)

                mode_configs[mode_name] = {
                    "condition": condition,
                    "platforms": platforms,
                }

        return mode_configs

    def _expand_versioned_devices(self):
        """生成版本化设备的独立配置"""
        for device_type, base_config in list(self.static_configs.items()):
            if base_config.get("_features", {}).get("is_versioned"):
                # 获取版本配置
                version_configs = self._VERSIONED_DEVICE_CONFIG.get(device_type, {})

                for version, version_specific in version_configs.items():
                    versioned_device_type = f"{device_type}_{version}"
                    versioned_config = self._create_version_config(
                        base_config, version_specific
                    )
                    self.static_configs[versioned_device_type] = versioned_config
                    self.preprocessing_stats["versioned_devices"] += 1

    def _preprocess_special_devices(self):
        """预处理特殊设备能力"""
        for device_type, config in self.static_configs.items():
            # 应用特殊设备特性
            if device_type in self._SPECIAL_DEVICE_FEATURES:
                special_features = self._SPECIAL_DEVICE_FEATURES[device_type]

                # 合并特殊特性到_features中
                if "_features" not in config:
                    config["_features"] = {}

                config["_features"].update(special_features)

                # 标记为特殊设备
                config["_features"]["is_special"] = True

    def _expand_virtual_subdevices(self):
        """生成虚拟子设备配置"""
        for device_type, config in list(self.static_configs.items()):
            virtual_type = config.get("_features", {}).get("virtual_subdevice_type")

            if virtual_type == "bitmask":
                # 生成bitmask虚拟子设备
                self._generate_bitmask_subdevices(device_type, config)

    def _validate_all_configs(self):
        """验证所有配置的完整性"""
        validation_errors = []

        for device_type, config in self.static_configs.items():
            # 基本结构验证
            required_fields = ["name", "_features", "platforms"]
            for field in required_fields:
                if field not in config:
                    validation_errors.append(f"{device_type}: 缺少必需字段 '{field}'")

            # 新格式特殊配置验证
            features = config.get("_features", {})
            if features.get("generation") == 2:  # 新格式
                # 验证嵌入配置的完整性
                if (
                    features.get("has_climate_config")
                    and "_climate_config" not in config
                ):
                    validation_errors.append(f"{device_type}: 缺少climate_config配置")

                if (
                    features.get("has_bitmask_config")
                    and "_bitmask_config" not in config
                ):
                    validation_errors.append(f"{device_type}: 缺少bitmask_config配置")

        if validation_errors:
            _LOGGER.warning(f"配置验证发现问题: {validation_errors}")
        else:
            _LOGGER.info("所有配置验证通过")

    # ==================== Legacy处理方法（从StaticConfigPreprocessor迁移） ====================

    def _detect_positioning_capability(self, device_type: str) -> bool:
        """检测设备定位能力"""
        return self._COVER_POSITIONING_MAP.get(device_type, False)

    def _detect_dynamic_color(self, raw_config: Dict[str, Any]) -> bool:
        """检测动态颜色支持"""
        # 检查是否有颜色相关的IO端口
        for platform_config in raw_config.values():
            if isinstance(platform_config, dict):
                for io_config in platform_config.values():
                    if isinstance(io_config, dict):
                        if "color" in io_config.get("description", "").lower():
                            return True
                        if io_config.get("data_type") in ["color", "rgb", "hsv"]:
                            return True
        return False

    def _get_cover_type(self, device_type: str) -> Optional[str]:
        """获取窗帘类型"""
        if device_type in self._COVER_POSITIONING_MAP:
            return (
                "positional"
                if self._COVER_POSITIONING_MAP[device_type]
                else "non_positional"
            )
        return None

    def _get_light_type(self, device_type: str) -> Optional[str]:
        """获取灯光类型"""
        # 从特殊设备特性中获取
        special_features = self._SPECIAL_DEVICE_FEATURES.get(device_type, {})
        return special_features.get("light_type")

    def _get_virtual_subdevice_type(self, raw_config: Dict[str, Any]) -> Optional[str]:
        """获取虚拟子设备类型"""
        # 检查是否有bitmask相关的IO
        for platform_config in raw_config.values():
            if isinstance(platform_config, dict):
                for io_key in platform_config.keys():
                    if "ALM" in io_key or "EVTLO" in io_key:
                        return "bitmask"
        return None

    def _extract_static_condition(
        self, mode_name: str, mode_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """转换动态条件为静态条件"""
        condition_str = mode_config.get("condition", "")

        # 解析条件字符串，转换为静态结构
        static_condition = {
            "type": "expression",
            "expression": condition_str,
            "evaluation_method": "bitwise_and" if "&" in condition_str else "equality",
        }

        # 提取字段名和值
        if "P5" in condition_str:
            static_condition["field"] = "P5"
            if "==" in condition_str:
                # P5&0xFF==1 类型
                value = condition_str.split("==")[-1].strip()
                static_condition["value"] = int(value) if value.isdigit() else value
            elif " in " in condition_str:
                # P5&0xFF in [3,6] 类型
                values_str = condition_str.split(" in ")[-1].strip()
                if values_str.startswith("[") and values_str.endswith("]"):
                    values_str = values_str[1:-1]
                    static_condition["values"] = [
                        int(v.strip()) for v in values_str.split(",")
                    ]

        return static_condition

    def _process_mode_platforms(self, mode_config: Dict[str, Any]) -> Dict[str, Any]:
        """处理模式平台配置"""
        platforms = {}

        # 支持的平台类型
        platform_types = [
            "switch",
            "sensor",
            "binary_sensor",
            "light",
            "cover",
            "climate",
            "camera",
            "fan",
        ]

        for platform_type in platform_types:
            if platform_type in mode_config:
                platforms[platform_type] = mode_config[platform_type]

        # 处理特殊的io字段
        if "io" in mode_config:
            # 将io字段转换为switch平台
            platforms["switch"] = {}
            for io_key in mode_config["io"]:
                platforms["switch"][io_key] = {
                    "description": f"开关控制 {io_key}",
                    "rw": "RW",
                    "data_type": "binary_switch",
                }

        if "sensor_io" in mode_config:
            # 将sensor_io字段转换为sensor平台
            platforms["sensor"] = {}
            for io_key in mode_config["sensor_io"]:
                platforms["sensor"][io_key] = {
                    "description": f"传感器数据 {io_key}",
                    "rw": "R",
                    "data_type": "sensor",
                }

        return platforms

    def _create_version_config(
        self, base_config: Dict[str, Any], version_specific: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建版本化配置"""
        import copy

        versioned_config = copy.deepcopy(base_config)

        # 合并版本特定特性
        if "_features" not in versioned_config:
            versioned_config["_features"] = {}

        versioned_config["_features"].update(version_specific)
        versioned_config["_features"]["is_versioned_instance"] = True

        return versioned_config

    def _generate_bitmask_subdevices(self, device_type: str, config: Dict[str, Any]):
        """生成bitmask虚拟子设备"""
        # 检查platforms中的bitmask相关IO
        platforms = config.get("platforms", {})

        for platform_name, platform_config in platforms.items():
            if isinstance(platform_config, dict):
                for io_key, io_config in platform_config.items():
                    if "ALM" in io_key:
                        # 生成ALM bitmask子设备
                        self._create_alm_subdevices(device_type, io_key, io_config)
                    elif "EVTLO" in io_key:
                        # 生成EVTLO bitmask子设备
                        self._create_evtlo_subdevices(device_type, io_key, io_config)

    def _create_alm_subdevices(
        self, device_type: str, io_key: str, io_config: Dict[str, Any]
    ):
        """创建ALM bitmask子设备"""
        # ALM位掩码定义（门锁报警位）
        alm_bits = {
            "bit0": "错误报警",
            "bit1": "劫持报警",
            "bit2": "防撬报警",
            "bit3": "低电报警",
            "bit4": "上锁报警",
            "bit5": "开锁报警",
            "bit6": "超时报警",
            "bit7": "异常报警",
            "bit8": "门磁报警",
            "bit9": "保留位",
        }

        for bit_name, bit_desc in alm_bits.items():
            subdevice_type = f"{device_type}_{io_key}_{bit_name}"
            subdevice_config = {
                "name": f"{device_type} {bit_desc}",
                "_features": {
                    "is_virtual_subdevice": True,
                    "parent_device": device_type,
                    "bitmask_type": "ALM",
                    "bit_position": int(bit_name.replace("bit", "")),
                    "generation": 1,
                },
                "platforms": {
                    "binary_sensor": {
                        io_key: {
                            "description": bit_desc,
                            "rw": "R",
                            "data_type": "binary",
                            "device_class": "problem",
                        }
                    }
                },
            }

            self.static_configs[subdevice_type] = subdevice_config
            self.preprocessing_stats["virtual_subdevices"] += 1

    def _create_evtlo_subdevices(
        self, device_type: str, io_key: str, io_config: Dict[str, Any]
    ):
        """创建EVTLO事件子设备"""
        # EVTLO多平台虚拟设备
        subdevice_type = f"{device_type}_{io_key}_event"
        subdevice_config = {
            "name": f"{device_type} 事件数据",
            "_features": {
                "is_virtual_subdevice": True,
                "parent_device": device_type,
                "bitmask_type": "EVTLO",
                "generation": 1,
            },
            "platforms": {
                "sensor": {
                    io_key: {
                        "description": "门锁事件数据",
                        "rw": "R",
                        "data_type": "event",
                        "device_class": "timestamp",
                    }
                },
                "binary_sensor": {
                    f"{io_key}_status": {
                        "description": "门锁状态",
                        "rw": "R",
                        "data_type": "binary",
                        "device_class": "lock",
                    }
                },
            },
        }

        self.static_configs[subdevice_type] = subdevice_config
        self.preprocessing_stats["virtual_subdevices"] += 1

    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """获取预处理统计信息"""
        return self.preprocessing_stats.copy()
