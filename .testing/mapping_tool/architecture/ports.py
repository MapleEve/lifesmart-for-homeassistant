"""
Port Layer Interface Definitions

This module defines the port interfaces for the mapping tool architecture.
Ports represent the boundaries of the application, handling input/output
operations and external system interactions.

Following ZEN MCP expert recommendations:
- Use Protocol for I/O boundaries to maintain flexibility
- Support both synchronous and asynchronous operations where needed
- Provide clear contracts for external system integration

Author: Architecture Designer Agent
Date: 2025-08-15
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Protocol,
    runtime_checkable,
    TextIO,
    BinaryIO,
    AsyncIterator,
    Iterator,
)

# Import core types
from ..data_types.core_types import (
    # Core Types
    DeviceData,
    AnalysisConfig,
    AnalysisResult,
    ReportData,
    ConfigValue,
    FilePath,
    LogLevel,
    # Enums
    ReportFormat,
    # Exceptions
    ConfigurationError,
    MappingToolError,
)

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    try:
        from typing_extensions import TypedDict
    except ImportError:
        # Fallback for environments without typing_extensions
        TypedDict = dict


# =============================================================================
# Configuration Port - Configuration Management Interface
# =============================================================================


@runtime_checkable
class ConfigurationPort(Protocol):
    """
    Port interface for configuration management and access.

    Handles loading, validation, and access to application configuration
    from various sources (files, environment variables, command line args).
    Uses Protocol for maximum flexibility in implementation approaches.
    """

    def load_config(self, source: Union[FilePath, Dict[str, Any]]) -> AnalysisConfig:
        """
        Load configuration from source.

        Args:
            source: Configuration source (file path or dict)

        Returns:
            Parsed and validated analysis configuration

        Raises:
            ConfigurationError: If config is invalid or cannot be loaded
        """
        ...

    def get_setting(
        self, key: str, default: Optional[ConfigValue] = None
    ) -> ConfigValue:
        """
        Get specific configuration setting.

        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        ...

    def set_setting(self, key: str, value: ConfigValue) -> None:
        """
        Set configuration setting value.

        Args:
            key: Configuration key
            value: New value to set
        """
        ...

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration dictionary.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid
        """
        ...

    def get_all_settings(self) -> Dict[str, ConfigValue]:
        """
        Get all configuration settings as dictionary.

        Returns:
            Complete configuration dictionary
        """
        ...


# =============================================================================
# Command Line Port - CLI Interface
# =============================================================================


@runtime_checkable
class CommandLinePort(Protocol):
    """
    Port interface for command-line interaction and argument processing.

    Handles command-line argument parsing, user input/output, and
    interactive prompts. Provides abstraction over CLI frameworks.
    """

    def parse_arguments(self, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Parse command-line arguments.

        Args:
            args: Command line arguments list (uses sys.argv if None)

        Returns:
            Parsed arguments as dictionary
        """
        ...

    def print_message(self, message: str, level: LogLevel = "INFO") -> None:
        """
        Print message to command line with appropriate formatting.

        Args:
            message: Message to display
            level: Log level for formatting/coloring
        """
        ...

    def print_error(self, error: str) -> None:
        """
        Print error message to stderr.

        Args:
            error: Error message to display
        """
        ...

    def prompt_user(self, question: str, default: Optional[str] = None) -> str:
        """
        Prompt user for input.

        Args:
            question: Question to ask user
            default: Default value if user provides no input

        Returns:
            User input string
        """
        ...

    def confirm_action(self, message: str) -> bool:
        """
        Ask user for yes/no confirmation.

        Args:
            message: Confirmation message

        Returns:
            True if user confirms, False otherwise
        """
        ...

    def display_progress(self, current: int, total: int, message: str = "") -> None:
        """
        Display progress information.

        Args:
            current: Current progress value
            total: Total progress value
            message: Optional progress message
        """
        ...


# =============================================================================
# File Port - File System Interface
# =============================================================================


@runtime_checkable
class FilePort(Protocol):
    """
    Port interface for file system operations.

    Provides abstraction over file I/O operations, supporting both
    synchronous and asynchronous file access patterns. Handles various
    file formats and provides path validation.
    """

    def read_text_file(self, path: FilePath, encoding: str = "utf-8") -> str:
        """
        Read text file content.

        Args:
            path: Path to text file
            encoding: Text encoding to use

        Returns:
            File content as string
        """
        ...

    def write_text_file(
        self, path: FilePath, content: str, encoding: str = "utf-8"
    ) -> None:
        """
        Write text content to file.

        Args:
            path: Path to write file
            content: Text content to write
            encoding: Text encoding to use
        """
        ...

    def read_json_file(self, path: FilePath) -> Dict[str, Any]:
        """
        Read and parse JSON file.

        Args:
            path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        ...

    def write_json_file(self, path: FilePath, data: Dict[str, Any]) -> None:
        """
        Write data to JSON file.

        Args:
            path: Path to write JSON file
            data: Data to serialize to JSON
        """
        ...

    def file_exists(self, path: FilePath) -> bool:
        """
        Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists
        """
        ...

    def create_directory(self, path: FilePath) -> None:
        """
        Create directory if it doesn't exist.

        Args:
            path: Directory path to create
        """
        ...

    def list_files(
        self, directory: FilePath, pattern: Optional[str] = None
    ) -> List[Path]:
        """
        List files in directory with optional pattern matching.

        Args:
            directory: Directory to list
            pattern: Optional glob pattern for filtering

        Returns:
            List of file paths
        """
        ...

    def get_file_size(self, path: FilePath) -> int:
        """
        Get file size in bytes.

        Args:
            path: Path to file

        Returns:
            File size in bytes
        """
        ...


# =============================================================================
# Report Port - Output and Reporting Interface
# =============================================================================


@runtime_checkable
class ReportPort(Protocol):
    """
    Port interface for report generation and output.

    Handles formatting and outputting analysis results in various formats.
    Supports multiple output destinations and formatting options.
    """

    def generate_text_report(
        self, data: AnalysisResult, template: Optional[str] = None
    ) -> str:
        """
        Generate plain text report from analysis results.

        Args:
            data: Analysis result data
            template: Optional template for formatting

        Returns:
            Formatted text report
        """
        ...

    def generate_json_report(self, data: AnalysisResult) -> Dict[str, Any]:
        """
        Generate JSON report from analysis results.

        Args:
            data: Analysis result data

        Returns:
            Report data as dictionary
        """
        ...

    def generate_markdown_report(self, data: AnalysisResult) -> str:
        """
        Generate Markdown report from analysis results.

        Args:
            data: Analysis result data

        Returns:
            Formatted Markdown report
        """
        ...

    def generate_html_report(
        self, data: AnalysisResult, style_template: Optional[str] = None
    ) -> str:
        """
        Generate HTML report from analysis results.

        Args:
            data: Analysis result data
            style_template: Optional CSS style template

        Returns:
            Formatted HTML report
        """
        ...

    def save_report(
        self, report_content: str, output_path: FilePath, format: ReportFormat
    ) -> ReportData:
        """
        Save report content to file.

        Args:
            report_content: Generated report content
            output_path: Path to save report
            format: Report format type

        Returns:
            Report metadata
        """
        ...

    def get_supported_formats(self) -> List[ReportFormat]:
        """
        Get list of supported report formats.

        Returns:
            List of supported format types
        """
        ...


# =============================================================================
# Async File Port - Asynchronous File Operations
# =============================================================================


@runtime_checkable
class AsyncFilePort(Protocol):
    """
    Port interface for asynchronous file operations.

    Provides async versions of file operations for I/O-intensive tasks.
    Useful for processing large files without blocking the event loop.
    """

    async def read_text_file_async(
        self, path: FilePath, encoding: str = "utf-8"
    ) -> str:
        """
        Asynchronously read text file content.

        Args:
            path: Path to text file
            encoding: Text encoding to use

        Returns:
            File content as string
        """
        ...

    async def write_text_file_async(
        self, path: FilePath, content: str, encoding: str = "utf-8"
    ) -> None:
        """
        Asynchronously write text content to file.

        Args:
            path: Path to write file
            content: Text content to write
            encoding: Text encoding to use
        """
        ...

    async def read_large_file_chunks(
        self, path: FilePath, chunk_size: int = 8192
    ) -> AsyncIterator[str]:
        """
        Read large file in chunks asynchronously.

        Args:
            path: Path to file
            chunk_size: Size of each chunk in bytes

        Yields:
            File content chunks
        """
        ...

    async def process_files_batch(
        self,
        file_paths: List[FilePath],
        processor: Any,  # Callable[[str], Any] but avoiding forward reference
    ) -> List[Any]:
        """
        Process multiple files concurrently.

        Args:
            file_paths: List of file paths to process
            processor: Function to process each file's content

        Returns:
            List of processing results
        """
        ...


# =============================================================================
# Data Source Port - External Data Interface
# =============================================================================


@runtime_checkable
class DataSourcePort(Protocol):
    """
    Port interface for external data source integration.

    Handles loading device data from various external sources such as
    databases, APIs, or structured files. Provides abstraction over
    different data source types.
    """

    def load_device_data(self, source_identifier: str) -> List[DeviceData]:
        """
        Load device data from external source.

        Args:
            source_identifier: Source identifier (file path, URL, etc.)

        Returns:
            List of loaded device data
        """
        ...

    def save_device_data(self, devices: List[DeviceData], destination: str) -> None:
        """
        Save device data to external destination.

        Args:
            devices: Device data to save
            destination: Destination identifier
        """
        ...

    def validate_source(self, source_identifier: str) -> bool:
        """
        Validate that data source is accessible and valid.

        Args:
            source_identifier: Source to validate

        Returns:
            True if source is valid and accessible
        """
        ...

    def get_source_metadata(self, source_identifier: str) -> Dict[str, Any]:
        """
        Get metadata about data source.

        Args:
            source_identifier: Source to get metadata for

        Returns:
            Source metadata dictionary
        """
        ...


# =============================================================================
# Logging Port - Logging and Monitoring Interface
# =============================================================================


@runtime_checkable
class LoggingPort(Protocol):
    """
    Port interface for logging and monitoring operations.

    Provides abstraction over logging frameworks and monitoring systems.
    Supports structured logging and metrics collection.
    """

    def log_message(
        self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log message with specified level and context.

        Args:
            level: Log level
            message: Log message
            context: Optional context data
        """
        ...

    def log_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log error with stack trace and context.

        Args:
            error: Exception to log
            context: Optional context data
        """
        ...

    def start_timing(self, operation_name: str) -> str:
        """
        Start timing an operation.

        Args:
            operation_name: Name of operation being timed

        Returns:
            Timer identifier for stopping the timer
        """
        ...

    def end_timing(self, timer_id: str) -> float:
        """
        End timing and get duration.

        Args:
            timer_id: Timer identifier from start_timing

        Returns:
            Operation duration in seconds
        """
        ...

    def record_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for metric
        """
        ...


# =============================================================================
# Port Adapter Base Class
# =============================================================================


class PortAdapter(ABC):
    """
    Base class for port adapters that implement port protocols.

    Provides common functionality for port implementations and
    ensures consistent error handling and resource management.
    """

    def __init__(self, name: str = "PortAdapter") -> None:
        """Initialize port adapter with name."""
        self._name = name
        self._connected = False

    @property
    def name(self) -> str:
        """Get adapter name."""
        return self._name

    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected/initialized."""
        return self._connected

    @abstractmethod
    def connect(self) -> None:
        """Connect/initialize the port adapter."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect/cleanup the port adapter."""
        pass

    def _mark_connected(self) -> None:
        """Mark adapter as connected."""
        self._connected = True

    def _mark_disconnected(self) -> None:
        """Mark adapter as disconnected."""
        self._connected = False


# =============================================================================
# Port Factory for Creating Port Implementations
# =============================================================================


class PortFactory(ABC):
    """
    Abstract factory for creating port implementations.

    Provides standardized creation of port adapters with proper
    configuration and dependency injection support.
    """

    @abstractmethod
    def create_configuration_port(self, config: Dict[str, Any]) -> ConfigurationPort:
        """Create configuration port implementation."""
        pass

    @abstractmethod
    def create_file_port(self) -> FilePort:
        """Create file port implementation."""
        pass

    @abstractmethod
    def create_report_port(self) -> ReportPort:
        """Create report port implementation."""
        pass

    @abstractmethod
    def create_command_line_port(self) -> CommandLinePort:
        """Create command line port implementation."""
        pass

    @abstractmethod
    def create_data_source_port(self, source_config: Dict[str, Any]) -> DataSourcePort:
        """Create data source port implementation."""
        pass

    @abstractmethod
    def create_logging_port(self, log_config: Dict[str, Any]) -> LoggingPort:
        """Create logging port implementation."""
        pass


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Core Port Interfaces
    "ConfigurationPort",
    "CommandLinePort",
    "FilePort",
    "ReportPort",
    # Async Interfaces
    "AsyncFilePort",
    # Extended Interfaces
    "DataSourcePort",
    "LoggingPort",
    # Base Classes
    "PortAdapter",
    "PortFactory",
]
