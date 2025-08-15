"""
Service Layer Interface Definitions

This module defines the core service interfaces for the mapping tool architecture.
Following the project's established ABC-based design pattern, all services use
abstract base classes to define strict contracts for implementations.

Based on ZEN MCP expert analysis recommendations:
- Use ABC pattern to maintain consistency with existing project style
- Support async/await for AI component performance optimization
- Provide clear separation of concerns between service responsibilities

Author: Architecture Designer Agent
Date: 2025-08-15
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    AsyncIterator,
    Callable,
    TypeVar,
    Generic,
)

from ..data_types.core_types import (
    # Core Types
    DeviceID,
    DeviceData,
    AnalysisResult,
    ComparisonResult,
    ReportData,
    Timestamp,
    FilePath,
    # Configuration Types
    AnalysisConfig,
    NLPConfig,
    # Enums
    AnalysisStatus,
    NLPProvider,
    ReportFormat,
    # Generic Types
    ServiceResponse,
    # Exceptions
    AnalysisError,
    NLPError,
    ConfigurationError,
)

# Type variables for generic service responses
T = TypeVar("T")
ServiceData = TypeVar("ServiceData")


# =============================================================================
# Base Service Classes - Foundation for All Services
# =============================================================================


class BaseService(ABC):
    """
    Abstract base class for all services in the mapping tool.

    Provides common functionality and enforces consistent interface patterns
    across all service implementations. Following the project's ABC tradition
    as identified in LifeSmartClientBase and DirectProcessor patterns.
    """

    def __init__(self, name: str = "BaseService") -> None:
        """Initialize base service with identification."""
        self._name = name
        self._initialized = False

    @property
    def name(self) -> str:
        """Get service name for logging and identification."""
        return self._name

    @property
    def is_initialized(self) -> bool:
        """Check if service has been properly initialized."""
        return self._initialized

    @abstractmethod
    def initialize(self) -> None:
        """Initialize service resources and dependencies."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up service resources and connections."""
        pass

    def _mark_initialized(self) -> None:
        """Mark service as successfully initialized."""
        self._initialized = True


class AsyncService(BaseService):
    """
    Abstract base class for asynchronous services.

    Extends BaseService with async/await support for AI components and
    I/O-intensive operations. Provides lifecycle management for async resources.
    """

    @abstractmethod
    async def async_initialize(self) -> None:
        """Asynchronously initialize service resources."""
        pass

    @abstractmethod
    async def async_cleanup(self) -> None:
        """Asynchronously clean up service resources."""
        pass

    async def health_check(self) -> bool:
        """Check if service is healthy and responsive."""
        return self.is_initialized


# =============================================================================
# Core Analysis Service - Main Business Logic Interface
# =============================================================================


class AnalysisService(AsyncService):
    """
    Core analysis service interface for device comparison and analysis.

    This is the main service that orchestrates the device analysis workflow,
    coordinating with NLP, comparison, and reporting services. Based on the
    analysis of SmartIOAllocationAnalyzer's core responsibilities.
    """

    @abstractmethod
    async def analyze_devices(
        self,
        config: AnalysisConfig,
        devices: List[DeviceData],
    ) -> AnalysisResult:
        """
        Perform comprehensive device analysis and comparison.

        Args:
            config: Analysis configuration and parameters
            devices: List of device data to analyze

        Returns:
            Complete analysis result with comparisons and insights

        Raises:
            AnalysisError: If analysis processing fails
            ConfigurationError: If config is invalid
        """
        pass

    @abstractmethod
    async def analyze_single_device(
        self,
        device: DeviceData,
        reference_devices: Optional[List[DeviceData]] = None,
    ) -> ComparisonResult:
        """
        Analyze a single device against reference data.

        Args:
            device: Target device to analyze
            reference_devices: Optional reference devices for comparison

        Returns:
            Comparison result with insights and recommendations
        """
        pass

    @abstractmethod
    async def batch_analyze(
        self,
        device_batches: List[List[DeviceData]],
        config: AnalysisConfig,
    ) -> AsyncIterator[AnalysisResult]:
        """
        Process multiple device batches asynchronously.

        Args:
            device_batches: List of device batches to process
            config: Analysis configuration

        Yields:
            Analysis results as they complete
        """
        pass

    @abstractmethod
    def get_analysis_progress(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get progress information for running analysis.

        Args:
            analysis_id: Unique analysis identifier

        Returns:
            Progress information including status and completion percentage
        """
        pass


# =============================================================================
# NLP Service - Natural Language Processing Interface
# =============================================================================


class NLPService(AsyncService):
    """
    Natural Language Processing service interface.

    Handles text analysis, semantic understanding, and document processing
    for device descriptions and comparison analysis. Supports multiple
    NLP providers with graceful degradation as found in pure_ai_analyzer.py.
    """

    @abstractmethod
    async def analyze_text(
        self,
        text: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Analyze text content for semantic meaning and structure.

        Args:
            text: Input text to analyze
            language: Language code for analysis

        Returns:
            Analysis results including entities, sentiment, and keywords
        """
        pass

    @abstractmethod
    async def compare_texts(
        self,
        text_a: str,
        text_b: str,
    ) -> float:
        """
        Calculate semantic similarity between two text passages.

        Args:
            text_a: First text for comparison
            text_b: Second text for comparison

        Returns:
            Similarity score between 0.0 and 1.0
        """
        pass

    @abstractmethod
    async def extract_device_features(
        self,
        device_description: str,
    ) -> Dict[str, Any]:
        """
        Extract device features and capabilities from text description.

        Args:
            device_description: Device description text

        Returns:
            Extracted features and capabilities
        """
        pass

    @abstractmethod
    def get_supported_providers(self) -> List[NLPProvider]:
        """
        Get list of available NLP providers.

        Returns:
            List of supported NLP provider types
        """
        pass

    @abstractmethod
    async def warm_up_models(self, providers: List[NLPProvider]) -> None:
        """
        Pre-load NLP models to reduce cold start latency.

        Args:
            providers: List of providers to warm up
        """
        pass


# =============================================================================
# Comparison Service - Device Comparison Logic
# =============================================================================


class ComparisonService(AsyncService):
    """
    Device comparison and analysis service interface.

    Handles the core logic for comparing devices, identifying similarities
    and differences, and generating recommendations. Abstracts the complex
    comparison logic found in the original SmartIOAllocationAnalyzer.
    """

    @abstractmethod
    async def compare_devices(
        self,
        device_a: DeviceData,
        device_b: DeviceData,
    ) -> ComparisonResult:
        """
        Compare two devices and generate detailed comparison result.

        Args:
            device_a: First device for comparison
            device_b: Second device for comparison

        Returns:
            Detailed comparison result with similarity metrics
        """
        pass

    @abstractmethod
    async def find_similar_devices(
        self,
        target_device: DeviceData,
        candidate_devices: List[DeviceData],
        threshold: float = 0.8,
    ) -> List[ComparisonResult]:
        """
        Find devices similar to target device from candidate list.

        Args:
            target_device: Device to find matches for
            candidate_devices: List of potential matches
            threshold: Minimum similarity threshold

        Returns:
            List of similar devices with comparison results
        """
        pass

    @abstractmethod
    async def classify_device_platform(
        self,
        device: DeviceData,
    ) -> str:
        """
        Classify device into appropriate platform category.

        Args:
            device: Device data to classify

        Returns:
            Platform classification (light, switch, sensor, etc.)
        """
        pass

    @abstractmethod
    def calculate_compatibility_score(
        self,
        device_a: DeviceData,
        device_b: DeviceData,
    ) -> float:
        """
        Calculate compatibility score between two devices.

        Args:
            device_a: First device
            device_b: Second device

        Returns:
            Compatibility score between 0.0 and 1.0
        """
        pass


# =============================================================================
# Report Service - Output Generation Interface
# =============================================================================


class ReportService(AsyncService):
    """
    Report generation and output formatting service interface.

    Handles conversion of analysis results into various output formats
    including JSON, Markdown, HTML, and CSV. Provides flexible reporting
    capabilities for different use cases.
    """

    @abstractmethod
    async def generate_report(
        self,
        analysis_result: AnalysisResult,
        format: ReportFormat,
        output_path: FilePath,
    ) -> ReportData:
        """
        Generate formatted report from analysis results.

        Args:
            analysis_result: Analysis data to include in report
            format: Desired output format
            output_path: Path to save the report

        Returns:
            Generated report data and metadata
        """
        pass

    @abstractmethod
    async def generate_summary_report(
        self,
        analysis_results: List[AnalysisResult],
        output_path: FilePath,
    ) -> ReportData:
        """
        Generate summary report from multiple analysis results.

        Args:
            analysis_results: List of analysis results to summarize
            output_path: Path to save the summary report

        Returns:
            Generated summary report data
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[ReportFormat]:
        """
        Get list of supported report output formats.

        Returns:
            List of supported format types
        """
        pass

    @abstractmethod
    async def validate_output_path(self, path: FilePath) -> bool:
        """
        Validate that output path is writable and accessible.

        Args:
            path: Output path to validate

        Returns:
            True if path is valid and writable
        """
        pass


# =============================================================================
# Document Service - Document Processing Interface
# =============================================================================


class DocumentService(AsyncService):
    """
    Document processing and parsing service interface.

    Handles loading, parsing, and processing of various document formats
    containing device data and configuration information. Abstracts the
    document handling logic from the core analysis workflow.
    """

    @abstractmethod
    async def load_device_data(
        self,
        file_path: FilePath,
    ) -> List[DeviceData]:
        """
        Load device data from file.

        Args:
            file_path: Path to device data file

        Returns:
            List of parsed device data objects
        """
        pass

    @abstractmethod
    async def parse_configuration(
        self,
        config_path: FilePath,
    ) -> AnalysisConfig:
        """
        Parse analysis configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Parsed analysis configuration
        """
        pass

    @abstractmethod
    async def save_device_data(
        self,
        devices: List[DeviceData],
        output_path: FilePath,
    ) -> None:
        """
        Save device data to file in standard format.

        Args:
            devices: Device data to save
            output_path: Path to save data file
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported document formats.

        Returns:
            List of supported file format extensions
        """
        pass

    @abstractmethod
    async def validate_document(
        self,
        file_path: FilePath,
    ) -> bool:
        """
        Validate document format and structure.

        Args:
            file_path: Path to document to validate

        Returns:
            True if document is valid and parseable
        """
        pass


# =============================================================================
# Service Factory and Registry
# =============================================================================


class ServiceFactory(ABC):
    """
    Abstract factory for creating service instances.

    Provides a standardized way to create and configure service instances
    with appropriate dependencies and configuration. Supports dependency
    injection patterns for better testability.
    """

    @abstractmethod
    def create_analysis_service(
        self,
        config: AnalysisConfig,
    ) -> AnalysisService:
        """Create configured analysis service instance."""
        pass

    @abstractmethod
    def create_nlp_service(
        self,
        config: NLPConfig,
    ) -> NLPService:
        """Create configured NLP service instance."""
        pass

    @abstractmethod
    def create_comparison_service(self) -> ComparisonService:
        """Create comparison service instance."""
        pass

    @abstractmethod
    def create_report_service(self) -> ReportService:
        """Create report service instance."""
        pass

    @abstractmethod
    def create_document_service(self) -> DocumentService:
        """Create document service instance."""
        pass


# =============================================================================
# Service Response Wrapper
# =============================================================================


class ServiceResult(Generic[T]):
    """
    Generic wrapper for service operation results.

    Provides consistent error handling and metadata for all service operations.
    Includes timing information and success/failure status for monitoring.
    """

    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        error: Optional[str] = None,
        processing_time: float = 0.0,
    ) -> None:
        self.success = success
        self.data = data
        self.error = error
        self.processing_time = processing_time
        self.timestamp = Timestamp.now() if hasattr(Timestamp, "now") else None

    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.success

    def get_data(self) -> T:
        """Get result data, raising exception if operation failed."""
        if not self.success:
            raise AnalysisError(self.error or "Service operation failed")
        return self.data

    def get_error(self) -> Optional[str]:
        """Get error message if operation failed."""
        return self.error if not self.success else None


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Base Classes
    "BaseService",
    "AsyncService",
    # Core Service Interfaces
    "AnalysisService",
    "NLPService",
    "ComparisonService",
    "ReportService",
    "DocumentService",
    # Factory and Utilities
    "ServiceFactory",
    "ServiceResult",
    # Type Variables
    "T",
    "ServiceData",
]
