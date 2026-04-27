"""
Cache Layer Interface Definitions

This module defines the cache interfaces for the mapping tool architecture.
The cache layer provides data persistence and performance optimization
through various caching strategies and storage mechanisms.

Following ZEN MCP expert recommendations and project ABC patterns:
- Use ABC for core cache interfaces to maintain consistency
- Support multiple caching strategies (LRU, TTL, Manual)
- Provide both synchronous and asynchronous cache operations
- Include cache metrics and monitoring capabilities

Author: Architecture Designer Agent
Date: 2025-08-15
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Generic,
    TypeVar,
    Callable,
    Iterator,
    AsyncIterator,
    Tuple,
)

# Import core types
from ..data_types.core_types import (
    # Core Types
    DeviceData,
    AnalysisResult,
    ComparisonResult,
    ConfigValue,
    Timestamp,
    FilePath,
    # Configuration Types
    CacheConfig,
    # Enums
    CacheStrategy,
    # Generic Types
    CacheEntry,
    # Exceptions
    CacheError,
    MappingToolError,
)

# Type variables for generic cache support
K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type
T = TypeVar("T")  # Generic type


# =============================================================================
# Base Cache Interface - Foundation for All Cache Implementations
# =============================================================================


class BaseCache(ABC, Generic[K, V]):
    """
    Abstract base class for all cache implementations.

    Provides the foundational interface that all cache types must implement.
    Following the project's ABC tradition for consistent design patterns.
    Supports generic key-value typing for type safety.
    """

    def __init__(self, name: str = "BaseCache") -> None:
        """Initialize base cache with identification."""
        self._name = name
        self._initialized = False
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "size": 0}

    @property
    def name(self) -> str:
        """Get cache name for identification."""
        return self._name

    @property
    def is_initialized(self) -> bool:
        """Check if cache has been properly initialized."""
        return self._initialized

    @abstractmethod
    def initialize(self, config: CacheConfig) -> None:
        """
        Initialize cache with configuration.

        Args:
            config: Cache configuration parameters
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up cache resources and persistent storage."""
        pass

    @abstractmethod
    def get(self, key: K) -> Optional[V]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key to lookup

        Returns:
            Cached value or None if not found
        """
        pass

    @abstractmethod
    def set(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds (None for no expiration)
        """
        pass

    @abstractmethod
    def delete(self, key: K) -> bool:
        """
        Remove key from cache.

        Args:
            key: Cache key to remove

        Returns:
            True if key was removed, False if not found
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries from cache."""
        pass

    @abstractmethod
    def exists(self, key: K) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of entries in cache
        """
        pass

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache performance metrics
        """
        return self._stats.copy()

    def _record_hit(self) -> None:
        """Record cache hit for statistics."""
        self._stats["hits"] += 1

    def _record_miss(self) -> None:
        """Record cache miss for statistics."""
        self._stats["misses"] += 1

    def _record_eviction(self) -> None:
        """Record cache eviction for statistics."""
        self._stats["evictions"] += 1

    def _update_size(self, new_size: int) -> None:
        """Update cache size statistic."""
        self._stats["size"] = new_size

    def _mark_initialized(self) -> None:
        """Mark cache as successfully initialized."""
        self._initialized = True


# =============================================================================
# Data Cache - General Purpose Data Caching
# =============================================================================


class DataCache(BaseCache[str, Any]):
    """
    General-purpose data cache interface.

    Handles caching of arbitrary data objects with configurable
    eviction policies and persistence options. Suitable for caching
    device data, configuration, and intermediate results.
    """

    @abstractmethod
    def get_or_set(
        self, key: str, factory: Callable[[], Any], ttl: Optional[float] = None
    ) -> Any:
        """
        Get value from cache or compute and store if not found.

        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time-to-live for new value

        Returns:
            Cached or computed value
        """
        pass

    @abstractmethod
    def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of found key-value pairs
        """
        pass

    @abstractmethod
    def set_multi(self, items: Dict[str, Any], ttl: Optional[float] = None) -> None:
        """
        Set multiple values in cache.

        Args:
            items: Dictionary of key-value pairs to cache
            ttl: Time-to-live for all values
        """
        pass

    @abstractmethod
    def expire(self, key: str, ttl: float) -> bool:
        """
        Set expiration time for existing key.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds

        Returns:
            True if expiration was set
        """
        pass

    @abstractmethod
    def get_ttl(self, key: str) -> Optional[float]:
        """
        Get remaining time-to-live for key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds or None if no expiration
        """
        pass

    @abstractmethod
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Get all cache keys matching optional pattern.

        Args:
            pattern: Optional glob pattern for filtering

        Returns:
            List of matching cache keys
        """
        pass


# =============================================================================
# Result Cache - Analysis Result Caching
# =============================================================================


class ResultCache(BaseCache[str, Union[AnalysisResult, ComparisonResult]]):
    """
    Specialized cache for analysis and comparison results.

    Optimized for caching expensive analysis operations with
    intelligent cache invalidation based on input data changes.
    Includes result versioning and dependency tracking.
    """

    @abstractmethod
    def cache_analysis_result(
        self,
        input_hash: str,
        result: AnalysisResult,
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """
        Cache analysis result with dependency tracking.

        Args:
            input_hash: Hash of input data that produced result
            result: Analysis result to cache
            dependencies: Optional list of dependency identifiers
        """
        pass

    @abstractmethod
    def get_analysis_result(self, input_hash: str) -> Optional[AnalysisResult]:
        """
        Retrieve cached analysis result.

        Args:
            input_hash: Hash of input data

        Returns:
            Cached analysis result or None if not found/expired
        """
        pass

    @abstractmethod
    def cache_comparison_result(
        self, device_pair_hash: str, result: ComparisonResult
    ) -> None:
        """
        Cache device comparison result.

        Args:
            device_pair_hash: Hash of device pair being compared
            result: Comparison result to cache
        """
        pass

    @abstractmethod
    def get_comparison_result(
        self, device_pair_hash: str
    ) -> Optional[ComparisonResult]:
        """
        Retrieve cached comparison result.

        Args:
            device_pair_hash: Hash of device pair

        Returns:
            Cached comparison result or None if not found
        """
        pass

    @abstractmethod
    def invalidate_by_dependency(self, dependency: str) -> int:
        """
        Invalidate all results that depend on a specific dependency.

        Args:
            dependency: Dependency identifier

        Returns:
            Number of invalidated results
        """
        pass

    @abstractmethod
    def get_result_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about cached result.

        Args:
            key: Result cache key

        Returns:
            Metadata dictionary or None if not found
        """
        pass


# =============================================================================
# Config Cache - Configuration Caching
# =============================================================================


class ConfigCache(BaseCache[str, ConfigValue]):
    """
    Configuration-specific cache interface.

    Handles caching of configuration values with hot-reload support
    and change notification. Optimized for frequent configuration
    access patterns in the application.
    """

    @abstractmethod
    def load_from_source(self, source: FilePath) -> None:
        """
        Load configuration from source file into cache.

        Args:
            source: Path to configuration file
        """
        pass

    @abstractmethod
    def reload_if_changed(self, source: FilePath) -> bool:
        """
        Reload configuration if source file has changed.

        Args:
            source: Path to configuration file

        Returns:
            True if configuration was reloaded
        """
        pass

    @abstractmethod
    def get_nested(
        self, key_path: str, default: Optional[ConfigValue] = None
    ) -> ConfigValue:
        """
        Get nested configuration value using dot notation.

        Args:
            key_path: Dot-separated key path (e.g., "nlp.provider")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        pass

    @abstractmethod
    def set_nested(self, key_path: str, value: ConfigValue) -> None:
        """
        Set nested configuration value using dot notation.

        Args:
            key_path: Dot-separated key path
            value: Configuration value to set
        """
        pass

    @abstractmethod
    def watch_for_changes(
        self, key: str, callback: Callable[[str, ConfigValue], None]
    ) -> None:
        """
        Register callback for configuration changes.

        Args:
            key: Configuration key to watch
            callback: Function called when key changes
        """
        pass

    @abstractmethod
    def get_config_section(self, section: str) -> Dict[str, ConfigValue]:
        """
        Get all configuration values in a section.

        Args:
            section: Configuration section name

        Returns:
            Dictionary of section key-value pairs
        """
        pass

    @abstractmethod
    def persist_to_source(self, source: FilePath) -> None:
        """
        Save cached configuration back to source file.

        Args:
            source: Path to save configuration
        """
        pass


# =============================================================================
# Async Cache Interface - Asynchronous Cache Operations
# =============================================================================


class AsyncCache(ABC, Generic[K, V]):
    """
    Asynchronous cache interface for non-blocking operations.

    Provides async versions of cache operations for high-performance
    scenarios where cache operations should not block the event loop.
    """

    @abstractmethod
    async def async_get(self, key: K) -> Optional[V]:
        """
        Asynchronously retrieve value from cache.

        Args:
            key: Cache key to lookup

        Returns:
            Cached value or None if not found
        """
        pass

    @abstractmethod
    async def async_set(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """
        Asynchronously store value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds
        """
        pass

    @abstractmethod
    async def async_delete(self, key: K) -> bool:
        """
        Asynchronously remove key from cache.

        Args:
            key: Cache key to remove

        Returns:
            True if key was removed
        """
        pass

    @abstractmethod
    async def async_get_multi(self, keys: List[K]) -> Dict[K, V]:
        """
        Asynchronously get multiple values.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of found key-value pairs
        """
        pass

    @abstractmethod
    async def async_set_multi(
        self, items: Dict[K, V], ttl: Optional[float] = None
    ) -> None:
        """
        Asynchronously set multiple values.

        Args:
            items: Dictionary of key-value pairs
            ttl: Time-to-live for all values
        """
        pass


# =============================================================================
# Cache Manager - Cache Coordination and Management
# =============================================================================


class CacheManager(ABC):
    """
    Cache manager for coordinating multiple cache instances.

    Provides unified management of different cache types,
    handles cache warming, cleanup, and monitoring across
    the entire cache subsystem.
    """

    @abstractmethod
    def register_cache(self, name: str, cache: BaseCache[Any, Any]) -> None:
        """
        Register a cache instance with the manager.

        Args:
            name: Unique cache identifier
            cache: Cache instance to register
        """
        pass

    @abstractmethod
    def get_cache(self, name: str) -> Optional[BaseCache[Any, Any]]:
        """
        Get registered cache by name.

        Args:
            name: Cache identifier

        Returns:
            Cache instance or None if not found
        """
        pass

    @abstractmethod
    def initialize_all(self) -> None:
        """Initialize all registered caches."""
        pass

    @abstractmethod
    def cleanup_all(self) -> None:
        """Clean up all registered caches."""
        pass

    @abstractmethod
    def get_global_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all registered caches.

        Returns:
            Dictionary mapping cache names to their statistics
        """
        pass

    @abstractmethod
    def warm_caches(self, data_sources: Dict[str, Any]) -> None:
        """
        Pre-populate caches with commonly accessed data.

        Args:
            data_sources: Dictionary of data sources for cache warming
        """
        pass

    @abstractmethod
    def invalidate_all(self) -> None:
        """Invalidate all caches."""
        pass


# =============================================================================
# Cache Factory - Cache Instance Creation
# =============================================================================


class CacheFactory(ABC):
    """
    Abstract factory for creating cache instances.

    Provides standardized creation of cache implementations
    with proper configuration and dependency injection support.
    """

    @abstractmethod
    def create_data_cache(self, config: CacheConfig) -> DataCache:
        """
        Create data cache instance.

        Args:
            config: Cache configuration

        Returns:
            Configured data cache instance
        """
        pass

    @abstractmethod
    def create_result_cache(self, config: CacheConfig) -> ResultCache:
        """
        Create result cache instance.

        Args:
            config: Cache configuration

        Returns:
            Configured result cache instance
        """
        pass

    @abstractmethod
    def create_config_cache(self, config: CacheConfig) -> ConfigCache:
        """
        Create configuration cache instance.

        Args:
            config: Cache configuration

        Returns:
            Configured config cache instance
        """
        pass

    @abstractmethod
    def create_cache_manager(self) -> CacheManager:
        """
        Create cache manager instance.

        Returns:
            Cache manager for coordinating caches
        """
        pass


# =============================================================================
# Cache Utilities and Helpers
# =============================================================================


def generate_cache_key(*components: Any) -> str:
    """
    Generate consistent cache key from components.

    Args:
        components: Key components to combine

    Returns:
        Generated cache key string
    """
    return ":".join(str(component) for component in components)


def hash_device_data(device: DeviceData) -> str:
    """
    Generate consistent hash for device data.

    Args:
        device: Device data to hash

    Returns:
        Device data hash string
    """
    # Simple implementation - in practice would use more sophisticated hashing
    key_data = f"{device['device_id']}:{device['device_name']}:{len(device.get('io_ports', {}))}"
    return str(hash(key_data))


def hash_device_pair(device_a: DeviceData, device_b: DeviceData) -> str:
    """
    Generate consistent hash for device pair comparison.

    Args:
        device_a: First device
        device_b: Second device

    Returns:
        Device pair hash string
    """
    hash_a = hash_device_data(device_a)
    hash_b = hash_device_data(device_b)
    # Ensure consistent ordering regardless of parameter order
    if hash_a > hash_b:
        hash_a, hash_b = hash_b, hash_a
    return f"{hash_a}:{hash_b}"


class CacheMetrics:
    """
    Cache metrics collection and reporting.

    Provides standardized metrics collection for cache performance
    monitoring and optimization insights.
    """

    def __init__(self) -> None:
        self._metrics: Dict[str, Dict[str, float]] = {}

    def record_operation(
        self, cache_name: str, operation: str, duration: float, success: bool = True
    ) -> None:
        """
        Record cache operation metrics.

        Args:
            cache_name: Name of cache
            operation: Operation type (get, set, delete, etc.)
            duration: Operation duration in seconds
            success: Whether operation succeeded
        """
        if cache_name not in self._metrics:
            self._metrics[cache_name] = {}

        key = f"{operation}_{'success' if success else 'failure'}"
        self._metrics[cache_name][key] = duration

    def get_metrics(
        self, cache_name: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get collected metrics.

        Args:
            cache_name: Optional specific cache name

        Returns:
            Metrics dictionary
        """
        if cache_name:
            return {cache_name: self._metrics.get(cache_name, {})}
        return self._metrics.copy()


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Base Cache Classes
    "BaseCache",
    "AsyncCache",
    # Specialized Cache Interfaces
    "DataCache",
    "ResultCache",
    "ConfigCache",
    # Management Classes
    "CacheManager",
    "CacheFactory",
    # Utilities
    "CacheMetrics",
    "generate_cache_key",
    "hash_device_data",
    "hash_device_pair",
    # Type Variables
    "K",
    "V",
    "T",
]
