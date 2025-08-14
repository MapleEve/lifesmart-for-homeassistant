"""
DeviceSpecRegistry - 设备规格统一存储注册表

这是架构分离Phase 1的核心组件，负责：
- 统一设备规格数据存储
- 提供标准化查询接口
- 实现数据验证机制
- 确保向后兼容性

由 @MapleEve 创建，基于架构分离实施计划
"""

from typing import Dict, Any, List, Optional, Set
import logging
from dataclasses import dataclass
from enum import Enum

# 导入特殊设备处理器
try:
    from .special_device_handler import (
        SpecialDeviceHandler,
        SpecialDeviceType,
        create_special_device_handler,
    )
except ImportError:
    # 如果无法导入，使用空实现作为回退
    SpecialDeviceHandler = None
    SpecialDeviceType = None
    create_special_device_handler = None


_LOGGER = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """数据验证级别"""

    STRICT = "strict"  # 严格验证，任何错误都拒绝
    LENIENT = "lenient"  # 宽松验证，记录警告但接受数据
    NONE = "none"  # 不验证，直接接受


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class DeviceSpecValidator:
    """设备规格数据验证器"""

    # 必需字段
    REQUIRED_FIELDS = {"name"}

    def __init__(self):
        """初始化验证器，包含特殊设备处理器"""
        # 初始化特殊设备处理器
        if SpecialDeviceHandler is not None:
            try:
                self.special_handler = create_special_device_handler()
                self._has_special_handler = True
            except Exception as e:
                _LOGGER.warning(f"Failed to create special device handler: {e}")
                self.special_handler = None
                self._has_special_handler = False
        else:
            self.special_handler = None
            self._has_special_handler = False

    # 有效的平台类型
    VALID_PLATFORMS = {
        "switch",
        "sensor",
        "binary_sensor",
        "light",
        "cover",
        "climate",
        "fan",
        "lock",
        "button",
        "valve",
        "air_quality",
    }

    # 有效的数据类型
    VALID_DATA_TYPES = {
        "binary_switch",
        "temperature",
        "humidity",
        "pressure",
        "voltage",
        "current",
        "power",
        "energy",
        "sensor",
        "hvac_mode",
        "fan_speed",
        "device_type",
        "config_bitmask",
        "generic",
    }

    # 有效的读写权限
    VALID_RW_PERMISSIONS = {"R", "W", "RW"}

    def validate_device_spec(
        self, device_type: str, spec: Dict[str, Any]
    ) -> ValidationResult:
        """验证完整设备规格"""
        errors = []
        warnings = []

        # 检查必需字段 - 使用特殊设备处理器进行智能验证
        for field in self.REQUIRED_FIELDS:
            if field not in spec:
                # 使用特殊设备处理器检查是否为特殊设备类型
                if self._has_special_handler and self.special_handler:
                    try:
                        # 使用特殊设备处理器进行设备分类
                        device_info = self.special_handler.classify_device(
                            device_type, spec
                        )

                        # 检查特殊设备类型（使用枚举成员直接对比，更安全）
                        if device_info.special_type == SpecialDeviceType.VERSIONED:
                            # 版本化设备
                            metadata = device_info.metadata
                            if metadata.get("resolved_name"):
                                # 版本化设备有有效的名称解析
                                continue
                            else:
                                errors.append(
                                    f"Versioned device '{device_type}' missing valid name in version modes"
                                )
                                continue

                        elif device_info.special_type == SpecialDeviceType.DYNAMIC:
                            # 动态分类设备可能没有统一的name，尝试解析
                            metadata = device_info.metadata
                            resolved_name = metadata.get("resolved_name")
                            if resolved_name:
                                warnings.append(
                                    f"Dynamic device '{device_type}' using resolved name: {resolved_name}"
                                )
                            else:
                                warnings.append(
                                    f"Dynamic device '{device_type}' has no unified name field - this is acceptable"
                                )
                            continue

                        elif device_info.special_type == SpecialDeviceType.CAM:
                            # CAM分类设备
                            metadata = device_info.metadata
                            resolved_name = metadata.get("resolved_name")
                            if resolved_name:
                                warnings.append(
                                    f"CAM device '{device_type}' using resolved name: {resolved_name}"
                                )
                            else:
                                warnings.append(
                                    f"CAM device '{device_type}' may have complex naming structure"
                                )
                            continue

                        elif device_info.special_type == SpecialDeviceType.DYN_COLOR:
                            # DYN Color处理设备
                            metadata = device_info.metadata
                            resolved_name = metadata.get("resolved_name")
                            if resolved_name:
                                warnings.append(
                                    f"DYN Color device '{device_type}' using resolved name: {resolved_name}"
                                )
                            else:
                                warnings.append(
                                    f"DYN Color device '{device_type}' may have complex color naming"
                                )
                            continue

                    except Exception as e:
                        _LOGGER.warning(
                            f"Special device handler failed for {device_type}: {e}"
                        )
                        # 回退到基础验证逻辑

                # 回退到基础验证逻辑（兼容没有特殊处理器的情况）
                if field == "name" and "versioned" in spec and "version_modes" in spec:
                    # 基础版本化设备检查
                    has_name_in_versions = any(
                        "name" in version_config
                        for version_config in spec["version_modes"].values()
                        if isinstance(version_config, dict)
                    )
                    if not has_name_in_versions:
                        errors.append(
                            f"Versioned device missing 'name' in version_modes"
                        )
                elif field == "name" and "dynamic" in spec:
                    # 基础动态分类设备检查
                    warnings.append(
                        f"Dynamic device '{device_type}' has no unified name field"
                    )
                else:
                    errors.append(f"Missing required field: {field}")

        # 验证基本结构
        if not isinstance(spec, dict):
            errors.append("Device spec must be a dictionary")
            return ValidationResult(False, errors, warnings)

        # 验证平台配置
        for platform_key, platform_config in spec.items():
            if platform_key == "name":
                continue

            # 检查是否是有效平台
            if (
                platform_key not in self.VALID_PLATFORMS
                and not platform_key.startswith("_")
            ):
                warnings.append(f"Unknown platform: {platform_key}")
                continue

            # 验证平台配置
            if isinstance(platform_config, dict):
                platform_result = self._validate_platform_config(
                    platform_key, platform_config
                )
                errors.extend(platform_result.errors)
                warnings.extend(platform_result.warnings)

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)

    def _validate_platform_config(
        self, platform: str, config: Dict[str, Any]
    ) -> ValidationResult:
        """验证平台配置"""
        errors = []
        warnings = []

        for io_port, io_config in config.items():
            if isinstance(io_config, dict):
                io_result = self.validate_io_config(platform, io_port, io_config)
                errors.extend(io_result.errors)
                warnings.extend(io_result.warnings)

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_io_config(
        self, platform: str, io_port: str, io_config: Dict[str, Any]
    ) -> ValidationResult:
        """验证IO口配置"""
        errors = []
        warnings = []

        # 检查必需的IO字段
        if "description" not in io_config:
            warnings.append(f"{platform}.{io_port}: Missing description")

        # 验证读写权限
        rw = io_config.get("rw", "RW")
        if rw not in self.VALID_RW_PERMISSIONS:
            errors.append(f"{platform}.{io_port}: Invalid rw permission '{rw}'")

        # 验证数据类型
        data_type = io_config.get("data_type")
        if data_type and data_type not in self.VALID_DATA_TYPES:
            warnings.append(f"{platform}.{io_port}: Unknown data_type '{data_type}'")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)


class DeviceSpecRegistry:
    """设备规格统一存储注册表"""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.LENIENT):
        """
        初始化设备规格注册表

        Args:
            validation_level: 数据验证级别
        """
        self._specs: Dict[str, Dict[str, Any]] = {}
        self._loaded: bool = False
        self._cache: Dict[str, Any] = {}
        self._validation_level = validation_level
        self._validator = DeviceSpecValidator()  # 现在包含特殊设备处理器

        # Phase 1.2: 分散映射存储
        self._scattered_mappings: Dict[str, Any] = {}
        self._mapping_aliases: Dict[str, str] = {}

        # 统计信息
        self._stats = {
            "total_devices": 0,
            "platforms": set(),
            "load_time": None,
            "validation_errors": 0,
            "validation_warnings": 0,
            "scattered_mappings_count": 0,
        }

    def load_specs(self, force_reload: bool = False) -> None:
        """
        加载设备规格数据

        Args:
            force_reload: 是否强制重新加载
        """
        if self._loaded and not force_reload:
            return

        try:
            import time

            start_time = time.time()

            # 从device_specs.py导入数据
            from .device_specs import _RAW_DEVICE_DATA

            # 清理缓存
            self._cache.clear()
            self._specs.clear()
            self._stats["validation_errors"] = 0
            self._stats["validation_warnings"] = 0

            # 加载和验证数据
            for device_type, spec in _RAW_DEVICE_DATA.items():
                if self._validation_level != ValidationLevel.NONE:
                    result = self._validator.validate_device_spec(device_type, spec)

                    if result.has_errors():
                        self._stats["validation_errors"] += len(result.errors)
                        if self._validation_level == ValidationLevel.STRICT:
                            _LOGGER.error(
                                f"Device {device_type} validation failed: {result.errors}"
                            )
                            continue
                        else:
                            _LOGGER.warning(
                                f"Device {device_type} has errors: {result.errors}"
                            )

                    if result.has_warnings():
                        self._stats["validation_warnings"] += len(result.warnings)
                        _LOGGER.debug(
                            f"Device {device_type} has warnings: {result.warnings}"
                        )

                # 存储设备规格
                self._specs[device_type] = spec.copy()

                # 更新统计信息
                self._update_device_stats(device_type, spec)

            # Phase 1.2: 加载分散映射配置
            self._load_scattered_mappings()

            self._loaded = True
            self._stats["load_time"] = time.time() - start_time
            self._stats["total_devices"] = len(self._specs)
            self._stats["scattered_mappings_count"] = len(self._scattered_mappings)

            _LOGGER.info(
                f"DeviceSpecRegistry loaded {self._stats['total_devices']} devices "
                f"and {self._stats['scattered_mappings_count']} scattered mappings "
                f"in {self._stats['load_time']:.3f}s"
            )

            if self._stats["validation_errors"] > 0:
                _LOGGER.warning(
                    f"Found {self._stats['validation_errors']} validation errors"
                )
            if self._stats["validation_warnings"] > 0:
                _LOGGER.info(
                    f"Found {self._stats['validation_warnings']} validation warnings"
                )

        except ImportError as e:
            _LOGGER.error(f"Failed to import device specs: {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to load device specs: {e}")
            raise

    def _update_device_stats(self, device_type: str, spec: Dict[str, Any]) -> None:
        """更新设备统计信息"""
        for key in spec:
            if key != "name" and not key.startswith("_"):
                self._stats["platforms"].add(key)

    def get_device_spec(self, device_type: str) -> Dict[str, Any]:
        """
        获取设备规格

        Args:
            device_type: 设备类型

        Returns:
            设备规格字典，如果不存在则返回空字典
        """
        self._ensure_loaded()

        # 检查缓存
        cache_key = f"spec_{device_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        spec = self._specs.get(device_type, {})

        # 缓存结果
        if spec:
            self._cache[cache_key] = spec.copy()

        return spec

    def has_device_spec(self, device_type: str) -> bool:
        """
        检查是否有指定设备的规格

        Args:
            device_type: 设备类型

        Returns:
            是否存在
        """
        self._ensure_loaded()
        return device_type in self._specs

    def list_device_types(self) -> List[str]:
        """
        获取所有设备类型列表

        Returns:
            设备类型列表
        """
        self._ensure_loaded()
        return list(self._specs.keys())

    def get_device_count(self) -> int:
        """
        获取设备总数

        Returns:
            设备总数
        """
        self._ensure_loaded()
        return len(self._specs)

    def find_by_platform(self, platform: str) -> List[str]:
        """
        根据平台查找设备类型

        Args:
            platform: 平台名称（如 "switch", "sensor"）

        Returns:
            包含该平台的设备类型列表
        """
        self._ensure_loaded()

        # 检查缓存
        cache_key = f"platform_{platform}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = []
        for device_type, spec in self._specs.items():
            if platform in spec:
                result.append(device_type)

        # 缓存结果
        self._cache[cache_key] = result
        return result

    def find_by_capability(self, capability: str) -> List[str]:
        """
        根据能力查找设备类型

        Args:
            capability: 能力名称（如特定的data_type或功能）

        Returns:
            具有该能力的设备类型列表
        """
        self._ensure_loaded()

        cache_key = f"capability_{capability}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = []
        for device_type, spec in self._specs.items():
            if self._has_capability(spec, capability):
                result.append(device_type)

        self._cache[cache_key] = result
        return result

    def _has_capability(self, spec: Dict[str, Any], capability: str) -> bool:
        """检查设备规格是否具有指定能力"""
        for platform_key, platform_config in spec.items():
            if platform_key == "name" or not isinstance(platform_config, dict):
                continue

            for io_key, io_config in platform_config.items():
                if isinstance(io_config, dict):
                    if io_config.get("data_type") == capability:
                        return True
                    if capability in io_config.get("description", "").lower():
                        return True

        return False

    def get_spec_metadata(self, device_type: str) -> Dict[str, Any]:
        """
        获取设备规格元数据

        Args:
            device_type: 设备类型

        Returns:
            元数据字典
        """
        self._ensure_loaded()

        if device_type not in self._specs:
            return {}

        spec = self._specs[device_type]
        platforms = []
        io_count = 0

        for key, value in spec.items():
            if key != "name" and isinstance(value, dict):
                platforms.append(key)
                io_count += len(value)

        return {
            "device_type": device_type,
            "name": spec.get("name", ""),
            "platforms": platforms,
            "io_count": io_count,
            "has_dynamic_config": "dynamic" in spec,
            "has_versioned_config": "versioned" in spec or "version_modes" in spec,
        }

    def validate_spec(self, device_type: str, spec: Dict[str, Any]) -> bool:
        """
        验证设备规格

        Args:
            device_type: 设备类型
            spec: 设备规格字典

        Returns:
            是否有效
        """
        result = self._validator.validate_device_spec(device_type, spec)
        return result.is_valid

    def get_validation_errors(self, device_type: str) -> List[str]:
        """
        获取设备的验证错误

        Args:
            device_type: 设备类型

        Returns:
            验证错误列表
        """
        self._ensure_loaded()

        if device_type not in self._specs:
            return [f"Device type '{device_type}' not found"]

        spec = self._specs[device_type]
        result = self._validator.validate_device_spec(device_type, spec)
        return result.errors

    def get_stats(self) -> Dict[str, Any]:
        """
        获取注册表统计信息

        Returns:
            统计信息字典
        """
        self._ensure_loaded()
        stats = self._stats.copy()
        stats["platforms"] = list(stats["platforms"])
        stats["cache_size"] = len(self._cache)
        stats["loaded"] = self._loaded
        return stats

    def clear_cache(self) -> None:
        """清理缓存"""
        self._cache.clear()
        _LOGGER.debug("DeviceSpecRegistry cache cleared")

    def _ensure_loaded(self) -> None:
        """确保数据已加载"""
        if not self._loaded:
            self.load_specs()

    def _load_scattered_mappings(self) -> None:
        """加载分散映射配置 - Phase 1.2核心功能"""
        try:
            # 从device_specs.py导入分散映射
            from .device_specs import (
                NON_POSITIONAL_COVER_CONFIG,
                LIFESMART_F_HVAC_MODE_MAP,
                LIFESMART_HVAC_MODE_MAP,
                REVERSE_LIFESMART_HVAC_MODE_MAP,
                LIFESMART_CP_AIR_HVAC_MODE_MAP,
                REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP,
                LIFESMART_ACIPM_FAN_MAP,
                LIFESMART_CP_AIR_FAN_MAP,
                REVERSE_LIFESMART_CP_AIR_FAN_MAP,
                LIFESMART_TF_FAN_MAP,
            )

            # 存储映射配置
            scattered_mappings = {
                # 窗帘配置映射
                "cover": {
                    "non_positional_config": NON_POSITIONAL_COVER_CONFIG,
                },
                # HVAC模式映射
                "hvac": {
                    "f_series_mode_map": LIFESMART_F_HVAC_MODE_MAP,
                    "general_mode_map": LIFESMART_HVAC_MODE_MAP,
                    "reverse_mode_map": REVERSE_LIFESMART_HVAC_MODE_MAP,
                    "cp_air_mode_map": LIFESMART_CP_AIR_HVAC_MODE_MAP,
                    "reverse_cp_air_mode_map": REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP,
                },
                # 风扇速度映射
                "fan": {
                    "acipm_fan_map": LIFESMART_ACIPM_FAN_MAP,
                    "cp_air_fan_map": LIFESMART_CP_AIR_FAN_MAP,
                    "reverse_cp_air_fan_map": REVERSE_LIFESMART_CP_AIR_FAN_MAP,
                    "tf_fan_map": LIFESMART_TF_FAN_MAP,
                },
            }

            # 更新内部存储
            self._scattered_mappings.update(scattered_mappings)

            # 建立别名映射（向后兼容）
            self._mapping_aliases.update(
                {
                    "NON_POSITIONAL_COVER_CONFIG": "cover.non_positional_config",
                    "LIFESMART_F_HVAC_MODE_MAP": "hvac.f_series_mode_map",
                    "LIFESMART_HVAC_MODE_MAP": "hvac.general_mode_map",
                    "REVERSE_LIFESMART_HVAC_MODE_MAP": "hvac.reverse_mode_map",
                    "LIFESMART_CP_AIR_HVAC_MODE_MAP": "hvac.cp_air_mode_map",
                    "REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP": "hvac.reverse_cp_air_mode_map",
                    "LIFESMART_ACIPM_FAN_MAP": "fan.acipm_fan_map",
                    "LIFESMART_CP_AIR_FAN_MAP": "fan.cp_air_fan_map",
                    "REVERSE_LIFESMART_CP_AIR_FAN_MAP": "fan.reverse_cp_air_fan_map",
                    "LIFESMART_TF_FAN_MAP": "fan.tf_fan_map",
                }
            )

            _LOGGER.debug(
                f"Loaded {len(self._scattered_mappings)} scattered mapping categories"
            )

        except ImportError as e:
            _LOGGER.warning(f"Failed to load scattered mappings: {e}")
        except Exception as e:
            _LOGGER.error(f"Error loading scattered mappings: {e}")

    def get_scattered_mapping(self, mapping_key: str) -> Dict[str, Any]:
        """获取分散映射配置

        Args:
            mapping_key: 映射键，支持点分割路径如 'hvac.general_mode_map'
                       或向后兼容的别名如 'LIFESMART_HVAC_MODE_MAP'

        Returns:
            映射配置字典，如果不存在则返回空字典
        """
        self._ensure_loaded()

        # 检查是否是别名
        if mapping_key in self._mapping_aliases:
            mapping_key = self._mapping_aliases[mapping_key]

        # 支持点分割路径
        parts = mapping_key.split(".")
        current = self._scattered_mappings

        try:
            for part in parts:
                current = current[part]
            return current if isinstance(current, dict) else {}
        except (KeyError, TypeError):
            return {}

    def list_scattered_mappings(self) -> List[str]:
        """获取所有分散映射的键列表

        Returns:
            映射键列表
        """
        self._ensure_loaded()

        def _flatten_keys(obj: Dict[str, Any], prefix: str = "") -> List[str]:
            keys = []
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict) and not any(
                    isinstance(v, (int, str, float, bool)) for v in value.values()
                ):
                    keys.extend(_flatten_keys(value, full_key))
                else:
                    keys.append(full_key)
            return keys

        return _flatten_keys(self._scattered_mappings)

    def has_scattered_mapping(self, mapping_key: str) -> bool:
        """检查是否存在指定的分散映射

        Args:
            mapping_key: 映射键

        Returns:
            是否存在
        """
        self._ensure_loaded()
        return len(self.get_scattered_mapping(mapping_key)) > 0

    # Phase 1.3: 统一查询接口 - 高级查询方法
    def get_device_config(
        self, device_type: str, platform: str, io_port: str = None
    ) -> Dict[str, Any]:
        """
        获取设备配置（统一查询接口之一）

        Args:
            device_type: 设备类型
            platform: 平台名称
            io_port: IO口名称（可选）

        Returns:
            设备配置字典
        """
        self._ensure_loaded()

        spec = self.get_device_spec(device_type)
        if not spec or platform not in spec:
            return {}

        platform_config = spec[platform]
        if not isinstance(platform_config, dict):
            return {}

        if io_port:
            return platform_config.get(io_port, {})
        else:
            return platform_config

    def resolve_platform(self, device_type: str, **criteria) -> List[str]:
        """
        解析设备支持的平台（统一查询接口之二）

        Args:
            device_type: 设备类型
            **criteria: 筛选条件，如 data_type='temperature'

        Returns:
            支持的平台列表
        """
        self._ensure_loaded()

        spec = self.get_device_spec(device_type)
        if not spec:
            return []

        supported_platforms = []

        for platform_key, platform_config in spec.items():
            if platform_key == "name" or not isinstance(platform_config, dict):
                continue

            # 检查是否符合条件
            if self._platform_matches_criteria(platform_config, criteria):
                supported_platforms.append(platform_key)

        return supported_platforms

    def get_capabilities(
        self, device_type: str, platform: str = None
    ) -> Dict[str, List[str]]:
        """
        获取设备能力（统一查询接口之三）

        Args:
            device_type: 设备类型
            platform: 平台名称（可选，不指定则返回所有平台）

        Returns:
            能力字典，格式: {platform: [capabilities]}
        """
        self._ensure_loaded()

        spec = self.get_device_spec(device_type)
        if not spec:
            return {}

        capabilities = {}

        # 如果指定了平台，只返回该平台的能力
        if platform:
            if platform in spec and isinstance(spec[platform], dict):
                capabilities[platform] = self._extract_platform_capabilities(
                    spec[platform]
                )
        else:
            # 返回所有平台的能力
            for platform_key, platform_config in spec.items():
                if platform_key != "name" and isinstance(platform_config, dict):
                    capabilities[platform_key] = self._extract_platform_capabilities(
                        platform_config
                    )

        return capabilities

    def query_devices_by_criteria(self, **criteria) -> List[str]:
        """
        根据条件查询设备（统一查询接口之四）

        Args:
            **criteria: 查询条件，如:
                platform='sensor'
                data_type='temperature'
                rw='R'
                device_class='temperature'

        Returns:
            符合条件的设备类型列表
        """
        self._ensure_loaded()

        matching_devices = []

        for device_type, spec in self._specs.items():
            if self._device_matches_criteria(device_type, spec, criteria):
                matching_devices.append(device_type)

        return matching_devices

    def get_platform_io_summary(
        self, device_type: str, platform: str
    ) -> Dict[str, Any]:
        """
        获取平台IO口摘要信息（统一查询接口之五）

        Args:
            device_type: 设备类型
            platform: 平台名称

        Returns:
            IO口摘要信息
        """
        self._ensure_loaded()

        platform_config = self.get_device_config(device_type, platform)
        if not platform_config:
            return {}

        summary = {
            "total_io_ports": 0,
            "readable_ports": 0,
            "writable_ports": 0,
            "data_types": set(),
            "device_classes": set(),
            "io_ports": [],
        }

        for io_port, io_config in platform_config.items():
            if isinstance(io_config, dict):
                summary["total_io_ports"] += 1

                # 统计读写权限
                rw = io_config.get("rw", "RW")
                if "R" in rw:
                    summary["readable_ports"] += 1
                if "W" in rw:
                    summary["writable_ports"] += 1

                # 收集数据类型和设备类
                if "data_type" in io_config:
                    summary["data_types"].add(io_config["data_type"])
                if "device_class" in io_config:
                    summary["device_classes"].add(io_config["device_class"])

                # IO口信息
                summary["io_ports"].append(
                    {
                        "port": io_port,
                        "description": io_config.get("description", ""),
                        "rw": rw,
                        "data_type": io_config.get("data_type"),
                        "device_class": io_config.get("device_class"),
                    }
                )

        # 转换set为列表
        summary["data_types"] = list(summary["data_types"])
        summary["device_classes"] = list(summary["device_classes"])

        return summary

    # Phase 1.3: 辅助方法
    def _platform_matches_criteria(
        self, platform_config: Dict[str, Any], criteria: Dict[str, Any]
    ) -> bool:
        """检查平台配置是否符合条件"""
        if not criteria:
            return True

        for io_port, io_config in platform_config.items():
            if isinstance(io_config, dict):
                if self._io_config_matches_criteria(io_config, criteria):
                    return True
        return False

    def _io_config_matches_criteria(
        self, io_config: Dict[str, Any], criteria: Dict[str, Any]
    ) -> bool:
        """检查IO配置是否符合条件"""
        for key, expected_value in criteria.items():
            if key in io_config:
                if io_config[key] != expected_value:
                    return False
            elif key == "rw" and "rw" not in io_config:
                # 默认rw为RW
                if expected_value != "RW":
                    return False
        return True

    def _device_matches_criteria(
        self, device_type: str, spec: Dict[str, Any], criteria: Dict[str, Any]
    ) -> bool:
        """检查设备是否符合条件"""
        if not criteria:
            return True

        # 如果指定了平台，检查设备是否有该平台
        if "platform" in criteria:
            target_platform = criteria["platform"]
            if target_platform not in spec:
                return False

            platform_config = spec[target_platform]
            if not isinstance(platform_config, dict):
                return False

            # 检查平台下的其他条件
            platform_criteria = {k: v for k, v in criteria.items() if k != "platform"}
            return self._platform_matches_criteria(platform_config, platform_criteria)
        else:
            # 在所有平台中查找符合条件的
            for platform_key, platform_config in spec.items():
                if platform_key != "name" and isinstance(platform_config, dict):
                    if self._platform_matches_criteria(platform_config, criteria):
                        return True
            return False

    def _extract_platform_capabilities(
        self, platform_config: Dict[str, Any]
    ) -> List[str]:
        """提取平台能力列表"""
        capabilities = set()

        for io_port, io_config in platform_config.items():
            if isinstance(io_config, dict):
                # 数据类型能力
                if "data_type" in io_config:
                    capabilities.add(f"data_type:{io_config['data_type']}")

                # 设备类能力
                if "device_class" in io_config:
                    capabilities.add(f"device_class:{io_config['device_class']}")

                # 读写权限能力
                rw = io_config.get("rw", "RW")
                if "R" in rw:
                    capabilities.add("readable")
                if "W" in rw:
                    capabilities.add("writable")

                # IO口功能能力
                description = io_config.get("description", "").lower()
                if "temperature" in description:
                    capabilities.add("temperature_sensing")
                if "humidity" in description:
                    capabilities.add("humidity_sensing")
                if "motion" in description:
                    capabilities.add("motion_detection")
                if "switch" in description or "control" in description:
                    capabilities.add("switch_control")

        return list(capabilities)


# 向后兼容性支持：提供全局实例
_global_registry: Optional[DeviceSpecRegistry] = None


def get_device_spec_registry() -> DeviceSpecRegistry:
    """
    获取全局设备规格注册表实例

    Returns:
        DeviceSpecRegistry实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = DeviceSpecRegistry()
    return _global_registry


def get_device_spec(device_type: str) -> Dict[str, Any]:
    """
    便捷函数：获取设备规格（向后兼容）

    Args:
        device_type: 设备类型

    Returns:
        设备规格字典
    """
    return get_device_spec_registry().get_device_spec(device_type)


# Phase 1.2: 分散映射便捷访问函数
def get_scattered_mapping(mapping_key: str) -> Dict[str, Any]:
    """
    便捷函数：获取分散映射配置

    Args:
        mapping_key: 映射键，支持点分割路径或别名

    Returns:
        映射配置字典
    """
    return get_device_spec_registry().get_scattered_mapping(mapping_key)


def list_scattered_mappings() -> List[str]:
    """
    便捷函数：获取所有分散映射键列表

    Returns:
        映射键列表
    """
    return get_device_spec_registry().list_scattered_mappings()


# Phase 1.3: 统一查询接口便捷函数
def get_device_config(
    device_type: str, platform: str, io_port: str = None
) -> Dict[str, Any]:
    """
    便捷函数：获取设备配置

    Args:
        device_type: 设备类型
        platform: 平台名称
        io_port: IO口名称（可选）

    Returns:
        设备配置字典
    """
    return get_device_spec_registry().get_device_config(device_type, platform, io_port)


def resolve_platform(device_type: str, **criteria) -> List[str]:
    """
    便捷函数：解析设备支持的平台

    Args:
        device_type: 设备类型
        **criteria: 筛选条件

    Returns:
        支持的平台列表
    """
    return get_device_spec_registry().resolve_platform(device_type, **criteria)


def get_capabilities(device_type: str, platform: str = None) -> Dict[str, List[str]]:
    """
    便捷函数：获取设备能力

    Args:
        device_type: 设备类型
        platform: 平台名称（可选）

    Returns:
        能力字典
    """
    return get_device_spec_registry().get_capabilities(device_type, platform)


def query_devices_by_criteria(**criteria) -> List[str]:
    """
    便捷函数：按条件查询设备

    Args:
        **criteria: 查询条件

    Returns:
        符合条件的设备类型列表
    """
    return get_device_spec_registry().query_devices_by_criteria(**criteria)


def get_platform_io_summary(device_type: str, platform: str) -> Dict[str, Any]:
    """
    便捷函数：获取平台IO口摘要信息

    Args:
        device_type: 设备类型
        platform: 平台名称

    Returns:
        IO口摘要信息
    """
    return get_device_spec_registry().get_platform_io_summary(device_type, platform)


# Phase 1.2: 向后兼容映射常量（基于DeviceSpecRegistry）
class ScatteredMappingProxy:
    """分散映射代理类，实现向后兼容的常量访问"""

    def __getattr__(self, name: str) -> Any:
        """动态获取分散映射常量"""
        mapping = get_scattered_mapping(name)
        if mapping:
            return mapping
        raise AttributeError(f"Scattered mapping '{name}' not found")

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.__getattr__(key)

    def get(self, key: str, default=None) -> Any:
        """安全获取映射，支持默认值"""
        try:
            return self.__getattr__(key)
        except AttributeError:
            return default


# 创建代理实例（向后兼容）
scattered_mappings = ScatteredMappingProxy()


# 兼容性别名 - 向后兼容device_specs.py中的常量访问
# 这些将自动代理到DeviceSpecRegistry中的数据
DEVICE_SPECS_DATA = get_device_spec_registry()  # 替换原有的别名


# Phase 1.2: 向后兼容常量 - 通过代理提供直接访问
# 这些将让现有代码无需修改，同时使用新的统一存储
def __getattr__(name: str) -> Any:
    """
    模块级别的动态属性访问，实现向后兼容

    支持的访问模式：
    - from device_spec_registry import NON_POSITIONAL_COVER_CONFIG
    - from device_spec_registry import LIFESMART_HVAC_MODE_MAP
    """
    # 尝试从分散映射获取
    try:
        return scattered_mappings.get(name)
    except AttributeError:
        pass

    # 如果没有找到，抛出AttributeError
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
