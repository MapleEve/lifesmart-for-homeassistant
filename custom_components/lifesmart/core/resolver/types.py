"""
DeviceResolver类型定义 - Phase 2核心数据结构

这是Phase 2 DeviceResolver Interface Design的类型系统，提供：
- 强类型替代泛型dict操作
- IDE友好的代码提示和类型检查
- 统一的数据结构标准

由 @MapleEve 创建，基于ZEN专家深度分析结果
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class SupportLevel(Enum):
    """设备支持级别"""

    FULL = "full"  # 完全支持
    PARTIAL = "partial"  # 部分支持
    LIMITED = "limited"  # 有限支持
    NONE = "none"  # 不支持


class ValidationStatus(Enum):
    """配置验证状态"""

    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    PARTIAL = "partial"


@dataclass
class IOConfig:
    """IO口配置信息"""

    # 基础信息
    description: str
    cmd_type: Optional[str] = None
    idx: Optional[int] = None

    # 功能配置
    device_class: Optional[str] = None
    state_class: Optional[str] = None
    unit_of_measurement: Optional[str] = None

    # HA特定配置
    icon: Optional[str] = None
    entity_category: Optional[str] = None

    # 数据转换
    value_template: Optional[str] = None
    state_mapping: Optional[Dict[str, Any]] = None

    # 验证状态
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_errors: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """检查IO配置是否有效"""
        return (
            self.validation_status == ValidationStatus.VALID
            and len(self.validation_errors) == 0
        )


@dataclass
class PlatformConfig:
    """平台配置信息"""

    # 平台基础信息
    platform_type: str  # light, switch, sensor等
    supported: bool
    support_level: SupportLevel = SupportLevel.NONE

    # IO配置映射
    ios: Dict[str, IOConfig] = field(default_factory=dict)

    # 平台特定配置
    features: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)

    # 统计信息
    io_count: int = 0
    valid_io_count: int = 0

    def __post_init__(self):
        """初始化后计算统计信息"""
        self.io_count = len(self.ios)
        self.valid_io_count = sum(1 for io in self.ios.values() if io.is_valid())

        # 根据有效IO数量调整支持级别
        if self.valid_io_count == 0:
            self.support_level = SupportLevel.NONE
            self.supported = False
        elif self.valid_io_count == self.io_count:
            self.support_level = SupportLevel.FULL
            self.supported = True
        else:
            self.support_level = SupportLevel.PARTIAL
            self.supported = True

    def get_valid_ios(self) -> Dict[str, IOConfig]:
        """获取所有有效的IO配置"""
        return {key: io for key, io in self.ios.items() if io.is_valid()}

    def has_io(self, io_key: str) -> bool:
        """检查是否包含特定IO"""
        return io_key in self.ios and self.ios[io_key].is_valid()


@dataclass
class DeviceConfig:
    """设备完整配置信息"""

    # 设备基础信息
    device_type: str
    name: str
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None

    # 平台配置映射
    platforms: Dict[str, PlatformConfig] = field(default_factory=dict)

    # 设备元信息
    supported_platforms: List[str] = field(default_factory=list)
    primary_platform: Optional[str] = None

    # 原始数据引用（用于兼容和调试）
    raw_device: Optional[Dict[str, Any]] = None
    source_mapping: Optional[Dict[str, Any]] = None

    # 验证信息
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后计算支持的平台列表"""
        self.supported_platforms = [
            platform for platform, config in self.platforms.items() if config.supported
        ]

        # 确定主要平台 (支持度最高的平台)
        if self.supported_platforms:
            best_platform = max(
                self.platforms.items(),
                key=lambda x: (x[1].support_level.value, x[1].valid_io_count),
                default=(None, None),
            )
            if best_platform[0]:
                self.primary_platform = best_platform[0]

    def is_supported(self, platform: str) -> bool:
        """检查是否支持特定平台"""
        return platform in self.platforms and self.platforms[platform].supported

    def get_platform_config(self, platform: str) -> Optional[PlatformConfig]:
        """获取特定平台配置"""
        return self.platforms.get(platform)

    def get_io_config(self, platform: str, io_key: str) -> Optional[IOConfig]:
        """获取特定平台的IO配置"""
        platform_config = self.get_platform_config(platform)
        if platform_config:
            return platform_config.ios.get(io_key)
        return None

    def is_valid(self) -> bool:
        """检查设备配置是否完全有效"""
        return (
            self.validation_status == ValidationStatus.VALID
            and len(self.validation_errors) == 0
            and len(self.supported_platforms) > 0
        )


@dataclass
class ResolutionResult:
    """设备解析结果"""

    success: bool
    device_config: Optional[DeviceConfig] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # 性能指标
    resolution_time_ms: Optional[float] = None
    cache_hit: bool = False

    @classmethod
    def success_result(cls, device_config: DeviceConfig) -> "ResolutionResult":
        """创建成功结果"""
        return cls(success=True, device_config=device_config)

    @classmethod
    def error_result(cls, error_message: str) -> "ResolutionResult":
        """创建错误结果"""
        return cls(success=False, error_message=error_message)

    @classmethod
    def warning_result(
        cls, device_config: DeviceConfig, warning_message: str
    ) -> "ResolutionResult":
        """创建警告结果"""
        result = cls(success=True, device_config=device_config)
        result.add_warning(warning_message)
        return result

    def add_warning(self, warning: str):
        """添加警告信息"""
        self.warnings.append(warning)


# 类型别名，提高代码可读性
DeviceData = Dict[str, Any]  # 原始设备数据
MappingData = Dict[str, Any]  # 映射配置数据
PlatformName = str  # 平台名称
IOKey = str  # IO键名
