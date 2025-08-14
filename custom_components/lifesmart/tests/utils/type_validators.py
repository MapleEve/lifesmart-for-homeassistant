"""
类型验证工具。
提供运行时类型检查，确保强类型设备数据的完整性和正确性。

本文件是Phase 1增量基础设施建设的核心组件，基于ZEN专家指导设计。
扩展了DeviceSpecValidator，为强类型设备提供额外的验证功能。
"""

from typing import Any, Dict, List, Optional, Union, Type
from dataclasses import is_dataclass
import logging

from custom_components.lifesmart.core.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_CONFIG,
)
from .models import (
    IOConfig,
    TypedDevice,
    TypedSwitchDevice,
    TypedSensorDevice,
    TypedLightDevice,
)
from .constants import TEST_HUB_IDS
from custom_components.lifesmart.core.config.device_spec_registry import (
    DeviceSpecValidator,
    ValidationResult,
    get_device_spec_registry,
)

_LOGGER = logging.getLogger(__name__)


class TypedDeviceValidationError(Exception):
    """强类型设备验证异常"""

    def __init__(self, message: str, device_type: str = None, field: str = None):
        super().__init__(message)
        self.device_type = device_type
        self.field = field


class IOConfigValidator:
    """IO配置验证器"""

    # 有效的CMD_TYPE常量
    VALID_CMD_TYPES = {
        CMD_TYPE_ON,
        CMD_TYPE_OFF,
        CMD_TYPE_SET_CONFIG,
    }

    @classmethod
    def validate_io_config(
        cls, io_config: IOConfig, port_name: str = None
    ) -> ValidationResult:
        """
        验证IO配置的完整性和正确性。

        Args:
            io_config: IO配置实例
            port_name: 端口名称（用于错误消息）

        Returns:
            验证结果
        """
        errors = []
        warnings = []

        # 检查是否是IOConfig实例
        if not isinstance(io_config, IOConfig):
            errors.append(
                f"{port_name}: Expected IOConfig instance, got {type(io_config)}"
            )
            return ValidationResult(False, errors, warnings)

        # 验证type字段
        if io_config.type is not None:
            if isinstance(io_config.type, int):
                # 检查是否是有效的CMD_TYPE常量
                if io_config.type not in cls.VALID_CMD_TYPES:
                    warnings.append(
                        f"{port_name}: type={io_config.type} is not a recognized CMD_TYPE constant"
                    )
            elif isinstance(io_config.type, str):
                # 字符串类型的type字段（某些设备可能使用）
                if not io_config.type:
                    warnings.append(f"{port_name}: Empty string type field")
            else:
                errors.append(
                    f"{port_name}: Invalid type field type, expected int or str, got {type(io_config.type)}"
                )

        # 验证val字段（必需字段）
        if io_config.val is None:
            warnings.append(f"{port_name}: val field is None, this may cause issues")

        # 验证v字段（如果存在）
        if io_config.v is not None:
            if isinstance(io_config.val, (int, float)) and isinstance(
                io_config.v, (int, float)
            ):
                # 检查v和val的关系（对于温度等传感器数据）
                if abs(io_config.v * 10 - io_config.val) > 1:  # 允许1的误差
                    warnings.append(
                        f"{port_name}: v={io_config.v} and val={io_config.val} relationship seems inconsistent"
                    )

        # 验证name字段
        if io_config.name is not None and not isinstance(io_config.name, str):
            errors.append(
                f"{port_name}: name field must be string, got {type(io_config.name)}"
            )

        return ValidationResult(len(errors) == 0, errors, warnings)


class TypedDeviceValidator:
    """强类型设备验证器"""

    def __init__(self):
        """初始化验证器"""
        self.device_spec_validator = DeviceSpecValidator()
        self.io_validator = IOConfigValidator()
        self.registry = get_device_spec_registry()

    def validate_typed_device(self, typed_device: TypedDevice) -> ValidationResult:
        """
        验证强类型设备的完整性。

        Args:
            typed_device: 强类型设备实例

        Returns:
            验证结果
        """
        errors = []
        warnings = []

        # 1. 基础类型检查
        if not isinstance(typed_device, TypedDevice):
            errors.append(f"Expected TypedDevice instance, got {type(typed_device)}")
            return ValidationResult(False, errors, warnings)

        # 2. 必需字段验证
        required_result = self._validate_required_fields(typed_device)
        errors.extend(required_result.errors)
        warnings.extend(required_result.warnings)

        # 3. Hub ID验证
        hub_result = self._validate_hub_id(typed_device)
        errors.extend(hub_result.errors)
        warnings.extend(hub_result.warnings)

        # 4. 设备类型验证
        devtype_result = self._validate_device_type(typed_device)
        errors.extend(devtype_result.errors)
        warnings.extend(devtype_result.warnings)

        # 5. IO配置验证
        io_result = self._validate_io_data(typed_device)
        errors.extend(io_result.errors)
        warnings.extend(io_result.warnings)

        # 6. 数据一致性验证
        consistency_result = self._validate_data_consistency(typed_device)
        errors.extend(consistency_result.errors)
        warnings.extend(consistency_result.warnings)

        # 7. 专用类型验证
        specialized_result = self._validate_specialized_device(typed_device)
        errors.extend(specialized_result.errors)
        warnings.extend(specialized_result.warnings)

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_required_fields(self, device: TypedDevice) -> ValidationResult:
        """验证必需字段"""
        errors = []
        warnings = []

        if not device.agt:
            errors.append("agt (Hub ID) is required and cannot be empty")

        if not device.me:
            errors.append("me (Device ID) is required and cannot be empty")

        if not device.devtype:
            errors.append("devtype (Device Type) is required and cannot be empty")

        if not device.name:
            errors.append("name (Device Name) is required and cannot be empty")

        # 检查stat字段
        if not isinstance(device.stat, int) or device.stat < 0:
            warnings.append("stat should be a non-negative integer")

        # 检查ver字段
        if device.ver and not isinstance(device.ver, str):
            errors.append("ver field must be a string")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_hub_id(self, device: TypedDevice) -> ValidationResult:
        """验证Hub ID格式"""
        errors = []
        warnings = []

        # 检查Hub ID是否在测试列表中（对于测试环境）
        if device.agt not in TEST_HUB_IDS:
            warnings.append(f"Hub ID '{device.agt}' not in standard test hub list")

        # 检查Hub ID格式（基本长度检查）
        if len(device.agt) < 10:
            warnings.append("Hub ID seems too short, may not be valid")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_device_type(self, device: TypedDevice) -> ValidationResult:
        """验证设备类型"""
        errors = []
        warnings = []

        # 检查设备类型是否在设备规格注册表中
        if self.registry.has_device_spec(device.devtype):
            # 获取设备规格
            spec = self.registry.get_device_spec(device.devtype)

            # 使用DeviceSpecValidator验证规格
            spec_result = self.device_spec_validator.validate_device_spec(
                device.devtype, spec
            )
            if spec_result.has_errors():
                warnings.append(
                    f"Device spec for {device.devtype} has validation issues: {spec_result.errors}"
                )
        else:
            warnings.append(
                f"Device type '{device.devtype}' not found in device spec registry"
            )

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_io_data(self, device: TypedDevice) -> ValidationResult:
        """验证IO数据配置"""
        errors = []
        warnings = []

        if not isinstance(device.data, dict):
            errors.append("data field must be a dictionary")
            return ValidationResult(False, errors, warnings)

        # 验证每个IO配置
        for port_name, io_config in device.data.items():
            io_result = self.io_validator.validate_io_config(io_config, port_name)
            errors.extend(io_result.errors)
            warnings.extend(io_result.warnings)

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_data_consistency(self, device: TypedDevice) -> ValidationResult:
        """验证数据一致性"""
        errors = []
        warnings = []

        # 检查转换为字典后的一致性
        try:
            dict_data = device.to_dict()

            # 验证关键字段保持一致
            if dict_data.get("agt") != device.agt:
                errors.append("agt field inconsistent after to_dict() conversion")

            if dict_data.get("me") != device.me:
                errors.append("me field inconsistent after to_dict() conversion")

            if dict_data.get("devtype") != device.devtype:
                errors.append("devtype field inconsistent after to_dict() conversion")

            # 验证IO数据转换
            dict_io_data = dict_data.get("data", {})
            if len(dict_io_data) != len(device.data):
                errors.append("IO data count inconsistent after to_dict() conversion")

        except Exception as e:
            errors.append(f"Failed to convert device to dict: {e}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_specialized_device(self, device: TypedDevice) -> ValidationResult:
        """验证专用设备类型"""
        errors = []
        warnings = []

        # 根据设备类型进行专门验证
        if isinstance(device, TypedSwitchDevice):
            switch_result = self._validate_switch_device(device)
            errors.extend(switch_result.errors)
            warnings.extend(switch_result.warnings)

        elif isinstance(device, TypedSensorDevice):
            sensor_result = self._validate_sensor_device(device)
            errors.extend(sensor_result.errors)
            warnings.extend(sensor_result.warnings)

        elif isinstance(device, TypedLightDevice):
            light_result = self._validate_light_device(device)
            errors.extend(light_result.errors)
            warnings.extend(light_result.warnings)

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_switch_device(self, device: TypedSwitchDevice) -> ValidationResult:
        """验证开关设备"""
        errors = []
        warnings = []

        # 检查开关端口
        switch_ports = device.get_switch_ports()
        if not switch_ports:
            warnings.append("Switch device has no switch ports")

        # 验证开关状态值
        for port_name, io_config in switch_ports.items():
            if io_config.val not in [0, 1]:
                warnings.append(
                    f"Switch port {port_name} has non-binary value: {io_config.val}"
                )

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_sensor_device(self, device: TypedSensorDevice) -> ValidationResult:
        """验证传感器设备"""
        errors = []
        warnings = []

        # 检查传感器端口
        sensor_ports = device.get_sensor_ports()
        if not sensor_ports:
            warnings.append("Sensor device has no sensor ports")

        # 验证传感器数据
        for port_name, io_config in sensor_ports.items():
            if port_name in ["T", "H"] and io_config.v is not None:
                # 温湿度传感器数据格式验证
                if not isinstance(io_config.v, (int, float)):
                    warnings.append(
                        f"Temperature/Humidity port {port_name} v field should be numeric"
                    )

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_light_device(self, device: TypedLightDevice) -> ValidationResult:
        """验证灯光设备"""
        errors = []
        warnings = []

        # 检查颜色端口
        color_ports = device.get_color_ports()
        brightness_ports = device.get_brightness_ports()

        if not color_ports and not brightness_ports:
            warnings.append("Light device has no color or brightness control ports")

        # 验证RGB值
        for port_name, io_config in color_ports.items():
            if "RGB" in port_name and io_config.val is not None:
                if (
                    not isinstance(io_config.val, int)
                    or io_config.val < 0
                    or io_config.val > 0xFFFFFF
                ):
                    warnings.append(
                        f"RGB port {port_name} value out of valid range: {io_config.val}"
                    )

        return ValidationResult(len(errors) == 0, errors, warnings)


class CompatibilityValidator:
    """兼容性验证器，确保强类型设备与现有系统兼容"""

    def __init__(self):
        self.typed_validator = TypedDeviceValidator()

    def validate_dict_conversion(self, typed_device: TypedDevice) -> ValidationResult:
        """
        验证强类型设备与字典的双向转换。

        Args:
            typed_device: 强类型设备实例

        Returns:
            验证结果
        """
        errors = []
        warnings = []

        try:
            # 转换为字典
            dict_device = typed_device.to_dict()

            # 验证字典结构
            if not self._validate_dict_structure(dict_device):
                errors.append("Converted dictionary has invalid structure")

            # 尝试从字典重建（如果有工厂函数）
            from .typed_factories import create_typed_device_from_dict

            reconstructed_device = create_typed_device_from_dict(dict_device)

            # 验证重建的设备
            reconstruction_result = self.typed_validator.validate_typed_device(
                reconstructed_device
            )
            if reconstruction_result.has_errors():
                errors.extend(
                    [
                        f"Reconstructed device error: {e}"
                        for e in reconstruction_result.errors
                    ]
                )

            # 验证关键字段一致性
            if reconstructed_device.agt != typed_device.agt:
                errors.append("agt field inconsistent after round-trip conversion")
            if reconstructed_device.devtype != typed_device.devtype:
                errors.append("devtype field inconsistent after round-trip conversion")

        except Exception as e:
            errors.append(f"Dictionary conversion failed: {e}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_dict_structure(self, device_dict: dict) -> bool:
        """验证字典设备结构"""
        required_fields = ["agt", "me", "devtype", "name", "data"]
        return all(field in device_dict for field in required_fields)

    def validate_factory_compatibility(self, device_type: str) -> ValidationResult:
        """
        验证工厂函数兼容性。

        Args:
            device_type: 设备类型

        Returns:
            验证结果
        """
        errors = []
        warnings = []

        try:
            from .typed_factories import create_typed_core_devices
            from .factories import validate_device_data

            # 获取所有核心设备
            typed_devices = create_typed_core_devices()

            # 找到指定设备类型的设备
            target_device = None
            for device in typed_devices:
                if device.devtype == device_type:
                    target_device = device
                    break

            if target_device is None:
                warnings.append(
                    f"Device type {device_type} not found in typed factories"
                )
                return ValidationResult(True, errors, warnings)

            # 转换为字典并验证与现有工厂的兼容性
            dict_device = target_device.to_dict()

            # 使用现有的验证函数
            is_valid = validate_device_data(dict_device)
            if not is_valid:
                errors.append(f"Device {device_type} fails existing factory validation")

        except ImportError:
            warnings.append(
                "Cannot import required factory modules for compatibility test"
            )
        except Exception as e:
            errors.append(f"Factory compatibility validation failed: {e}")

        return ValidationResult(len(errors) == 0, errors, warnings)


# ============================================================================
# === 便捷验证函数 ===
# ============================================================================


def validate_typed_device(typed_device: TypedDevice) -> ValidationResult:
    """
    便捷函数：验证强类型设备。

    Args:
        typed_device: 强类型设备实例

    Returns:
        验证结果
    """
    validator = TypedDeviceValidator()
    return validator.validate_typed_device(typed_device)


def validate_device_compatibility(typed_device: TypedDevice) -> ValidationResult:
    """
    便捷函数：验证设备兼容性。

    Args:
        typed_device: 强类型设备实例

    Returns:
        验证结果
    """
    validator = CompatibilityValidator()
    return validator.validate_dict_conversion(typed_device)


def is_valid_typed_device(typed_device: TypedDevice) -> bool:
    """
    便捷函数：检查强类型设备是否有效。

    Args:
        typed_device: 强类型设备实例

    Returns:
        是否有效
    """
    result = validate_typed_device(typed_device)
    return result.is_valid


def get_validation_errors(typed_device: TypedDevice) -> List[str]:
    """
    便捷函数：获取验证错误列表。

    Args:
        typed_device: 强类型设备实例

    Returns:
        错误列表
    """
    result = validate_typed_device(typed_device)
    return result.errors


def get_validation_warnings(typed_device: TypedDevice) -> List[str]:
    """
    便捷函数：获取验证警告列表。

    Args:
        typed_device: 强类型设备实例

    Returns:
        警告列表
    """
    result = validate_typed_device(typed_device)
    return result.warnings


# ============================================================================
# === 批量验证工具 ===
# ============================================================================


def validate_typed_device_list(
    devices: List[TypedDevice],
) -> Dict[str, ValidationResult]:
    """
    批量验证强类型设备列表。

    Args:
        devices: 强类型设备列表

    Returns:
        验证结果字典，键为设备标识
    """
    validator = TypedDeviceValidator()
    results = {}

    for device in devices:
        device_key = f"{device.devtype}_{device.me}"
        results[device_key] = validator.validate_typed_device(device)

    return results


def get_validation_summary(devices: List[TypedDevice]) -> Dict[str, Any]:
    """
    获取验证摘要信息。

    Args:
        devices: 强类型设备列表

    Returns:
        验证摘要字典
    """
    results = validate_typed_device_list(devices)

    total_devices = len(devices)
    valid_devices = sum(1 for result in results.values() if result.is_valid)
    total_errors = sum(len(result.errors) for result in results.values())
    total_warnings = sum(len(result.warnings) for result in results.values())

    return {
        "total_devices": total_devices,
        "valid_devices": valid_devices,
        "invalid_devices": total_devices - valid_devices,
        "success_rate": valid_devices / total_devices if total_devices > 0 else 0,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "details": results,
    }
