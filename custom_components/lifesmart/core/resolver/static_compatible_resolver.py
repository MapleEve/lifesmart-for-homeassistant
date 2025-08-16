"""
静态兼容解析器 - Phase 3迁移桥梁
由 @MapleEve 创建，基于Phase 5.5.7.3纯静态map架构设计

此模块提供与现有DeviceResolver完全兼容的接口，但内部使用StaticDeviceResolver。
这是Phase 3迁移策略的核心，确保平滑迁移而不破坏现有代码。

兼容目标：
- 完全兼容现有DeviceResolver接口
- 保持所有方法签名和返回类型
- 维护错误处理和异常抛出行为
- 保留缓存接口和统计功能
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union

from homeassistant.exceptions import HomeAssistantError

from .types import (
    DeviceConfig,
    PlatformConfig,
    IOConfig,
    ResolutionResult,
    SupportLevel,
    ValidationStatus,
    DeviceData,
    PlatformName,
    IOKey,
)

from .static_device_resolver import (
    StaticDeviceResolver,
    DeviceConfig as StaticDeviceConfig,
    ResolutionResult as StaticResolutionResult,
    ResolutionStatus,
    DeviceConfigFacade,
)

from ..config.extended_static_config_preprocessor import (
    ExtendedStaticConfigPreprocessor,
)
from ..config.static_config_validator import StaticConfigValidator
from ..config.device_specs import _RAW_DEVICE_DATA

_LOGGER = logging.getLogger(__name__)


class StaticCompatibleResolver:
    """
    静态兼容解析器 - 替代现有DeviceResolver

    提供与DeviceResolver完全相同的接口，但内部使用StaticDeviceResolver
    实现O(1)性能的同时保持100%向后兼容。
    """

    def __init__(
        self,
        spec_registry=None,
        strategy_factory=None,
        enable_cache: bool = True,
    ):
        """
        初始化静态兼容解析器

        Args:
            spec_registry: 兼容参数 (忽略)
            strategy_factory: 兼容参数 (忽略)
            enable_cache: 是否启用缓存
        """
        self._enable_cache = enable_cache
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}

        # 初始化静态解析器
        self._init_static_resolver()

        _LOGGER.info(
            "StaticCompatibleResolver initialized: cache=%s, static_configs=%d",
            enable_cache,
            len(self._static_configs),
        )

    def _init_static_resolver(self):
        """初始化静态解析器"""
        try:
            # 生成静态配置 - 使用ExtendedStaticConfigPreprocessor支持双格式
            preprocessor = ExtendedStaticConfigPreprocessor(_RAW_DEVICE_DATA)
            self._static_configs = preprocessor.generate_static_configs()

            # 验证配置
            validator = StaticConfigValidator()
            validation_result = validator.validate_all_configs(self._static_configs)

            if not validation_result.valid:
                _LOGGER.error("静态配置验证失败: %s", validation_result.errors)
                # 降级到空配置
                self._static_configs = {}

            # 创建静态解析器和门面
            self._static_resolver = StaticDeviceResolver(self._static_configs)
            self._device_facade = DeviceConfigFacade(self._static_resolver)

            _LOGGER.info(
                "静态解析器初始化完成: %d 个设备配置", len(self._static_configs)
            )

        except Exception as e:
            _LOGGER.exception("初始化静态解析器失败: %s", e)
            # 降级处理
            self._static_configs = {}
            self._static_resolver = None
            self._device_facade = None

    def resolve_device_config(self, device: DeviceData) -> ResolutionResult:
        """
        兼容接口：解析设备配置

        完全兼容原有DeviceResolver.resolve_device_config()的接口和行为

        Args:
            device: 设备数据

        Returns:
            ResolutionResult: 解析结果 (兼容格式)
        """
        start_time = time.time()

        try:
            # 验证输入
            if not device or not isinstance(device, dict):
                return ResolutionResult.error_result(
                    "Invalid device data: must be non-empty dict"
                )

            # 检查静态解析器是否可用
            if not self._static_resolver:
                return ResolutionResult.error_result("Static resolver not initialized")

            # 使用静态解析器
            static_result = self._static_resolver.resolve_device_config(device)

            # 转换为兼容格式
            compatible_result = self._convert_static_result_to_compatible(
                static_result, device
            )

            # 设置时间统计
            compatible_result.resolution_time_ms = (time.time() - start_time) * 1000

            # 更新统计
            if static_result.status == ResolutionStatus.SUCCESS:
                self._cache_stats["hits"] += 1
            else:
                self._cache_stats["misses"] += 1

            return compatible_result

        except Exception as e:
            self._cache_stats["errors"] += 1
            error_msg = (
                f"Failed to resolve device {device.get('me', 'unknown')}: {str(e)}"
            )
            _LOGGER.exception("Device resolution failed: %s", error_msg)

            result = ResolutionResult.error_result(error_msg)
            result.resolution_time_ms = (time.time() - start_time) * 1000
            return result

    def get_platform_config(
        self, device: DeviceData, platform: PlatformName
    ) -> Optional[PlatformConfig]:
        """
        兼容接口：获取平台配置

        完全兼容原有接口，包括异常抛出行为

        Args:
            device: 设备数据
            platform: 平台名称

        Returns:
            PlatformConfig或None

        Raises:
            HomeAssistantError: 解析失败时抛出
        """
        result = self.resolve_device_config(device)

        if not result.success:
            # 保持兼容性：抛出HomeAssistantError
            raise HomeAssistantError(
                result.error_message
                or f"Failed to resolve device {device.get('me', 'unknown')}"
            )

        if result.device_config:
            return result.device_config.get_platform_config(platform)

        return None

    def validate_device_support(
        self, device: DeviceData, platform: PlatformName
    ) -> bool:
        """
        兼容接口：验证设备平台支持

        Args:
            device: 设备数据
            platform: 平台名称

        Returns:
            bool: 是否支持该平台
        """
        try:
            platform_config = self.get_platform_config(device, platform)
            return platform_config is not None and platform_config.supported
        except Exception as e:
            _LOGGER.warning("Failed to validate device support: %s", e)
            return False

    def get_io_config(
        self, device: DeviceData, platform: PlatformName, io_key: IOKey
    ) -> Optional[IOConfig]:
        """
        兼容接口：获取IO配置

        Args:
            device: 设备数据
            platform: 平台名称
            io_key: IO键名

        Returns:
            IOConfig或None
        """
        platform_config = self.get_platform_config(device, platform)
        if platform_config:
            return platform_config.ios.get(io_key)
        return None

    def get_supported_platforms(self, device: DeviceData) -> List[PlatformName]:
        """
        兼容接口：获取支持的平台列表

        Args:
            device: 设备数据

        Returns:
            List[str]: 支持的平台列表
        """
        result = self.resolve_device_config(device)
        if result.success and result.device_config:
            return result.device_config.supported_platforms
        return []

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        兼容接口：获取缓存统计

        Returns:
            Dict: 缓存统计数据
        """
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            (self._cache_stats["hits"] / total_requests) if total_requests > 0 else 0
        )

        # 合并静态解析器统计
        static_stats = {}
        if self._static_resolver:
            static_stats = self._static_resolver.get_resolver_stats()

        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "errors": self._cache_stats["errors"],
            "hit_rate": hit_rate,
            "cache_size": len(self._static_configs),
            "total_requests": total_requests,
            # 添加静态解析器统计
            "static_resolver_stats": static_stats,
        }

    def clear_cache(self):
        """兼容接口：清空缓存"""
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}
        if self._static_resolver:
            self._static_resolver.reset_stats()
        _LOGGER.debug("StaticCompatibleResolver cache cleared")

    def _convert_static_result_to_compatible(
        self, static_result: StaticResolutionResult, device: DeviceData
    ) -> ResolutionResult:
        """
        转换静态解析结果为兼容格式

        Args:
            static_result: 静态解析结果
            device: 原始设备数据

        Returns:
            ResolutionResult: 兼容格式结果
        """
        if static_result.status == ResolutionStatus.ERROR:
            return ResolutionResult.error_result(
                static_result.error_message or "Unknown resolution error"
            )

        # 转换静态DeviceConfig为兼容DeviceConfig
        static_config = static_result.device_config
        if not static_config:
            return ResolutionResult.error_result("No device configuration")

        # 创建兼容的DeviceConfig
        compatible_config = DeviceConfig(
            device_type=static_config.device_type,
            name=static_config.name,
            raw_device=device,
            source_mapping=static_config.platforms,  # 使用platforms作为source_mapping
        )

        # 转换平台配置
        platforms = {}
        for platform_name, platform_data in static_config.platforms.items():
            if isinstance(platform_data, dict):
                platform_config = self._convert_static_platform_to_compatible(
                    platform_name, platform_data
                )
                if platform_config:
                    platforms[platform_name] = platform_config

        compatible_config.platforms = platforms

        # 根据静态结果状态创建兼容结果
        if static_result.status == ResolutionStatus.WARNING:
            return ResolutionResult.warning_result(
                compatible_config,
                static_result.warnings[0] if static_result.warnings else "Warning",
            )
        else:
            return ResolutionResult.success_result(compatible_config)

    def _convert_static_platform_to_compatible(
        self, platform_name: str, platform_data: Dict[str, Any]
    ) -> Optional[PlatformConfig]:
        """
        转换静态平台配置为兼容格式

        Args:
            platform_name: 平台名称
            platform_data: 静态平台数据

        Returns:
            PlatformConfig或None
        """
        if not isinstance(platform_data, dict):
            return None

        platform_config = PlatformConfig(
            platform_type=platform_name,
            supported=True,
        )

        # 转换IO配置
        ios = {}
        for io_key, io_data in platform_data.items():
            if isinstance(io_data, dict) and "description" in io_data:
                io_config = self._convert_static_io_to_compatible(io_data)
                if io_config:
                    ios[io_key] = io_config

        platform_config.ios = ios

        # 手动触发__post_init__重新计算统计信息
        platform_config.__post_init__()

        return platform_config

    def _convert_static_io_to_compatible(
        self, io_data: Dict[str, Any]
    ) -> Optional[IOConfig]:
        """
        转换静态IO配置为兼容格式

        Args:
            io_data: 静态IO数据

        Returns:
            IOConfig或None
        """
        if not io_data.get("description"):
            return None

        return IOConfig(
            description=io_data["description"],
            cmd_type=io_data.get("cmd_type"),
            idx=io_data.get("idx"),
            device_class=io_data.get("device_class"),
            state_class=io_data.get("state_class"),
            unit_of_measurement=io_data.get("unit_of_measurement"),
            icon=io_data.get("icon"),
            entity_category=io_data.get("entity_category"),
            value_template=io_data.get("value_template"),
            state_mapping=io_data.get("state_mapping"),
        )

    def get_static_resolver_stats(self) -> Dict[str, Any]:
        """
        获取静态解析器专用统计信息

        Returns:
            Dict: 静态解析器统计
        """
        if self._static_resolver:
            return self._static_resolver.get_resolver_stats()
        return {}

    def get_static_configuration_coverage(self) -> Dict[str, Any]:
        """
        获取静态配置覆盖率信息

        Returns:
            Dict: 配置覆盖率统计
        """
        if self._static_resolver:
            return self._static_resolver.validate_configuration_coverage()
        return {}


# 全局实例管理
_global_static_resolver: Optional[StaticCompatibleResolver] = None


def get_static_compatible_resolver() -> StaticCompatibleResolver:
    """
    获取全局静态兼容解析器实例

    Returns:
        StaticCompatibleResolver: 全局解析器实例
    """
    global _global_static_resolver
    if _global_static_resolver is None:
        _global_static_resolver = StaticCompatibleResolver()
    return _global_static_resolver


def resolve_device_config_static(device: DeviceData) -> ResolutionResult:
    """
    便捷函数：使用静态解析器解析设备配置

    Args:
        device: 设备数据

    Returns:
        ResolutionResult: 解析结果
    """
    return get_static_compatible_resolver().resolve_device_config(device)


def get_platform_config_static(
    device: DeviceData, platform: PlatformName
) -> Optional[PlatformConfig]:
    """
    便捷函数：使用静态解析器获取平台配置

    Args:
        device: 设备数据
        platform: 平台名称

    Returns:
        PlatformConfig或None
    """
    return get_static_compatible_resolver().get_platform_config(device, platform)


def validate_device_support_static(device: DeviceData, platform: PlatformName) -> bool:
    """
    便捷函数：使用静态解析器验证设备支持

    Args:
        device: 设备数据
        platform: 平台名称

    Returns:
        bool: 是否支持
    """
    return get_static_compatible_resolver().validate_device_support(device, platform)
