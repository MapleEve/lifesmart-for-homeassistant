"""
Architecture Module for Mapping Tool

Provides interface definitions for the port-service-cache architecture pattern.
Following the project's established ABC-based design conventions.
"""

from .services import (
    # Core Service Interfaces
    AnalysisService,
    NLPService,
    ComparisonService,
    ReportService,
    DocumentService,
    # Service Base Classes
    BaseService,
    AsyncService,
)

from .ports import (
    # Input/Output Ports
    ConfigurationPort,
    CommandLinePort,
    ReportPort,
    FilePort,
)

from .cache import (
    # Cache Layer Interfaces
    DataCache,
    ResultCache,
    ConfigCache,
    # Cache Base Classes
    BaseCache,
)

__all__ = [
    # Service Layer
    "AnalysisService",
    "NLPService",
    "ComparisonService",
    "ReportService",
    "DocumentService",
    "BaseService",
    "AsyncService",
    # Port Layer
    "ConfigurationPort",
    "CommandLinePort",
    "ReportPort",
    "FilePort",
    # Cache Layer
    "DataCache",
    "ResultCache",
    "ConfigCache",
    "BaseCache",
]
