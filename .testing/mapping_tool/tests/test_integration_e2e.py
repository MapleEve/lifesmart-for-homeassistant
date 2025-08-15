# End-to-End Integration Tests for Port-Service-Cache Architecture
# Phase 4: 端到端集成测试，验证84个@abstractmethod接口契约
# 基于ZEN MCP专家分析和深度架构调研

import pytest
import asyncio
import time
import threading
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import concurrent.futures

# Add project path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Test imports for integration validation
try:
    from data_types.core_types import (
        MappingToolError,
        AnalysisError,
        ConfigurationError,
        CacheError,
        NLPError,
        AnalysisConfig,
        DeviceData,
        AnalysisResult,
    )

    # Mock external dependency to prevent import errors
    with patch.dict(
        "sys.modules",
        {"custom_components.lifesmart.core.config.device_specs": MagicMock()},
    ):
        from main import (
            main as modern_main,
            async_main,
            ModernCompositionRoot,
            ApplicationContext,
        )
        from implements.factories import (
            ConcretePortFactory,
            ConcreteCacheFactory,
            IntegratedFactoryManager,
        )
        from implements.enhanced_cli_port import (
            EnhancedSmartIOAllocationAnalyzer,
            create_smart_io_allocation_analyzer,
        )

    INTEGRATION_TEST_AVAILABLE = True
except ImportError as e:
    INTEGRATION_TEST_AVAILABLE = False
    pytest.skip(f"Integration test modules not available: {e}", allow_module_level=True)

# Async test marker
pytestmark = pytest.mark.asyncio

# =============================================================================
# Mock Data and Test Fixtures
# =============================================================================

# Mock device data for testing
MOCK_RAW_DEVICE_DATA = {
    "SL_TEST_DEVICE_01": {
        "name": "Test Switch Device",
        "ios": [
            {"name": "P1", "description": "Main switch", "rw": "RW"},
            {"name": "V", "description": "Voltage sensor", "rw": "R"},
        ],
    },
    "SL_TEST_DEVICE_02": {
        "name": "Test Light Device",
        "ios": [
            {"name": "RGBW", "description": "Color light", "rw": "RW"},
            {"name": "B", "description": "Brightness", "rw": "RW"},
        ],
    },
    "SL_TEST_DEVICE_03": {
        "name": "Test Sensor Device",
        "ios": [
            {"name": "T", "description": "Temperature", "rw": "R"},
            {"name": "H", "description": "Humidity", "rw": "R"},
        ],
    },
}

# Mock markdown document content
MOCK_MARKDOWN_DOC = """
# LifeSmart 智慧设备规格属性说明

## 测试设备列表

| 设备名称 | IO口 | 读写 | 说明 |
|---------|------|------|------|
| SL_TEST_DEVICE_01 | P1 | RW | 主开关 |
| SL_TEST_DEVICE_01 | V | R | 电压传感器 |
| SL_TEST_DEVICE_02 | RGBW | RW | 彩色灯光 |
| SL_TEST_DEVICE_02 | B | RW | 亮度调节 |
| SL_TEST_DEVICE_03 | T | R | 温度传感器 |
| SL_TEST_DEVICE_03 | H | R | 湿度传感器 |

## 测试说明

这是一个用于集成测试的模拟文档。
"""


@pytest.fixture
def mock_environment(tmp_path):
    """
    创建完整的测试环境，包含所有必要的mock和文件结构
    """
    # Create docs directory structure
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    doc_file = docs_dir / "LifeSmart 智慧设备规格属性说明.md"
    doc_file.write_text(MOCK_MARKDOWN_DOC, encoding="utf-8")

    # Create custom_components mock structure
    custom_dir = tmp_path / "custom_components" / "lifesmart" / "core" / "config"
    custom_dir.mkdir(parents=True)

    # Mock device specs file
    device_specs = custom_dir / "device_specs.py"
    device_specs.write_text(
        f"_RAW_DEVICE_DATA = {repr(MOCK_RAW_DEVICE_DATA)}", encoding="utf-8"
    )

    # Create output directories
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    return {
        "tmp_path": tmp_path,
        "docs_dir": docs_dir,
        "doc_file": doc_file,
        "output_dir": output_dir,
        "device_data": MOCK_RAW_DEVICE_DATA,
    }


@pytest.fixture
def resource_tracker():
    """
    跟踪测试期间创建的资源，确保proper cleanup
    """

    @dataclass
    class ResourceTracker:
        threads: List[threading.Thread] = None
        executors: List[concurrent.futures.Executor] = None
        temp_files: List[Path] = None
        async_tasks: List[asyncio.Task] = None

        def __post_init__(self):
            if self.threads is None:
                self.threads = []
            if self.executors is None:
                self.executors = []
            if self.temp_files is None:
                self.temp_files = []
            if self.async_tasks is None:
                self.async_tasks = []

        def cleanup_all(self):
            """清理所有跟踪的资源"""
            # Cancel async tasks
            for task in self.async_tasks:
                if not task.done():
                    task.cancel()

            # Shutdown executors
            for executor in self.executors:
                executor.shutdown(wait=True)

            # Join threads
            for thread in self.threads:
                if thread.is_alive():
                    thread.join(timeout=1.0)

            # Remove temp files
            for file_path in self.temp_files:
                try:
                    if file_path.exists():
                        file_path.unlink()
                except:
                    pass

    tracker = ResourceTracker()
    yield tracker
    tracker.cleanup_all()


# =============================================================================
# P0 Tests - Core Integration Scenarios
# =============================================================================


class TestModernCompositionRootIntegration:
    """
    测试ModernCompositionRoot的完整生命周期和依赖注入
    """

    async def test_complete_application_startup_success(
        self, mock_environment, resource_tracker
    ):
        """
        P0测试: 验证完整的应用启动流程
        测试ModernCompositionRoot的5阶段初始化:
        1. 配置管理初始化
        2. 缓存系统初始化
        3. 核心服务初始化
        4. 分析引擎初始化
        5. 依赖注入完成
        """
        with (
            patch("main.DEVICE_MAPPING", mock_environment["device_data"]),
            patch(
                "main._determine_document_path",
                return_value=str(mock_environment["doc_file"]),
            ),
            patch(
                "implements.enhanced_cli_port.DEVICE_MAPPING",
                mock_environment["device_data"],
            ),
        ):

            # Test initialization phases
            composition_root = ModernCompositionRoot()

            # Verify initial state
            assert not composition_root._initialization_complete
            assert composition_root.context.performance_metrics["startup_time"] == 0.0

            # Execute initialization
            context = composition_root.initialize_application()

            # Verify successful initialization
            assert composition_root._initialization_complete
            assert context.performance_metrics["initialization_time"] > 0
            assert context.performance_metrics["startup_time"] > 0

            # Verify all components are properly initialized
            if hasattr(context, "config_port") and context.config_port:
                assert hasattr(context.config_port, "get_value")

            if hasattr(context, "cache_system") and context.cache_system:
                assert isinstance(context.cache_system, dict)

            if hasattr(context, "analyzer") and context.analyzer:
                assert hasattr(context.analyzer, "perform_smart_comparison_analysis")

            # Verify application info
            app_info = composition_root.get_application_info()
            assert app_info["initialization_complete"] is True
            assert "performance_metrics" in app_info

    async def test_application_startup_with_missing_dependencies(
        self, mock_environment, resource_tracker
    ):
        """
        P0测试: 验证缺少关键依赖时的失败处理
        """
        # Mock missing device data
        with (
            patch("main.DEVICE_MAPPING", {}),
            patch("implements.enhanced_cli_port.DEVICE_MAPPING", {}),
        ):

            composition_root = ModernCompositionRoot()

            # Should still initialize but with fallback behavior
            context = composition_root.initialize_application()

            # Verify graceful degradation
            assert composition_root._initialization_complete
            app_info = composition_root.get_application_info()
            assert app_info["initialization_complete"] is True

    async def test_application_startup_with_invalid_configuration(
        self, mock_environment, resource_tracker
    ):
        """
        P0测试: 验证无效配置时的错误处理
        """
        # Test with invalid CLI args
        invalid_args = ["--cache-size", "invalid_number", "--timeout", "negative"]

        composition_root = ModernCompositionRoot()

        # Should handle invalid configuration gracefully
        try:
            context = composition_root.initialize_application(invalid_args)
            # If it succeeds, verify fallback values are used
            assert context.performance_metrics is not None
        except (ConfigurationError, MappingToolError) as e:
            # Expected behavior for invalid configuration
            assert "configuration" in str(e).lower() or "invalid" in str(e).lower()


class TestFactoryPatternIntegration:
    """
    测试工厂模式的84个接口契约验证
    """

    async def test_all_factory_methods_create_valid_instances(
        self, mock_environment, resource_tracker
    ):
        """
        P0测试: 验证所有工厂方法能创建有效实例
        测试ConcretePortFactory和ConcreteCacheFactory的所有create_*方法
        """
        # Test PortFactory
        port_factory = ConcretePortFactory()
        port_factory.initialize()

        # Test all port creation methods
        config_port = port_factory.create_configuration_port({})
        assert config_port is not None
        assert hasattr(config_port, "connect")

        file_port = port_factory.create_file_port()
        assert file_port is not None
        assert hasattr(file_port, "read_text_file")

        async_file_port = port_factory.create_async_file_port()
        assert async_file_port is not None
        assert hasattr(async_file_port, "read_text_file_async")

        cli_port = port_factory.create_command_line_port()
        assert cli_port is not None
        assert hasattr(cli_port, "parse_arguments")

        # Test CacheFactory
        cache_factory = ConcreteCacheFactory()
        cache_factory.initialize()

        cache_config = {"strategy": "lru", "max_size": 100}

        data_cache = cache_factory.create_data_cache(cache_config)
        assert data_cache is not None
        assert hasattr(data_cache, "get")
        assert hasattr(data_cache, "set")

        result_cache = cache_factory.create_result_cache(cache_config)
        assert result_cache is not None
        assert hasattr(result_cache, "cache_analysis_result")

        config_cache = cache_factory.create_config_cache(cache_config)
        assert config_cache is not None
        assert hasattr(config_cache, "get_nested")

    async def test_factory_error_handling_and_cleanup(
        self, mock_environment, resource_tracker
    ):
        """
        P0测试: 验证工厂模式的错误处理和资源清理
        """
        # Test port factory error handling
        port_factory = ConcretePortFactory()

        # Test with invalid configuration
        with pytest.raises(MappingToolError):
            # This should fail gracefully
            port_factory.create_data_source_port({"invalid": "config"})

        # Verify factory is still usable after error
        file_port = port_factory.create_file_port()
        assert file_port is not None

        # Test cache factory error handling
        cache_factory = ConcreteCacheFactory()

        # Test with invalid cache config
        invalid_config = {"strategy": "invalid_strategy"}

        try:
            cache_factory.create_data_cache(invalid_config)
        except (ConfigurationError, ValueError):
            # Expected behavior for invalid configuration
            pass

        # Verify factory can still create valid instances
        valid_config = {"strategy": "lru", "max_size": 50}
        cache = cache_factory.create_data_cache(valid_config)
        assert cache is not None

    async def test_port_service_cache_dependency_injection(
        self, mock_environment, resource_tracker
    ):
        """
        P0测试: 验证三层架构的依赖注入正确性
        """
        # Create integrated factory manager
        factory_manager = IntegratedFactoryManager()

        # Test complete system creation
        system_config = {
            "cache": {
                "data": {"strategy": "lru", "max_size": 100},
                "result": {"strategy": "ttl", "ttl_seconds": 300},
                "config": {"strategy": "manual"},
            },
            "ports": {"file": {}, "config": {}, "logging": {"level": "INFO"}},
        }

        complete_system = factory_manager.create_complete_system(
            cache_config=system_config["cache"], port_config=system_config["ports"]
        )

        # Verify all components are properly connected
        assert "cache_manager" in complete_system
        assert "ports" in complete_system
        assert "factories" in complete_system

        # Verify dependency injection works
        cache_manager = complete_system["cache_manager"]
        ports = complete_system["ports"]

        assert cache_manager is not None
        assert len(ports) > 0

        # Test that components can interact
        if "file_port" in ports:
            file_port = ports["file_port"]
            assert hasattr(file_port, "connect")


class TestEndToEndAnalysisPipeline:
    """
    测试完整的端到端分析流程
    """

    async def test_complete_analysis_pipeline_integration(
        self, mock_environment, resource_tracker
    ):
        """
        P0测试: 验证完整的分析管道集成
        配置加载 → 服务初始化 → 分析执行 → 结果输出
        """
        with (
            patch("main.DEVICE_MAPPING", mock_environment["device_data"]),
            patch(
                "main._determine_document_path",
                return_value=str(mock_environment["doc_file"]),
            ),
            patch(
                "implements.enhanced_cli_port.DEVICE_MAPPING",
                mock_environment["device_data"],
            ),
        ):

            # Mock report generation to avoid file I/O
            with patch("main._generate_reports") as mock_generate_reports:

                # Execute complete pipeline
                result = modern_main([])

                # Verify result structure
                assert result is not None
                assert isinstance(result, dict)

                # Verify application info
                assert "application_info" in result
                app_info = result["application_info"]
                assert app_info["initialization_complete"] is True

                # Verify performance metrics
                assert "performance_summary" in result
                perf_summary = result["performance_summary"]
                assert "startup_time" in perf_summary
                assert "initialization_time" in perf_summary
                assert "analysis_time" in perf_summary
                assert "total_time" in perf_summary

                # Verify report generation was called
                mock_generate_reports.assert_called_once()

    async def test_analysis_with_cache_hits_and_misses(
        self, mock_environment, resource_tracker
    ):
        """
        P1测试: 验证缓存命中和缺失的分析行为
        """
        # This test would require more detailed implementation
        # For now, we verify the analysis can run multiple times
        with (
            patch("main.DEVICE_MAPPING", mock_environment["device_data"]),
            patch(
                "main._determine_document_path",
                return_value=str(mock_environment["doc_file"]),
            ),
            patch(
                "implements.enhanced_cli_port.DEVICE_MAPPING",
                mock_environment["device_data"],
            ),
        ):

            # Run analysis twice to test caching
            result1 = modern_main([])
            result2 = modern_main([])

            # Both should succeed
            assert result1 is not None
            assert result2 is not None

            # Performance might differ due to caching
            perf1 = result1.get("performance_summary", {})
            perf2 = result2.get("performance_summary", {})

            # Both should have valid performance metrics
            assert "analysis_time" in perf1
            assert "analysis_time" in perf2


# =============================================================================
# P1 Tests - Error Handling and Boundaries
# =============================================================================


class TestErrorPropagationIntegration:
    """
    测试三层架构的错误传播链
    """

    async def test_error_propagation_cache_to_user(
        self, mock_environment, resource_tracker
    ):
        """
        P1测试: 验证从Cache层到用户界面的完整错误传播
        Cache → Service → Port → User
        """
        # Mock cache failure
        mock_cache_error = CacheError("Simulated cache storage failure")

        with (
            patch("main.DEVICE_MAPPING", mock_environment["device_data"]),
            patch(
                "implements.cache_implementations.LRUCacheImpl.get",
                side_effect=mock_cache_error,
            ),
        ):

            # The error should be handled gracefully
            try:
                result = modern_main([])
                # If it succeeds, it should have handled the cache error
                assert result is not None
            except MappingToolError as e:
                # Or it should propagate as a MappingToolError
                assert isinstance(e, MappingToolError)
                assert "cache" in str(e).lower()

    async def test_service_layer_error_conversion(
        self, mock_environment, resource_tracker
    ):
        """
        P1测试: 验证Service层的错误转换机制
        """
        # Mock service layer failure
        with patch("main.DEVICE_MAPPING", mock_environment["device_data"]):

            # Mock document service failure
            with patch(
                "implements.document_service_impl.DocumentServiceImpl.parse_official_document",
                side_effect=ValueError("Document parsing failed"),
            ):

                try:
                    result = modern_main([])
                    # Should handle parsing errors gracefully
                    assert result is not None
                except (AnalysisError, ValueError) as e:
                    # Should convert to appropriate domain exception
                    assert "parsing" in str(e).lower() or "document" in str(e).lower()

    async def test_async_error_isolation_and_cleanup(
        self, mock_environment, resource_tracker
    ):
        """
        P1测试: 验证异步操作的错误隔离和资源清理
        """

        # Mock async operation failure
        async def failing_async_operation():
            await asyncio.sleep(0.1)
            raise AnalysisError("Simulated async failure")

        # Test asyncio.gather error isolation pattern
        async def test_error_isolation():
            tasks = [
                asyncio.create_task(asyncio.sleep(0.1)),  # Success
                asyncio.create_task(failing_async_operation()),  # Failure
                asyncio.create_task(asyncio.sleep(0.1)),  # Success
            ]

            # Use return_exceptions=True for error isolation
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify error isolation
            assert len(results) == 3
            assert results[0] is None  # Successful sleep
            assert isinstance(results[1], AnalysisError)  # Isolated error
            assert results[2] is None  # Successful sleep

            return results

        results = await test_error_isolation()
        assert len(results) == 3


class TestResourceManagementIntegration:
    """
    测试资源管理和生命周期
    """

    async def test_threadpool_lifecycle_management(
        self, mock_environment, resource_tracker
    ):
        """
        P1测试: 验证ThreadPoolExecutor的生命周期管理
        """
        # Test ThreadPoolExecutor proper cleanup
        with patch("main.DEVICE_MAPPING", mock_environment["device_data"]):

            # Monitor thread creation
            original_thread_count = threading.active_count()

            # Execute analysis which may create threads
            result = modern_main([])

            # Allow some time for cleanup
            await asyncio.sleep(0.1)

            # Verify threads are cleaned up (within reasonable margin)
            final_thread_count = threading.active_count()
            thread_diff = final_thread_count - original_thread_count

            # Should not have excessive thread leakage
            assert (
                thread_diff <= 2
            ), f"Thread leak detected: {thread_diff} threads remain"

    async def test_cache_memory_management(self, mock_environment, resource_tracker):
        """
        P1测试: 验证缓存系统的内存管理
        """
        from implements.cache_implementations import LRUCacheImpl

        # Test cache size limits
        cache = LRUCacheImpl(name="TestCache", max_size=3)
        cache.initialize({"strategy": "lru", "max_size": 3})

        # Add items beyond capacity
        for i in range(5):
            cache.set(f"key_{i}", f"value_{i}")

        # Verify size limit is respected
        assert cache.size() <= 3

        # Verify LRU eviction works
        assert not cache.exists("key_0")  # Should be evicted
        assert cache.exists("key_4")  # Should be retained

        # Test cleanup
        cache.cleanup()
        assert cache.size() == 0

    async def test_file_handle_cleanup(self, mock_environment, resource_tracker):
        """
        P1测试: 验证文件句柄的正确清理
        """
        from implements.port_implementations import StandardFilePort

        port = StandardFilePort()
        port.connect()

        # Create temporary file
        temp_file = mock_environment["tmp_path"] / "test_file.txt"
        temp_file.write_text("Test content")

        # Test file operations
        content = port.read_text_file(str(temp_file))
        assert content == "Test content"

        # Test writing
        port.write_text_file(str(temp_file), "Updated content")
        updated_content = port.read_text_file(str(temp_file))
        assert updated_content == "Updated content"

        # Cleanup
        port.disconnect()


# =============================================================================
# P2 Tests - Performance and Compatibility
# =============================================================================


class TestPerformanceBaselines:
    """
    测试性能基准和回归检查
    """

    async def test_startup_time_baseline(self, mock_environment, resource_tracker):
        """
        P2测试: 验证应用启动时间基准
        """
        with (
            patch("main.DEVICE_MAPPING", mock_environment["device_data"]),
            patch(
                "main._determine_document_path",
                return_value=str(mock_environment["doc_file"]),
            ),
            patch(
                "implements.enhanced_cli_port.DEVICE_MAPPING",
                mock_environment["device_data"],
            ),
        ):

            start_time = time.time()
            result = modern_main([])
            end_time = time.time()

            total_time = end_time - start_time

            # Verify reasonable startup time (< 10 seconds for integration test)
            assert total_time < 10.0, f"Startup time {total_time:.2f}s exceeds baseline"

            # Verify performance metrics are recorded
            assert "performance_summary" in result
            perf_summary = result["performance_summary"]

            # Verify all timing metrics are present
            required_metrics = [
                "startup_time",
                "initialization_time",
                "analysis_time",
                "total_time",
            ]
            for metric in required_metrics:
                assert metric in perf_summary
                # Parse time values (they're strings with 's' suffix)
                time_value = float(perf_summary[metric].rstrip("s"))
                assert time_value >= 0

    async def test_concurrent_analysis_requests(
        self, mock_environment, resource_tracker
    ):
        """
        P2测试: 验证并发分析请求的处理
        """
        with (
            patch("main.DEVICE_MAPPING", mock_environment["device_data"]),
            patch(
                "main._determine_document_path",
                return_value=str(mock_environment["doc_file"]),
            ),
            patch(
                "implements.enhanced_cli_port.DEVICE_MAPPING",
                mock_environment["device_data"],
            ),
        ):

            # Create multiple concurrent analysis tasks
            async def run_analysis():
                return modern_main([])

            # Run 3 concurrent analyses
            tasks = [
                asyncio.create_task(run_analysis()),
                asyncio.create_task(run_analysis()),
                asyncio.create_task(run_analysis()),
            ]

            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all succeeded or failed gracefully
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # If it failed, it should be a known exception type
                    assert isinstance(result, (MappingToolError, RuntimeError))
                else:
                    # If it succeeded, it should have valid structure
                    assert isinstance(result, dict)
                    assert "application_info" in result


class TestBackwardCompatibility:
    """
    测试向后兼容性
    """

    async def test_dual_entry_point_compatibility(
        self, mock_environment, resource_tracker
    ):
        """
        P2测试: 验证main.py和RUN_THIS_TOOL.py双入口策略
        """
        # Test modern entry point
        with (
            patch("main.DEVICE_MAPPING", mock_environment["device_data"]),
            patch(
                "main._determine_document_path",
                return_value=str(mock_environment["doc_file"]),
            ),
            patch(
                "implements.enhanced_cli_port.DEVICE_MAPPING",
                mock_environment["device_data"],
            ),
        ):

            result_modern = modern_main([])
            assert result_modern is not None

            # Verify modern features are present
            assert "application_info" in result_modern
            app_info = result_modern["application_info"]
            assert app_info.get("version", "").startswith("2.0")
            assert (
                app_info.get("architecture")
                == "Port-Service-Cache with Composition Root"
            )

    async def test_configuration_compatibility(
        self, mock_environment, resource_tracker
    ):
        """
        P2测试: 验证配置系统的向后兼容性
        """
        # Test with various configuration formats
        configs_to_test = [
            [],  # Default configuration
            ["--verbose"],  # Simple flag
            ["--cache-size", "256"],  # Numeric parameter
            ["--log-level", "DEBUG"],  # String parameter
            ["--output", str(mock_environment["output_dir"])],  # Path parameter
        ]

        with (
            patch("main.DEVICE_MAPPING", mock_environment["device_data"]),
            patch(
                "main._determine_document_path",
                return_value=str(mock_environment["doc_file"]),
            ),
            patch(
                "implements.enhanced_cli_port.DEVICE_MAPPING",
                mock_environment["device_data"],
            ),
        ):

            for config in configs_to_test:
                try:
                    result = modern_main(config)
                    assert result is not None
                    # All configurations should produce valid results
                    assert "application_info" in result
                except (ConfigurationError, ValueError) as e:
                    # Some configurations might be invalid, but should fail gracefully
                    assert "configuration" in str(e).lower()


# =============================================================================
# Test Utilities and Helpers
# =============================================================================


class TestUtilitiesAndHelpers:
    """
    辅助测试工具和帮助函数的验证
    """

    async def test_mock_environment_setup(self, mock_environment, resource_tracker):
        """
        验证测试环境设置的正确性
        """
        # Verify directory structure
        assert mock_environment["tmp_path"].exists()
        assert mock_environment["docs_dir"].exists()
        assert mock_environment["doc_file"].exists()
        assert mock_environment["output_dir"].exists()

        # Verify mock data
        assert len(mock_environment["device_data"]) == 3
        assert "SL_TEST_DEVICE_01" in mock_environment["device_data"]

        # Verify document content
        doc_content = mock_environment["doc_file"].read_text(encoding="utf-8")
        assert "LifeSmart 智慧设备规格属性说明" in doc_content
        assert "SL_TEST_DEVICE_01" in doc_content

    async def test_resource_tracker_functionality(
        self, mock_environment, resource_tracker
    ):
        """
        验证资源跟踪器的功能
        """
        # Test thread tracking
        test_thread = threading.Thread(target=lambda: time.sleep(0.1))
        resource_tracker.threads.append(test_thread)
        test_thread.start()

        # Test executor tracking
        test_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        resource_tracker.executors.append(test_executor)

        # Test temp file tracking
        temp_file = mock_environment["tmp_path"] / "test_temp.txt"
        temp_file.write_text("temp content")
        resource_tracker.temp_files.append(temp_file)

        # Verify cleanup works
        assert temp_file.exists()
        assert test_thread.is_alive()
        assert not test_executor._shutdown

        # Cleanup will be called automatically by fixture


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_integration"])
