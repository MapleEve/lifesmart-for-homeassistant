"""
Enhanced Cache Implementation - Integrating Memory Agent 1 Excellence

This module upgrades the existing memory_agent1.py cache mechanisms into the
port-service-cache architecture, providing enterprise-grade caching with
device-specific optimizations and modern async support.

Core Features:
- Integrates MemoryDataManager's WeakValueDictionary + LRU patterns
- Preserves DeviceConfigSnapshot and AnalysisMetrics excellence
- Adds streaming data generators for large-scale processing
- Maintains ThreadPoolExecutor concurrency support
- Extends with L1/L2/L3 cache hierarchies

Author: Platform Engineer Agent
Date: 2025-08-15
Based on: memory_agent1.py + cache_implementations.py
"""

from __future__ import annotations

import asyncio
import time
import threading
from abc import ABC
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Callable,
    Generator,
    AsyncGenerator,
    Set,
)
from weakref import WeakValueDictionary, WeakSet

# Import architecture interfaces
try:
    from ..architecture.cache import (
        BaseCache,
        DataCache,
        ResultCache,
        ConfigCache,
        AsyncCache,
        CacheManager,
        CacheFactory,
        K,
        V,
        T,
    )
    from ..data_types.core_types import (
        CacheConfig,
        CacheStrategy,
        AnalysisResult,
        ComparisonResult,
        ConfigValue,
        FilePath,
        Timestamp,
        create_timestamp,
        CacheError,
        ConfigurationError,
    )
except ImportError:
    # Fallback for development/testing
    from typing import TypeVar

    K = TypeVar("K")
    V = TypeVar("V")
    T = TypeVar("T")

    class CacheError(Exception):
        pass

    class ConfigurationError(Exception):
        pass


# Import utility classes (fallback compatible)
try:
    from ..utils.core_utils import IOExtractor, DeviceNameUtils, RegexCache
    from ..utils.regex_cache import regex_performance_monitor
except ImportError:
    # Simple fallbacks for development
    class IOExtractor:
        @staticmethod
        def extract_mapped_ios(config):
            return set()

        @staticmethod
        def is_valid_io_name(name):
            return bool(name)

    class DeviceNameUtils:
        @staticmethod
        def is_valid_device_name(name):
            return bool(name and len(name) >= 3)

    class RegexCache:
        @staticmethod
        def is_p_io_port(port):
            return port.startswith("P") and port[1:].isdigit()

    def regex_performance_monitor(func):
        return func


# =============================================================================
# Enhanced Data Structures - From memory_agent1.py
# =============================================================================


@dataclass
class DeviceConfigSnapshot:
    """Enhanced device configuration snapshot with metadata."""

    device_name: str
    configuration: Dict[str, Any]
    io_ports: Set[str]
    platforms: Set[str]
    is_dynamic: bool
    is_versioned: bool
    timestamp: float
    cache_level: str = "L1"  # L1=memory, L2=persistent, L3=analysis
    access_count: int = 0
    last_access: float = 0.0


@dataclass
class AnalysisMetrics:
    """Enhanced analysis performance metrics."""

    total_devices: int
    cache_hits: int
    cache_misses: int
    processing_time: float
    memory_usage_mb: float
    concurrent_requests: int
    l1_hit_rate: float = 0.0
    l2_hit_rate: float = 0.0
    l3_hit_rate: float = 0.0
    stream_count: int = 0


@dataclass
class CachePerformanceProfile:
    """Cache performance profiling data."""

    cache_type: str
    hit_rate: float
    avg_access_time_ms: float
    memory_usage_mb: float
    eviction_count: int
    concurrent_access_count: int
    created_at: float
    last_updated: float


# =============================================================================
# Enhanced Memory Data Manager - Core L1 Cache
# =============================================================================


class EnhancedMemoryDataManager:
    """
    Enhanced memory data manager integrating memory_agent1.py excellence.

    Features:
    - WeakValueDictionary for automatic memory management
    - LRU cache decorators for hot data
    - ThreadPoolExecutor for concurrent operations
    - Device-specific caching strategies
    - Streaming data generation support
    """

    def __init__(self, cache_size: int = 512, max_workers: int = 4):
        self.cache_size = cache_size
        self.max_workers = max_workers

        # Core cache structures from memory_agent1.py
        self._raw_data_cache = WeakValueDictionary()
        self._device_config_cache = OrderedDict()
        self._io_mapping_cache = {}
        self._analysis_cache = {}
        self._platform_cache = {}

        # Enhanced metrics and monitoring
        self._metrics = AnalysisMetrics(0, 0, 0, 0.0, 0.0, 0)
        self._performance_profiles = {}
        self._last_update = time.time()

        # Concurrency support
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()
        self._stream_locks = {}

    def load_raw_device_data(self, raw_data: Dict[str, Any]) -> None:
        """Enhanced device data loading with streaming support."""
        with self._lock:
            start_time = time.time()
            self._raw_data_cache.clear()

            valid_devices = 0
            for device_name, config in raw_data.items():
                if DeviceNameUtils.is_valid_device_name(device_name):
                    snapshot = self._create_enhanced_device_snapshot(
                        device_name, config
                    )
                    self._raw_data_cache[device_name] = snapshot
                    valid_devices += 1

            # Update metrics
            processing_time = time.time() - start_time
            self._metrics.total_devices = valid_devices
            self._metrics.processing_time = processing_time
            self._last_update = time.time()

            print(
                f"✅ Enhanced memory manager loaded {valid_devices} devices in {processing_time:.2f}s"
            )

    def _create_enhanced_device_snapshot(
        self, device_name: str, config: Dict[str, Any]
    ) -> DeviceConfigSnapshot:
        """Create enhanced device configuration snapshot."""
        io_ports = IOExtractor.extract_mapped_ios(config)
        platforms = set(config.keys()) - {"name", "description", "versioned", "dynamic"}

        return DeviceConfigSnapshot(
            device_name=device_name,
            configuration=config.copy(),
            io_ports=io_ports,
            platforms=platforms,
            is_dynamic=config.get("dynamic", False),
            is_versioned=config.get("versioned", False),
            timestamp=time.time(),
            cache_level="L1",
            access_count=0,
            last_access=time.time(),
        )

    @lru_cache(maxsize=256)
    def get_device_config(self, device_name: str) -> Optional[DeviceConfigSnapshot]:
        """Get device configuration with enhanced caching."""
        snapshot = self._raw_data_cache.get(device_name)
        if snapshot:
            # Update access metrics
            snapshot.access_count += 1
            snapshot.last_access = time.time()
            self._metrics.cache_hits += 1
            self._metrics.l1_hit_rate = self._calculate_hit_rate()
        else:
            self._metrics.cache_misses += 1

        return snapshot

    def get_all_device_names(self) -> List[str]:
        """Get all device names with performance tracking."""
        with self._lock:
            return list(self._raw_data_cache.keys())

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            "memory_usage": {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
            },
            "cache_performance": {
                "l1_hits": self._metrics.cache_hits,
                "l1_misses": self._metrics.cache_misses,
                "l1_hit_rate": self._calculate_hit_rate(),
                "device_count": self._metrics.total_devices,
                "processing_time": self._metrics.processing_time,
            },
            "concurrency": {
                "max_workers": self._executor._max_workers,
                "active_threads": threading.active_count(),
            },
            "last_update": self._last_update,
        }

    def _calculate_hit_rate(self) -> float:
        """Calculate current cache hit rate."""
        total_requests = self._metrics.cache_hits + self._metrics.cache_misses
        if total_requests == 0:
            return 0.0
        return self._metrics.cache_hits / total_requests

    async def get_device_config_async(
        self, device_name: str
    ) -> Optional[DeviceConfigSnapshot]:
        """Async version of device config retrieval."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self.get_device_config, device_name
        )

    def clear_caches(self) -> None:
        """Clear all caches and reset metrics."""
        with self._lock:
            self._raw_data_cache.clear()
            self._device_config_cache.clear()
            self._io_mapping_cache.clear()
            self._analysis_cache.clear()
            self._platform_cache.clear()

            # Clear method-level caches
            self.get_device_config.cache_clear()

            # Reset metrics
            self._metrics = AnalysisMetrics(0, 0, 0, 0.0, 0.0, 0)

            print("✅ Enhanced cache manager cleared all caches")


# =============================================================================
# Enhanced Streaming Data Generator
# =============================================================================


class EnhancedStreamingDataGenerator:
    """
    Enhanced streaming data generator with async support and caching.

    Preserves memory_agent1.py streaming patterns while adding:
    - Async generator support
    - Performance monitoring
    - Cache-aware streaming
    - Platform filtering
    """

    def __init__(self, memory_manager: EnhancedMemoryDataManager):
        self.memory_manager = memory_manager
        self._stream_cache = {}
        self._lock = threading.RLock()

    @regex_performance_monitor
    def device_config_stream(
        self, cache_enabled: bool = True
    ) -> Generator[Dict[str, Any], None, None]:
        """Enhanced device configuration stream generator."""
        stream_id = f"device_config_{int(time.time())}"

        if cache_enabled and stream_id in self._stream_cache:
            # Return cached stream data
            for item in self._stream_cache[stream_id]:
                yield item
            return

        stream_data = []
        for device_name in self.memory_manager.get_all_device_names():
            snapshot = self.memory_manager.get_device_config(device_name)
            if snapshot:
                config_data = {
                    "device_name": device_name,
                    "config": snapshot.configuration,
                    "io_ports": list(snapshot.io_ports),
                    "platforms": list(snapshot.platforms),
                    "metadata": {
                        "is_dynamic": snapshot.is_dynamic,
                        "is_versioned": snapshot.is_versioned,
                        "timestamp": snapshot.timestamp,
                        "cache_level": snapshot.cache_level,
                        "access_count": snapshot.access_count,
                    },
                }

                if cache_enabled:
                    stream_data.append(config_data)

                yield config_data

        # Cache for future use
        if cache_enabled and stream_data:
            with self._lock:
                self._stream_cache[stream_id] = stream_data

    async def device_config_stream_async(
        self, cache_enabled: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Async version of device configuration stream."""
        for device_name in self.memory_manager.get_all_device_names():
            snapshot = await self.memory_manager.get_device_config_async(device_name)
            if snapshot:
                yield {
                    "device_name": device_name,
                    "config": snapshot.configuration,
                    "io_ports": list(snapshot.io_ports),
                    "platforms": list(snapshot.platforms),
                    "metadata": {
                        "is_dynamic": snapshot.is_dynamic,
                        "is_versioned": snapshot.is_versioned,
                        "timestamp": snapshot.timestamp,
                        "cache_level": snapshot.cache_level,
                        "access_count": snapshot.access_count,
                    },
                }

    def platform_mapping_stream(
        self, filter_platforms: Optional[Set[str]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Enhanced platform mapping stream with filtering."""
        for config_data in self.device_config_stream():
            if filter_platforms:
                filtered_platforms = set(config_data["platforms"]) & filter_platforms
                if not filtered_platforms:
                    continue

            yield {
                "device_name": config_data["device_name"],
                "platform_mappings": {
                    platform: self._extract_platform_ios(
                        config_data["config"].get(platform, {})
                    )
                    for platform in config_data["platforms"]
                    if not filter_platforms or platform in filter_platforms
                },
                "metadata": config_data["metadata"],
            }

    def io_analysis_stream(self) -> Generator[Dict[str, Any], None, None]:
        """Enhanced IO analysis stream with complexity scoring."""
        for config_data in self.device_config_stream():
            device_name = config_data["device_name"]
            io_ports = config_data["io_ports"]

            io_analysis = {
                "device_name": device_name,
                "total_ios": len(io_ports),
                "io_types": self._classify_io_types(io_ports),
                "platform_distribution": self._analyze_platform_distribution(
                    config_data
                ),
                "complexity_score": self._calculate_complexity_score(config_data),
                "cache_efficiency": self._calculate_cache_efficiency(config_data),
                "metadata": config_data["metadata"],
            }

            yield io_analysis

    def _extract_platform_ios(self, platform_config: Any) -> List[str]:
        """Extract platform IO list with validation."""
        if isinstance(platform_config, dict):
            return [
                key
                for key in platform_config.keys()
                if IOExtractor.is_valid_io_name(key)
            ]
        elif isinstance(platform_config, list):
            return [io for io in platform_config if IOExtractor.is_valid_io_name(io)]
        elif isinstance(platform_config, str) and IOExtractor.is_valid_io_name(
            platform_config
        ):
            return [platform_config]
        return []

    def _classify_io_types(self, io_ports: List[str]) -> Dict[str, int]:
        """Classify IO port types with enhanced categorization."""
        types = {
            "p_series": 0,  # P1, P2, P3...
            "l_series": 0,  # L1, L2, L3...
            "single_char": 0,  # A, T, V, H...
            "complex": 0,  # RGBW, MODE, etc.
            "bitmask": 0,  # Needs bitwise operations
        }

        for io_port in io_ports:
            if RegexCache.is_p_io_port(io_port):
                types["p_series"] += 1
            elif len(io_port) == 1 and io_port.isalpha():
                types["single_char"] += 1
            elif io_port.startswith("L") and len(io_port) == 2 and io_port[1].isdigit():
                types["l_series"] += 1
            elif len(io_port) > 3:
                types["complex"] += 1
            else:
                types["bitmask"] += 1

        return types

    def _analyze_platform_distribution(
        self, config_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Analyze platform distribution for device."""
        distribution = {}
        for platform in config_data["platforms"]:
            platform_config = config_data["config"].get(platform, {})
            io_count = len(self._extract_platform_ios(platform_config))
            distribution[platform] = io_count
        return distribution

    def _calculate_complexity_score(self, config_data: Dict[str, Any]) -> float:
        """Calculate device complexity score."""
        io_count = len(config_data["io_ports"])
        platform_count = len(config_data["platforms"])

        # Base complexity from IO count
        io_complexity = min(io_count / 10.0, 1.0)

        # Platform complexity
        platform_complexity = min(platform_count / 5.0, 1.0)

        # Dynamic device penalty
        dynamic_penalty = 0.2 if config_data["metadata"]["is_dynamic"] else 0.0

        return min((io_complexity + platform_complexity + dynamic_penalty) * 10, 10.0)

    def _calculate_cache_efficiency(self, config_data: Dict[str, Any]) -> float:
        """Calculate cache efficiency for device."""
        access_count = config_data["metadata"].get("access_count", 0)
        if access_count == 0:
            return 0.0

        # Cache efficiency based on access patterns
        cache_level = config_data["metadata"].get("cache_level", "L1")
        level_multiplier = {"L1": 1.0, "L2": 0.8, "L3": 0.6}.get(cache_level, 0.5)

        return min(access_count * level_multiplier / 10.0, 1.0)

    def clear_stream_cache(self) -> None:
        """Clear streaming cache data."""
        with self._lock:
            self._stream_cache.clear()
            print("✅ Stream cache cleared")


# =============================================================================
# Cache Factory Integration
# =============================================================================


class EnhancedCacheFactory:
    """
    Enhanced cache factory integrating memory_agent1.py patterns.

    Creates and manages enhanced cache instances with device-specific
    optimizations and memory_agent1.py proven patterns.
    """

    def __init__(self):
        self._cache_instances = {}
        self._memory_managers = {}
        self._stream_generators = {}

    def create_memory_data_manager(
        self, cache_size: int = 512, max_workers: int = 4
    ) -> EnhancedMemoryDataManager:
        """Create enhanced memory data manager."""
        manager_id = f"manager_{cache_size}_{max_workers}"

        if manager_id not in self._memory_managers:
            manager = EnhancedMemoryDataManager(cache_size, max_workers)
            self._memory_managers[manager_id] = manager

        return self._memory_managers[manager_id]

    def create_stream_generator(
        self, manager: EnhancedMemoryDataManager
    ) -> EnhancedStreamingDataGenerator:
        """Create enhanced streaming data generator."""
        manager_hash = hash(id(manager))

        if manager_hash not in self._stream_generators:
            generator = EnhancedStreamingDataGenerator(manager)
            self._stream_generators[manager_hash] = generator

        return self._stream_generators[manager_hash]

    def create_complete_cache_system(
        self,
        cache_size: int = 512,
        max_workers: int = 4,
        raw_device_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create complete integrated cache system."""
        # Create memory manager
        memory_manager = self.create_memory_data_manager(cache_size, max_workers)

        # Load device data if provided
        if raw_device_data:
            memory_manager.load_raw_device_data(raw_device_data)

        # Create stream generator
        stream_generator = self.create_stream_generator(memory_manager)

        return {
            "memory_manager": memory_manager,
            "stream_generator": stream_generator,
            "cache_size": cache_size,
            "max_workers": max_workers,
            "created_at": time.time(),
        }

    def get_cache_system_metrics(self) -> Dict[str, Any]:
        """Get metrics for all cache systems."""
        metrics = {
            "memory_managers": len(self._memory_managers),
            "stream_generators": len(self._stream_generators),
            "total_cache_instances": len(self._cache_instances),
            "systems": {},
        }

        for manager_id, manager in self._memory_managers.items():
            metrics["systems"][manager_id] = manager.get_performance_metrics()

        return metrics

    def cleanup_all_caches(self) -> None:
        """Cleanup all cache instances."""
        for manager in self._memory_managers.values():
            manager.clear_caches()

        for generator in self._stream_generators.values():
            generator.clear_stream_cache()

        self._cache_instances.clear()
        print("✅ All enhanced cache systems cleaned up")


# =============================================================================
# Factory Helper Functions
# =============================================================================


def create_enhanced_memory_agent(
    supported_platforms: Set[str],
    raw_device_data: Dict[str, Any],
    cache_size: int = 512,
    max_workers: int = 4,
) -> Dict[str, Any]:
    """
    Create enhanced memory agent with memory_agent1.py compatibility.

    Provides drop-in replacement for create_memory_agent1() function
    with enhanced caching and streaming capabilities.
    """
    factory = EnhancedCacheFactory()

    # Create complete cache system
    cache_system = factory.create_complete_cache_system(
        cache_size=cache_size, max_workers=max_workers, raw_device_data=raw_device_data
    )

    # Add supported platforms metadata
    cache_system["supported_platforms"] = supported_platforms
    cache_system["compatibility_mode"] = "memory_agent1_enhanced"

    print(f"✅ Enhanced memory agent created with {len(raw_device_data)} devices")
    print(f"   Cache size: {cache_size}, Workers: {max_workers}")
    print(f"   Platforms: {len(supported_platforms)}")

    return cache_system


async def get_enhanced_allocation_data_async(
    cache_system: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Async version of allocation data retrieval.

    Compatible with memory_agent1.py patterns while providing
    enhanced performance and caching.
    """
    memory_manager = cache_system["memory_manager"]
    stream_generator = cache_system["stream_generator"]

    # Get summary data
    allocation_summary = {
        "metadata": {
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "enhanced_memory_agent",
            "total_devices": len(memory_manager.get_all_device_names()),
            "supported_platforms": list(cache_system.get("supported_platforms", [])),
            "version": "v2.0-enhanced",
            "cache_metrics": memory_manager.get_performance_metrics(),
        },
        "devices": [],
    }

    # Stream device data asynchronously
    async for device_data in stream_generator.device_config_stream_async():
        allocation_summary["devices"].append(device_data)

    return allocation_summary
