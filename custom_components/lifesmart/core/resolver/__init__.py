"""
DeviceResolver模块 - Phase 2统一设备解析接口

这个模块提供了统一的设备解析接口，简化19个平台文件的调用复杂性。
基于Facade + Strategy模式设计，提供：

- 统一的设备配置解析接口
- 强类型安全和错误处理
- 简化平台文件调用复杂度75%
- 为Phase 3-4 mapping_engine重构奠定基础

由 @MapleEve 创建，基于ZEN专家深度分析结果
"""

from .types import (
    # 核心数据类型
    DeviceConfig,
    PlatformConfig,
    IOConfig,
    ResolutionResult,
    # 枚举类型
    SupportLevel,
    ValidationStatus,
    # 类型别名
    DeviceData,
    MappingData,
    PlatformName,
    IOKey,
)

from .device_resolver import (
    DeviceResolver,
    get_device_resolver,
    resolve_device_config,
    get_platform_config,
    validate_device_support,
)

# Phase 3: 静态兼容解析器
from .static_compatible_resolver import (
    StaticCompatibleResolver,
    get_static_compatible_resolver,
    resolve_device_config_static,
    get_platform_config_static,
    validate_device_support_static,
)

# 静态解析器作为默认选择 (Phase 3)
# 可以通过环境变量LIFESMART_USE_DYNAMIC_RESOLVER=1切换回动态解析器
import os

USE_STATIC_RESOLVER = os.getenv("LIFESMART_USE_DYNAMIC_RESOLVER", "0") != "1"

if USE_STATIC_RESOLVER:
    # 使用静态解析器作为默认实现
    get_device_resolver = get_static_compatible_resolver
    resolve_device_config = resolve_device_config_static
    get_platform_config = get_platform_config_static
    validate_device_support = validate_device_support_static

    # 将StaticCompatibleResolver作为DeviceResolver的别名
    DeviceResolver = StaticCompatibleResolver

__all__ = [
    # 类型系统
    "DeviceConfig",
    "PlatformConfig",
    "IOConfig",
    "ResolutionResult",
    "SupportLevel",
    "ValidationStatus",
    "DeviceData",
    "MappingData",
    "PlatformName",
    "IOKey",
    # 核心接口 (自动选择动态或静态实现)
    "DeviceResolver",
    "get_device_resolver",
    # 便捷函数 (自动选择动态或静态实现)
    "resolve_device_config",
    "get_platform_config",
    "validate_device_support",
    # 静态解析器专用接口 (Phase 3)
    "StaticCompatibleResolver",
    "get_static_compatible_resolver",
    "resolve_device_config_static",
    "get_platform_config_static",
    "validate_device_support_static",
    # 配置开关
    "USE_STATIC_RESOLVER",
]
