"""
Factory Implementations for Dependency Injection

This module provides concrete factory implementations for creating
port and cache instances with proper configuration and dependency
injection support. Completes the implementation layer architecture.

Implementation Strategy:
- ConcretePortFactory: Complete port factory with all implementations
- ConcreteCacheFactory: Complete cache factory with configuration support
- Unified dependency injection system

Author: Architecture Implementation Agent
Date: 2025-08-15
"""

from __future__ import annotations

from typing import Any, Dict

# Import architecture interfaces
from ..architecture.ports import PortFactory
from ..architecture.cache import CacheFactory

# Import all implementations
from .cache_implementations import (
    DataCacheImpl,
    ResultCacheImpl,
    ConfigCacheImpl,
    CacheManagerImpl,
)

from .port_implementations import (
    StandardFilePort,
    JSONConfigurationPort,
    AsyncFilePortImpl,
)

from .data_ports import (
    CSVDataSourcePort,
    MarkdownReportPort,
)

from .interface_ports import (
    ClickCommandLinePort,
    StructuredLoggingPort,
)

# Import core types
from ..data_types.core_types import (
    CacheConfig,
    CacheStrategy,
    MappingToolError,
)


# =============================================================================
# Concrete Port Factory Implementation - Complete Port Creation
# =============================================================================


class ConcretePortFactory(PortFactory):
    """
    Complete port factory implementation.

    Creates instances of all port implementations with proper configuration
    and dependency injection. Provides a centralized factory for all
    port types used in the mapping tool architecture.
    """

    def __init__(self) -> None:
        self._port_cache: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the port factory."""
        self._initialized = True

    def create_configuration_port(
        self, config: Dict[str, Any]
    ) -> JSONConfigurationPort:
        """Create JSON configuration port implementation."""
        try:
            port = JSONConfigurationPort("MainConfigurationPort")
            port.connect()

            # Cache for reuse
            self._port_cache["configuration"] = port
            return port

        except Exception as e:
            raise MappingToolError(f"Failed to create configuration port: {e}")

    def create_file_port(self) -> StandardFilePort:
        """Create standard file port implementation."""
        try:
            port = StandardFilePort("MainFilePort")
            port.connect()

            # Cache for reuse
            self._port_cache["file"] = port
            return port

        except Exception as e:
            raise MappingToolError(f"Failed to create file port: {e}")

    def create_async_file_port(self) -> AsyncFilePortImpl:
        """Create async file port implementation."""
        try:
            port = AsyncFilePortImpl("MainAsyncFilePort")
            port.connect()

            # Cache for reuse
            self._port_cache["async_file"] = port
            return port

        except Exception as e:
            raise MappingToolError(f"Failed to create async file port: {e}")

    def create_report_port(self) -> MarkdownReportPort:
        """Create markdown report port implementation."""
        try:
            port = MarkdownReportPort("MainReportPort")
            port.connect()

            # Cache for reuse
            self._port_cache["report"] = port
            return port

        except Exception as e:
            raise MappingToolError(f"Failed to create report port: {e}")

    def create_command_line_port(self) -> ClickCommandLinePort:
        """Create click command line port implementation."""
        try:
            port = ClickCommandLinePort("MainCommandLinePort")
            port.connect()

            # Cache for reuse
            self._port_cache["cli"] = port
            return port

        except Exception as e:
            raise MappingToolError(f"Failed to create command line port: {e}")

    def create_data_source_port(
        self, source_config: Dict[str, Any]
    ) -> CSVDataSourcePort:
        """Create CSV data source port implementation."""
        try:
            port = CSVDataSourcePort("MainDataSourcePort")
            port.connect()

            # Configure based on source_config
            if "cache_enabled" in source_config:
                # Additional configuration could be applied here
                pass

            # Cache for reuse
            cache_key = f"data_source_{hash(str(source_config))}"
            self._port_cache[cache_key] = port
            return port

        except Exception as e:
            raise MappingToolError(f"Failed to create data source port: {e}")

    def create_logging_port(self, log_config: Dict[str, Any]) -> StructuredLoggingPort:
        """Create structured logging port implementation."""
        try:
            port = StructuredLoggingPort("MainLoggingPort")
            port.connect()

            # Configure logging based on log_config
            if "level" in log_config:
                try:
                    port.set_log_level(log_config["level"])
                except Exception:
                    pass  # Use default level

            if "file_path" in log_config:
                try:
                    port.add_file_handler(log_config["file_path"])
                except Exception:
                    pass  # File logging optional

            # Cache for reuse
            self._port_cache["logging"] = port
            return port

        except Exception as e:
            raise MappingToolError(f"Failed to create logging port: {e}")

    def get_cached_port(self, port_type: str) -> Any:
        """Get cached port instance by type."""
        return self._port_cache.get(port_type)

    def cleanup_all_ports(self) -> None:
        """Cleanup all created ports."""
        for port in self._port_cache.values():
            try:
                if hasattr(port, "disconnect"):
                    port.disconnect()
            except Exception:
                pass  # Continue cleanup even if one fails

        self._port_cache.clear()

    @property
    def is_initialized(self) -> bool:
        """Check if factory is initialized."""
        return self._initialized


# =============================================================================
# Concrete Cache Factory Implementation - Complete Cache Creation
# =============================================================================


class ConcreteCacheFactory(CacheFactory):
    """
    Complete cache factory implementation.

    Creates instances of all cache implementations with proper configuration
    and strategy selection. Supports multiple cache strategies and
    provides intelligent defaults based on usage patterns.
    """

    def __init__(self) -> None:
        self._cache_instances: Dict[str, Any] = {}
        self._default_config: CacheConfig = {
            "strategy": CacheStrategy.LRU,
            "max_size": 128,
            "ttl_seconds": 3600.0,
            "enable_persistence": False,
        }

    def create_data_cache(self, config: CacheConfig) -> DataCacheImpl:
        """Create data cache instance with configuration."""
        try:
            # Merge with defaults
            effective_config = self._merge_config(config)

            cache = DataCacheImpl("MainDataCache")
            cache.initialize(effective_config)

            # Store for management
            self._cache_instances["data"] = cache
            return cache

        except Exception as e:
            raise MappingToolError(f"Failed to create data cache: {e}")

    def create_result_cache(self, config: CacheConfig) -> ResultCacheImpl:
        """Create result cache instance with configuration."""
        try:
            # Merge with defaults, but use longer TTL for results
            effective_config = self._merge_config(config)
            if "ttl_seconds" not in config:
                effective_config["ttl_seconds"] = 7200.0  # 2 hours for results

            cache = ResultCacheImpl("MainResultCache")
            cache.initialize(effective_config)

            # Store for management
            self._cache_instances["result"] = cache
            return cache

        except Exception as e:
            raise MappingToolError(f"Failed to create result cache: {e}")

    def create_config_cache(self, config: CacheConfig) -> ConfigCacheImpl:
        """Create configuration cache instance with configuration."""
        try:
            # Merge with defaults, config cache should have longer TTL
            effective_config = self._merge_config(config)
            if "ttl_seconds" not in config:
                effective_config["ttl_seconds"] = None  # No expiration for config

            cache = ConfigCacheImpl("MainConfigCache")
            cache.initialize(effective_config)

            # Store for management
            self._cache_instances["config"] = cache
            return cache

        except Exception as e:
            raise MappingToolError(f"Failed to create config cache: {e}")

    def create_cache_manager(self) -> CacheManagerImpl:
        """Create cache manager instance."""
        try:
            manager = CacheManagerImpl()

            # Register all existing cache instances
            for cache_type, cache_instance in self._cache_instances.items():
                manager.register_cache(cache_type, cache_instance)

            # Initialize the manager
            manager.initialize_all()

            return manager

        except Exception as e:
            raise MappingToolError(f"Failed to create cache manager: {e}")

    def create_complete_cache_system(
        self,
        data_config: Optional[CacheConfig] = None,
        result_config: Optional[CacheConfig] = None,
        config_config: Optional[CacheConfig] = None,
    ) -> CacheManagerImpl:
        """Create complete cache system with all cache types."""
        try:
            # Create all cache types
            data_cache = self.create_data_cache(data_config or {})
            result_cache = self.create_result_cache(result_config or {})
            config_cache = self.create_config_cache(config_config or {})

            # Create and configure manager
            manager = self.create_cache_manager()

            return manager

        except Exception as e:
            raise MappingToolError(f"Failed to create complete cache system: {e}")

    def get_cached_instance(self, cache_type: str) -> Any:
        """Get existing cache instance by type."""
        return self._cache_instances.get(cache_type)

    def cleanup_all_caches(self) -> None:
        """Cleanup all created cache instances."""
        for cache in self._cache_instances.values():
            try:
                if hasattr(cache, "cleanup"):
                    cache.cleanup()
            except Exception:
                pass  # Continue cleanup even if one fails

        self._cache_instances.clear()

    def get_cache_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all cache instances."""
        stats = {}

        for cache_type, cache_instance in self._cache_instances.items():
            try:
                if hasattr(cache_instance, "get_stats"):
                    stats[cache_type] = cache_instance.get_stats()
                elif hasattr(cache_instance, "size"):
                    stats[cache_type] = {"size": cache_instance.size()}
                else:
                    stats[cache_type] = {"status": "unknown"}
            except Exception:
                stats[cache_type] = {"status": "error"}

        return stats

    def _merge_config(self, config: CacheConfig) -> CacheConfig:
        """Merge provided config with defaults."""
        merged = self._default_config.copy()
        merged.update(config)
        return merged

    def set_default_config(self, config: CacheConfig) -> None:
        """Set default configuration for new cache instances."""
        self._default_config.update(config)


# =============================================================================
# Integrated Factory Manager - Complete System Creation
# =============================================================================


class IntegratedFactoryManager:
    """
    Integrated factory manager for complete system creation.

    Provides a single point of access for creating complete port-service-cache
    systems with proper dependency injection and configuration management.
    """

    def __init__(self) -> None:
        self.port_factory = ConcretePortFactory()
        self.cache_factory = ConcreteCacheFactory()
        self._initialized = False

    def initialize(self, system_config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the complete factory system."""
        try:
            # Initialize individual factories
            self.port_factory.initialize()

            # Apply system-wide configuration
            if system_config:
                self._apply_system_config(system_config)

            self._initialized = True

        except Exception as e:
            raise MappingToolError(f"Failed to initialize factory manager: {e}")

    def create_complete_system(
        self,
        cache_config: Optional[Dict[str, CacheConfig]] = None,
        port_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create complete port-cache system."""
        try:
            if not self._initialized:
                self.initialize()

            system = {}

            # Create cache system
            cache_configs = cache_config or {}
            cache_manager = self.cache_factory.create_complete_cache_system(
                data_config=cache_configs.get("data"),
                result_config=cache_configs.get("result"),
                config_config=cache_configs.get("config"),
            )
            system["cache_manager"] = cache_manager

            # Create port system
            port_configs = port_config or {}

            system["file_port"] = self.port_factory.create_file_port()
            system["async_file_port"] = self.port_factory.create_async_file_port()
            system["config_port"] = self.port_factory.create_configuration_port(
                port_configs.get("config", {})
            )
            system["report_port"] = self.port_factory.create_report_port()
            system["cli_port"] = self.port_factory.create_command_line_port()
            system["data_source_port"] = self.port_factory.create_data_source_port(
                port_configs.get("data_source", {})
            )
            system["logging_port"] = self.port_factory.create_logging_port(
                port_configs.get("logging", {})
            )

            return system

        except Exception as e:
            raise MappingToolError(f"Failed to create complete system: {e}")

    def cleanup_system(self) -> None:
        """Cleanup the complete system."""
        try:
            self.cache_factory.cleanup_all_caches()
            self.port_factory.cleanup_all_ports()
        except Exception as e:
            # Log error but don't raise to ensure cleanup continues
            print(f"Warning: Error during system cleanup: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of the complete system."""
        status = {
            "initialized": self._initialized,
            "cache_statistics": self.cache_factory.get_cache_statistics(),
            "port_count": len(self.port_factory._port_cache),
            "cache_count": len(self.cache_factory._cache_instances),
        }

        return status

    def _apply_system_config(self, config: Dict[str, Any]) -> None:
        """Apply system-wide configuration."""
        # Apply cache defaults
        if "cache_defaults" in config:
            self.cache_factory.set_default_config(config["cache_defaults"])

        # Additional system configuration could be applied here
        # For example: logging levels, performance settings, etc.


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Factory Implementations
    "ConcretePortFactory",
    "ConcreteCacheFactory",
    # Integrated Management
    "IntegratedFactoryManager",
]
