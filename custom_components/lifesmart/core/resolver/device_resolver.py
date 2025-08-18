"""
DeviceResolver - Phase 2统一设备解析接口实现

这是Phase 2的核心组件，基于Facade + Strategy模式设计。
替代22处分散的mapping_engine直接调用，提供：

- 统一的设备配置解析接口
- 内建错误处理和类型验证
- 简化平台文件调用复杂度75% (8→2行代码)
- 强类型安全和IDE友好

实现策略：
1. Facade模式包装现有mapping_engine (保持向后兼容)
2. 统一错误处理和日志记录
3. 强类型转换 (dict → DeviceConfig/PlatformConfig)
4. 性能优化和缓存支持

由 @MapleEve 创建，基于ZEN专家深度分析结果
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

from ..config.device_spec_registry import DeviceSpecRegistry, get_device_spec_registry
from ..strategies.strategy_factory import (
    DeviceStrategyFactory,
    get_device_strategy_factory,
)


_LOGGER = logging.getLogger(__name__)


class DeviceResolver:
    """
    统一设备解析接口 - Phase 2核心组件

    基于Facade模式包装mapping_engine，提供简化的统一接口。
    替代19个平台文件中22处分散的直接调用。
    """

    def __init__(
        self,
        spec_registry: Optional[DeviceSpecRegistry] = None,
        strategy_factory: Optional[DeviceStrategyFactory] = None,
        enable_cache: bool = True,
    ):
        """
        初始化DeviceResolver - Phase 2.5 重构版本

        Args:
            spec_registry: 设备规格注册表 (Phase 1)
            strategy_factory: 策略工厂 (Phase 2.5新增)
            enable_cache: 是否启用缓存
        """
        self._spec_registry = spec_registry or get_device_spec_registry()

        # Phase 2.5: 集成策略工厂，替代直接调用mapping_engine
        self._strategy_factory = strategy_factory or get_device_strategy_factory()

        # 缓存配置
        self._enable_cache = enable_cache
        self._resolution_cache: Dict[str, DeviceConfig] = {}
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}

        _LOGGER.info(
            "DeviceResolver initialized: cache=%s, registry=%s, strategy_factory=%s",
            enable_cache,
            type(self._spec_registry).__name__,
            type(self._strategy_factory).__name__,
        )

    def resolve_device_config(self, device: DeviceData) -> ResolutionResult:
        """
        统一设备配置解析 - 替代mapping_engine.resolve_device_mapping_from_data()

        这是核心接口，将原来8行重复代码简化为1行调用:
        Before: mapping_engine.resolve_device_mapping_from_data() + 错误检查 + 平台提取
        After: resolver.resolve_device_config(device).device_config

        Args:
            device: 原始设备数据字典

        Returns:
            ResolutionResult: 包含DeviceConfig或错误信息的解析结果
        """
        start_time = time.time()

        try:
            # 输入验证
            if not device or not isinstance(device, dict):
                return ResolutionResult.error_result(
                    "Invalid device data: must be non-empty dict"
                )

            device_type = device.get("devtype")
            device_me = device.get("me", "unknown")

            if not device_type:
                return ResolutionResult.error_result(
                    f"Missing device type for device {device_me}"
                )

            # 缓存检查
            cache_key = self._generate_cache_key(device)
            if self._enable_cache and cache_key in self._resolution_cache:
                self._cache_stats["hits"] += 1
                cached_config = self._resolution_cache[cache_key]
                result = ResolutionResult.success_result(cached_config)
                result.cache_hit = True
                return result

            self._cache_stats["misses"] += 1

            # Phase 2.5: 获取原始设备配置并使用策略工厂解析
            raw_config = self._spec_registry.get_device_spec(device_type)
            if not raw_config:
                error_msg = f"Device specification not found for {device_me} (type: {device_type})"
                _LOGGER.error("设备规格未找到: %s", device)
                return ResolutionResult.error_result(error_msg)

            # 使用策略工厂解析 (Phase 2.5新架构)
            raw_mapping = self._strategy_factory.resolve_device_mapping(
                device_type, device, raw_config
            )

            if not raw_mapping or (
                isinstance(raw_mapping, dict) and raw_mapping.get("_error")
            ):
                if isinstance(raw_mapping, dict) and "_error" in raw_mapping:
                    error_msg = (
                        f"Strategy failed for {device_me}: {raw_mapping['_error']}"
                    )
                else:
                    error_msg = f"Device configuration not found for {device_me} (type: {device_type})"
                _LOGGER.error("策略工厂无法解析设备配置: %s", device)
                return ResolutionResult.error_result(error_msg)

            # 转换为强类型DeviceConfig
            device_config = self._convert_to_device_config(device, raw_mapping)

            # 缓存结果
            if self._enable_cache:
                self._resolution_cache[cache_key] = device_config

            # 创建成功结果
            result = ResolutionResult.success_result(device_config)
            result.resolution_time_ms = (time.time() - start_time) * 1000

            _LOGGER.debug(
                "Device resolved successfully: %s -> %d platforms in %.2fms",
                device_me,
                len(device_config.platforms),
                result.resolution_time_ms,
            )

            return result

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
        获取特定平台配置 - 简化平台文件调用

        Before (8行代码):
            from .core.config.mapping_engine import mapping_engine
            device_config = mapping_engine.resolve_device_mapping_from_data(device)
            if not device_config:
                _LOGGER.error("映射引擎无法解析设备配置: %s", device)
                raise HomeAssistantError(...)
            platform_config = device_config.get(platform)
            if not platform_config:
                return None

        After (1行代码):
            platform_config = resolver.get_platform_config(device, platform)

        Args:
            device: 设备数据
            platform: 平台名称 (light, switch, sensor等)

        Returns:
            PlatformConfig或None
        """
        result = self.resolve_device_config(device)

        if not result.success:
            # 统一错误处理 - 抛出HomeAssistantError保持兼容性
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
        验证设备平台支持 - 返回清晰boolean

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
        获取特定IO配置 - 深度简化调用

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
        获取设备支持的所有平台列表

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
        获取缓存统计信息 - 用于性能监控

        Returns:
            Dict: 缓存统计数据
        """
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            (self._cache_stats["hits"] / total_requests) if total_requests > 0 else 0
        )

        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "errors": self._cache_stats["errors"],
            "hit_rate": hit_rate,
            "cache_size": len(self._resolution_cache),
            "total_requests": total_requests,
        }

    def clear_cache(self):
        """清空解析缓存"""
        self._resolution_cache.clear()
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}
        _LOGGER.debug("DeviceResolver cache cleared")

    def _generate_cache_key(self, device: DeviceData) -> str:
        """
        生成设备缓存键

        Args:
            device: 设备数据

        Returns:
            str: 缓存键
        """
        device_type = device.get("devtype", "unknown")
        device_me = device.get("me", "unknown")
        device_agt = device.get("agt", "unknown")  # 添加网关ID确保唯一性
        return f"{device_agt}:{device_me}:{device_type}"

    def _convert_to_device_config(
        self, device: DeviceData, raw_mapping: Dict[str, Any]
    ) -> DeviceConfig:
        """
        将原始映射转换为强类型DeviceConfig

        Args:
            device: 原始设备数据
            raw_mapping: mapping_engine返回的原始映射

        Returns:
            DeviceConfig: 强类型设备配置
        """
        device_type = device.get("devtype", "unknown")
        device_name = device.get("name", f"Device {device.get('me', 'Unknown')}")

        # 获取Generation 2元数据从设备规格
        device_spec = self._spec_registry.get_device_spec(device_type)
        manufacturer = None
        model = None
        category = None

        if device_spec:
            manufacturer = device_spec.get("manufacturer", "LifeSmart")
            model = device_spec.get("model", device_type)
            category = device_spec.get("category")

        # 创建DeviceConfig基础结构
        device_config = DeviceConfig(
            device_type=device_type,
            name=device_name,
            manufacturer=manufacturer,
            model=model,
            category=category,
            raw_device=device,
            source_mapping=raw_mapping,
        )

        # 转换平台配置
        platforms = {}
        for platform_name, platform_data in raw_mapping.items():
            if isinstance(platform_data, dict):
                platform_config = self._convert_to_platform_config(
                    platform_name, platform_data
                )
                if platform_config:
                    platforms[platform_name] = platform_config

        device_config.platforms = platforms

        return device_config

    def _convert_to_platform_config(
        self, platform_name: str, platform_data: Dict[str, Any]
    ) -> Optional[PlatformConfig]:
        """
        将平台数据转换为PlatformConfig

        Args:
            platform_name: 平台名称
            platform_data: 平台数据

        Returns:
            PlatformConfig或None
        """
        if not isinstance(platform_data, dict):
            return None

        # 创建平台配置
        platform_config = PlatformConfig(
            platform_type=platform_name,
            supported=True,  # 如果存在数据就认为支持
        )

        # 转换IO配置
        ios = {}
        for io_key, io_data in platform_data.items():
            if isinstance(io_data, dict) and "description" in io_data:
                io_config = self._convert_to_io_config(io_data)
                if io_config:
                    ios[io_key] = io_config

        platform_config.ios = ios

        # 手动触发__post_init__重新计算统计信息
        platform_config.__post_init__()

        return platform_config

    def _convert_to_io_config(self, io_data: Dict[str, Any]) -> Optional[IOConfig]:
        """
        将IO数据转换为IOConfig

        Args:
            io_data: IO数据字典

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


# 全局实例和便捷函数
_global_resolver: Optional[DeviceResolver] = None


def get_device_resolver() -> DeviceResolver:
    """
    获取全局DeviceResolver实例

    Returns:
        DeviceResolver: 全局解析器实例
    """
    global _global_resolver
    if _global_resolver is None:
        _global_resolver = DeviceResolver()
    return _global_resolver


def resolve_device_config(device: DeviceData) -> ResolutionResult:
    """
    便捷函数：解析设备配置

    Args:
        device: 设备数据

    Returns:
        ResolutionResult: 解析结果
    """
    return get_device_resolver().resolve_device_config(device)


def get_platform_config(
    device: DeviceData, platform: PlatformName
) -> Optional[PlatformConfig]:
    """
    便捷函数：获取平台配置

    Args:
        device: 设备数据
        platform: 平台名称

    Returns:
        PlatformConfig或None
    """
    return get_device_resolver().get_platform_config(device, platform)


def validate_device_support(device: DeviceData, platform: PlatformName) -> bool:
    """
    便捷函数：验证设备支持

    Args:
        device: 设备数据
        platform: 平台名称

    Returns:
        bool: 是否支持
    """
    return get_device_resolver().validate_device_support(device, platform)
