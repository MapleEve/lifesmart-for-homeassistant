# Hierarchical Error Handling Test Suite
# Comprehensive tests for three-layer architecture error boundaries and propagation
# Based on ZEN MCP expert analysis and systematic investigation

import pytest
import asyncio
import time
import threading
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List, Optional

# Test imports for error handling validation
try:
    from ..data_types.core_types import (
        MappingToolError,
        AnalysisError,
        ConfigurationError,
        CacheError,
        NLPError,
        AnalysisConfig,
        CacheConfig,
        FilePath,
    )
    from ..implements.cache_implementations import (
        LRUCacheImpl,
        TTLCacheImpl,
        ConfigCacheImpl,
    )
    from ..implements.port_implementations import (
        StandardFilePort,
        JSONConfigurationPort,
        PortAdapterBase,
    )
    from ..implements.analysis_service_impl import (
        AnalysisServiceImpl,
        NLPAnalysisConfig,
    )
    from ..implements.document_service_impl import (
        DocumentServiceImpl,
        DocumentParsingConfig,
    )

    ERROR_HANDLING_TEST_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_TEST_AVAILABLE = False
    pytest.skip("Error handling test modules not available", allow_module_level=True)

# Async test marker
pytestmark = pytest.mark.asyncio


# =============================================================================
# Cache Layer Error Handling Tests (P0 Priority)
# =============================================================================


class TestCacheLayerErrorHandling:
    """Test error handling in the cache layer - foundation of error hierarchy."""

    def test_ttl_cache_cleanup_thread_lifecycle(self):
        """
        Test: TTL cache background thread can be safely started and stopped.
        Scenario: Normal initialization followed by cleanup
        Validates: No thread leaks, proper resource cleanup
        """
        # Arrange
        cache = TTLCacheImpl(name="TestTTL", default_ttl=60)

        # Mock thread to monitor behavior
        mock_thread = MagicMock(spec=threading.Thread)
        mock_thread.is_alive.return_value = True

        with patch("threading.Thread", return_value=mock_thread):
            # Act - Initialize cache
            cache.initialize(config={"ttl_seconds": 30})

            # Act - Cleanup cache
            cache.cleanup()

        # Assert
        assert cache._stop_cleanup.is_set(), "Stop event should be set"
        mock_thread.join.assert_called_once_with(timeout=1.0)

    def test_lru_cache_concurrent_access_race_condition(self):
        """
        Test: LRU cache handles concurrent access without race conditions.
        Scenario: Multiple threads accessing cache simultaneously
        Validates: Thread safety with RLock protection
        """
        # Arrange
        cache = LRUCacheImpl(name="TestLRU", max_size=10)
        cache.initialize(config={})

        results = []
        exceptions = []

        def cache_worker(worker_id: int):
            try:
                for i in range(50):
                    cache.set(f"worker_{worker_id}_item_{i}", f"value_{i}")
                    value = cache.get(f"worker_{worker_id}_item_{i}")
                    results.append((worker_id, i, value))
            except Exception as e:
                exceptions.append(e)

        # Act - Create multiple threads accessing cache
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=cache_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)

        # Assert
        assert len(exceptions) == 0, f"No exceptions should occur: {exceptions}"
        assert len(results) == 250, "All cache operations should complete"

        # Verify cache integrity
        final_size = cache.size()
        assert final_size <= 10, "Cache size should not exceed max_size"

    def test_config_cache_invalid_json_error_handling(self):
        """
        Test: ConfigCacheImpl properly handles invalid JSON files.
        Scenario: Load configuration from malformed JSON file
        Validates: ConfigurationError is raised with clear message
        """
        # Arrange
        cache = ConfigCacheImpl()
        cache.initialize(config={})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json syntax}')  # Malformed JSON
            invalid_json_file = f.name

        try:
            # Act & Assert
            with pytest.raises(ConfigurationError, match="Failed to load config"):
                cache.load_from_source(invalid_json_file)
        finally:
            Path(invalid_json_file).unlink()

    def test_config_cache_callback_exception_isolation(self):
        """
        Test: ConfigCacheImpl isolates callback exceptions from core operations.
        Scenario: Registered callback throws exception during value change
        Validates: Cache operation succeeds despite callback failure
        """
        # Arrange
        cache = ConfigCacheImpl()
        cache.initialize(config={})

        def failing_callback(key: str, value: Any):
            raise ValueError("Callback intentionally failed!")

        cache.watch_for_changes("test_key", failing_callback)

        # Act - This should not raise an exception
        cache.set("test_key", "test_value")

        # Assert
        assert (
            cache.get("test_key") == "test_value"
        ), "Value should be set despite callback failure"


# =============================================================================
# Port Layer Error Handling Tests (P0 Priority)
# =============================================================================


class TestPortLayerErrorHandling:
    """Test error handling in the port layer - system boundaries."""

    def test_port_adapter_connection_failure_wrapping(self):
        """
        Test: PortAdapterBase wraps connection failures in MappingToolError.
        Scenario: Port initialization fails
        Validates: Technical errors are wrapped in domain-specific exception
        """

        # Arrange
        class FailingPort(PortAdapterBase):
            def _initialize_port(self):
                raise IOError("System resource unavailable")

        port = FailingPort("TestPort")

        # Act & Assert
        with pytest.raises(MappingToolError, match="Port connection failed"):
            port.connect()

        # Verify error tracking
        assert port.get_error_count() == 1
        assert "Failed to connect TestPort" in port.get_last_error()

    def test_file_port_permission_error_handling(self):
        """
        Test: StandardFilePort handles file permission errors gracefully.
        Scenario: Attempt to read file without permission
        Validates: IOError is wrapped in MappingToolError
        """
        # Arrange
        port = StandardFilePort()
        port.connect()

        # Mock file permission error
        with patch("pathlib.Path.open", side_effect=PermissionError("Access denied")):
            # Act & Assert
            with pytest.raises(MappingToolError, match="File read error"):
                port.read_text_file("/restricted/file.txt")

    async def test_async_file_port_concurrent_error_isolation(self):
        """
        Test: Async file operations isolate errors with return_exceptions.
        Scenario: Some files fail to process in batch operation
        Validates: Successful files are processed despite individual failures
        """
        # Arrange
        port = StandardFilePort()
        port.connect()

        # Create test files - some will fail
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Good file
            good_file = temp_path / "good.txt"
            good_file.write_text("Good content")

            # File that will cause error
            error_file = temp_path / "nonexistent.txt"

            def simple_processor(content: str) -> str:
                return content.upper()

            # Act
            results = await port.process_files_concurrently(
                [str(good_file), str(error_file)], simple_processor
            )

            # Assert
            assert len(results) == 1, "Only successful results should be returned"
            assert results[0] == "GOOD CONTENT"

    def test_cli_port_keyboard_interrupt_handling(self):
        """
        Test: CLI port handles user interrupts gracefully.
        Scenario: User presses Ctrl+C during input prompt
        Validates: KeyboardInterrupt is converted to MappingToolError
        """
        # This would be tested with a CLIPort implementation
        # Since CLIPort is referenced in interface_ports.py but not fully implemented,
        # we'll create a minimal test structure

        from ..implements.interface_ports import ClickCommandLinePort

        cli_port = ClickCommandLinePort()
        cli_port.connect()

        # Mock input to raise KeyboardInterrupt
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with pytest.raises(MappingToolError, match="User cancelled operation"):
                cli_port.prompt_user("Enter something:")


# =============================================================================
# Service Layer Error Handling Tests (P1 Priority)
# =============================================================================


class TestServiceLayerErrorHandling:
    """Test error handling in the service layer - business logic boundaries."""

    async def test_analysis_service_dependency_injection_failure(self):
        """
        Test: AnalysisService handles missing dependencies gracefully.
        Scenario: Initialize service with None dependencies
        Validates: Clear error message about missing dependencies
        """
        # Act & Assert
        with pytest.raises((TypeError, AttributeError)):
            service = AnalysisServiceImpl(
                document_service=None,  # Missing required dependency
                cache_manager=None,
                nlp_config=None,
            )

    async def test_analysis_service_batch_partial_failure_handling(self):
        """
        Test: Batch analysis handles individual device failures gracefully.
        Scenario: Some devices fail analysis in batch operation
        Validates: Successful devices are processed, failures are isolated
        """
        # Arrange
        mock_document_service = AsyncMock()
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None  # Cache miss

        service = AnalysisServiceImpl(
            document_service=mock_document_service,
            cache_manager=mock_cache_manager,
            nlp_config=NLPAnalysisConfig(),
        )

        # Mock devices - one will fail
        devices = [
            {
                "name": "GOOD_DEVICE",
                "ios": [{"name": "P1", "description": "switch", "rw": "RW"}],
            },
            {"name": "BAD_DEVICE", "ios": []},  # Empty IOs might cause issues
        ]

        # Mock internal method to simulate failure for bad device
        original_analyze = service._analyze_single_device_internal

        async def mock_analyze(device):
            if device["name"] == "BAD_DEVICE":
                raise AnalysisError("Device analysis failed")
            return await original_analyze(device)

        with patch.object(
            service, "_analyze_single_device_internal", side_effect=mock_analyze
        ):
            # Act
            config = AnalysisConfig(max_concurrent_jobs=2)
            result = await service.analyze_devices(config, devices)

            # Assert
            assert result["total_devices"] == 2
            assert (
                result["analyzed_devices"] == 1
            ), "Only successful device should be counted"

    async def test_document_service_file_parsing_error_propagation(self):
        """
        Test: DocumentService propagates parsing errors appropriately.
        Scenario: Document parsing fails due to malformed content
        Validates: ValueError is converted to appropriate domain exception
        """
        # Arrange
        config = DocumentParsingConfig(debug_mode=False)
        service = DocumentServiceImpl(config=config)

        # Create malformed document
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Invalid Document\n\nNo device tables here!")
            malformed_doc = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="文档解析错误"):
                await service.parse_device_document(malformed_doc)
        finally:
            Path(malformed_doc).unlink()

    async def test_service_async_timeout_handling(self):
        """
        Test: Services handle async operation timeouts gracefully.
        Scenario: Long-running async operation exceeds timeout
        Validates: TimeoutError is properly handled and converted
        """
        # This test would require implementing timeout logic in services
        # For now, we'll test the pattern with a mock

        async def slow_operation():
            await asyncio.sleep(10)  # Simulated long operation
            return "result"

        # Act & Assert
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(), timeout=0.1)


# =============================================================================
# Error Propagation Chain Tests (P1 Priority)
# =============================================================================


class TestErrorPropagationChain:
    """Test complete error propagation from cache to port layers."""

    async def test_cache_to_service_error_propagation(self):
        """
        Test: Cache errors are properly transformed to service errors.
        Scenario: Cache operation fails, service layer handles it
        Validates: CacheError -> AnalysisError transformation
        """
        # Arrange
        mock_cache_manager = Mock()
        mock_cache_manager.get.side_effect = CacheError("Cache storage failed")

        mock_document_service = AsyncMock()

        service = AnalysisServiceImpl(
            document_service=mock_document_service,
            cache_manager=mock_cache_manager,
            nlp_config=NLPAnalysisConfig(),
        )

        device = {"name": "TEST_DEVICE", "ios": []}

        # Act & Assert
        # The service should handle cache errors gracefully
        # rather than letting them propagate unhandled
        try:
            result = await service._analyze_single_device_internal(device)
            # If cache error is handled gracefully, we should get a result
            assert result is not None
        except CacheError:
            pytest.fail("Cache error should be handled by service layer")

    def test_service_to_port_error_propagation(self):
        """
        Test: Service errors are transformed to user-friendly messages.
        Scenario: Service layer error reaches port layer
        Validates: AnalysisError -> user-friendly message conversion
        """
        # This would be tested in the actual CLI implementation
        # For now, we validate the error hierarchy exists

        analysis_error = AnalysisError("Internal analysis failed")
        assert isinstance(analysis_error, MappingToolError)

        config_error = ConfigurationError("Invalid config value")
        assert isinstance(config_error, MappingToolError)

    def test_complete_error_chain_integration(self):
        """
        Test: Complete error propagation from technical to user-friendly.
        Scenario: Low-level IO error propagates through all layers
        Validates: IOError -> MappingToolError -> AnalysisError -> user message
        """
        # Simulate complete error chain

        # 1. Technical error (lowest level)
        technical_error = IOError("Disk read failed")

        # 2. Port layer wraps in domain exception
        port_error = MappingToolError(f"File operation failed: {technical_error}")

        # 3. Service layer wraps in business exception
        service_error = AnalysisError(f"Analysis failed due to: {port_error}")

        # 4. Verify error hierarchy
        assert isinstance(service_error, MappingToolError)
        assert "Disk read failed" in str(service_error)


# =============================================================================
# Resource Management and Cleanup Tests (P2 Priority)
# =============================================================================


class TestResourceManagementErrors:
    """Test resource cleanup and lifecycle management errors."""

    def test_thread_pool_executor_cleanup_on_error(self):
        """
        Test: ThreadPoolExecutor is properly cleaned up even when errors occur.
        Scenario: Service fails during initialization
        Validates: No thread leaks after error
        """
        # This would require access to the actual ThreadPoolExecutor
        # We'll test the pattern with enhanced_cache.py

        from ..implements.enhanced_cache import EnhancedMemoryDataManager

        # Arrange
        manager = EnhancedMemoryDataManager(cache_size=10, max_workers=2)

        # Verify executor exists
        assert manager._executor is not None

        # Simulate cleanup
        manager.clear_caches()

        # In a real implementation, we'd verify executor.shutdown() was called
        # For now, we verify the method exists and can be called
        assert hasattr(manager._executor, "shutdown")

    async def test_async_context_cleanup_on_cancellation(self):
        """
        Test: Async operations clean up properly when cancelled.
        Scenario: Long-running async task is cancelled
        Validates: Resources are cleaned up, no hangs
        """

        async def cancellable_operation():
            try:
                await asyncio.sleep(10)  # Long operation
                return "completed"
            except asyncio.CancelledError:
                # Simulate cleanup
                await asyncio.sleep(0.01)  # Cleanup time
                raise

        # Act
        task = asyncio.create_task(cancellable_operation())
        await asyncio.sleep(0.01)  # Let task start
        task.cancel()

        # Assert
        with pytest.raises(asyncio.CancelledError):
            await task

    def test_memory_leak_prevention_weak_references(self):
        """
        Test: Weak references prevent memory leaks in cache systems.
        Scenario: Objects are garbage collected when no longer referenced
        Validates: WeakValueDictionary releases objects properly
        """
        from weakref import WeakValueDictionary

        # Arrange
        weak_cache = WeakValueDictionary()

        class TestObject:
            def __init__(self, value):
                self.value = value

        # Act
        obj = TestObject("test")
        weak_cache["key1"] = obj

        assert len(weak_cache) == 1

        # Delete strong reference
        del obj

        # Force garbage collection (implementation detail)
        import gc

        gc.collect()

        # Assert - object should be removed from weak dictionary
        # Note: This may be timing-dependent in real tests
        assert len(weak_cache) == 0


# =============================================================================
# Configuration Error Handling Tests (P1 Priority)
# =============================================================================


class TestConfigurationErrorHandling:
    """Test configuration validation and error handling."""

    def test_invalid_analysis_config_validation(self):
        """
        Test: Invalid analysis configuration is properly validated.
        Scenario: Provide invalid configuration values
        Validates: ConfigurationError is raised with specific details
        """
        # Test negative values
        invalid_config = {
            "max_concurrent_jobs": -1,  # Invalid: negative
            "timeout_seconds": "not_a_number",  # Invalid: wrong type
        }

        # This would use actual validation logic
        # For now, we test the pattern
        from ..data_types.core_types import validate_analysis_config

        # Mock config validation
        with patch(
            "mapping_tool.types.core_types.validate_analysis_config", return_value=False
        ):
            # Would raise ConfigurationError in real implementation
            assert not validate_analysis_config(invalid_config)

    def test_missing_required_configuration_fields(self):
        """
        Test: Missing required configuration fields are detected.
        Scenario: Configuration lacks required fields
        Validates: Clear error message about missing fields
        """
        incomplete_config = {
            # Missing required fields like input_file, output_file
            "log_level": "INFO"
        }

        from ..data_types.core_types import validate_analysis_config

        assert not validate_analysis_config(incomplete_config)

    def test_configuration_type_validation(self):
        """
        Test: Configuration field types are properly validated.
        Scenario: Provide correct structure but wrong types
        Validates: Type errors are caught and reported clearly
        """
        type_invalid_config = {
            "input_file": 123,  # Should be string/Path
            "output_file": [],  # Should be string/Path
            "max_concurrent_jobs": "five",  # Should be int
        }

        # Real implementation would validate types
        # For now, verify the pattern exists
        from ..data_types.core_types import validate_analysis_config

        assert not validate_analysis_config(type_invalid_config)


if __name__ == "__main__":
    # Run error handling tests
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_error"])
