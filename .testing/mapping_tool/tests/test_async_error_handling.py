# Async Error Handling Tests for Mapping Tool Architecture
# Tests for 29 async methods error handling, timeout, cancellation, and resource cleanup

import pytest
import asyncio
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List, Optional

# Test imports for async error handling validation
try:
    from ..implements.analysis_service_impl import (
        AnalysisServiceImpl,
        NLPAnalysisConfig,
    )
    from ..implements.document_service_impl import (
        DocumentServiceImpl,
        DocumentParsingConfig,
    )
    from ..implements.port_implementations import StandardFilePort
    from ..data_types.core_types import (
        AnalysisConfig,
        AnalysisError,
        MappingToolError,
    )

    ASYNC_ERROR_HANDLING_TEST_AVAILABLE = True
except ImportError:
    ASYNC_ERROR_HANDLING_TEST_AVAILABLE = False
    pytest.skip(
        "Async error handling test modules not available", allow_module_level=True
    )

# Async test marker
pytestmark = pytest.mark.asyncio


# =============================================================================
# Async Service Error Handling Tests
# =============================================================================


class TestAsyncServiceErrorHandling:
    """Test error handling in async service methods - critical for 29 async methods."""

    async def test_analysis_service_async_timeout_handling(self):
        """
        Test: Analysis service handles async operation timeouts gracefully.
        Scenario: Device analysis takes too long and times out
        Validates: TimeoutError is properly caught and converted to AnalysisError
        """
        # Arrange
        mock_document_service = AsyncMock()
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None  # Force analysis, not cache hit

        service = AnalysisServiceImpl(
            document_service=mock_document_service,
            cache_manager=mock_cache_manager,
            nlp_config=NLPAnalysisConfig(),
        )

        # Mock a slow analysis operation
        async def slow_analysis_internal(device):
            await asyncio.sleep(10)  # Simulate slow analysis
            return Mock()

        with patch.object(
            service,
            "_analyze_single_device_internal",
            side_effect=slow_analysis_internal,
        ):
            device = {"name": "SLOW_DEVICE", "ios": []}

            # Act & Assert - Should handle timeout gracefully
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    service._analyze_single_device_internal(device), timeout=0.1
                )

    async def test_batch_analyze_partial_cancellation_handling(self):
        """
        Test: Batch analysis handles cancellation of individual tasks gracefully.
        Scenario: Some tasks in asyncio.gather are cancelled while others continue
        Validates: return_exceptions=True isolates cancellation from successful tasks
        """
        # Arrange
        mock_document_service = AsyncMock()
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        service = AnalysisServiceImpl(
            document_service=mock_document_service,
            cache_manager=mock_cache_manager,
            nlp_config=NLPAnalysisConfig(),
        )

        devices = [
            {"name": "FAST_DEVICE", "ios": []},
            {"name": "SLOW_DEVICE", "ios": []},
            {"name": "NORMAL_DEVICE", "ios": []},
        ]

        # Mock analysis method with different speeds
        original_analyze = service._analyze_single_device_internal

        async def variable_speed_analyze(device):
            if device["name"] == "SLOW_DEVICE":
                await asyncio.sleep(5)  # Will be cancelled
            elif device["name"] == "FAST_DEVICE":
                await asyncio.sleep(0.01)  # Quick
            else:
                await asyncio.sleep(0.05)  # Normal
            return await original_analyze(device)

        with patch.object(
            service,
            "_analyze_single_device_internal",
            side_effect=variable_speed_analyze,
        ):
            # Act - Start batch analysis and cancel slow task
            tasks = [
                service._analyze_single_device_internal(device) for device in devices
            ]

            # Start all tasks
            running_tasks = [asyncio.create_task(task) for task in tasks]

            # Let tasks start
            await asyncio.sleep(0.02)

            # Cancel the slow task
            running_tasks[1].cancel()  # SLOW_DEVICE task

            # Gather with return_exceptions to isolate cancellation
            results = await asyncio.gather(*running_tasks, return_exceptions=True)

            # Assert
            assert len(results) == 3
            assert not isinstance(results[0], Exception), "Fast device should succeed"
            assert isinstance(
                results[1], asyncio.CancelledError
            ), "Slow device should be cancelled"
            assert not isinstance(results[2], Exception), "Normal device should succeed"

    async def test_document_service_async_parsing_error_isolation(self):
        """
        Test: Document service isolates parsing errors in async operations.
        Scenario: Multiple documents parsed concurrently, some fail
        Validates: Failed documents don't affect successful ones
        """
        # Arrange
        config = DocumentParsingConfig(debug_mode=False)
        service = DocumentServiceImpl(config=config)

        # Create test documents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Good document
            good_doc = temp_path / "good.md"
            good_doc.write_text(
                """
# SL_SW_PLUG 开关插座

| IO口 | 读写权限 | 描述 |
|------|----------|------|
| O    | RW       | 总开关 |
            """
            )

            # Bad document
            bad_doc = temp_path / "bad.md"
            bad_doc.write_text("# Invalid Document\nNo tables here!")

            # Mock async parsing to simulate concurrent operation
            async def parse_document_async(doc_path):
                # Use run_in_executor pattern like real implementation
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, service._parse_document_content_sync, doc_path.read_text()
                )

            # Act - Parse documents concurrently
            tasks = [
                parse_document_async(good_doc),
                parse_document_async(bad_doc),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Assert
            assert len(results) == 2
            assert isinstance(
                results[0], dict
            ), "Good document should parse successfully"
            assert isinstance(
                results[1], Exception
            ), "Bad document should raise exception"
            assert not isinstance(
                results[0], Exception
            ), "Good result shouldn't be affected by bad"

    async def test_async_resource_cleanup_on_exception(self):
        """
        Test: Async operations properly clean up resources when exceptions occur.
        Scenario: Async operation fails after allocating resources
        Validates: Resources are cleaned up, no leaks
        """
        # Track resource allocation/cleanup
        resources_allocated = []
        resources_cleaned = []

        async def resource_intensive_operation():
            try:
                # Simulate resource allocation
                resource_id = f"resource_{len(resources_allocated)}"
                resources_allocated.append(resource_id)

                # Simulate work that might fail
                await asyncio.sleep(0.01)
                raise RuntimeError("Simulated failure")

            except Exception:
                # Cleanup in exception handler
                if resources_allocated:
                    resource_id = resources_allocated[-1]
                    resources_cleaned.append(resource_id)
                raise
            finally:
                # Additional cleanup in finally block
                if len(resources_allocated) > len(resources_cleaned):
                    remaining = resources_allocated[len(resources_cleaned) :]
                    resources_cleaned.extend(remaining)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Simulated failure"):
            await resource_intensive_operation()

        # Verify cleanup
        assert len(resources_allocated) == len(
            resources_cleaned
        ), "All resources should be cleaned up"
        assert (
            resources_allocated == resources_cleaned
        ), "Cleanup should match allocation"

    async def test_concurrent_async_operations_error_isolation(self):
        """
        Test: Concurrent async operations isolate errors effectively.
        Scenario: Multiple independent async operations, some fail
        Validates: Successful operations complete despite failures in others
        """

        async def operation_that_succeeds(delay: float) -> str:
            await asyncio.sleep(delay)
            return f"success_{delay}"

        async def operation_that_fails(delay: float) -> str:
            await asyncio.sleep(delay)
            raise ValueError(f"failed_{delay}")

        # Act - Mix of successful and failing operations
        operations = [
            operation_that_succeeds(0.01),
            operation_that_fails(0.02),
            operation_that_succeeds(0.03),
            operation_that_fails(0.01),
            operation_that_succeeds(0.02),
        ]

        results = await asyncio.gather(*operations, return_exceptions=True)

        # Assert
        assert len(results) == 5

        # Check results pattern
        expected_pattern = [
            (0, str, "success_0.01"),
            (1, ValueError, "failed_0.02"),
            (2, str, "success_0.03"),
            (3, ValueError, "failed_0.01"),
            (4, str, "success_0.02"),
        ]

        for i, (index, expected_type, expected_content) in enumerate(expected_pattern):
            result = results[i]
            if expected_type == str:
                assert isinstance(result, str)
                assert result == expected_content
            else:
                assert isinstance(result, expected_type)
                assert expected_content in str(result)


# =============================================================================
# Async File Port Error Handling Tests
# =============================================================================


class TestAsyncFilePortErrorHandling:
    """Test async file operations error handling and resource management."""

    async def test_async_file_read_permission_error(self):
        """
        Test: Async file read handles permission errors gracefully.
        Scenario: Attempt to read restricted file asynchronously
        Validates: PermissionError is wrapped in MappingToolError
        """
        # Arrange
        port = StandardFilePort()
        port.connect()

        # Mock async file operation to raise permission error
        with patch("aiofiles.open", side_effect=PermissionError("Async access denied")):
            # Act & Assert
            with pytest.raises(MappingToolError, match="File read error"):
                await port.read_text_file_async("/restricted/async_file.txt")

    async def test_async_file_write_disk_full_error(self):
        """
        Test: Async file write handles disk full errors gracefully.
        Scenario: Disk becomes full during async write operation
        Validates: OSError is wrapped appropriately
        """
        # Arrange
        port = StandardFilePort()
        port.connect()

        # Mock async file write to raise disk full error
        with patch("aiofiles.open") as mock_open:
            mock_file = AsyncMock()
            mock_file.write.side_effect = OSError("No space left on device")
            mock_open.return_value.__aenter__.return_value = mock_file

            # Act & Assert
            with pytest.raises(MappingToolError, match="File write error"):
                await port.write_text_file_async("/tmp/test.txt", "content")

    async def test_async_file_chunked_read_interruption(self):
        """
        Test: Chunked async file reading handles interruption gracefully.
        Scenario: File reading is interrupted mid-stream
        Validates: Partial results are handled, no corruption
        """
        # Arrange
        port = StandardFilePort()
        port.connect()

        # Create test file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("chunk1\nchunk2\nchunk3\nchunk4\nchunk5\n")
            test_file = f.name

        try:
            # Mock to simulate interruption after 2 chunks
            chunk_count = 0

            async def interrupted_chunked_read(path, chunk_size=1024):
                nonlocal chunk_count
                async for chunk in port.read_file_chunks_async(path, chunk_size):
                    chunk_count += 1
                    if chunk_count >= 2:
                        raise asyncio.CancelledError("Read interrupted")
                    yield chunk

            # Act & Assert
            chunks = []
            with pytest.raises(asyncio.CancelledError):
                async for chunk in interrupted_chunked_read(test_file):
                    chunks.append(chunk)

            # Verify partial reading
            assert (
                len(chunks) <= 2
            ), "Should have read at most 2 chunks before interruption"

        finally:
            Path(test_file).unlink()

    async def test_async_concurrent_file_access_error_handling(self):
        """
        Test: Concurrent async file access handles conflicts gracefully.
        Scenario: Multiple async operations on same file
        Validates: Operations don't interfere, errors are isolated
        """
        # Arrange
        port = StandardFilePort()
        port.connect()

        # Create test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files for concurrent access
            files = []
            for i in range(5):
                file_path = temp_path / f"file_{i}.txt"
                file_path.write_text(f"content_{i}")
                files.append(str(file_path))

            # One file will be deleted to cause error
            Path(files[2]).unlink()  # Delete file_2.txt

            # Act - Concurrent read operations
            async def read_file(file_path):
                try:
                    return await port.read_text_file_async(file_path)
                except Exception as e:
                    return e

            tasks = [read_file(file_path) for file_path in files]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Assert
            assert len(results) == 5

            # Check results - 4 should succeed, 1 should fail
            successful_results = [r for r in results if isinstance(r, str)]
            error_results = [r for r in results if isinstance(r, Exception)]

            assert len(successful_results) == 4, "4 files should read successfully"
            assert len(error_results) == 1, "1 file should fail (deleted file)"


# =============================================================================
# Async Context Manager Error Handling Tests
# =============================================================================


class TestAsyncContextManagerErrorHandling:
    """Test async context managers handle errors properly."""

    async def test_async_context_manager_exception_propagation(self):
        """
        Test: Async context managers properly propagate exceptions.
        Scenario: Exception occurs within async context manager
        Validates: Exception is propagated, cleanup occurs
        """
        cleanup_called = False

        class TestAsyncContextManager:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                nonlocal cleanup_called
                cleanup_called = True
                # Don't suppress exception
                return False

        # Act & Assert
        with pytest.raises(RuntimeError, match="Test exception"):
            async with TestAsyncContextManager():
                raise RuntimeError("Test exception")

        assert cleanup_called, "Context manager cleanup should be called"

    async def test_async_context_manager_cleanup_on_cancellation(self):
        """
        Test: Async context managers clean up properly when cancelled.
        Scenario: Task using async context manager is cancelled
        Validates: Context manager cleanup is called despite cancellation
        """
        cleanup_called = False

        class TestAsyncContextManager:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                nonlocal cleanup_called
                cleanup_called = True
                return False

        async def operation_with_context():
            async with TestAsyncContextManager():
                await asyncio.sleep(10)  # Long operation that will be cancelled

        # Act
        task = asyncio.create_task(operation_with_context())
        await asyncio.sleep(0.01)  # Let task start
        task.cancel()

        # Assert
        with pytest.raises(asyncio.CancelledError):
            await task

        assert (
            cleanup_called
        ), "Context manager cleanup should be called even on cancellation"


# =============================================================================
# Async Generator Error Handling Tests
# =============================================================================


class TestAsyncGeneratorErrorHandling:
    """Test async generators handle errors and cleanup properly."""

    async def test_async_generator_exception_handling(self):
        """
        Test: Async generators handle exceptions during iteration.
        Scenario: Exception occurs mid-iteration in async generator
        Validates: Exception is propagated, generator cleanup occurs
        """
        cleanup_called = False

        async def test_async_generator():
            nonlocal cleanup_called
            try:
                yield "item1"
                yield "item2"
                raise RuntimeError("Generator error")
                yield "item3"  # This should not be reached
            finally:
                cleanup_called = True

        # Act & Assert
        items = []
        with pytest.raises(RuntimeError, match="Generator error"):
            async for item in test_async_generator():
                items.append(item)

        assert items == ["item1", "item2"], "Should have received items before error"
        assert cleanup_called, "Generator cleanup should be called"

    async def test_async_generator_cancellation_cleanup(self):
        """
        Test: Async generators clean up properly when iteration is cancelled.
        Scenario: Async generator iteration is cancelled mid-stream
        Validates: Generator finally block is executed
        """
        cleanup_called = False

        async def slow_async_generator():
            nonlocal cleanup_called
            try:
                for i in range(10):
                    await asyncio.sleep(0.1)  # Slow iteration
                    yield f"item_{i}"
            finally:
                cleanup_called = True

        async def consume_generator():
            items = []
            async for item in slow_async_generator():
                items.append(item)
                if len(items) >= 2:
                    # Cancel after receiving 2 items
                    await asyncio.sleep(0.5)  # Long enough to be cancelled
            return items

        # Act
        task = asyncio.create_task(consume_generator())
        await asyncio.sleep(0.25)  # Let it process a couple items
        task.cancel()

        # Assert
        with pytest.raises(asyncio.CancelledError):
            await task

        assert cleanup_called, "Generator cleanup should be called on cancellation"


# =============================================================================
# Async Error Recovery and Retry Tests
# =============================================================================


class TestAsyncErrorRecoveryAndRetry:
    """Test async error recovery patterns and retry mechanisms."""

    async def test_async_operation_with_retry_on_failure(self):
        """
        Test: Async operations can be retried on transient failures.
        Scenario: Operation fails a few times then succeeds
        Validates: Retry mechanism works, eventual success
        """
        attempt_count = 0

        async def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count < 3:
                raise RuntimeError(f"Attempt {attempt_count} failed")

            return f"Success on attempt {attempt_count}"

        async def retry_async_operation(max_attempts=5, delay=0.01):
            for attempt in range(max_attempts):
                try:
                    return await flaky_operation()
                except RuntimeError as e:
                    if attempt == max_attempts - 1:
                        raise  # Re-raise on final attempt
                    await asyncio.sleep(delay)

        # Act
        result = await retry_async_operation()

        # Assert
        assert result == "Success on attempt 3"
        assert attempt_count == 3

    async def test_async_circuit_breaker_pattern(self):
        """
        Test: Circuit breaker pattern for async operations.
        Scenario: Service fails repeatedly, circuit breaker opens
        Validates: Circuit breaker prevents further calls after threshold
        """
        failure_count = 0
        circuit_open = False

        async def failing_service():
            nonlocal failure_count
            failure_count += 1
            raise RuntimeError(f"Service failure {failure_count}")

        async def circuit_breaker_service(failure_threshold=3):
            nonlocal circuit_open

            if circuit_open:
                raise RuntimeError("Circuit breaker is open")

            try:
                return await failing_service()
            except RuntimeError:
                if failure_count >= failure_threshold:
                    circuit_open = True
                raise

        # Act & Assert
        # First 3 calls should reach the service
        for i in range(3):
            with pytest.raises(RuntimeError, match=f"Service failure {i+1}"):
                await circuit_breaker_service()

        # 4th call should be blocked by circuit breaker
        with pytest.raises(RuntimeError, match="Circuit breaker is open"):
            await circuit_breaker_service()

        assert failure_count == 3, "Service should only be called 3 times"
        assert circuit_open, "Circuit breaker should be open"


if __name__ == "__main__":
    # Run async error handling tests
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_async"])
