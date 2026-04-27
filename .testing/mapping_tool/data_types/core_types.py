"""
Core Type Definitions for Mapping Tool Architecture

This module defines the foundational data types used throughout the
port-service-cache architecture. All type definitions follow Python 3.11+
modern typing standards and patterns established in the project.

Author: Architecture Designer Agent
Date: 2025-08-15
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    TypedDict,
    Protocol,
    runtime_checkable,
    Generic,
    TypeVar,
    Literal,
)

# Python version check for advanced typing features
if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    # Fallback for older Python versions
    TypeAlias = type

# =============================================================================
# Type Variables for Generic Support
# =============================================================================

T = TypeVar("T")
ConfigValueT = TypeVar(
    "ConfigValueT", bound=Union[str, int, float, bool, Dict[str, Any]]
)


# =============================================================================
# Type Aliases - Simple Types for Better Readability
# =============================================================================

DeviceID: TypeAlias = str
IOPort: TypeAlias = int
ConfigValue: TypeAlias = Union[str, int, float, bool, Dict[str, Any], List[Any]]
Timestamp: TypeAlias = datetime
FilePath: TypeAlias = Union[str, Path]
LogLevel: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# =============================================================================
# Enumeration Types - Status and Configuration Values
# =============================================================================


class AnalysisStatus(Enum):
    """Analysis processing status enumeration."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class NLPProvider(Enum):
    """Supported NLP providers for text analysis."""

    SPACY = "spacy"
    NLTK = "nltk"
    TRANSFORMERS = "transformers"
    NONE = "none"  # Fallback for basic text processing


class CacheStrategy(Enum):
    """Cache invalidation and eviction strategies."""

    LRU = "lru"
    TTL = "ttl"
    MANUAL = "manual"
    NONE = "none"


class ReportFormat(Enum):
    """Supported output report formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"
    PLAIN_TEXT = "plain"


class DevicePlatform(Enum):
    """Supported device platform categories."""

    LIGHT = "light"
    SWITCH = "switch"
    SENSOR = "sensor"
    COVER = "cover"
    FAN = "fan"
    CLIMATE = "climate"
    UNKNOWN = "unknown"


# =============================================================================
# Configuration Types - TypedDict for Structured Configuration
# =============================================================================


class NLPConfig(TypedDict, total=False):
    """Configuration for NLP processing components."""

    provider: NLPProvider
    model_name: Optional[str]
    language: str
    max_tokens: int
    timeout_seconds: float
    enable_caching: bool
    cache_size: int


class CacheConfig(TypedDict, total=False):
    """Configuration for caching layer components."""

    strategy: CacheStrategy
    max_size: int
    ttl_seconds: Optional[float]
    enable_persistence: bool
    storage_path: Optional[FilePath]


class AnalysisConfig(TypedDict, total=False):
    """Main configuration for analysis operations."""

    input_file: FilePath
    output_file: FilePath
    log_level: LogLevel
    enable_ai_analysis: bool
    nlp_config: NLPConfig
    cache_config: CacheConfig
    max_concurrent_jobs: int
    timeout_seconds: float


# =============================================================================
# Data Types - Core Business Objects
# =============================================================================


class DeviceData(TypedDict):
    """Device information and metadata."""

    device_id: DeviceID
    device_name: str
    platform: DevicePlatform
    io_ports: Dict[IOPort, Any]
    metadata: Dict[str, Any]
    created_at: Timestamp
    updated_at: Optional[Timestamp]


class ComparisonResult(TypedDict):
    """Result of device comparison analysis."""

    device_a: DeviceID
    device_b: DeviceID
    similarity_score: float
    differences: List[str]
    recommendations: List[str]
    confidence: float
    analysis_timestamp: Timestamp


class AnalysisResult(TypedDict):
    """Comprehensive analysis result container."""

    status: AnalysisStatus
    device_count: int
    comparisons: List[ComparisonResult]
    summary: str
    processing_time_seconds: float
    created_at: Timestamp
    metadata: Dict[str, Any]


class ReportData(TypedDict):
    """Structured report data for output generation."""

    title: str
    analysis_result: AnalysisResult
    format: ReportFormat
    generated_at: Timestamp
    version: str
    author: Optional[str]


# =============================================================================
# Generic Container Types
# =============================================================================


class CacheEntry(TypedDict, Generic[T]):
    """Generic cache entry with metadata."""

    key: str
    value: T
    created_at: Timestamp
    accessed_at: Timestamp
    ttl_seconds: Optional[float]
    access_count: int


class ServiceResponse(TypedDict, Generic[T]):
    """Generic service response wrapper."""

    success: bool
    data: Optional[T]
    error_message: Optional[str]
    processing_time_seconds: float
    timestamp: Timestamp


# =============================================================================
# Protocol Definitions - For Flexible Interface Contracts
# =============================================================================


@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialized."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Serializable:
        """Create object from dictionary representation."""
        ...


@runtime_checkable
class Cacheable(Protocol):
    """Protocol for objects that can be cached."""

    def cache_key(self) -> str:
        """Generate unique cache key for this object."""
        ...

    def cache_ttl(self) -> Optional[float]:
        """Return cache TTL in seconds, None for no expiration."""
        ...


# =============================================================================
# Exception Types - Custom Exceptions for Error Handling
# =============================================================================


class MappingToolError(Exception):
    """Base exception for mapping tool errors."""

    pass


class ConfigurationError(MappingToolError):
    """Raised when configuration is invalid or missing."""

    pass


class AnalysisError(MappingToolError):
    """Raised when analysis processing fails."""

    pass


class NLPError(MappingToolError):
    """Raised when NLP processing fails."""

    pass


class CacheError(MappingToolError):
    """Raised when cache operations fail."""

    pass


# =============================================================================
# Utility Functions - Type-Related Helper Functions
# =============================================================================


def create_timestamp() -> Timestamp:
    """Create current timestamp for data objects."""
    return datetime.now()


def validate_device_data(data: Dict[str, Any]) -> bool:
    """Validate if dictionary can be used as DeviceData."""
    required_fields = {
        "device_id",
        "device_name",
        "platform",
        "io_ports",
        "metadata",
        "created_at",
    }
    return all(field in data for field in required_fields)


def validate_analysis_config(config: Dict[str, Any]) -> bool:
    """Validate if dictionary can be used as AnalysisConfig."""
    required_fields = {"input_file", "output_file"}
    return all(field in config for field in required_fields)


# =============================================================================
# Module Export Management
# =============================================================================

__all__ = [
    # Type Variables
    "T",
    "ConfigValueT",
    # Type Aliases
    "DeviceID",
    "IOPort",
    "ConfigValue",
    "Timestamp",
    "FilePath",
    "LogLevel",
    # Enumerations
    "AnalysisStatus",
    "NLPProvider",
    "CacheStrategy",
    "ReportFormat",
    "DevicePlatform",
    # Configuration Types
    "NLPConfig",
    "CacheConfig",
    "AnalysisConfig",
    # Data Types
    "DeviceData",
    "ComparisonResult",
    "AnalysisResult",
    "ReportData",
    # Generic Types
    "CacheEntry",
    "ServiceResponse",
    # Protocols
    "Serializable",
    "Cacheable",
    # Exceptions
    "MappingToolError",
    "ConfigurationError",
    "AnalysisError",
    "NLPError",
    "CacheError",
    # Utility Functions
    "create_timestamp",
    "validate_device_data",
    "validate_analysis_config",
]
