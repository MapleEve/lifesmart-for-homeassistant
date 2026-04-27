"""
静态配置验证器 - 确保配置完整性
由 @MapleEve 创建，基于Phase 5.5.7.3纯静态map架构设计

此模块验证静态配置的完整性和正确性，确保：
- 所有必需字段存在
- 特性标记逻辑一致性
- 平台配置有效性
- 动态设备模式配置完整
- IO口配置正确性
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

_LOGGER = logging.getLogger(__name__)


class ValidationResult:
    """验证结果类"""

    def __init__(
        self, valid: bool, errors: List[str], warnings: List[str], total_devices: int
    ):
        self.valid = valid
        self.errors = errors
        self.warnings = warnings
        self.total_devices = total_devices

    def __str__(self) -> str:
        if self.valid:
            return f"✅ 验证通过 ({self.total_devices} 个设备)"
        else:
            return f"❌ 验证失败: {len(self.errors)} 错误, {len(self.warnings)} 警告"


class StaticConfigValidator:
    """静态配置验证器 - 确保配置完整性"""

    def __init__(self):
        self.validation_rules = {
            "required_fields": ["name", "_features", "platforms"],
            "required_features": ["is_dynamic", "is_versioned", "has_positioning"],
            "valid_platforms": [
                "switch",
                "sensor",
                "binary_sensor",
                "light",
                "cover",
                "climate",
                "camera",
                "button",
                "number",
            ],
            "valid_data_types": [
                "binary_switch",
                "sensor",
                "temperature",
                "humidity",
                "energy",
                "power",
                "light",
                "cover",
                "indicator_light",
                "rgbw_light",
                "brightness_light",
                "dimmer_light",
                "quantum_light",
                "dual_rgbw_light",
                "spot_rgbw_light",
                "spot_rgb_light",
                "dynamic_effect",
                "infrared_light",
                "color_temperature",
                "single_io_rgbw_light",
                "binary_sensor",
                "button",
                "button_state",
                "battery",
                "battery_level",
                "aqi",
                "alarm_status",
                "door_lock",
                "lock_event",
                "recent_unlock",
                "operation_record",
                "doorbell_message",
                "hvac_mode",
                "fan_speed",
                "mode_config",
                "generic_value",
                "energy_consumption",
                "power_factor",
                "frequency",
                "current",
                "voltage",
                "pm25",
                "pm10",
                "co_concentration",
                "co2_concentration",
                "voc_concentration",
                "formaldehyde_concentration",
                "oxygen_concentration",
                "ammonia_concentration",
                "h2s_concentration",
                "tvoc_concentration",
                "noise_level",
                "smoke_concentration",
                "illuminance",
                "motion_status",
                "keypad_status",
                "tamper_status",
                "camera_status",
                "motion_detection",
                "garage_door_status",
                "garage_door_control",
                "alarm_playback",
                "volume_control",
                "valve_status",
                "config_bitmask",
                "cover_control",
                "position_status",
                "position_control",
                "generic",
                "power_threshold",
                "camera_stream",
                "charging_status",
                "indicator_brightness",
                "dimming_config",
                "dynamic_config",
                "device_type",
                "status_input",
                "control_config",
            ],
        }

    def validate_all_configs(self, static_configs: Dict[str, Any]) -> ValidationResult:
        """
        验证所有静态配置

        Args:
            static_configs: 静态配置字典

        Returns:
            验证结果
        """
        _LOGGER.info(f"开始验证 {len(static_configs)} 个设备配置...")

        all_errors = []
        all_warnings = []

        for device_type, config in static_configs.items():
            device_errors, device_warnings = self._validate_device_config(
                device_type, config
            )
            all_errors.extend(device_errors)
            all_warnings.extend(device_warnings)

        # 验证设备间的一致性
        consistency_errors, consistency_warnings = self._validate_config_consistency(
            static_configs
        )
        all_errors.extend(consistency_errors)
        all_warnings.extend(consistency_warnings)

        result = ValidationResult(
            valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            total_devices=len(static_configs),
        )

        if result.valid:
            _LOGGER.info(f"✅ 所有配置验证通过: {len(static_configs)} 个设备")
        else:
            _LOGGER.error(
                f"❌ 配置验证失败: {len(all_errors)} 错误, {len(all_warnings)} 警告"
            )

        return result

    def _validate_device_config(
        self, device_type: str, config: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """
        验证单个设备配置

        Args:
            device_type: 设备类型
            config: 设备配置

        Returns:
            (错误列表, 警告列表)
        """
        errors = []
        warnings = []

        # 基础结构验证
        self._validate_basic_structure(device_type, config, errors, warnings)

        # 特性标记验证
        features = config.get("_features", {})
        self._validate_features(device_type, features, errors, warnings)

        # 平台配置验证
        platforms = config.get("platforms", {})
        self._validate_platforms(device_type, platforms, errors, warnings)

        # 动态设备验证
        if features.get("is_dynamic"):
            mode_configs = config.get("_mode_configs", {})
            self._validate_mode_configs(device_type, mode_configs, errors, warnings)

        # 版本化设备验证
        if features.get("is_versioned"):
            self._validate_versioned_device(device_type, config, errors, warnings)

        # 虚拟子设备验证
        if features.get("virtual_subdevice_type"):
            self._validate_virtual_subdevices(device_type, config, errors, warnings)

        return errors, warnings

    def _validate_basic_structure(
        self,
        device_type: str,
        config: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ):
        """验证基础结构"""
        for field in self.validation_rules["required_fields"]:
            if field not in config:
                errors.append(f"{device_type}: 缺少必需字段 '{field}'")

        # 验证名称
        if "name" in config and not isinstance(config["name"], str):
            errors.append(f"{device_type}: name 必须是字符串")

        if "name" in config and not config["name"].strip():
            warnings.append(f"{device_type}: name 为空")

    def _validate_features(
        self,
        device_type: str,
        features: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ):
        """验证特性标记"""
        # 检查必需的特性标记
        for feature in self.validation_rules["required_features"]:
            if feature not in features:
                warnings.append(f"{device_type}: 缺少特性标记 '{feature}'")

        # 逻辑一致性检查
        if features.get("is_dynamic") and not features.get("default_mode"):
            warnings.append(f"{device_type}: 动态设备建议设置 default_mode")

        if features.get("is_versioned") and not features.get("version"):
            warnings.append(f"{device_type}: 版本化设备应该包含 version 信息")

        # 窗帘设备特殊验证
        if features.get("cover_type"):
            valid_cover_types = ["positional", "non_positional"]
            if features["cover_type"] not in valid_cover_types:
                errors.append(
                    f"{device_type}: 无效的 cover_type '{features['cover_type']}'"
                )

        # 灯光设备特殊验证
        if features.get("light_type"):
            valid_light_types = ["dimmer", "quantum", "color", "color_temp", "rgbw"]
            if features["light_type"] not in valid_light_types:
                errors.append(
                    f"{device_type}: 无效的 light_type '{features['light_type']}'"
                )

    def _validate_platforms(
        self,
        device_type: str,
        platforms: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ):
        """验证平台配置"""
        valid_platforms = self.validation_rules["valid_platforms"]

        # 检查平台类型有效性
        for platform in platforms:
            if platform not in valid_platforms:
                warnings.append(f"{device_type}: 未知平台类型 '{platform}'")

        # 检查是否有任何平台配置
        if not platforms:
            warnings.append(f"{device_type}: 没有平台配置")

        # 验证每个平台的IO口配置
        for platform, platform_config in platforms.items():
            if not isinstance(platform_config, dict):
                errors.append(f"{device_type}.{platform}: 平台配置必须是字典")
                continue

            self._validate_platform_ios(
                device_type, platform, platform_config, errors, warnings
            )

    def _validate_platform_ios(
        self,
        device_type: str,
        platform: str,
        platform_config: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ):
        """验证平台IO口配置"""
        for io_port, io_config in platform_config.items():
            if not isinstance(io_config, dict):
                errors.append(f"{device_type}.{platform}.{io_port}: IO配置必须是字典")
                continue

            # 验证基本IO字段
            if "description" not in io_config:
                warnings.append(f"{device_type}.{platform}.{io_port}: 缺少 description")

            # 验证数据类型
            data_type = io_config.get("data_type")
            if data_type and data_type not in self.validation_rules["valid_data_types"]:
                warnings.append(
                    f"{device_type}.{platform}.{io_port}: 未知数据类型 '{data_type}'"
                )

            # 验证读写模式
            rw = io_config.get("rw")
            if rw and rw not in ["R", "RW", "W"]:
                errors.append(
                    f"{device_type}.{platform}.{io_port}: 无效的 rw 值 '{rw}'"
                )

    def _validate_mode_configs(
        self,
        device_type: str,
        mode_configs: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ):
        """验证动态设备模式配置"""
        if not mode_configs:
            errors.append(f"{device_type}: 动态设备缺少模式配置")
            return

        valid_mode_names = [
            "switch_mode",
            "climate_mode",
            "cover_mode",
            "curtain_mode",
            "free_mode",
            "sensor_mode",
        ]

        for mode_name, mode_config in mode_configs.items():
            # 检查模式名称
            if mode_name not in valid_mode_names:
                warnings.append(f"{device_type}: 未知模式名称 '{mode_name}'")

            # 验证模式配置结构
            if not isinstance(mode_config, dict):
                errors.append(f"{device_type}.{mode_name}: 模式配置必须是字典")
                continue

            # 验证条件配置
            condition = mode_config.get("condition", {})
            if not isinstance(condition, dict):
                errors.append(f"{device_type}.{mode_name}: condition 必须是字典")

            # 验证平台配置
            platforms = mode_config.get("platforms", {})
            if not isinstance(platforms, dict):
                errors.append(f"{device_type}.{mode_name}: platforms 必须是字典")
            elif not platforms:
                warnings.append(f"{device_type}.{mode_name}: 模式没有平台配置")

    def _validate_versioned_device(
        self,
        device_type: str,
        config: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ):
        """验证版本化设备"""
        features = config.get("_features", {})

        # 检查版本信息
        if "version" not in features:
            warnings.append(f"{device_type}: 版本化设备应该包含版本信息")

        # 检查是否是明确的版本化设备名称
        if not any(v in device_type for v in ["_V1", "_V2", "_V3"]):
            warnings.append(f"{device_type}: 版本化设备建议在名称中包含版本号")

    def _validate_virtual_subdevices(
        self,
        device_type: str,
        config: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ):
        """验证虚拟子设备配置"""
        features = config.get("_features", {})
        virtual_type = features.get("virtual_subdevice_type")

        if virtual_type == "bitmask":
            platforms = config.get("platforms", {})
            binary_sensor_config = platforms.get("binary_sensor", {})

            # 检查是否有位掩码IO口
            has_bitmask_ios = any(
                io_port.endswith(f"_bit{i}")
                for io_port in binary_sensor_config.keys()
                for i in range(10)
            )

            if not has_bitmask_ios:
                warnings.append(f"{device_type}: 标记为 bitmask 类型但缺少虚拟子设备")

    def _validate_config_consistency(
        self, static_configs: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """验证配置间的一致性"""
        errors = []
        warnings = []

        # 统计信息
        stats = {
            "dynamic_devices": 0,
            "versioned_devices": 0,
            "cover_devices": 0,
            "light_devices": 0,
        }

        # 收集统计信息
        for device_type, config in static_configs.items():
            features = config.get("_features", {})

            if features.get("is_dynamic"):
                stats["dynamic_devices"] += 1

            if features.get("is_versioned"):
                stats["versioned_devices"] += 1

            if features.get("cover_type"):
                stats["cover_devices"] += 1

            if features.get("light_type"):
                stats["light_devices"] += 1

        # 验证一致性
        if stats["dynamic_devices"] == 0:
            warnings.append("没有发现动态设备配置")

        if stats["versioned_devices"] == 0:
            warnings.append("没有发现版本化设备配置")

        _LOGGER.info(f"配置统计: {stats}")

        return errors, warnings

    def validate_device_resolution(
        self, device_data: Dict[str, Any], static_config: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        验证设备数据与静态配置的匹配性

        Args:
            device_data: 实际设备数据
            static_config: 静态配置

        Returns:
            (是否匹配, 错误列表)
        """
        errors = []

        # 验证平台覆盖
        platforms = static_config.get("platforms", {})
        for platform_type, platform_config in platforms.items():
            for io_port in platform_config.keys():
                if io_port not in device_data:
                    errors.append(f"配置中的IO口 {io_port} 在设备数据中不存在")

        # 验证动态设备模式条件
        features = static_config.get("_features", {})
        if features.get("is_dynamic"):
            mode_configs = static_config.get("_mode_configs", {})
            matched_modes = []

            for mode_name, mode_config in mode_configs.items():
                condition = mode_config.get("condition", {})
                if self._check_mode_condition(condition, device_data):
                    matched_modes.append(mode_name)

            if not matched_modes:
                errors.append("设备数据不匹配任何动态模式条件")
            elif len(matched_modes) > 1:
                errors.append(f"设备数据匹配多个模式: {matched_modes}")

        return len(errors) == 0, errors

    def _check_mode_condition(
        self, condition: Dict[str, Any], device_data: Dict[str, Any]
    ) -> bool:
        """检查模式条件是否匹配"""
        if not condition:
            return True

        for field, expected_values in condition.items():
            io_data = device_data.get(field, {})
            actual_value = io_data.get("val")

            if actual_value not in expected_values:
                return False

        return True

    def generate_validation_report(self, result: ValidationResult) -> str:
        """
        生成验证报告

        Args:
            result: 验证结果

        Returns:
            格式化的验证报告
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("静态配置验证报告")
        report_lines.append("=" * 60)

        if result.valid:
            report_lines.append("✅ 验证状态: 通过")
        else:
            report_lines.append("❌ 验证状态: 失败")

        report_lines.append(f"📊 设备总数: {result.total_devices}")
        report_lines.append(f"🔥 错误数量: {len(result.errors)}")
        report_lines.append(f"⚠️  警告数量: {len(result.warnings)}")

        if result.errors:
            report_lines.append("\n🔥 错误详情:")
            for error in result.errors:
                report_lines.append(f"  - {error}")

        if result.warnings:
            report_lines.append("\n⚠️  警告详情:")
            for warning in result.warnings:
                report_lines.append(f"  - {warning}")

        if result.valid:
            report_lines.append("\n🎉 所有配置已准备就绪，可以投入生产使用！")
        else:
            report_lines.append("\n🛠️  请修复上述问题后重新验证。")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)
