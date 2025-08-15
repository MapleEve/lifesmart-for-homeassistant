# Enhanced Test Suite for AnalysisService Implementation
# Based on ZEN MCP Expert Analysis and Testgen Recommendations

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass

# 待测试的模块
try:
    from ..implements.analysis_service_impl import (
        AnalysisServiceImpl,
        NLPAnalysisConfig,
        PlatformType,
    )
    from ..data_types.core_types import (
        DeviceData,
        AnalysisConfig,
        AnalysisResult,
        ConfigValue,
        CacheConfig,
    )
    from ..architecture.services import AnalysisService
except ImportError:
    # Development fallback
    pytest.skip("Implementation modules not available", allow_module_level=True)

# 异步测试标记
pytestmark = pytest.mark.asyncio


# =============================================================================
# Test Fixtures - Enhanced Dependency Injection
# =============================================================================


@pytest.fixture
def mock_document_service() -> Mock:
    """Enhanced DocumentService mock with async methods."""
    mock = Mock()
    mock.parse_device_document = AsyncMock(return_value={})
    mock.load_device_data = AsyncMock(return_value=[])
    mock.validate_document = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_cache_manager() -> Mock:
    """Enhanced CacheManager mock with async operations."""
    mock = Mock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock(return_value=True)
    mock.clear = AsyncMock()
    mock.get_performance_metrics = Mock(
        return_value={"cache_hits": 0, "cache_misses": 0, "hit_rate": 0.0}
    )
    return mock


@pytest.fixture
def nlp_config() -> NLPAnalysisConfig:
    """Standard NLP analysis configuration."""
    return NLPAnalysisConfig(
        enhanced_parsing=True,
        aggressive_matching=True,
        debug_mode=False,
        confidence_threshold=0.7,
        platform_exclusion_rules=True,
    )


@pytest.fixture
def analysis_service(
    mock_document_service: Mock,
    mock_cache_manager: Mock,
    nlp_config: NLPAnalysisConfig,
) -> AnalysisServiceImpl:
    """
    Main System Under Test (SUT) with injected dependencies.

    This fixture provides a fully configured AnalysisService implementation
    with mocked dependencies for isolated testing.
    """
    return AnalysisServiceImpl(
        document_service=mock_document_service,
        cache_manager=mock_cache_manager,
        nlp_config=nlp_config,
    )


@pytest.fixture
def sample_device_data() -> List[Dict[str, Any]]:
    """Sample device data for testing - covers multiple device types."""
    return [
        {
            "name": "SL_OE_DE",  # 计量插座
            "ios": [
                {"name": "P1", "description": "开关控制", "rw": "RW"},
                {"name": "V", "description": "电压值", "rw": "R"},
                {"name": "A", "description": "电流值", "rw": "R"},
                {"name": "P", "description": "功率值", "rw": "R"},
            ],
            "source": "test_device_data",
        },
        {
            "name": "SL_SW_PLUG",  # 开关插座
            "ios": [
                {"name": "L1", "description": "第一路开关", "rw": "W"},
                {"name": "O", "description": "总开关", "rw": "RW"},
            ],
            "source": "test_device_data",
        },
        {
            "name": "SL_RGBW_LIGHT",  # RGBW灯光
            "ios": [
                {"name": "RGBW", "description": "灯光颜色", "rw": "RW"},
                {"name": "BRI", "description": "亮度", "rw": "W"},
                {"name": "CT", "description": "色温", "rw": "RW"},
            ],
            "source": "test_device_data",
        },
        {
            "name": "SL_SC_TH",  # 温湿度传感器
            "ios": [
                {"name": "T", "description": "温度值", "rw": "R"},
                {"name": "H", "description": "湿度值", "rw": "R"},
            ],
            "source": "test_device_data",
        },
    ]


@pytest.fixture
def empty_device() -> Dict[str, Any]:
    """Empty device for edge case testing."""
    return {"name": "EMPTY_DEVICE", "ios": [], "source": "test_edge_case"}


@pytest.fixture
def malformed_device() -> Dict[str, Any]:
    """Malformed device data for error handling tests."""
    return {
        "name": "MALFORMED_DEVICE",
        "ios": [
            {"name": "BAD_IO"},  # Missing required fields
            {"description": "No name", "rw": "RW"},  # Missing name
            {"name": "GOOD_IO", "description": "Valid IO", "rw": "RW"},
        ],
        "source": "test_malformed",
    }


# =============================================================================
# P0 Tests: Core Classification Logic (Critical Priority)
# =============================================================================


class TestCoreClassificationLogic:
    """Critical tests for core business logic accuracy."""

    @pytest.mark.parametrize(
        "device_name, platform, expected",
        [
            # Switch device exclusion rules
            ("SL_SW_PLUG", "binary_sensor", True),
            ("SL_SW_PLUG", "sensor", True),
            ("SL_SW_PLUG", "climate", True),
            ("SL_SW_PLUG", "cover", True),
            ("SL_SW_PLUG", "lock", True),
            ("SL_SW_PLUG", "switch", False),  # Should NOT be excluded
            # Light device exclusion rules
            ("SL_LI_LIGHT", "binary_sensor", True),
            ("SL_LI_LIGHT", "climate", True),
            ("SL_LI_LIGHT", "cover", True),
            ("SL_LI_LIGHT", "light", False),  # Should NOT be excluded
            # Sensor device exclusion rules
            ("SL_SC_SENSOR", "switch", True),
            ("SL_SC_SENSOR", "light", True),
            ("SL_SC_SENSOR", "cover", True),
            ("SL_SC_SENSOR", "climate", True),
            ("SL_SC_SENSOR", "sensor", False),  # Should NOT be excluded
            # Climate device exclusion rules
            ("SL_AC_CLIMATE", "switch", True),
            ("SL_AC_CLIMATE", "light", True),
            ("SL_AC_CLIMATE", "binary_sensor", True),
            ("SL_AC_CLIMATE", "sensor", True),
            ("SL_AC_CLIMATE", "cover", True),
            ("SL_AC_CLIMATE", "climate", False),  # Should NOT be excluded
            # Unknown device - no exclusions
            ("UNKNOWN_DEVICE", "switch", False),
            ("UNKNOWN_DEVICE", "light", False),
            ("UNKNOWN_DEVICE", "sensor", False),
        ],
    )
    def test_device_exclusion_rules(
        self,
        analysis_service: AnalysisServiceImpl,
        device_name: str,
        platform: str,
        expected: bool,
    ):
        """
        Test platform exclusion rules based on device name prefixes.

        This is the first line of defense in the classification system,
        preventing incompatible platform suggestions.
        """
        # Act
        result = analysis_service._should_exclude_platform(device_name, platform)

        # Assert
        assert (
            result == expected
        ), f"Device {device_name} platform {platform} exclusion failed"

    @pytest.mark.parametrize(
        "io_name, io_description, rw_permission, device_name, platform_type, expected_min_confidence",
        [
            # Switch platform tests - P0 critical paths
            ("P1", "开关控制", "RW", "SL_OE_DE", PlatformType.SWITCH, 0.95),
            ("L1", "第一路开关", "W", "SL_SW_CTRL", PlatformType.SWITCH, 0.85),
            ("O", "总开关", "RW", "SL_SW_PLUG", PlatformType.SWITCH, 0.90),
            # Sensor platform tests - P0 critical paths
            ("T", "温度值", "R", "SL_SC_TH", PlatformType.SENSOR, 0.90),
            ("V", "电压值", "R", "SL_OE_DE", PlatformType.SENSOR, 0.90),
            ("H", "湿度值", "R", "SL_SC_TH", PlatformType.SENSOR, 0.90),
            ("PM", "功率", "R", "SL_PM_METER", PlatformType.SENSOR, 0.90),
            # Light platform tests - P0 critical paths
            ("RGBW", "灯光颜色", "RW", "SL_RGBW_LIGHT", PlatformType.LIGHT, 0.95),
            ("BRI", "亮度", "W", "SL_LI_DIM", PlatformType.LIGHT, 0.90),
            ("CT", "色温", "RW", "SL_CT_LIGHT", PlatformType.LIGHT, 0.90),
            # Cover platform tests
            ("OP", "打开窗帘", "W", "SL_CV_BLIND", PlatformType.COVER, 0.85),
            ("CL", "关闭窗帘", "W", "SL_CV_BLIND", PlatformType.COVER, 0.85),
            ("POS", "位置", "RW", "SL_CV_BLIND", PlatformType.COVER, 0.90),
            # Climate platform tests
            ("TEMP", "温度设置", "RW", "SL_AC_UNIT", PlatformType.CLIMATE, 0.90),
            ("MODE", "模式", "RW", "SL_AC_UNIT", PlatformType.CLIMATE, 0.85),
            ("FAN", "风扇", "W", "SL_AC_UNIT", PlatformType.CLIMATE, 0.80),
        ],
    )
    async def test_classification_accuracy_success_cases(
        self,
        analysis_service: AnalysisServiceImpl,
        io_name: str,
        io_description: str,
        rw_permission: str,
        device_name: str,
        platform_type: PlatformType,
        expected_min_confidence: float,
    ):
        """
        Test core classification logic accuracy for expected success cases.

        This validates the heart of the business logic - the platform
        classification algorithm that determines device capabilities.
        """
        # Act
        result = await analysis_service._classify_single_platform(
            io_name, io_description, rw_permission, device_name, platform_type
        )

        # Assert
        assert (
            result is not None
        ), f"Classification failed for {io_name} on {device_name}"
        assert result.platform == platform_type
        assert result.confidence >= expected_min_confidence, (
            f"Confidence {result.confidence} below expected {expected_min_confidence} "
            f"for {io_name} -> {platform_type}"
        )
        assert len(result.reasoning) > 0, "Classification reasoning should not be empty"

    @pytest.mark.parametrize(
        "io_name, io_description, rw_permission, device_name, platform_type",
        [
            # Permission mismatches - should fail
            (
                "P1",
                "开关控制",
                "R",
                "SL_SW_PLUG",
                PlatformType.SWITCH,
            ),  # Switch needs W/RW
            ("T", "温度值", "W", "SL_SC_TH", PlatformType.SENSOR),  # Sensor needs R
            (
                "RGBW",
                "灯光颜色",
                "R",
                "SL_LI_LIGHT",
                PlatformType.LIGHT,
            ),  # Light needs W/RW
            # Keyword mismatches - should fail
            ("UNKNOWN", "未知功能", "RW", "SL_SW_PLUG", PlatformType.SWITCH),
            ("RANDOM", "随机数据", "R", "SL_SC_TH", PlatformType.SENSOR),
            ("DATA", "数据", "W", "SL_LI_LIGHT", PlatformType.LIGHT),
            # Device exclusion matches - should fail
            (
                "P1",
                "开关控制",
                "RW",
                "SL_SC_SENSOR",
                PlatformType.SWITCH,
            ),  # Sensor device to switch
        ],
    )
    async def test_classification_rejection_cases(
        self,
        analysis_service: AnalysisServiceImpl,
        io_name: str,
        io_description: str,
        rw_permission: str,
        device_name: str,
        platform_type: PlatformType,
    ):
        """
        Test classification logic correctly rejects inappropriate platform assignments.

        This ensures the system doesn't make false positive classifications
        that could confuse users or break Home Assistant integrations.
        """
        # Act
        result = await analysis_service._classify_single_platform(
            io_name, io_description, rw_permission, device_name, platform_type
        )

        # Assert
        assert result is None, (
            f"Classification should have failed for {io_name} -> {platform_type} "
            f"on device {device_name}"
        )


# =============================================================================
# P1 Tests: Main Analysis Workflow and Caching (High Priority)
# =============================================================================


class TestAnalysisWorkflow:
    """High priority tests for main analysis workflow and caching."""

    async def test_analyze_single_device_cache_miss(
        self,
        analysis_service: AnalysisServiceImpl,
        mock_cache_manager: Mock,
        sample_device_data: List[Dict[str, Any]],
    ):
        """
        Test full analysis workflow when cache misses.

        Verifies that the complete analysis pipeline executes correctly
        and results are properly cached for future use.
        """
        # Arrange
        device = sample_device_data[0]  # SL_OE_DE
        mock_cache_manager.get.return_value = None  # Cache miss

        # Act
        result = await analysis_service._analyze_single_device_internal(device)

        # Assert
        # Verify cache was checked
        mock_cache_manager.get.assert_called_once()

        # Verify analysis result structure
        assert result is not None
        assert result.device_name == "SL_OE_DE"
        assert isinstance(result.suggested_platforms, set)
        assert len(result.suggested_platforms) > 0
        assert isinstance(result.ios_analysis, list)
        assert len(result.ios_analysis) > 0
        assert 0.0 <= result.confidence <= 1.0

        # Verify expected platforms for SL_OE_DE (metering outlet)
        assert "switch" in result.suggested_platforms  # P1 switch control
        assert "sensor" in result.suggested_platforms  # V, A, P sensors

        # Verify result was cached
        mock_cache_manager.set.assert_called_once()
        cached_key = mock_cache_manager.set.call_args[0][0]
        cached_value = mock_cache_manager.set.call_args[0][1]
        assert "SL_OE_DE" in cached_key
        assert cached_value == result

    async def test_analyze_single_device_cache_hit(
        self,
        analysis_service: AnalysisServiceImpl,
        mock_cache_manager: Mock,
        sample_device_data: List[Dict[str, Any]],
    ):
        """
        Test analysis workflow when cache hits.

        Verifies that cached results are returned directly without
        executing the expensive analysis pipeline.
        """
        # Arrange
        device = sample_device_data[0]

        # Mock cached result
        from ..implements.analysis_service_impl import DeviceAnalysisResult

        cached_result = DeviceAnalysisResult(
            device_name="SL_OE_DE",
            suggested_platforms={"switch", "sensor"},
            ios_analysis=[],
            confidence=0.95,
        )
        mock_cache_manager.get.return_value = cached_result

        # Spy on internal method to verify it's not called
        with patch.object(analysis_service, "_classify_io_platform") as mock_classify:
            # Act
            result = await analysis_service._analyze_single_device_internal(device)

            # Assert
            # Verify cache was checked
            mock_cache_manager.get.assert_called_once()

            # Verify cached result was returned
            assert result is cached_result

            # Verify analysis was not executed
            mock_classify.assert_not_called()

            # Verify no cache write occurred
            mock_cache_manager.set.assert_not_called()

    async def test_analyze_devices_empty_list(
        self, analysis_service: AnalysisServiceImpl
    ):
        """
        Test batch analysis handles empty device list gracefully.

        Ensures the system behaves correctly when no devices are provided,
        returning appropriate empty results without errors.
        """
        # Arrange
        empty_devices = []
        config = AnalysisConfig(max_concurrent_jobs=5)

        # Act
        result = await analysis_service.analyze_devices(config, empty_devices)

        # Assert
        assert isinstance(result, dict)
        assert result["total_devices"] == 0
        assert result["analyzed_devices"] == 0
        assert result["average_confidence"] == 0.0
        assert result["device_results"] == []
        assert "analysis_timestamp" in result

    async def test_analyze_devices_single_device(
        self,
        analysis_service: AnalysisServiceImpl,
        sample_device_data: List[Dict[str, Any]],
    ):
        """
        Test batch analysis with single device.

        Validates that single-device analysis works correctly through
        the batch processing pipeline.
        """
        # Arrange
        single_device = [sample_device_data[0]]
        config = AnalysisConfig(max_concurrent_jobs=5)

        # Act
        result = await analysis_service.analyze_devices(config, single_device)

        # Assert
        assert result["total_devices"] == 1
        assert result["analyzed_devices"] == 1
        assert len(result["device_results"]) == 1

        device_result = result["device_results"][0]
        assert device_result.device_name == "SL_OE_DE"
        assert result["average_confidence"] > 0.0

    async def test_analyze_devices_multiple_batches(
        self,
        analysis_service: AnalysisServiceImpl,
        sample_device_data: List[Dict[str, Any]],
    ):
        """
        Test batch analysis with multiple devices across batches.

        Verifies that the batch processing logic correctly handles
        multiple devices with proper concurrent execution.
        """
        # Arrange
        # Use all sample devices to force multiple batches
        config = AnalysisConfig(max_concurrent_jobs=2)  # Small batch size

        # Act
        result = await analysis_service.analyze_devices(config, sample_device_data)

        # Assert
        assert result["total_devices"] == len(sample_device_data)
        assert result["analyzed_devices"] == len(sample_device_data)
        assert len(result["device_results"]) == len(sample_device_data)

        # Verify all devices were processed
        processed_names = {dr.device_name for dr in result["device_results"]}
        expected_names = {device["name"] for device in sample_device_data}
        assert processed_names == expected_names

        # Verify average confidence is reasonable
        assert 0.0 < result["average_confidence"] <= 1.0

    async def test_analyze_devices_handles_partial_failure(
        self,
        analysis_service: AnalysisServiceImpl,
        sample_device_data: List[Dict[str, Any]],
        malformed_device: Dict[str, Any],
    ):
        """
        Test batch analysis resilience to partial failures.

        Ensures that when some devices fail analysis, others continue
        to be processed and the system returns meaningful results.
        """
        # Arrange
        # Mix good and bad devices
        mixed_devices = sample_device_data[:2] + [malformed_device]
        config = AnalysisConfig(max_concurrent_jobs=5)

        # Mock internal method to simulate failures
        original_analyze = analysis_service._analyze_single_device_internal

        async def mock_analyze(device):
            if device["name"] == "MALFORMED_DEVICE":
                raise ValueError("Simulated analysis failure")
            return await original_analyze(device)

        with patch.object(
            analysis_service,
            "_analyze_single_device_internal",
            side_effect=mock_analyze,
        ):
            # Act
            result = await analysis_service.analyze_devices(config, mixed_devices)

            # Assert
            assert result["total_devices"] == 3
            assert result["analyzed_devices"] == 2  # Only successful ones
            assert len(result["device_results"]) == 2

            # Verify successful devices were processed
            processed_names = {dr.device_name for dr in result["device_results"]}
            expected_names = {"SL_OE_DE", "SL_SW_PLUG"}
            assert processed_names == expected_names


# =============================================================================
# P1 Tests: Concurrency and Thread Safety (High Priority)
# =============================================================================


class TestConcurrencySafety:
    """Tests for concurrent execution and thread safety."""

    async def test_concurrent_analysis_stats_race_condition(
        self,
        analysis_service: AnalysisServiceImpl,
        sample_device_data: List[Dict[str, Any]],
    ):
        """
        Test for race conditions in analysis statistics.

        This test attempts to expose race conditions in the shared
        analysis_stats dictionary when multiple concurrent analyses run.

        Note: This test may intermittently fail if proper synchronization
        is not implemented, which helps identify the concurrency bug.
        """
        # Arrange
        devices_batch_1 = sample_device_data[:2] * 5  # 10 devices
        devices_batch_2 = sample_device_data[2:] * 7  # 14 devices
        config = AnalysisConfig(max_concurrent_jobs=4)

        # Reset stats
        analysis_service.analysis_stats = {
            "total_devices_analyzed": 0,
            "total_ios_classified": 0,
            "cache_hits": 0,
            "average_confidence": 0.0,
        }

        # Act
        # Run two concurrent batch analyses
        results = await asyncio.gather(
            analysis_service.analyze_devices(config, devices_batch_1),
            analysis_service.analyze_devices(config, devices_batch_2),
            return_exceptions=True,
        )

        # Assert
        # Verify both analyses succeeded
        assert len(results) == 2
        for result in results:
            assert not isinstance(result, Exception), f"Analysis failed: {result}"

        # Check if race condition occurred in stats
        final_stats = analysis_service.analysis_stats
        expected_total = len(devices_batch_1) + len(devices_batch_2)

        # This assertion may fail if there's a race condition
        # The actual value might be less than expected due to concurrent updates
        assert final_stats["total_devices_analyzed"] == expected_total, (
            f"Race condition detected! Expected {expected_total}, "
            f"got {final_stats['total_devices_analyzed']}"
        )

    async def test_concurrent_cache_access(
        self,
        analysis_service: AnalysisServiceImpl,
        sample_device_data: List[Dict[str, Any]],
        mock_cache_manager: Mock,
    ):
        """
        Test concurrent cache access patterns.

        Verifies that concurrent cache reads and writes don't interfere
        with each other and maintain data consistency.
        """
        # Arrange
        device = sample_device_data[0]

        # Configure cache to simulate concurrent access
        cache_call_count = 0
        original_get = mock_cache_manager.get

        async def concurrent_cache_get(key):
            nonlocal cache_call_count
            cache_call_count += 1
            # Simulate some processing time
            await asyncio.sleep(0.01)
            return await original_get(key)

        mock_cache_manager.get = concurrent_cache_get

        # Act
        # Run multiple concurrent analyses of the same device
        tasks = [
            analysis_service._analyze_single_device_internal(device) for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)

        # Assert
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.device_name == first_result.device_name
            assert result.suggested_platforms == first_result.suggested_platforms
            assert result.confidence == first_result.confidence

        # Cache should have been accessed multiple times
        assert cache_call_count >= 5


# =============================================================================
# P2 Tests: Edge Cases and Error Handling (Medium Priority)
# =============================================================================


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling scenarios."""

    async def test_analyze_device_with_empty_ios(
        self,
        analysis_service: AnalysisServiceImpl,
        empty_device: Dict[str, Any],
    ):
        """
        Test analysis of device with no IO ports.

        Ensures the system handles devices without IO ports gracefully
        without crashing or producing invalid results.
        """
        # Act
        result = await analysis_service._analyze_single_device_internal(empty_device)

        # Assert
        assert result is not None
        assert result.device_name == "EMPTY_DEVICE"
        assert len(result.ios_analysis) == 0
        assert len(result.suggested_platforms) == 0
        assert result.confidence == 0.0  # No IOs means no confidence

    async def test_analyze_device_with_malformed_ios(
        self,
        analysis_service: AnalysisServiceImpl,
        malformed_device: Dict[str, Any],
    ):
        """
        Test analysis resilience to malformed IO data.

        Verifies that the system can handle incomplete or corrupted
        IO data without crashing and still process valid IOs.
        """
        # Act
        result = await analysis_service._analyze_single_device_internal(
            malformed_device
        )

        # Assert
        assert result is not None
        assert result.device_name == "MALFORMED_DEVICE"

        # Should have processed only the valid IO
        assert len(result.ios_analysis) >= 1  # At least the valid IO

        # System should still provide a reasonable confidence
        assert 0.0 <= result.confidence <= 1.0

    async def test_confidence_calculation_edge_cases(
        self, analysis_service: AnalysisServiceImpl
    ):
        """
        Test confidence calculation with edge case inputs.

        Ensures the confidence calculation algorithm handles
        edge cases without division by zero or other mathematical errors.
        """
        # Test with empty lists
        confidence_empty = analysis_service._calculate_device_confidence([], set())
        assert confidence_empty == 0.0

        # Test with no platforms
        mock_ios = [Mock(confidence=0.8), Mock(confidence=0.9)]
        confidence_no_platforms = analysis_service._calculate_device_confidence(
            mock_ios, set()
        )
        assert confidence_no_platforms == 0.0

        # Test with single platform
        confidence_single = analysis_service._calculate_device_confidence(
            mock_ios, {"switch"}
        )
        assert 0.0 <= confidence_single <= 1.0

    async def test_invalid_configuration_handling(
        self,
        mock_document_service: Mock,
        mock_cache_manager: Mock,
    ):
        """
        Test handling of invalid configuration parameters.

        Ensures the service gracefully handles configuration errors
        without compromising system stability.
        """
        # Test with invalid configuration
        invalid_config = NLPAnalysisConfig(
            enhanced_parsing=True,
            aggressive_matching=True,
            debug_mode=False,
            confidence_threshold=-0.5,  # Invalid: negative threshold
            platform_exclusion_rules=True,
        )

        # Should not raise an exception during initialization
        service = AnalysisServiceImpl(
            document_service=mock_document_service,
            cache_manager=mock_cache_manager,
            nlp_config=invalid_config,
        )

        # Service should still be functional with corrected values
        assert service.config.confidence_threshold >= 0.0


# =============================================================================
# Performance and Benchmarking Tests
# =============================================================================


class TestPerformanceAndBenchmarks:
    """Performance tests and benchmarking for analysis service."""

    async def test_analysis_performance_benchmark(
        self,
        analysis_service: AnalysisServiceImpl,
        sample_device_data: List[Dict[str, Any]],
    ):
        """
        Benchmark analysis performance for regression testing.

        Ensures that the analysis service meets performance requirements
        and doesn't regress over time.
        """
        # Arrange
        # Scale up devices for realistic performance test
        large_device_set = sample_device_data * 25  # 100 devices
        config = AnalysisConfig(max_concurrent_jobs=4)

        # Act
        start_time = time.time()
        result = await analysis_service.analyze_devices(config, large_device_set)
        end_time = time.time()

        execution_time = end_time - start_time

        # Assert
        # Performance requirements based on ZEN analysis
        assert (
            execution_time < 10.0
        ), f"Analysis took {execution_time:.2f}s, expected < 10s"
        assert result["analyzed_devices"] == len(large_device_set)

        # Throughput requirements
        devices_per_second = len(large_device_set) / execution_time
        assert (
            devices_per_second > 10
        ), f"Throughput {devices_per_second:.1f} devices/s too low"

    async def test_memory_usage_stability(
        self,
        analysis_service: AnalysisServiceImpl,
        sample_device_data: List[Dict[str, Any]],
    ):
        """
        Test memory usage stability during extended operation.

        Ensures that the analysis service doesn't have memory leaks
        during prolonged operation with many devices.
        """
        import psutil
        import os

        # Arrange
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        config = AnalysisConfig(max_concurrent_jobs=4)

        # Act
        # Run multiple analysis cycles
        for _ in range(10):
            await analysis_service.analyze_devices(config, sample_device_data)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Assert
        # Memory growth should be reasonable (< 50MB for this test)
        assert (
            memory_growth < 50
        ), f"Memory grew by {memory_growth:.1f}MB, possible leak"

    async def test_cache_efficiency_metrics(
        self,
        analysis_service: AnalysisServiceImpl,
        sample_device_data: List[Dict[str, Any]],
        mock_cache_manager: Mock,
    ):
        """
        Test cache efficiency and hit rate optimization.

        Validates that the caching strategy achieves the target
        hit rate of > 80% for repeated analyses.
        """
        # Arrange
        # Configure cache to track hits/misses
        cache_hits = 0
        cache_misses = 0
        cached_results = {}

        async def smart_cache_get(key):
            nonlocal cache_hits, cache_misses
            if key in cached_results:
                cache_hits += 1
                return cached_results[key]
            else:
                cache_misses += 1
                return None

        async def smart_cache_set(key, value, ttl=None):
            cached_results[key] = value

        mock_cache_manager.get = smart_cache_get
        mock_cache_manager.set = smart_cache_set
        config = AnalysisConfig(max_concurrent_jobs=4)

        # Act
        # First run - populate cache
        await analysis_service.analyze_devices(config, sample_device_data)

        # Reset counters for actual test
        cache_hits = 0
        cache_misses = 0

        # Second run - should hit cache
        await analysis_service.analyze_devices(config, sample_device_data)

        # Assert
        total_accesses = cache_hits + cache_misses
        if total_accesses > 0:
            hit_rate = cache_hits / total_accesses
            assert hit_rate > 0.8, f"Cache hit rate {hit_rate:.1%} below target 80%"


# =============================================================================
# Integration Tests with Real Components
# =============================================================================


class TestRealComponentIntegration:
    """Integration tests with actual implementation components."""

    async def test_end_to_end_analysis_workflow(
        self,
        sample_device_data: List[Dict[str, Any]],
    ):
        """
        End-to-end test with real components (no mocks).

        This test uses actual implementations to verify the complete
        integration works correctly in a realistic scenario.
        """
        # Skip if dependencies not available
        pytest.importorskip("mapping_tool.implements.document_service_impl")
        pytest.importorskip("mapping_tool.implements.cache_implementations")

        # Arrange
        from ..implements.document_service_impl import (
            DocumentServiceImpl,
            DocumentParsingConfig,
        )
        from ..implements.cache_implementations import LRUCacheImpl

        # Create real components
        doc_config = DocumentParsingConfig(debug_mode=False)
        document_service = DocumentServiceImpl(config=doc_config)

        cache_manager = LRUCacheImpl("integration_test", max_size=100)
        cache_config = CacheConfig(max_size=100, ttl_seconds=300)
        cache_manager.initialize(cache_config)

        nlp_config = NLPAnalysisConfig(debug_mode=False)
        analysis_service = AnalysisServiceImpl(
            document_service=document_service,
            cache_manager=cache_manager,
            nlp_config=nlp_config,
        )

        # Act
        config = AnalysisConfig(max_concurrent_jobs=4)
        result = await analysis_service.analyze_devices(config, sample_device_data)

        # Assert
        assert result["total_devices"] == len(sample_device_data)
        assert result["analyzed_devices"] > 0
        assert result["average_confidence"] > 0.0
        assert len(result["device_results"]) > 0

        # Verify specific platform detections
        device_results_map = {dr.device_name: dr for dr in result["device_results"]}

        # SL_OE_DE should be detected as switch + sensor
        if "SL_OE_DE" in device_results_map:
            platforms = device_results_map["SL_OE_DE"].suggested_platforms
            assert "switch" in platforms or "sensor" in platforms

        # Clean up
        cache_manager.cleanup()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
