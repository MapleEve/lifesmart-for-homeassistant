"""
DeviceResolver 单元测试 - Phase 2 核心组件

测试 DeviceResolver 的所有公共接口，包括：
- 核心解析逻辑 (resolve_device_config)
- 缓存机制 (命中/未命中/清理)
- 错误处理和边界条件
- 平台配置获取的便捷方法

基于 @MapleEve 的 Phase 2.5 重构设计
"""
import time
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.lifesmart.core.resolver.device_resolver import DeviceResolver
from custom_components.lifesmart.core.resolver.types import (
    DeviceConfig,
    ResolutionResult,
    PlatformConfig,
    IOConfig,
)
from custom_components.lifesmart.core.strategies.strategy_factory import (
    DeviceStrategyFactory,
)
from custom_components.lifesmart.core.config.device_spec_registry import (
    DeviceSpecRegistry,
)

# 从强类型工厂导入测试数据
from ...utils.typed_factories import (
    create_typed_smart_plug,
    create_typed_thermostat_panel,
    create_typed_power_meter_plug,
)


@pytest.fixture
def mock_spec_registry():
    """提供一个 DeviceSpecRegistry 的模拟实例。"""
    registry = MagicMock(spec=DeviceSpecRegistry)
    # 默认让 get_device_spec 返回一个有效的空配置
    registry.get_device_spec.return_value = {"name": "Mock Spec"}
    return registry


@pytest.fixture
def mock_strategy_factory():
    """提供一个 DeviceStrategyFactory 的模拟实例。"""
    factory = MagicMock(spec=DeviceStrategyFactory)
    # 默认让 resolve_device_mapping 返回一个有效的映射
    factory.resolve_device_mapping.return_value = {
        "name": "Mock Mapping",
        "switch": {"P1": {"description": "Test Switch"}},
    }
    return factory


@pytest.fixture
def resolver(mock_spec_registry, mock_strategy_factory) -> DeviceResolver:
    """提供一个带有模拟依赖的 DeviceResolver 实例，用于隔离测试。"""
    return DeviceResolver(
        spec_registry=mock_spec_registry,
        strategy_factory=mock_strategy_factory,
        enable_cache=True,
    )


@pytest.fixture
def resolver_no_cache(mock_spec_registry, mock_strategy_factory) -> DeviceResolver:
    """提供一个禁用缓存的 DeviceResolver 实例。"""
    return DeviceResolver(
        spec_registry=mock_spec_registry,
        strategy_factory=mock_strategy_factory,
        enable_cache=False,
    )


class TestDeviceResolverCore:
    """DeviceResolver 核心功能测试套件。"""

    def test_resolve_device_config_success_path(
        self, resolver: DeviceResolver, mock_spec_registry, mock_strategy_factory
    ):
        """
        测试 resolve_device_config 的核心成功路径。
        Hypothesis: 当所有依赖项都正常工作时，应返回一个成功的 ResolutionResult，
                    其中包含一个正确转换的 DeviceConfig 对象。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        mock_spec_registry.get_device_spec.return_value = {"name": "Smart Plug Spec"}
        mock_strategy_factory.resolve_device_mapping.return_value = {
            "name": "Smart Plug Mapping",
            "switch": {
                "O": {
                    "description": "Switch",
                    "rw": "RW",
                    "data_type": "binary_switch",
                }
            },
        }

        # Act
        with patch("time.time", return_value=1000.0):  # Mock时间以获得确定性结果
            result = resolver.resolve_device_config(device_data)

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.cache_hit is False
        assert isinstance(result.device_config, DeviceConfig)
        assert result.device_config.device_type == "SL_OL"
        assert "switch" in result.device_config.platforms
        assert result.device_config.platforms["switch"].has_io("O")
        assert result.resolution_time_ms is not None

        # 验证依赖项是否被正确调用
        mock_spec_registry.get_device_spec.assert_called_once_with("SL_OL")
        mock_strategy_factory.resolve_device_mapping.assert_called_once()

    def test_resolve_device_config_cache_hit(self, resolver: DeviceResolver):
        """
        测试缓存命中逻辑。
        Hypothesis: 对同一设备的第二次调用应从缓存中获取结果，
                    并且不应再次调用策略工厂。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()

        # Act
        result1 = resolver.resolve_device_config(device_data)
        # 清除 mock 调用记录，以便验证第二次调用
        resolver._strategy_factory.resolve_device_mapping.reset_mock()
        result2 = resolver.resolve_device_config(device_data)

        # Assert
        assert result1.success and result2.success
        assert result1.cache_hit is False
        assert result2.cache_hit is True
        assert result1.device_config == result2.device_config  # 确保返回相同的配置

        # 验证第二次调用没有触发策略解析
        resolver._strategy_factory.resolve_device_mapping.assert_not_called()

        # 验证缓存统计
        stats = resolver.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_resolve_device_config_cache_disabled(self, resolver_no_cache: DeviceResolver):
        """
        测试缓存禁用时的行为。
        Hypothesis: 当缓存禁用时，每次调用都应执行完整解析流程。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()

        # Act
        result1 = resolver_no_cache.resolve_device_config(device_data)
        result2 = resolver_no_cache.resolve_device_config(device_data)

        # Assert
        assert result1.success and result2.success
        assert result1.cache_hit is False
        assert result2.cache_hit is False

        # 验证缓存统计为空
        stats = resolver_no_cache.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 2

    @pytest.mark.parametrize(
        "invalid_input, expected_error",
        [
            (None, "Invalid device data: must be non-empty dict"),
            ({}, "Invalid device data: must be non-empty dict"),
            ({}, "Invalid device data: must be non-empty dict"),
            ({\"me\": \"some_id\"}, \"Missing device type for device some_id\"),
        ],
    )
    def test_resolve_device_config_invalid_input(
        self, resolver: DeviceResolver, invalid_input, expected_error
    ):
        """
        测试 resolve_device_config 对无效输入的处理。
        Hypothesis: 当输入数据不符合要求时，应立即返回一个包含清晰错误信息的 error_result。
        """
        # Act
        result = resolver.resolve_device_config(invalid_input)

        # Assert
        assert result.success is False
        assert result.device_config is None
        assert result.error_message == expected_error

    def test_resolve_device_config_missing_devtype(self, resolver: DeviceResolver):
        """
        测试缺少设备类型时的处理。
        Hypothesis: 缺少devtype字段应返回明确的错误信息。
        """
        # Arrange
        device_data = {"me": "test_device", "name": "Test Device"}

        # Act
        result = resolver.resolve_device_config(device_data)

        # Assert
        assert result.success is False
        assert "Missing device type for device test_device" in result.error_message

    def test_resolve_device_config_no_spec_found(
        self, resolver: DeviceResolver, mock_spec_registry
    ):
        """
        测试当设备规格不存在时的处理。
        Hypothesis: 如果 spec_registry 返回 None，应返回一个明确的错误结果。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        mock_spec_registry.get_device_spec.return_value = None

        # Act
        result = resolver.resolve_device_config(device_data)

        # Assert
        assert result.success is False
        assert "Device specification not found" in result.error_message

    def test_resolve_device_config_strategy_failure(
        self, resolver: DeviceResolver, mock_strategy_factory
    ):
        """
        测试当策略工厂解析失败时的处理。
        Hypothesis: 如果 strategy_factory 返回一个包含 _error 的字典，
                    应将其转换为一个失败的 ResolutionResult。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        mock_strategy_factory.resolve_device_mapping.return_value = {
            "_error": "No suitable strategy"
        }

        # Act
        result = resolver.resolve_device_config(device_data)

        # Assert
        assert result.success is False
        assert "Strategy failed" in result.error_message
        assert "No suitable strategy" in result.error_message

    def test_resolve_device_config_strategy_returns_none(
        self, resolver: DeviceResolver, mock_strategy_factory
    ):
        """
        测试当策略工厂返回None时的处理。
        Hypothesis: 如果 strategy_factory 返回 None，应返回配置未找到的错误。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        mock_strategy_factory.resolve_device_mapping.return_value = None

        # Act
        result = resolver.resolve_device_config(device_data)

        # Assert
        assert result.success is False
        assert "Device configuration not found" in result.error_message

    def test_resolve_device_config_conversion_exception(
        self, resolver: DeviceResolver
    ):
        """
        测试类型转换时发生异常的处理。
        Hypothesis: 如果 _convert_to_device_config 抛出异常，应被捕获并返回错误结果。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        
        # Mock _convert_to_device_config 抛出异常
        with patch.object(
            resolver, "_convert_to_device_config", side_effect=ValueError("Conversion failed")
        ):
            # Act
            result = resolver.resolve_device_config(device_data)

        # Assert
        assert result.success is False
        assert "Failed to resolve device" in result.error_message
        assert "Conversion failed" in result.error_message

        # 验证错误统计被更新
        stats = resolver.get_cache_stats()
        assert stats["errors"] == 1

    def test_resolve_device_config_performance_timing(self, resolver: DeviceResolver):
        """
        测试性能计时功能。
        Hypothesis: resolve_device_config 应记录准确的解析时间。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        start_time = 1000.0
        end_time = 1000.05  # 50ms

        # Act
        with patch("time.time", side_effect=[start_time, end_time]):
            result = resolver.resolve_device_config(device_data)

        # Assert
        assert result.success is True
        assert result.resolution_time_ms == 50.0


class TestDeviceResolverPlatformMethods:
    """DeviceResolver 平台相关方法测试套件。"""

    def test_get_platform_config_success(self, resolver: DeviceResolver):
        """
        测试 get_platform_config 的成功场景。
        Hypothesis: 当平台存在时应返回 PlatformConfig。
        """
        # Arrange
        device_data = create_typed_thermostat_panel().to_dict()
        device_config = DeviceConfig(
            device_type="SL_NATURE",
            name="Test Thermo",
            platforms={
                "climate": PlatformConfig(platform_type="climate", supported=True),
                "sensor": PlatformConfig(platform_type="sensor", supported=True),
            },
        )
        
        with patch.object(
            resolver, "resolve_device_config",
            return_value=ResolutionResult.success_result(device_config)
        ):
            # Act
            climate_config = resolver.get_platform_config(device_data, "climate")

        # Assert
        assert isinstance(climate_config, PlatformConfig)
        assert climate_config.platform_type == "climate"
        assert climate_config.supported is True

    def test_get_platform_config_not_found(self, resolver: DeviceResolver):
        """
        测试 get_platform_config 当平台不存在时的处理。
        Hypothesis: 不存在的平台应返回 None。
        """
        # Arrange
        device_data = create_typed_thermostat_panel().to_dict()
        device_config = DeviceConfig(
            device_type="SL_NATURE",
            name="Test Thermo",
            platforms={
                "climate": PlatformConfig(platform_type="climate", supported=True),
            },
        )
        
        with patch.object(
            resolver, "resolve_device_config",
            return_value=ResolutionResult.success_result(device_config)
        ):
            # Act
            light_config = resolver.get_platform_config(device_data, "light")

        # Assert
        assert light_config is None

    def test_get_platform_config_raises_error_on_resolve_failure(
        self, resolver: DeviceResolver
    ):
        """
        测试当设备解析失败时，get_platform_config 是否抛出 HomeAssistantError。
        Hypothesis: 这是为了保持与现有平台文件代码的兼容性，错误应向上抛出。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        
        with patch.object(
            resolver, "resolve_device_config",
            return_value=ResolutionResult.error_result("Resolution failed")
        ):
            # Act & Assert
            with pytest.raises(HomeAssistantError, match="Resolution failed"):
                resolver.get_platform_config(device_data, "switch")

    def test_validate_device_support_success(self, resolver: DeviceResolver):
        """
        测试 validate_device_support 的成功验证。
        Hypothesis: 支持的平台应返回 True。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        platform_config = PlatformConfig(platform_type="switch", supported=True)
        
        with patch.object(resolver, "get_platform_config", return_value=platform_config):
            # Act
            is_supported = resolver.validate_device_support(device_data, "switch")

        # Assert
        assert is_supported is True

    def test_validate_device_support_not_supported(self, resolver: DeviceResolver):
        """
        测试 validate_device_support 当平台不支持时的处理。
        Hypothesis: 不支持的平台应返回 False。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        platform_config = PlatformConfig(platform_type="switch", supported=False)
        
        with patch.object(resolver, "get_platform_config", return_value=platform_config):
            # Act
            is_supported = resolver.validate_device_support(device_data, "switch")

        # Assert
        assert is_supported is False

    def test_validate_device_support_platform_not_found(self, resolver: DeviceResolver):
        """
        测试 validate_device_support 当平台不存在时的处理。
        Hypothesis: 不存在的平台应返回 False。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        
        with patch.object(resolver, "get_platform_config", return_value=None):
            # Act
            is_supported = resolver.validate_device_support(device_data, "light")

        # Assert
        assert is_supported is False

    def test_validate_device_support_exception_handling(self, resolver: DeviceResolver):
        """
        测试 validate_device_support 的异常处理。
        Hypothesis: 当 get_platform_config 抛出异常时，应返回 False 而不是传播异常。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        
        with patch.object(
            resolver, "get_platform_config", 
            side_effect=HomeAssistantError("Test error")
        ):
            # Act
            is_supported = resolver.validate_device_support(device_data, "switch")

        # Assert
        assert is_supported is False

    def test_get_io_config_success(self, resolver: DeviceResolver):
        """
        测试 get_io_config 的成功获取。
        Hypothesis: 存在的IO配置应被正确返回。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        io_config = IOConfig(description="Test IO")
        platform_config = PlatformConfig(
            platform_type="switch", 
            supported=True,
            ios={"O": io_config}
        )
        
        with patch.object(resolver, "get_platform_config", return_value=platform_config):
            # Act
            result_io = resolver.get_io_config(device_data, "switch", "O")

        # Assert
        assert result_io == io_config

    def test_get_io_config_io_not_found(self, resolver: DeviceResolver):
        """
        测试 get_io_config 当IO不存在时的处理。
        Hypothesis: 不存在的IO应返回 None。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        platform_config = PlatformConfig(
            platform_type="switch", 
            supported=True,
            ios={}
        )
        
        with patch.object(resolver, "get_platform_config", return_value=platform_config):
            # Act
            result_io = resolver.get_io_config(device_data, "switch", "P1")

        # Assert
        assert result_io is None

    def test_get_io_config_platform_not_found(self, resolver: DeviceResolver):
        """
        测试 get_io_config 当平台不存在时的处理。
        Hypothesis: 不存在的平台应返回 None。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        
        with patch.object(resolver, "get_platform_config", return_value=None):
            # Act
            result_io = resolver.get_io_config(device_data, "light", "P1")

        # Assert
        assert result_io is None

    def test_get_supported_platforms_success(self, resolver: DeviceResolver):
        """
        测试 get_supported_platforms 的成功获取。
        Hypothesis: 应返回设备支持的所有平台列表。
        """
        # Arrange
        device_data = create_typed_power_meter_plug().to_dict()
        device_config = DeviceConfig(
            device_type="SL_OE_3C",
            name="Power Meter",
            platforms={
                "switch": PlatformConfig(platform_type="switch", supported=True),
                "sensor": PlatformConfig(platform_type="sensor", supported=True),
            },
        )
        device_config.__post_init__()  # 触发supported_platforms计算
        
        with patch.object(
            resolver, "resolve_device_config",
            return_value=ResolutionResult.success_result(device_config)
        ):
            # Act
            platforms = resolver.get_supported_platforms(device_data)

        # Assert
        assert set(platforms) == {"switch", "sensor"}

    def test_get_supported_platforms_resolve_failure(self, resolver: DeviceResolver):
        """
        测试 get_supported_platforms 当解析失败时的处理。
        Hypothesis: 解析失败时应返回空列表。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        
        with patch.object(
            resolver, "resolve_device_config",
            return_value=ResolutionResult.error_result("Resolve failed")
        ):
            # Act
            platforms = resolver.get_supported_platforms(device_data)

        # Assert
        assert platforms == []


class TestDeviceResolverCacheManagement:
    """DeviceResolver 缓存管理测试套件。"""

    def test_cache_stats_initial_state(self, resolver: DeviceResolver):
        """
        测试缓存统计的初始状态。
        Hypothesis: 新建的resolver应有干净的缓存统计。
        """
        # Act
        stats = resolver.get_cache_stats()

        # Assert
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["errors"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["cache_size"] == 0
        assert stats["total_requests"] == 0

    def test_cache_stats_after_operations(self, resolver: DeviceResolver):
        """
        测试缓存操作后的统计准确性。
        Hypothesis: 缓存统计应准确反映操作历史。
        """
        # Arrange
        device1 = create_typed_smart_plug().to_dict()
        device2 = create_typed_thermostat_panel().to_dict()

        # Act
        resolver.resolve_device_config(device1)  # miss
        resolver.resolve_device_config(device1)  # hit
        resolver.resolve_device_config(device2)  # miss
        
        stats = resolver.get_cache_stats()

        # Assert
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["errors"] == 0
        assert stats["hit_rate"] == 1/3  # 1 hit out of 3 total
        assert stats["cache_size"] == 2
        assert stats["total_requests"] == 3

    def test_cache_clear(self, resolver: DeviceResolver):
        """
        测试缓存清理功能。
        Hypothesis: clear_cache 应重置缓存和统计。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()
        resolver.resolve_device_config(device_data)  # 创建缓存条目

        # Act
        resolver.clear_cache()
        stats_after_clear = resolver.get_cache_stats()

        # Assert
        assert stats_after_clear["hits"] == 0
        assert stats_after_clear["misses"] == 0
        assert stats_after_clear["errors"] == 0
        assert stats_after_clear["cache_size"] == 0
        assert stats_after_clear["hit_rate"] == 0.0

    def test_cache_key_generation_uniqueness(self, resolver: DeviceResolver):
        """
        测试缓存键生成的唯一性。
        Hypothesis: 不同的设备应生成不同的缓存键。
        """
        # Arrange
        device1 = {"agt": "hub1", "me": "dev1", "devtype": "TYPE1"}
        device2 = {"agt": "hub1", "me": "dev2", "devtype": "TYPE1"}
        device3 = {"agt": "hub2", "me": "dev1", "devtype": "TYPE1"}

        # Act
        key1 = resolver._generate_cache_key(device1)
        key2 = resolver._generate_cache_key(device2)
        key3 = resolver._generate_cache_key(device3)

        # Assert
        assert key1 != key2  # 不同me
        assert key1 != key3  # 不同agt
        assert key2 != key3  # 不同agt
        assert key1 == "hub1:dev1:TYPE1"

    def test_cache_key_missing_fields(self, resolver: DeviceResolver):
        """
        测试缓存键生成对缺失字段的处理。
        Hypothesis: 缺失的字段应使用默认值"unknown"。
        """
        # Arrange
        device = {"devtype": "TEST_TYPE"}  # 缺少agt和me

        # Act
        cache_key = resolver._generate_cache_key(device)

        # Assert
        assert cache_key == "unknown:unknown:TEST_TYPE"


class TestDeviceResolverPrivateMethods:
    """DeviceResolver 私有方法测试套件。"""

    def test_convert_to_device_config_basic(self, resolver: DeviceResolver):
        """
        测试基础的设备配置转换。
        Hypothesis: 基本的raw_mapping应被正确转换为DeviceConfig。
        """
        # Arrange
        device = {"devtype": "TEST_TYPE", "name": "Test Device", "me": "test_me"}
        raw_mapping = {
            "switch": {
                "P1": {"description": "Switch 1", "cmd_type": "on"},
                "P2": {"description": "Switch 2", "cmd_type": "off"}
            }
        }

        # Act
        device_config = resolver._convert_to_device_config(device, raw_mapping)

        # Assert
        assert isinstance(device_config, DeviceConfig)
        assert device_config.device_type == "TEST_TYPE"
        assert device_config.name == "Test Device"
        assert "switch" in device_config.platforms
        assert device_config.platforms["switch"].has_io("P1")
        assert device_config.platforms["switch"].has_io("P2")

    def test_convert_to_platform_config_valid_data(self, resolver: DeviceResolver):
        """
        测试有效平台数据的转换。
        Hypothesis: 有效的平台数据应被正确转换为PlatformConfig。
        """
        # Arrange
        platform_data = {
            "P1": {"description": "Test IO", "cmd_type": "toggle"},
            "P2": {"description": "Another IO", "device_class": "switch"}
        }

        # Act
        platform_config = resolver._convert_to_platform_config("switch", platform_data)

        # Assert
        assert isinstance(platform_config, PlatformConfig)
        assert platform_config.platform_type == "switch"
        assert platform_config.supported is True
        assert len(platform_config.ios) == 2
        assert "P1" in platform_config.ios
        assert "P2" in platform_config.ios

    def test_convert_to_platform_config_invalid_data(self, resolver: DeviceResolver):
        """
        测试无效平台数据的处理。
        Hypothesis: 无效的平台数据应返回None。
        """
        # Act
        platform_config = resolver._convert_to_platform_config("switch", "invalid_data")

        # Assert
        assert platform_config is None

    def test_convert_to_io_config_valid_data(self, resolver: DeviceResolver):
        """
        测试有效IO数据的转换。
        Hypothesis: 包含description的IO数据应被正确转换。
        """
        # Arrange
        io_data = {
            "description": "Test IO",
            "cmd_type": "on",
            "idx": 1,
            "device_class": "switch"
        }

        # Act
        io_config = resolver._convert_to_io_config(io_data)

        # Assert
        assert isinstance(io_config, IOConfig)
        assert io_config.description == "Test IO"
        assert io_config.cmd_type == "on"
        assert io_config.idx == 1
        assert io_config.device_class == "switch"

    def test_convert_to_io_config_missing_description(self, resolver: DeviceResolver):
        """
        测试缺少description的IO数据处理。
        Hypothesis: 缺少description的IO数据应返回None。
        """
        # Arrange
        io_data = {"cmd_type": "on", "idx": 1}

        # Act
        io_config = resolver._convert_to_io_config(io_data)

        # Assert
        assert io_config is None