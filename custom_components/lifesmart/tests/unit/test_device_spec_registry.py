"""
DeviceSpecRegistry单元测试

测试Phase 1架构分离中的DeviceSpecRegistry功能：
- 数据加载和验证
- 查询接口
- 缓存机制
- 向后兼容性
- MappingEngine集成

由 @MapleEve 创建，基于架构分离实施计划
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from custom_components.lifesmart.core.config.device_spec_registry import (
    DeviceSpecRegistry,
    DeviceSpecValidator,
    ValidationLevel,
    ValidationResult,
    get_device_spec_registry,
    get_device_spec,
)


class TestDeviceSpecValidator:
    """测试设备规格验证器"""

    def test_validate_valid_device_spec(self):
        """测试验证有效的设备规格"""
        validator = DeviceSpecValidator()

        spec = {
            "name": "测试设备",
            "switch": {
                "P1": {"description": "开关", "rw": "RW", "data_type": "binary_switch"}
            },
        }

        result = validator.validate_device_spec("TEST_DEVICE", spec)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_missing_name_field(self):
        """测试验证缺少name字段的设备"""
        validator = DeviceSpecValidator()

        spec = {"switch": {"P1": {"description": "开关"}}}

        result = validator.validate_device_spec("TEST_DEVICE", spec)

        assert result.is_valid is False
        assert "Missing required field: name" in result.errors

    def test_validate_invalid_rw_permission(self):
        """测试验证无效的读写权限"""
        validator = DeviceSpecValidator()

        spec = {
            "name": "测试设备",
            "switch": {
                "P1": {
                    "description": "开关",
                    "rw": "INVALID",
                    "data_type": "binary_switch",
                }
            },
        }

        result = validator.validate_device_spec("TEST_DEVICE", spec)

        assert result.is_valid is False
        assert any("Invalid rw permission" in error for error in result.errors)


class TestDeviceSpecRegistry:
    """测试设备规格注册表"""

    def test_registry_initialization(self):
        """测试注册表初始化"""
        registry = DeviceSpecRegistry()

        assert registry._loaded is False
        assert len(registry._specs) == 0
        assert len(registry._cache) == 0
        assert registry._validation_level == ValidationLevel.LENIENT

    def test_load_specs_success(self):
        """测试成功加载设备规格"""
        registry = DeviceSpecRegistry()

        # 第一次加载
        registry.load_specs()

        assert registry._loaded is True
        assert registry.get_device_count() > 0

        # 再次加载不应重复
        initial_load_time = registry._stats["load_time"]
        registry.load_specs()
        assert registry._stats["load_time"] == initial_load_time

        # 强制重新加载
        registry.load_specs(force_reload=True)
        assert registry._stats["load_time"] != initial_load_time

    def test_get_device_spec(self):
        """测试获取设备规格"""
        registry = DeviceSpecRegistry()

        # 测试存在的设备
        spec = registry.get_device_spec("SL_OL")
        assert spec is not None
        assert "name" in spec

        # 测试不存在的设备
        spec = registry.get_device_spec("NON_EXISTENT")
        assert spec == {}

    def test_has_device_spec(self):
        """测试检查设备规格是否存在"""
        registry = DeviceSpecRegistry()

        assert registry.has_device_spec("SL_OL") is True
        assert registry.has_device_spec("NON_EXISTENT") is False

    def test_list_device_types(self):
        """测试获取所有设备类型列表"""
        registry = DeviceSpecRegistry()

        device_types = registry.list_device_types()

        assert isinstance(device_types, list)
        assert len(device_types) > 0
        assert "SL_OL" in device_types

    def test_find_by_platform(self):
        """测试根据平台查找设备"""
        registry = DeviceSpecRegistry()

        switch_devices = registry.find_by_platform("switch")
        sensor_devices = registry.find_by_platform("sensor")

        assert isinstance(switch_devices, list)
        assert isinstance(sensor_devices, list)
        assert len(switch_devices) > 0
        assert len(sensor_devices) > 0

        # 测试缓存
        switch_devices_cached = registry.find_by_platform("switch")
        assert switch_devices == switch_devices_cached

    def test_find_by_capability(self):
        """测试根据能力查找设备"""
        registry = DeviceSpecRegistry()

        temperature_devices = registry.find_by_capability("temperature")

        assert isinstance(temperature_devices, list)
        # 根据实际数据结构，可能有温度传感器

        # 测试缓存
        temperature_devices_cached = registry.find_by_capability("temperature")
        assert temperature_devices == temperature_devices_cached

    def test_get_spec_metadata(self):
        """测试获取设备规格元数据"""
        registry = DeviceSpecRegistry()

        metadata = registry.get_spec_metadata("SL_OL")

        assert isinstance(metadata, dict)
        assert metadata["device_type"] == "SL_OL"
        assert "name" in metadata
        assert "platforms" in metadata
        assert "io_count" in metadata

        # 测试不存在的设备
        metadata = registry.get_spec_metadata("NON_EXISTENT")
        assert metadata == {}

    def test_validation_functionality(self):
        """测试验证功能"""
        registry = DeviceSpecRegistry()

        # 测试验证已加载的设备
        is_valid = registry.validate_spec("SL_OL", registry.get_device_spec("SL_OL"))
        assert isinstance(is_valid, bool)

        # 测试获取验证错误
        errors = registry.get_validation_errors("SL_OL")
        assert isinstance(errors, list)

        # 测试不存在的设备
        errors = registry.get_validation_errors("NON_EXISTENT")
        assert len(errors) > 0
        assert "not found" in errors[0]

    def test_get_stats(self):
        """测试获取统计信息"""
        registry = DeviceSpecRegistry()

        stats = registry.get_stats()

        assert isinstance(stats, dict)
        assert "total_devices" in stats
        assert "platforms" in stats
        assert "load_time" in stats
        assert "validation_errors" in stats
        assert "validation_warnings" in stats
        assert "cache_size" in stats
        assert "loaded" in stats

        assert stats["loaded"] is True
        assert stats["total_devices"] > 0
        assert isinstance(stats["platforms"], list)

    def test_cache_functionality(self):
        """测试缓存功能"""
        registry = DeviceSpecRegistry()

        # 确保缓存为空
        registry.clear_cache()
        assert len(registry._cache) == 0

        # 进行查询，应该填充缓存
        spec = registry.get_device_spec("SL_OL")
        assert len(registry._cache) > 0

        # 再次查询，应该从缓存获取
        spec_cached = registry.get_device_spec("SL_OL")
        assert spec == spec_cached

        # 清理缓存
        registry.clear_cache()
        assert len(registry._cache) == 0


class TestBackwardCompatibility:
    """测试向后兼容性"""

    def test_get_device_spec_function(self):
        """测试便捷函数get_device_spec"""
        spec = get_device_spec("SL_OL")

        assert spec is not None
        assert isinstance(spec, dict)
        assert "name" in spec

    def test_get_device_spec_registry_function(self):
        """测试获取全局注册表实例"""
        registry1 = get_device_spec_registry()
        registry2 = get_device_spec_registry()

        # 应该返回同一个实例（单例模式）
        assert registry1 is registry2

        assert registry1.get_device_count() > 0


class TestMappingEngineIntegration:
    """测试与MappingEngine的集成"""

    def test_mapping_engine_with_registry(self):
        """测试MappingEngine使用Registry"""
        from custom_components.lifesmart.core.resolver.device_resolver import (
            DeviceResolver,
        )

        # 创建自定义Registry
        registry = DeviceSpecRegistry()

        # 创建使用Registry的DeviceResolver
        resolver = DeviceResolver(registry)

        # 验证集成
        assert resolver.device_registry is registry

        # 测试设备映射解析
        test_device = {"devtype": "SL_OL", "data": {"O": {"val": 1, "type": 1}}}

        result = resolver.resolve_device_config(test_device)
        assert result is not None
        assert result.success

    def test_device_resolver_default_registry(self):
        """测试DeviceResolver使用默认Registry"""
        from custom_components.lifesmart.core.resolver.device_resolver import (
            get_device_resolver,
        )

        # 不传入Registry，应该使用默认的
        resolver = get_device_resolver()

        assert resolver.device_registry is not None
        assert isinstance(resolver.device_registry, DeviceSpecRegistry)

        # 测试功能正常
        test_device = {"devtype": "SL_OL", "data": {"O": {"val": 1, "type": 1}}}

        result = resolver.resolve_device_config(test_device)
        assert result is not None
        assert result.success


class TestValidationLevels:
    """测试不同验证级别"""

    def test_strict_validation(self):
        """测试严格验证模式"""
        with patch(
            "custom_components.lifesmart.core.config.device_specs._RAW_DEVICE_DATA",
            {
                "INVALID_DEVICE": {
                    # 缺少name字段，应该被拒绝
                    "switch": {"P1": {"description": "测试"}}
                },
                "VALID_DEVICE": {
                    "name": "有效设备",
                    "switch": {"P1": {"description": "测试", "rw": "RW"}},
                },
            },
        ):
            registry = DeviceSpecRegistry(ValidationLevel.STRICT)
            registry.load_specs()

            # 严格模式下，无效设备应该被拒绝
            assert not registry.has_device_spec("INVALID_DEVICE")
            assert registry.has_device_spec("VALID_DEVICE")

    def test_lenient_validation(self):
        """测试宽松验证模式"""
        with patch(
            "custom_components.lifesmart.core.config.device_specs._RAW_DEVICE_DATA",
            {
                "INVALID_DEVICE": {
                    # 缺少name字段，但在宽松模式下会被接受
                    "switch": {"P1": {"description": "测试"}}
                }
            },
        ):
            registry = DeviceSpecRegistry(ValidationLevel.LENIENT)
            registry.load_specs()

            # 宽松模式下，无效设备也会被接受
            assert registry.has_device_spec("INVALID_DEVICE")

            # 但验证错误仍会被记录
            stats = registry.get_stats()
            assert stats["validation_errors"] > 0

    def test_no_validation(self):
        """测试无验证模式"""
        with patch(
            "custom_components.lifesmart.core.config.device_specs._RAW_DEVICE_DATA",
            {
                "ANY_DEVICE": {
                    # 任何数据都会被接受
                    "invalid_structure": "whatever"
                }
            },
        ):
            registry = DeviceSpecRegistry(ValidationLevel.NONE)
            registry.load_specs()

            assert registry.has_device_spec("ANY_DEVICE")

            # 无验证模式下，不会有验证错误
            stats = registry.get_stats()
            assert stats["validation_errors"] == 0
            assert stats["validation_warnings"] == 0


# 性能测试
class TestPerformance:
    """测试性能相关功能"""

    def test_load_performance(self):
        """测试加载性能"""
        registry = DeviceSpecRegistry()

        start_time = time.time()
        registry.load_specs()
        load_time = time.time() - start_time

        # 加载应该在合理时间内完成（<1秒）
        assert load_time < 1.0

        stats = registry.get_stats()
        assert stats["load_time"] is not None
        assert stats["load_time"] > 0

    def test_query_performance(self):
        """测试查询性能"""
        registry = DeviceSpecRegistry()
        registry.load_specs()

        # 测试单次查询性能
        start_time = time.time()
        spec = registry.get_device_spec("SL_OL")
        query_time = time.time() - start_time

        # 单次查询应该很快（<10ms）
        assert query_time < 0.01

        # 测试批量查询性能
        device_types = registry.list_device_types()[:10]  # 取前10个

        start_time = time.time()
        for device_type in device_types:
            registry.get_device_spec(device_type)
        batch_query_time = time.time() - start_time

        # 批量查询应该很快
        assert batch_query_time < 0.1
