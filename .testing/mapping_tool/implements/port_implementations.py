"""
Core Port Layer Implementations

This module provides concrete implementations of the core port interfaces,
specifically FilePort and ConfigurationPort. These are the foundational
ports that other components depend on.

Implementation Strategy:
- StandardFilePort: Wraps pathlib and aiofiles for sync/async file operations
- JSONConfigurationPort: Configuration management with validation
- PortAdapterBase: Common functionality for all port adapters

Author: Architecture Implementation Agent
Date: 2025-08-15
"""

from __future__ import annotations

import json
import asyncio
from abc import ABC
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TextIO, BinaryIO

# Standard library async file support
try:
    import aiofiles
    import aiofiles.os

    ASYNC_FILE_SUPPORT = True
except ImportError:
    ASYNC_FILE_SUPPORT = False

# Import architecture interfaces
from ..architecture.ports import (
    ConfigurationPort,
    FilePort,
    AsyncFilePort,
    PortAdapter,
    PortFactory,
)

# Import core types
from ..data_types.core_types import (
    AnalysisConfig,
    ConfigValue,
    FilePath,
    LogLevel,
    ReportFormat,
    ConfigurationError,
    MappingToolError,
    validate_analysis_config,
)


# =============================================================================
# Port Adapter Base Implementation - Common Port Functionality
# =============================================================================


class PortAdapterBase(PortAdapter):
    """
    Base implementation for port adapters.

    Provides common functionality for port implementations including
    connection management, error handling, and resource cleanup.
    """

    def __init__(self, name: str = "PortAdapter") -> None:
        super().__init__(name)
        self._error_count = 0
        self._last_error: Optional[str] = None

    def connect(self) -> None:
        """Connect/initialize the port adapter."""
        try:
            self._initialize_port()
            self._mark_connected()
        except Exception as e:
            self._record_error(f"Failed to connect {self.name}: {e}")
            raise MappingToolError(f"Port connection failed: {e}")

    def disconnect(self) -> None:
        """Disconnect/cleanup the port adapter."""
        try:
            self._cleanup_port()
            self._mark_disconnected()
        except Exception as e:
            self._record_error(f"Failed to disconnect {self.name}: {e}")

    def get_error_count(self) -> int:
        """Get number of errors encountered."""
        return self._error_count

    def get_last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self._last_error

    def _initialize_port(self) -> None:
        """Initialize port-specific resources. Override in subclasses."""
        pass

    def _cleanup_port(self) -> None:
        """Cleanup port-specific resources. Override in subclasses."""
        pass

    def _record_error(self, error_message: str) -> None:
        """Record an error for monitoring."""
        self._error_count += 1
        self._last_error = error_message


# =============================================================================
# Standard File Port Implementation - File System Operations
# =============================================================================


class StandardFilePort(PortAdapterBase):
    """
    Standard file port implementation.

    Provides both synchronous and asynchronous file operations using
    pathlib for sync operations and aiofiles for async operations.
    Maintains backward compatibility with existing file operations.
    """

    def __init__(self, name: str = "StandardFilePort") -> None:
        super().__init__(name)
        self._encoding = "utf-8"
        self._async_enabled = ASYNC_FILE_SUPPORT

    def _initialize_port(self) -> None:
        """Initialize file port resources."""
        # Verify we can access the file system
        try:
            Path.cwd()  # Basic file system access test
        except Exception as e:
            raise MappingToolError(f"File system access failed: {e}")

    def read_text_file(self, path: FilePath, encoding: str = "utf-8") -> str:
        """Read text file content synchronously."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                raise MappingToolError(f"File not found: {path}")

            with open(file_path, "r", encoding=encoding) as f:
                return f.read()

        except Exception as e:
            self._record_error(f"Failed to read file {path}: {e}")
            raise MappingToolError(f"File read error: {e}")

    def write_text_file(
        self, path: FilePath, content: str, encoding: str = "utf-8"
    ) -> None:
        """Write text content to file synchronously."""
        try:
            file_path = Path(path)
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)

        except Exception as e:
            self._record_error(f"Failed to write file {path}: {e}")
            raise MappingToolError(f"File write error: {e}")

    def read_json_file(self, path: FilePath) -> Dict[str, Any]:
        """Read and parse JSON file."""
        try:
            content = self.read_text_file(path)
            return json.loads(content)

        except json.JSONDecodeError as e:
            self._record_error(f"Invalid JSON in file {path}: {e}")
            raise MappingToolError(f"JSON parse error: {e}")
        except Exception as e:
            self._record_error(f"Failed to read JSON file {path}: {e}")
            raise MappingToolError(f"JSON file read error: {e}")

    def write_json_file(self, path: FilePath, data: Dict[str, Any]) -> None:
        """Write data to JSON file."""
        try:
            content = json.dumps(data, indent=2, ensure_ascii=False)
            self.write_text_file(path, content)

        except Exception as e:
            self._record_error(f"Failed to write JSON file {path}: {e}")
            raise MappingToolError(f"JSON file write error: {e}")

    def file_exists(self, path: FilePath) -> bool:
        """Check if file exists."""
        try:
            return Path(path).exists()
        except Exception:
            return False

    def create_directory(self, path: FilePath) -> None:
        """Create directory if it doesn't exist."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._record_error(f"Failed to create directory {path}: {e}")
            raise MappingToolError(f"Directory creation error: {e}")

    def list_files(
        self, directory: FilePath, pattern: Optional[str] = None
    ) -> List[Path]:
        """List files in directory with optional pattern matching."""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                raise MappingToolError(f"Directory not found: {directory}")

            if not dir_path.is_dir():
                raise MappingToolError(f"Path is not a directory: {directory}")

            if pattern:
                return list(dir_path.glob(pattern))
            else:
                return [f for f in dir_path.iterdir() if f.is_file()]

        except Exception as e:
            self._record_error(f"Failed to list files in {directory}: {e}")
            raise MappingToolError(f"Directory listing error: {e}")

    def get_file_size(self, path: FilePath) -> int:
        """Get file size in bytes."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                raise MappingToolError(f"File not found: {path}")

            return file_path.stat().st_size

        except Exception as e:
            self._record_error(f"Failed to get size of file {path}: {e}")
            raise MappingToolError(f"File size error: {e}")


# =============================================================================
# Async File Port Implementation - Asynchronous File Operations
# =============================================================================


class AsyncFilePortImpl(PortAdapterBase):
    """
    Asynchronous file port implementation.

    Provides async file operations for I/O-intensive tasks without
    blocking the event loop. Falls back to sync operations if aiofiles
    is not available.
    """

    def __init__(self, name: str = "AsyncFilePort") -> None:
        super().__init__(name)
        self._async_enabled = ASYNC_FILE_SUPPORT

    def _initialize_port(self) -> None:
        """Initialize async file port."""
        if not self._async_enabled:
            # Use sync fallback but log warning
            import warnings

            warnings.warn(
                "aiofiles not available, falling back to synchronous file operations",
                UserWarning,
            )

    async def read_text_file_async(
        self, path: FilePath, encoding: str = "utf-8"
    ) -> str:
        """Asynchronously read text file content."""
        try:
            if self._async_enabled:
                async with aiofiles.open(path, mode="r", encoding=encoding) as f:
                    return await f.read()
            else:
                # Fallback to sync operation in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, self._sync_read_text_file, path, encoding
                )

        except Exception as e:
            self._record_error(f"Failed to async read file {path}: {e}")
            raise MappingToolError(f"Async file read error: {e}")

    async def write_text_file_async(
        self, path: FilePath, content: str, encoding: str = "utf-8"
    ) -> None:
        """Asynchronously write text content to file."""
        try:
            file_path = Path(path)

            if self._async_enabled:
                # Create parent directories
                file_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(path, mode="w", encoding=encoding) as f:
                    await f.write(content)
            else:
                # Fallback to sync operation in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, self._sync_write_text_file, path, content, encoding
                )

        except Exception as e:
            self._record_error(f"Failed to async write file {path}: {e}")
            raise MappingToolError(f"Async file write error: {e}")

    async def read_large_file_chunks(
        self, path: FilePath, chunk_size: int = 8192
    ) -> AsyncIterator[str]:
        """Read large file in chunks asynchronously."""
        try:
            if self._async_enabled:
                async with aiofiles.open(path, mode="r") as f:
                    while True:
                        chunk = await f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            else:
                # Fallback to sync chunked reading
                with open(path, "r") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                        # Yield control to prevent blocking
                        await asyncio.sleep(0)

        except Exception as e:
            self._record_error(f"Failed to read chunks from {path}: {e}")
            raise MappingToolError(f"Chunked file read error: {e}")

    async def process_files_batch(
        self,
        file_paths: List[FilePath],
        processor: Any,  # Callable[[str], Any]
    ) -> List[Any]:
        """Process multiple files concurrently."""
        try:
            tasks = []
            for file_path in file_paths:
                task = self._process_single_file(file_path, processor)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self._record_error(f"Failed to process {file_paths[i]}: {result}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)

            return processed_results

        except Exception as e:
            self._record_error(f"Failed to process file batch: {e}")
            raise MappingToolError(f"Batch file processing error: {e}")

    async def _process_single_file(self, path: FilePath, processor: Any) -> Any:
        """Process a single file with the given processor function."""
        content = await self.read_text_file_async(path)
        # Run processor in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, processor, content)

    def _sync_read_text_file(self, path: FilePath, encoding: str) -> str:
        """Synchronous fallback for text file reading."""
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    def _sync_write_text_file(
        self, path: FilePath, content: str, encoding: str
    ) -> None:
        """Synchronous fallback for text file writing."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding=encoding) as f:
            f.write(content)


# =============================================================================
# JSON Configuration Port Implementation - Configuration Management
# =============================================================================


class JSONConfigurationPort(PortAdapterBase):
    """
    JSON-based configuration port implementation.

    Handles loading, validation, and management of JSON configuration
    files with nested key support and validation.
    """

    def __init__(self, name: str = "JSONConfigurationPort") -> None:
        super().__init__(name)
        self._file_port = StandardFilePort(f"{name}_FilePort")
        self._config_data: Dict[str, Any] = {}
        self._config_source: Optional[str] = None

    def _initialize_port(self) -> None:
        """Initialize configuration port."""
        self._file_port.connect()

    def _cleanup_port(self) -> None:
        """Cleanup configuration port."""
        self._file_port.disconnect()
        self._config_data.clear()

    def load_config(self, source: Union[FilePath, Dict[str, Any]]) -> AnalysisConfig:
        """Load configuration from source."""
        try:
            if isinstance(source, (str, Path)):
                # Load from file
                self._config_source = str(source)
                raw_data = self._file_port.read_json_file(source)
            else:
                # Load from dictionary
                self._config_source = "<dict>"
                raw_data = source.copy()

            # Validate the configuration
            if not validate_analysis_config(raw_data):
                raise ConfigurationError("Configuration validation failed")

            # Store configuration data
            self._config_data = raw_data

            # Return as AnalysisConfig TypedDict
            return raw_data  # type: ignore

        except Exception as e:
            self._record_error(f"Failed to load config from {source}: {e}")
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Configuration load error: {e}")

    def get_setting(
        self, key: str, default: Optional[ConfigValue] = None
    ) -> ConfigValue:
        """Get specific configuration setting with dot notation support."""
        try:
            parts = key.split(".")
            current = self._config_data

            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default

            return current

        except Exception as e:
            self._record_error(f"Failed to get setting {key}: {e}")
            return default

    def set_setting(self, key: str, value: ConfigValue) -> None:
        """Set configuration setting value with dot notation support."""
        try:
            parts = key.split(".")
            current = self._config_data

            # Navigate to the parent of the target key
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    raise ConfigurationError(
                        f"Cannot set nested key {key}: {part} is not a dict"
                    )
                current = current[part]

            # Set the final value
            current[parts[-1]] = value

        except Exception as e:
            self._record_error(f"Failed to set setting {key}: {e}")
            raise ConfigurationError(f"Configuration set error: {e}")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration dictionary."""
        try:
            return validate_analysis_config(config)
        except Exception as e:
            self._record_error(f"Configuration validation error: {e}")
            return False

    def get_all_settings(self) -> Dict[str, ConfigValue]:
        """Get all configuration settings as flattened dictionary."""
        return self._flatten_dict(self._config_data)

    def save_config(self, target: Optional[FilePath] = None) -> None:
        """Save current configuration to file."""
        try:
            save_path = target or self._config_source
            if not save_path:
                raise ConfigurationError("No save path available")

            self._file_port.write_json_file(save_path, self._config_data)

        except Exception as e:
            self._record_error(f"Failed to save config: {e}")
            raise ConfigurationError(f"Configuration save error: {e}")

    def reload_config(self) -> AnalysisConfig:
        """Reload configuration from original source."""
        if not self._config_source or self._config_source == "<dict>":
            raise ConfigurationError("Cannot reload configuration from dict source")

        return self.load_config(self._config_source)

    def get_nested_config(self, section: str) -> Dict[str, Any]:
        """Get nested configuration section."""
        section_data = self.get_setting(section, {})
        if isinstance(section_data, dict):
            return section_data
        else:
            return {}

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, ConfigValue]:
        """Flatten nested dictionary with dot notation keys."""
        items: List[tuple] = []

        for key, value in d.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep).items())
            else:
                items.append((new_key, value))

        return dict(items)


# =============================================================================
# Port Factory Implementation - Port Instance Creation
# =============================================================================


class StandardPortFactory(PortFactory):
    """
    Standard port factory implementation.

    Creates instances of the standard port implementations with
    proper configuration and dependency injection.
    """

    def create_configuration_port(self, config: Dict[str, Any]) -> ConfigurationPort:
        """Create JSON configuration port implementation."""
        port = JSONConfigurationPort()
        port.connect()
        return port

    def create_file_port(self) -> FilePort:
        """Create standard file port implementation."""
        port = StandardFilePort()
        port.connect()
        return port

    def create_report_port(self) -> ReportPort:
        """Create report port implementation."""
        # Import here to avoid circular imports
        from .data_ports import MarkdownReportPort

        port = MarkdownReportPort()
        port.connect()
        return port

    def create_command_line_port(self) -> CommandLinePort:
        """Create command line port implementation."""
        # Import here to avoid circular imports
        from .interface_ports import ClickCommandLinePort

        port = ClickCommandLinePort()
        port.connect()
        return port

    def create_data_source_port(self, source_config: Dict[str, Any]) -> DataSourcePort:
        """Create data source port implementation."""
        # Import here to avoid circular imports
        from .data_ports import CSVDataSourcePort

        port = CSVDataSourcePort()
        port.connect()
        return port

    def create_logging_port(self, log_config: Dict[str, Any]) -> LoggingPort:
        """Create logging port implementation."""
        # Import here to avoid circular imports
        from .interface_ports import StructuredLoggingPort

        port = StructuredLoggingPort()
        port.connect()
        return port


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Base Classes
    "PortAdapterBase",
    # Core Port Implementations
    "StandardFilePort",
    "AsyncFilePortImpl",
    "JSONConfigurationPort",
    # Factory Implementation
    "StandardPortFactory",
]
