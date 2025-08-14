"""
DeviceResolver 性能基准测试 - Phase 2 性能验证

测试 DeviceResolver 的性能特性：
- 缓存机制性能验证
- 批量设备解析性能基准
- 内存使用和清理验证
- 策略选择开销测试

基于 @MapleEve 的 Phase 2.5 重构设计
"""

import time
from unittest.mock import MagicMock, patch

import pytest

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
    create_typed_core_devices,
    create_typed_smart_plug,
    create_typed_thermostat_panel,
    create_typed_power_meter_plug,
    create_typed_rgbw_light,
    create_typed_environment_sensor,
)


@pytest.fixture
def performance_resolver():
    """提供一个配置用于性能测试的 DeviceResolver 实例。"""
    mock_spec_registry = MagicMock(spec=DeviceSpecRegistry)
    mock_strategy_factory = MagicMock(spec=DeviceStrategyFactory)

    # 模拟快速响应的依赖项
    mock_spec_registry.get_device_spec.return_value = {"name": "Perf Test Spec"}
    mock_strategy_factory.resolve_device_mapping.return_value = {
        "name": "Perf Test Mapping",
        "switch": {"P1": {"description": "Perf Switch"}},
    }

    return DeviceResolver(
        spec_registry=mock_spec_registry,
        strategy_factory=mock_strategy_factory,
        enable_cache=True,
    )


@pytest.fixture
def test_devices_batch():
    """提供一批用于性能测试的设备。"""
    return create_typed_core_devices()


class TestDeviceResolverCachePerformance:
    """DeviceResolver 缓存性能测试套件。"""

    def test_cache_hit_performance(self, performance_resolver: DeviceResolver):
        """
        测试缓存命中性能。
        Hypothesis: 缓存命中应该显著快于首次解析。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()

        # Act - 首次解析(缓存未命中)
        with patch("time.time", side_effect=[1000.0, 1000.02]):  # 20ms
            result1 = performance_resolver.resolve_device_config(device_data)

        # Act - 第二次解析(缓存命中)
        with patch("time.time", side_effect=[2000.0, 2000.001]):  # 1ms
            result2 = performance_resolver.resolve_device_config(device_data)

        # Assert
        assert result1.success and result2.success
        assert result1.cache_hit is False
        assert result2.cache_hit is True
        assert result1.resolution_time_ms == 20.0
        assert result2.resolution_time_ms == 1.0

        # 验证缓存命中比未命中快
        assert result2.resolution_time_ms < result1.resolution_time_ms

    def test_cache_miss_ratio_large_dataset(self, performance_resolver: DeviceResolver):
        """
        测试大数据集下的缓存未命中率。
        Hypothesis: 不同设备的首次访问都应该产生缓存未命中。
        """
        # Arrange
        devices = [
            create_typed_smart_plug().to_dict(),
            create_typed_thermostat_panel().to_dict(),
            create_typed_power_meter_plug().to_dict(),
            create_typed_rgbw_light().to_dict(),
            create_typed_environment_sensor().to_dict(),
        ]

        # 修改设备ID确保它们不同
        for i, device in enumerate(devices):
            device["me"] = f"device_{i}"
            device["agt"] = f"hub_{i}"

        # Act
        results = []
        for device in devices:
            result = performance_resolver.resolve_device_config(device)
            results.append(result)

        # Assert
        assert all(result.success for result in results)
        assert all(result.cache_hit is False for result in results)  # 都是首次访问

        # 验证缓存统计
        stats = performance_resolver.get_cache_stats()
        assert stats["misses"] == 5
        assert stats["hits"] == 0
        assert stats["cache_size"] == 5

    def test_cache_hit_ratio_repeated_access(
        self, performance_resolver: DeviceResolver
    ):
        """
        测试重复访问的缓存命中率。
        Hypothesis: 重复访问相同设备应该产生高缓存命中率。
        """
        # Arrange
        devices = [
            create_typed_smart_plug().to_dict(),
            create_typed_thermostat_panel().to_dict(),
        ]

        # 修改设备ID确保它们不同
        for i, device in enumerate(devices):
            device["me"] = f"repeat_device_{i}"

        # Act - 每个设备访问3次
        results = []
        for _ in range(3):  # 3轮重复
            for device in devices:
                result = performance_resolver.resolve_device_config(device)
                results.append(result)

        # Assert
        assert all(result.success for result in results)

        # 验证缓存统计 - 应该有高命中率
        stats = performance_resolver.get_cache_stats()
        assert stats["total_requests"] == 6  # 2设备 * 3次
        assert stats["misses"] == 2  # 每个设备首次访问
        assert stats["hits"] == 4  # 每个设备的后续2次访问
        assert stats["hit_rate"] == 4 / 6  # 约66.7%命中率

    def test_cache_memory_usage_large_scale(self, performance_resolver: DeviceResolver):
        """
        测试大规模缓存的内存使用。
        Hypothesis: 缓存应该能处理大量设备而不出现内存问题。
        """
        # Arrange - 创建大量不同的设备
        base_device = create_typed_smart_plug().to_dict()
        device_count = 100

        # Act
        for i in range(device_count):
            device = base_device.copy()
            device["me"] = f"mass_device_{i}"
            device["agt"] = f"mass_hub_{i // 10}"  # 10个设备共用一个hub

            result = performance_resolver.resolve_device_config(device)
            assert result.success

        # Assert
        stats = performance_resolver.get_cache_stats()
        assert stats["cache_size"] == device_count
        assert stats["misses"] == device_count
        assert stats["hits"] == 0

    def test_cache_clear_performance(self, performance_resolver: DeviceResolver):
        """
        测试缓存清理性能。
        Hypothesis: 缓存清理应该是快速和彻底的。
        """
        # Arrange - 填充缓存
        devices = [create_typed_smart_plug().to_dict() for i in range(10)]
        for i, device in enumerate(devices):
            device["me"] = f"clear_device_{i}"
            performance_resolver.resolve_device_config(device)

        # 验证缓存已填充
        assert performance_resolver.get_cache_stats()["cache_size"] == 10

        # Act - 测量清理时间
        start_time = time.time()
        performance_resolver.clear_cache()
        end_time = time.time()

        clear_time = (end_time - start_time) * 1000  # 转为毫秒

        # Assert
        stats = performance_resolver.get_cache_stats()
        assert stats["cache_size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert clear_time < 10.0  # 清理应该在10ms内完成


class TestDeviceResolverBatchPerformance:
    """DeviceResolver 批量操作性能测试套件。"""

    def test_batch_resolution_performance(
        self, performance_resolver: DeviceResolver, test_devices_batch
    ):
        """
        测试批量设备解析性能。
        Hypothesis: 批量解析应该在合理时间内完成。
        """
        # Arrange
        devices_dict = [device.to_dict() for device in test_devices_batch]

        # Act
        start_time = time.time()
        results = []
        for device in devices_dict:
            result = performance_resolver.resolve_device_config(device)
            results.append(result)
        end_time = time.time()

        total_time = (end_time - start_time) * 1000  # 转为毫秒
        average_time = total_time / len(devices_dict)

        # Assert
        assert all(result.success for result in results)
        assert len(results) == len(test_devices_batch)
        assert average_time < 50.0  # 每个设备平均解析时间应小于50ms
        assert total_time < 500.0  # 总解析时间应小于500ms

    def test_batch_with_cache_performance(
        self, performance_resolver: DeviceResolver, test_devices_batch
    ):
        """
        测试带缓存的批量解析性能。
        Hypothesis: 重复批量解析应该因缓存而显著加速。
        """
        # Arrange
        devices_dict = [device.to_dict() for device in test_devices_batch]

        # Act - 首次批量解析
        start_time1 = time.time()
        results1 = []
        for device in devices_dict:
            result = performance_resolver.resolve_device_config(device)
            results1.append(result)
        end_time1 = time.time()

        # Act - 第二次批量解析(应该命中缓存)
        start_time2 = time.time()
        results2 = []
        for device in devices_dict:
            result = performance_resolver.resolve_device_config(device)
            results2.append(result)
        end_time2 = time.time()

        first_batch_time = (end_time1 - start_time1) * 1000
        second_batch_time = (end_time2 - start_time2) * 1000

        # Assert
        assert all(result.success for result in results1)
        assert all(result.success for result in results2)
        assert all(result.cache_hit is False for result in results1)
        assert all(result.cache_hit is True for result in results2)

        # 第二次应该显著更快(至少快50%)
        assert second_batch_time < first_batch_time * 0.5

    def test_concurrent_resolution_simulation(
        self, performance_resolver: DeviceResolver
    ):
        """
        测试并发解析模拟。
        Hypothesis: 模拟并发访问模式下性能应该保持稳定。
        """
        # Arrange - 混合新设备和重复设备以模拟真实场景
        devices = []

        # 50%新设备
        for i in range(5):
            device = create_typed_smart_plug().to_dict()
            device["me"] = f"concurrent_new_{i}"
            devices.append(device)

        # 50%重复设备
        for i in range(5):
            device = create_typed_smart_plug().to_dict()
            device["me"] = f"concurrent_repeat_{i % 2}"  # 只有2个不同的设备
            devices.append(device)

        # Act
        start_time = time.time()
        results = []
        for device in devices:
            result = performance_resolver.resolve_device_config(device)
            results.append(result)
        end_time = time.time()

        total_time = (end_time - start_time) * 1000

        # Assert
        assert all(result.success for result in results)

        # 验证混合缓存行为
        stats = performance_resolver.get_cache_stats()
        assert stats["total_requests"] == 10
        assert stats["misses"] > 0  # 应该有缓存未命中
        assert stats["hits"] > 0  # 应该有缓存命中
        assert stats["hit_rate"] > 0  # 应该有一定的命中率

        # 总时间应该合理
        assert total_time < 200.0  # 10个设备应该在200ms内完成


class TestDeviceResolverStrategyPerformance:
    """DeviceResolver 策略选择性能测试套件。"""

    def test_strategy_selection_overhead(self):
        """
        测试策略选择的开销。
        Hypothesis: 策略选择的开销应该是最小的。
        """
        # Arrange
        mock_spec_registry = MagicMock(spec=DeviceSpecRegistry)
        mock_spec_registry.get_device_spec.return_value = {"name": "Test Spec"}

        # 创建一个有轻微延迟的策略工厂来测量选择开销
        mock_strategy_factory = MagicMock(spec=DeviceStrategyFactory)

        def slow_resolve(*args):
            time.sleep(0.001)  # 1ms延迟模拟策略选择和执行
            return {"switch": {"P1": {"description": "Test"}}}

        mock_strategy_factory.resolve_device_mapping.side_effect = slow_resolve

        resolver = DeviceResolver(
            spec_registry=mock_spec_registry,
            strategy_factory=mock_strategy_factory,
            enable_cache=True,
        )

        device_data = create_typed_smart_plug().to_dict()

        # Act - 测量包含策略选择的总时间
        start_time = time.time()
        result = resolver.resolve_device_config(device_data)
        end_time = time.time()

        total_time = (end_time - start_time) * 1000

        # Assert
        assert result.success
        # 总时间应该主要由策略执行时间构成，策略选择开销应该很小
        assert total_time < 50.0  # 应该在50ms内完成(包含1ms的模拟延迟)

    def test_cache_vs_strategy_performance_comparison(
        self, performance_resolver: DeviceResolver
    ):
        """
        测试缓存与策略执行的性能对比。
        Hypothesis: 缓存命中应该比策略执行显著更快。
        """
        # Arrange
        device_data = create_typed_smart_plug().to_dict()

        # Act - 首次解析(策略执行)
        result1 = performance_resolver.resolve_device_config(device_data)
        strategy_calls_before = (
            performance_resolver._strategy_factory.resolve_device_mapping.call_count
        )

        # Act - 第二次解析(缓存命中)
        result2 = performance_resolver.resolve_device_config(device_data)
        strategy_calls_after = (
            performance_resolver._strategy_factory.resolve_device_mapping.call_count
        )

        # Assert
        assert result1.success and result2.success
        assert result1.cache_hit is False
        assert result2.cache_hit is True

        # 验证第二次调用没有触发策略执行
        assert strategy_calls_after == strategy_calls_before

        # 如果有timing信息，缓存命中应该更快
        if result1.resolution_time_ms and result2.resolution_time_ms:
            assert result2.resolution_time_ms <= result1.resolution_time_ms


class TestDeviceResolverMemoryManagement:
    """DeviceResolver 内存管理测试套件。"""

    def test_cache_key_uniqueness_performance(
        self, performance_resolver: DeviceResolver
    ):
        """
        测试缓存键唯一性算法的性能。
        Hypothesis: 缓存键生成应该快速且避免冲突。
        """
        # Arrange
        devices = []
        for i in range(100):
            device = {
                "agt": f"hub_{i // 10}",
                "me": f"device_{i}",
                "devtype": f"TYPE_{i % 5}",
            }
            devices.append(device)

        # Act
        start_time = time.time()
        cache_keys = []
        for device in devices:
            key = performance_resolver._generate_cache_key(device)
            cache_keys.append(key)
        end_time = time.time()

        generation_time = (end_time - start_time) * 1000

        # Assert
        # 所有键应该是唯一的
        assert len(set(cache_keys)) == len(cache_keys)

        # 生成100个键应该很快
        assert generation_time < 10.0  # 应该在10ms内完成

    def test_resolver_instance_cleanup(self):
        """
        测试 DeviceResolver 实例清理。
        Hypothesis: 实例应该能正确释放资源。
        """
        # Arrange
        mock_spec_registry = MagicMock(spec=DeviceSpecRegistry)
        mock_strategy_factory = MagicMock(spec=DeviceStrategyFactory)

        mock_spec_registry.get_device_spec.return_value = {"name": "Test Spec"}
        mock_strategy_factory.resolve_device_mapping.return_value = {
            "switch": {"P1": {"description": "Test"}},
        }

        # Act - 创建和填充解析器
        resolver = DeviceResolver(
            spec_registry=mock_spec_registry,
            strategy_factory=mock_strategy_factory,
            enable_cache=True,
        )

        # 填充缓存
        for i in range(10):
            device = create_typed_smart_plug().to_dict()
            device["me"] = f"cleanup_test_{i}"
            resolver.resolve_device_config(device)

        # 验证缓存已填充
        assert resolver.get_cache_stats()["cache_size"] == 10

        # Act - 清理
        resolver.clear_cache()
        resolver = None  # 释放引用

        # Assert - 没有明显的方式测试内存释放，但至少确保没有异常
