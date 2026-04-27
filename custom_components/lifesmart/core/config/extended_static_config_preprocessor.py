"""
StaticConfigPreprocessor扩展 - Gen2-only DEVICE_CENTRIC_CONFIG预处理器

核心功能:
- 仅接受显式 _generation=2 的DEVICE_CENTRIC_CONFIG设备规格
- 拒绝LifeSmart旧格式/混合格式设备输入
- 处理嵌入的climate_config/bitmask_config/cover_config/fan_config
- 统一输出格式确保StaticDeviceResolver兼容性
"""

import ast
import logging
import re
from typing import Dict, Any, List, Optional, Set

_LOGGER = logging.getLogger(__name__)

# Explicit non-production/test-only records embedded in device_specs.py.
# Keep this allowlist narrow: real uppercase production entries still flow into
# _validate_gen2_device_entry() and must declare _generation=2.
_EXPLICIT_TEST_ONLY_NON_DEVICE_ENTRIES = frozenset({"VIRTUAL_TEST"})


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

        # Preserve current Gen2 embedded platform-level metadata for runtime
        # entities that initialize from the resolved DeviceConfig.source_mapping.
        # This is not a fallback path: only explicit fields from the Gen2 device
        # spec are copied through the static resolver facade.
        for metadata_key in ("_generation", "climate_features", "climate_config"):
            if metadata_key in raw_config:
                static_config[metadata_key] = raw_config[metadata_key]

        if raw_config.get("versioned") or "version_modes" in raw_config:
            static_config["_version_configs"] = (
                self._process_version_modes_from_new_format(
                    raw_config.get("version_modes", {})
                )
            )

        if raw_config.get("dynamic"):
            static_config["_mode_configs"] = (
                self._process_dynamic_modes_from_new_format(raw_config)
            )

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
            "is_dynamic": bool(raw_config.get("dynamic")),
            "is_versioned": bool(
                raw_config.get("versioned") or raw_config.get("version_modes")
            ),
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

    def _process_version_modes_from_new_format(
        self, version_modes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process DEVICE_CENTRIC version_modes without base/default fallback."""
        processed_versions = {}
        if not isinstance(version_modes, dict):
            return processed_versions

        for version, version_config in version_modes.items():
            if not isinstance(version_config, dict):
                continue
            processed_versions[version] = {
                "name": version_config.get("name", str(version)),
                "platforms": self._process_platforms_from_new_format(version_config),
            }
        return processed_versions

    def _process_dynamic_modes_from_new_format(
        self, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process current dynamic mode records into strict static mode descriptors."""
        mode_configs = {}
        for mode_name in ["switch_mode", "climate_mode"]:
            if mode_name in raw_config:
                mode_config = raw_config[mode_name]
                mode_configs[mode_name] = {
                    "condition": self._extract_static_condition(mode_config),
                    "platforms": self._process_mode_platforms(mode_config),
                }
        if "control_modes" in raw_config:
            for mode_name, mode_config in raw_config["control_modes"].items():
                mode_configs[mode_name] = {
                    "condition": self._extract_static_condition(mode_config),
                    "platforms": self._process_mode_platforms(mode_config),
                }
        cover_features = raw_config.get("cover_features")
        if isinstance(cover_features, dict) and isinstance(
            cover_features.get("control_modes"), dict
        ):
            for mode_name, mode_config in cover_features["control_modes"].items():
                if not isinstance(mode_config, dict):
                    continue
                mode_configs[mode_name] = {
                    "condition": self._extract_static_condition(mode_config),
                    "platforms": self._process_mode_platforms(mode_config),
                }
        return mode_configs

    def _extract_static_condition(self, mode_config: Dict[str, Any]) -> Dict[str, Any]:
        condition_str = mode_config.get("condition", "")
        static_condition = {
            "type": "expression",
            "expression": condition_str,
            "evaluation_method": "bitwise_and" if "&" in condition_str else "equality",
        }
        self._populate_expression_descriptor(static_condition, condition_str)
        return static_condition

    @staticmethod
    def _parse_static_int(value: str) -> int:
        return int(str(value).strip(), 0)

    def _populate_expression_descriptor(
        self, static_condition: Dict[str, Any], condition_str: str
    ) -> None:
        """Convert known mode expressions into strict static descriptors."""
        normalized = re.sub(r"\s+", "", condition_str or "")
        # Examples:
        #   P5&0xFF==1
        #   (P1>>24)&0xe in [2,4]
        pattern = re.compile(
            r"^\(?(?P<field>P\d+)(?:>>(?P<shift>\d+))?\)?&(?P<mask>0x[0-9a-fA-F]+|\d+)"
            r"(?P<op>==|in)(?P<rhs>.+)$"
        )
        match = pattern.match(normalized)
        if not match:
            return

        static_condition["field"] = match.group("field")
        static_condition["mask"] = self._parse_static_int(match.group("mask"))
        static_condition["bitwise_and"] = static_condition["mask"]
        shift = match.group("shift")
        if shift is not None:
            static_condition["shift"] = int(shift)

        rhs = match.group("rhs")
        if match.group("op") == "==":
            static_condition["value"] = self._parse_static_int(rhs)
            return

        try:
            values = ast.literal_eval(rhs)
        except (SyntaxError, ValueError):
            return
        if isinstance(values, (list, tuple, set)):
            static_condition["values"] = [int(value) for value in values]

    def _process_mode_platforms(self, mode_config: Dict[str, Any]) -> Dict[str, Any]:
        platforms = {}
        for platform_type in [
            "switch",
            "sensor",
            "binary_sensor",
            "light",
            "cover",
            "climate",
            "camera",
            "fan",
        ]:
            if platform_type in mode_config:
                platforms[platform_type] = mode_config[platform_type]
        if "io" in mode_config:
            platforms["switch"] = {
                io_key: {
                    "description": f"开关控制 {io_key}",
                    "rw": "RW",
                    "data_type": "binary_switch",
                }
                for io_key in mode_config["io"]
            }
        if "sensor_io" in mode_config:
            platforms["sensor"] = {
                io_key: {
                    "description": f"传感器数据 {io_key}",
                    "rw": "R",
                    "data_type": "sensor",
                }
                for io_key in mode_config["sensor_io"]
            }
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


class ExtendedStaticConfigPreprocessor:
    """Gen2-only static config preprocessor for DEVICE_CENTRIC_CONFIG records."""

    def __init__(self, raw_device_data: Dict[str, Any]):
        """
        Initialize the strict Gen2 preprocessor.

        Args:
            raw_device_data: Raw device specs. Device records must be explicit
                Generation 2 records; explicitly non-device entries are ignored.
        """
        self.raw_data = raw_device_data
        self.static_configs = {}
        self.preprocessing_stats = {
            "total_devices": 0,
            "device_centric_devices": 0,
            "dynamic_devices": 0,
            "versioned_devices": 0,
            "ignored_non_device_entries": 0,
        }
        self.device_centric_processor = DeviceCentricConfigProcessor()

    def generate_static_configs(self) -> Dict[str, Any]:
        """Generate strict Gen2 static configs; reject legacy/mixed device input."""
        _LOGGER.info("开始生成Gen2-only静态配置")

        for device_type, raw_config in self.raw_data.items():
            if self._is_explicit_non_device_entry(device_type, raw_config):
                self.preprocessing_stats["ignored_non_device_entries"] += 1
                continue

            self._validate_gen2_device_entry(device_type, raw_config)
            static_config = self.device_centric_processor.process_device_centric_config(
                device_type, raw_config
            )
            self.static_configs[device_type] = static_config

            self.preprocessing_stats["total_devices"] += 1
            self.preprocessing_stats["device_centric_devices"] += 1
            if static_config.get("_features", {}).get("is_dynamic"):
                self.preprocessing_stats["dynamic_devices"] += 1
            if static_config.get("_features", {}).get("is_versioned"):
                self.preprocessing_stats["versioned_devices"] += 1

        self._validate_all_configs()
        self.preprocessing_stats.update(
            self.device_centric_processor.get_processing_stats()
        )
        _LOGGER.info("Gen2-only静态配置生成完成: %s", self.preprocessing_stats)
        return self.static_configs

    @staticmethod
    def _is_explicit_non_device_entry(device_type: str, raw_config: Any) -> bool:
        """Return True only for entries that are explicitly not device specs."""
        if not isinstance(device_type, str):
            return True
        if device_type in _EXPLICIT_TEST_ONLY_NON_DEVICE_ENTRIES:
            return True
        if device_type.startswith("_"):
            return True
        if not device_type.isupper():
            return True
        return False

    def _validate_gen2_device_entry(
        self, device_type: str, raw_config: Any
    ) -> Dict[str, Any]:
        if not isinstance(raw_config, dict):
            raise ValueError(
                f"{device_type}: Gen2 device config must be a dict; "
                f"got {type(raw_config).__name__}"
            )
        if raw_config.get("_generation") != 2:
            raise ValueError(
                f"{device_type}: legacy/non-Gen2 config rejected; "
                "explicit _generation=2 is required"
            )
        if not self.device_centric_processor.is_device_centric_format(raw_config):
            raise ValueError(
                f"{device_type}: legacy config shape rejected; "
                "DEVICE_CENTRIC_CONFIG Gen2 shape is required"
            )
        return raw_config

    def _validate_all_configs(self):
        """Validate all generated Gen2 configs fail-hard."""
        validation_errors = []

        for device_type, config in self.static_configs.items():
            required_fields = ["name", "_features", "platforms"]
            for field in required_fields:
                if field not in config:
                    validation_errors.append(f"{device_type}: 缺少必需字段 '{field}'")

            features = config.get("_features", {})
            if features.get("generation") != 2:
                validation_errors.append(
                    f"{device_type}: 非Gen2配置 generation={features.get('generation')}"
                )

            if features.get("has_climate_config") and "_climate_config" not in config:
                validation_errors.append(f"{device_type}: 缺少climate_config配置")

            if features.get("has_bitmask_config") and "_bitmask_config" not in config:
                validation_errors.append(f"{device_type}: 缺少bitmask_config配置")

        if validation_errors:
            raise ValueError(
                "Gen2 static config validation failed: "
                + "; ".join(validation_errors)
            )
        _LOGGER.info("所有Gen2配置验证通过")

    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """获取预处理统计信息"""
        return self.preprocessing_stats.copy()
