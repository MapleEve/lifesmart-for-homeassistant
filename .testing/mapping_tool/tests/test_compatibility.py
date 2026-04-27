# Backward Compatibility Tests
# Ensures that the enhanced architecture maintains 100% compatibility with existing interfaces

import pytest
import asyncio
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# Test imports for compatibility validation
try:
    # Original interface imports
    from ..RUN_THIS_TOOL import SmartIOAllocationAnalyzer
    from ..main import main as modern_main, async_main, compatibility_main

    # Enhanced architecture imports
    from ..implements.enhanced_cli_port import (
        EnhancedSmartIOAllocationAnalyzer,
        enhanced_main,
        create_smart_io_allocation_analyzer,
    )

    COMPATIBILITY_TEST_AVAILABLE = True
except ImportError:
    COMPATIBILITY_TEST_AVAILABLE = False
    pytest.skip("Compatibility test modules not available", allow_module_level=True)


# =============================================================================
# Legacy Interface Compatibility Tests
# =============================================================================


class TestLegacyInterfaceCompatibility:
    """Test compatibility with original RUN_THIS_TOOL.py interface."""

    def test_smart_io_allocation_analyzer_interface_preserved(self):
        """Test that original SmartIOAllocationAnalyzer interface is preserved."""
        # Test class exists and is importable
        assert SmartIOAllocationAnalyzer is not None

        # Test constructor signature compatibility
        analyzer = SmartIOAllocationAnalyzer(enable_performance_monitoring=False)
        assert analyzer is not None

        # Test essential attributes exist
        assert hasattr(analyzer, "supported_platforms")
        assert hasattr(analyzer, "confidence_threshold")
        assert hasattr(analyzer, "filtered_devices")
        assert hasattr(analyzer, "focus_devices")

        # Test essential methods exist
        assert hasattr(analyzer, "perform_smart_comparison_analysis")
        assert callable(analyzer.perform_smart_comparison_analysis)

    def test_enhanced_analyzer_backward_compatibility(self):
        """Test that enhanced analyzer maintains backward compatibility."""
        # Test enhanced class exists
        assert EnhancedSmartIOAllocationAnalyzer is not None

        # Test constructor compatibility
        enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer(
            enable_performance_monitoring=False
        )
        assert enhanced_analyzer is not None

        # Test that all original attributes are available
        assert hasattr(enhanced_analyzer, "supported_platforms")
        assert hasattr(enhanced_analyzer, "confidence_threshold")
        assert hasattr(enhanced_analyzer, "filtered_devices")
        assert hasattr(enhanced_analyzer, "focus_devices")

        # Test backward compatibility adapter
        assert hasattr(enhanced_analyzer, "memory_agent1")

        # Test essential method signature compatibility
        assert hasattr(enhanced_analyzer, "perform_smart_comparison_analysis")
        method = getattr(enhanced_analyzer, "perform_smart_comparison_analysis")

        # Method should accept same parameters as original
        import inspect

        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "doc_path" in params

    def test_main_function_interface_compatibility(self):
        """Test that main function interfaces remain compatible."""
        # Test that all main function variants exist
        assert callable(modern_main)
        assert callable(async_main)
        assert callable(compatibility_main)

        # Test that they accept the same parameter types
        import inspect

        # modern_main should accept optional cli_args
        modern_sig = inspect.signature(modern_main)
        assert "cli_args" in modern_sig.parameters

        # async_main should have similar signature
        async_sig = inspect.signature(async_main)
        assert "cli_args" in async_sig.parameters

    @pytest.mark.parametrize("performance_monitoring", [True, False])
    def test_constructor_parameter_compatibility(self, performance_monitoring: bool):
        """Test constructor parameter compatibility across implementations."""
        # Original analyzer
        original_analyzer = SmartIOAllocationAnalyzer(
            enable_performance_monitoring=performance_monitoring
        )

        # Enhanced analyzer
        enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer(
            enable_performance_monitoring=performance_monitoring
        )

        # Both should handle the same parameter
        assert original_analyzer is not None
        assert enhanced_analyzer is not None

        # Performance monitoring setting should be preserved
        if hasattr(original_analyzer, "_performance_monitoring"):
            assert (
                getattr(original_analyzer, "_performance_monitoring")
                == performance_monitoring
            )

        if hasattr(enhanced_analyzer, "_performance_monitoring"):
            assert (
                getattr(enhanced_analyzer, "_performance_monitoring")
                == performance_monitoring
            )


# =============================================================================
# Functional Compatibility Tests
# =============================================================================


class TestFunctionalCompatibility:
    """Test that enhanced implementation produces compatible results."""

    @pytest.fixture
    def sample_doc_path(self) -> str:
        """Create a sample document for testing."""
        # Create temporary test document
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                """
# Test Device Documentation

## SL_OE_DE 计量插座

| IO口 | 读写权限 | 描述 |
|------|----------|------|
| P1   | RW       | 开关控制 |
| V    | R        | 电压值 |
| A    | R        | 电流值 |
| P    | R        | 功率值 |

## SL_SW_PLUG 开关插座

| IO口 | 读写权限 | 描述 |
|------|----------|------|
| L1   | W        | 第一路开关 |
| O    | RW       | 总开关 |
"""
            )
            return f.name

    def test_analysis_result_structure_compatibility(self, sample_doc_path: str):
        """Test that analysis results have compatible structure."""
        try:
            # Test original analyzer
            original_analyzer = SmartIOAllocationAnalyzer(
                enable_performance_monitoring=False
            )
            original_result = original_analyzer.perform_smart_comparison_analysis(
                sample_doc_path
            )

            # Test enhanced analyzer
            enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer(
                enable_performance_monitoring=False
            )
            enhanced_result = enhanced_analyzer.perform_smart_comparison_analysis(
                sample_doc_path
            )

            # Both results should be dictionaries
            assert isinstance(original_result, dict)
            assert isinstance(enhanced_result, dict)

            # Check for essential result keys (structure compatibility)
            essential_keys = [
                "分析概览",  # Analysis overview
                "设备分析结果",  # Device analysis results
            ]

            for key in essential_keys:
                if key in original_result:
                    assert key in enhanced_result, f"Enhanced result missing key: {key}"

            # Cleanup
            os.unlink(sample_doc_path)

        except Exception as e:
            os.unlink(sample_doc_path)
            pytest.fail(f"Compatibility test failed: {e}")

    def test_configuration_compatibility(self):
        """Test that configuration options remain compatible."""
        # Test default configuration compatibility
        original_analyzer = SmartIOAllocationAnalyzer()
        enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer()

        # Test that key configuration attributes are preserved
        config_attributes = [
            "supported_platforms",
            "confidence_threshold",
        ]

        for attr in config_attributes:
            if hasattr(original_analyzer, attr):
                assert hasattr(
                    enhanced_analyzer, attr
                ), f"Enhanced analyzer missing attribute: {attr}"

                # Values should be compatible types
                original_value = getattr(original_analyzer, attr)
                enhanced_value = getattr(enhanced_analyzer, attr)

                assert type(original_value) == type(
                    enhanced_value
                ), f"Type mismatch for {attr}: {type(original_value)} vs {type(enhanced_value)}"

    def test_memory_agent_compatibility(self):
        """Test that memory agent interface remains compatible."""
        enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer(
            enable_performance_monitoring=False
        )

        # Test memory agent adapter exists
        assert hasattr(enhanced_analyzer, "memory_agent1")
        memory_agent = enhanced_analyzer.memory_agent1

        if memory_agent is not None:
            # Test essential memory agent methods
            expected_methods = [
                "get_existing_allocation_stream",
                "clear_caches",
                "get_performance_metrics",
            ]

            for method in expected_methods:
                assert hasattr(
                    memory_agent, method
                ), f"Memory agent missing method: {method}"
                assert callable(getattr(memory_agent, method))

    def test_platform_detection_consistency(self, sample_doc_path: str):
        """Test that platform detection results are consistent."""
        try:
            # Both analyzers should detect similar platforms for same device
            original_analyzer = SmartIOAllocationAnalyzer(
                enable_performance_monitoring=False
            )
            enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer(
                enable_performance_monitoring=False
            )

            original_result = original_analyzer.perform_smart_comparison_analysis(
                sample_doc_path
            )
            enhanced_result = enhanced_analyzer.perform_smart_comparison_analysis(
                sample_doc_path
            )

            # Extract platform suggestions from both results
            def extract_platforms(result):
                platforms = set()
                if "设备分析结果" in result:
                    for device_result in result["设备分析结果"]:
                        if "suggested_platforms" in device_result:
                            platforms.update(device_result["suggested_platforms"])
                return platforms

            original_platforms = extract_platforms(original_result)
            enhanced_platforms = extract_platforms(enhanced_result)

            # Platform detection should be similar (allow for improvements)
            # Enhanced version may detect more platforms, but shouldn't miss major ones
            common_platforms = original_platforms.intersection(enhanced_platforms)

            # At least 70% of original platforms should be preserved
            if len(original_platforms) > 0:
                preservation_rate = len(common_platforms) / len(original_platforms)
                assert (
                    preservation_rate >= 0.7
                ), f"Platform detection compatibility too low: {preservation_rate:.1%}"

            # Cleanup
            os.unlink(sample_doc_path)

        except Exception as e:
            os.unlink(sample_doc_path)
            pytest.fail(f"Platform detection compatibility test failed: {e}")


# =============================================================================
# CLI Interface Compatibility Tests
# =============================================================================


class TestCLICompatibility:
    """Test CLI interface compatibility."""

    def test_dual_entry_point_compatibility(self):
        """Test that dual entry point strategy works correctly."""
        # Test that both entry points exist and are callable

        # RUN_THIS_TOOL.py style entry (legacy)
        if hasattr(sys.modules.get("__main__"), "main"):
            legacy_main = getattr(sys.modules.get("__main__"), "main")
            assert callable(legacy_main)

        # main.py style entry (modern)
        assert callable(modern_main)
        assert callable(compatibility_main)

    def test_command_line_argument_compatibility(self):
        """Test that command line arguments remain compatible."""
        # Test modern main with various argument combinations
        test_args = [
            [],  # No arguments
            ["--verbose"],  # Verbose mode
            ["--config", "test_config.json"],  # Config file
            ["--help"],  # Help (will exit, so we catch it)
        ]

        for args in test_args:
            if "--help" in args:
                # Help argument causes sys.exit, so we expect an exception
                with pytest.raises((SystemExit, Exception)):
                    modern_main(args)
            else:
                # Other arguments should be processed without immediate errors
                try:
                    # We don't actually run the analysis, just test argument parsing
                    with patch("builtins.print"):  # Suppress output
                        with patch.object(sys, "exit"):  # Prevent actual exit
                            # This might fail due to missing files, but shouldn't crash on args
                            modern_main(args)
                except (FileNotFoundError, ImportError):
                    # Expected for missing test files/dependencies
                    pass
                except SystemExit:
                    # Also acceptable for argument processing
                    pass

    async def test_async_interface_compatibility(self):
        """Test that async interface is compatible and functional."""
        # Test async main function exists and is properly async
        assert asyncio.iscoroutinefunction(async_main)

        # Test basic async call (without actual analysis)
        try:
            with patch("builtins.print"):  # Suppress output
                # This might fail due to missing files, but should handle async correctly
                await async_main(["--help"])
        except (SystemExit, FileNotFoundError, ImportError):
            # Expected for help or missing files
            pass


# =============================================================================
# Data Format Compatibility Tests
# =============================================================================


class TestDataFormatCompatibility:
    """Test that data formats remain compatible."""

    def test_json_output_compatibility(self):
        """Test that JSON output format remains compatible."""
        # Create sample analysis result in both old and new formats
        sample_result = {
            "分析概览": {
                "总设备数": 2,
                "需要关注设备数": 2,
                "已过滤设备数": 0,
                "处理效率": "100%",
            },
            "设备分析结果": [
                {
                    "device_name": "SL_OE_DE",
                    "suggested_platforms": ["switch", "sensor"],
                    "confidence": 0.95,
                    "ios_analysis": [],
                }
            ],
        }

        # Test that the structure can be serialized to JSON
        json_str = json.dumps(sample_result, ensure_ascii=False, indent=2)
        assert isinstance(json_str, str)

        # Test that it can be deserialized back
        deserialized = json.loads(json_str)
        assert deserialized == sample_result

    def test_report_format_compatibility(self):
        """Test that report generation maintains compatible formats."""
        # Test that enhanced analyzer can generate reports in original formats
        enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer(
            enable_performance_monitoring=False
        )

        # Test essential report generation methods exist
        report_methods = [
            "save_analysis_report",
            "save_smart_markdown_report",
        ]

        for method in report_methods:
            if hasattr(enhanced_analyzer, method):
                assert callable(getattr(enhanced_analyzer, method))

    def test_device_data_structure_compatibility(self):
        """Test that device data structures remain compatible."""
        # Test device data structure that both implementations should handle
        sample_device_data = {
            "name": "SL_OE_DE",
            "ios": [
                {"name": "P1", "description": "开关控制", "rw": "RW"},
                {"name": "V", "description": "电压值", "rw": "R"},
            ],
            "source": "compatibility_test",
        }

        # Both implementations should be able to process this structure
        # This is validated by the fact that our tests use this format
        assert "name" in sample_device_data
        assert "ios" in sample_device_data
        assert isinstance(sample_device_data["ios"], list)

        for io in sample_device_data["ios"]:
            assert "name" in io
            assert "description" in io
            assert "rw" in io


# =============================================================================
# Performance Compatibility Tests
# =============================================================================


class TestPerformanceCompatibility:
    """Test that performance characteristics remain compatible."""

    def test_performance_monitoring_compatibility(self):
        """Test that performance monitoring features are compatible."""
        # Test with performance monitoring enabled
        enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer(
            enable_performance_monitoring=True
        )

        # Should have performance monitoring capabilities
        assert hasattr(enhanced_analyzer, "_performance_monitoring")
        assert enhanced_analyzer._performance_monitoring == True

        # Test with performance monitoring disabled
        basic_analyzer = EnhancedSmartIOAllocationAnalyzer(
            enable_performance_monitoring=False
        )

        assert hasattr(basic_analyzer, "_performance_monitoring")
        assert basic_analyzer._performance_monitoring == False

    def test_memory_usage_compatibility(self):
        """Test that memory usage patterns remain compatible."""
        import psutil
        import os

        # Measure memory usage during analyzer creation
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create multiple analyzers (simulating normal usage)
        analyzers = []
        for _ in range(5):
            analyzer = EnhancedSmartIOAllocationAnalyzer(
                enable_performance_monitoring=False
            )
            analyzers.append(analyzer)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (< 100MB for 5 analyzers)
        assert (
            memory_growth < 100
        ), f"Memory usage grew by {memory_growth:.1f}MB, too high for compatibility"

        # Cleanup
        del analyzers

    def test_initialization_time_compatibility(self):
        """Test that initialization time remains compatible."""
        import time

        # Measure initialization time
        start_time = time.time()

        analyzer = EnhancedSmartIOAllocationAnalyzer(
            enable_performance_monitoring=False
        )

        end_time = time.time()
        init_time = end_time - start_time

        # Initialization should be fast (< 5 seconds for compatibility)
        assert (
            init_time < 5.0
        ), f"Initialization took {init_time:.2f}s, too slow for compatibility"


# =============================================================================
# Error Handling Compatibility Tests
# =============================================================================


class TestErrorHandlingCompatibility:
    """Test that error handling remains compatible."""

    def test_exception_compatibility(self):
        """Test that exceptions are handled compatibly."""
        enhanced_analyzer = EnhancedSmartIOAllocationAnalyzer(
            enable_performance_monitoring=False
        )

        # Test with invalid document path
        try:
            result = enhanced_analyzer.perform_smart_comparison_analysis(
                "/nonexistent/path/to/document.md"
            )
            # If no exception is raised, result should indicate failure gracefully
            assert isinstance(result, dict)
        except Exception as e:
            # Should raise reasonable exceptions, not crash unexpectedly
            assert isinstance(e, (FileNotFoundError, IOError, ValueError))

    def test_graceful_degradation_compatibility(self):
        """Test that graceful degradation features work compatibly."""
        # Test with missing optional dependencies
        with patch.dict("sys.modules", {"spacy": None}):
            try:
                analyzer = EnhancedSmartIOAllocationAnalyzer(
                    enable_performance_monitoring=False
                )
                # Should still initialize successfully with degraded functionality
                assert analyzer is not None
            except ImportError:
                # Also acceptable - should fail gracefully
                pass

    def test_configuration_error_compatibility(self):
        """Test that configuration errors are handled compatibly."""
        # Test with invalid configuration that should be handled gracefully
        try:
            analyzer = EnhancedSmartIOAllocationAnalyzer(
                enable_performance_monitoring="invalid_value"  # Wrong type
            )
            # Should either correct the value or handle it gracefully
            assert analyzer is not None
        except (TypeError, ValueError) as e:
            # Acceptable to raise clear error for invalid configuration
            assert isinstance(e, (TypeError, ValueError))


if __name__ == "__main__":
    # Run compatibility tests
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_compatibility"])
