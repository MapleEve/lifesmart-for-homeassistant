#!/usr/bin/env python3
"""
Agent1内存模式重构 - 消除所有文件依赖的智能分析器
专注于内存处理、流式输出、缓存优化和并发支持
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import lru_cache
from typing import Dict, Set, List, Any, Generator, Optional, Tuple, AsyncGenerator
from weakref import WeakValueDictionary

try:
    from .core_utils import IOExtractor, DeviceNameUtils, RegexCache
    from .regex_cache import regex_performance_monitor
except ImportError:
    # Fallback for development
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from core_utils import IOExtractor, DeviceNameUtils, RegexCache
    from regex_cache import regex_performance_monitor


@dataclass
class DeviceConfigSnapshot:
    """设备配置快照数据结构"""
    device_name: str
    configuration: Dict[str, Any]
    io_ports: Set[str]
    platforms: Set[str]
    is_dynamic: bool
    is_versioned: bool
    timestamp: float


@dataclass
class AnalysisMetrics:
    """分析性能指标"""
    total_devices: int
    cache_hits: int
    cache_misses: int
    processing_time: float
    memory_usage_mb: float
    concurrent_requests: int


class MemoryDataManager:
    """内存数据管理器 - 负责所有数据的内存管理和缓存"""
    
    def __init__(self, cache_size: int = 256):
        self.cache_size = cache_size
        self._raw_data_cache = WeakValueDictionary()
        self._device_config_cache = {}
        self._io_mapping_cache = {}
        self._analysis_cache = {}
        self._last_update = time.time()
        self._metrics = AnalysisMetrics(0, 0, 0, 0.0, 0.0, 0)
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    def load_raw_device_data(self, raw_data: Dict[str, Any]) -> None:
        """加载原始设备数据到内存"""
        self._raw_data_cache.clear()
        for device_name, config in raw_data.items():
            if DeviceNameUtils.is_valid_device_name(device_name):
                snapshot = self._create_device_snapshot(device_name, config)
                self._raw_data_cache[device_name] = snapshot
        self._last_update = time.time()
    
    def _create_device_snapshot(self, device_name: str, config: Dict[str, Any]) -> DeviceConfigSnapshot:
        """创建设备配置快照"""
        io_ports = IOExtractor.extract_mapped_ios(config)
        platforms = set(config.keys()) - {'name', 'description', 'versioned', 'dynamic'}
        
        return DeviceConfigSnapshot(
            device_name=device_name,
            configuration=config.copy(),
            io_ports=io_ports,
            platforms=platforms,
            is_dynamic=config.get('dynamic', False),
            is_versioned=config.get('versioned', False),
            timestamp=time.time()
        )
    
    @lru_cache(maxsize=128)
    def get_device_config(self, device_name: str) -> Optional[DeviceConfigSnapshot]:
        """获取设备配置（带缓存）"""
        self._metrics.cache_hits += 1
        return self._raw_data_cache.get(device_name)
    
    def get_all_device_names(self) -> List[str]:
        """获取所有设备名称列表"""
        return list(self._raw_data_cache.keys())
    
    def get_metrics(self) -> AnalysisMetrics:
        """获取分析性能指标"""
        return self._metrics


class StreamingDataGenerator:
    """流式数据生成器 - 实现Generator模式避免大量内存占用"""
    
    def __init__(self, memory_manager: MemoryDataManager):
        self.memory_manager = memory_manager
        
    @regex_performance_monitor
    def device_config_stream(self) -> Generator[Dict[str, Any], None, None]:
        """设备配置流生成器"""
        for device_name in self.memory_manager.get_all_device_names():
            snapshot = self.memory_manager.get_device_config(device_name)
            if snapshot:
                yield {
                    'device_name': device_name,
                    'config': snapshot.configuration,
                    'io_ports': list(snapshot.io_ports),
                    'platforms': list(snapshot.platforms),
                    'metadata': {
                        'is_dynamic': snapshot.is_dynamic,
                        'is_versioned': snapshot.is_versioned,
                        'timestamp': snapshot.timestamp
                    }
                }
    
    def platform_mapping_stream(self, filter_platforms: Optional[Set[str]] = None) -> Generator[Dict[str, Any], None, None]:
        """平台映射流生成器"""
        for config_data in self.device_config_stream():
            if filter_platforms:
                # 过滤指定平台
                filtered_platforms = set(config_data['platforms']) & filter_platforms
                if not filtered_platforms:
                    continue
            
            yield {
                'device_name': config_data['device_name'],
                'platform_mappings': {
                    platform: self._extract_platform_ios(config_data['config'].get(platform, {}))
                    for platform in config_data['platforms']
                    if not filter_platforms or platform in filter_platforms
                },
                'metadata': config_data['metadata']
            }
    
    def _extract_platform_ios(self, platform_config: Any) -> List[str]:
        """提取平台的IO口列表"""
        if isinstance(platform_config, dict):
            return [key for key in platform_config.keys() if IOExtractor.is_valid_io_name(key)]
        elif isinstance(platform_config, list):
            return [io for io in platform_config if IOExtractor.is_valid_io_name(io)]
        elif isinstance(platform_config, str) and IOExtractor.is_valid_io_name(platform_config):
            return [platform_config]
        return []
    
    def io_analysis_stream(self) -> Generator[Dict[str, Any], None, None]:
        """IO分析流生成器"""
        for config_data in self.device_config_stream():
            device_name = config_data['device_name']
            io_ports = config_data['io_ports']
            
            # 分析IO口特性
            io_analysis = {
                'device_name': device_name,
                'total_ios': len(io_ports),
                'io_types': self._classify_io_types(io_ports),
                'platform_distribution': self._analyze_platform_distribution(config_data),
                'complexity_score': self._calculate_complexity_score(config_data),
                'metadata': config_data['metadata']
            }
            
            yield io_analysis
    
    def _classify_io_types(self, io_ports: List[str]) -> Dict[str, int]:
        """分类IO口类型"""
        types = {
            'p_series': 0,      # P1, P2, P3...
            'l_series': 0,      # L1, L2, L3...
            'single_char': 0,   # A, T, V, H...
            'complex': 0,       # RGBW, MODE, etc.
            'bitmask': 0        # 需要位操作的IO口
        }
        
        for io_port in io_ports:
            if RegexCache.is_p_io_port(io_port):
                types['p_series'] += 1
            elif len(io_port) == 1 and io_port.isalpha():
                types['single_char'] += 1
            elif io_port.startswith('L') and len(io_port) == 2 and io_port[1].isdigit():
                types['l_series'] += 1
            elif len(io_port) > 3:
                types['complex'] += 1
            else:
                # 简单的多字符IO口，可能需要位操作
                types['bitmask'] += 1
        
        return types
    
    def _analyze_platform_distribution(self, config_data: Dict[str, Any]) -> Dict[str, int]:
        """分析平台分布"""
        distribution = {}
        for platform in config_data['platforms']:
            platform_config = config_data['config'].get(platform, {})
            io_count = len(self._extract_platform_ios(platform_config))
            distribution[platform] = io_count
        return distribution
    
    def _calculate_complexity_score(self, config_data: Dict[str, Any]) -> float:
        """计算设备复杂度分数"""
        base_score = len(config_data['io_ports']) * 0.1  # IO口数量基础分数
        
        # 平台数量奖励
        platform_bonus = len(config_data['platforms']) * 0.2
        
        # 动态设备奖励
        dynamic_bonus = 0.5 if config_data['metadata']['is_dynamic'] else 0
        
        # 版本设备奖励
        version_bonus = 0.3 if config_data['metadata']['is_versioned'] else 0
        
        return min(10.0, base_score + platform_bonus + dynamic_bonus + version_bonus)


class SmartCacheManager:
    """智能缓存管理器 - LRU缓存和过期策略"""
    
    def __init__(self, cache_ttl: int = 300):  # 5分钟缓存过期
        self.cache_ttl = cache_ttl
        self._computation_cache = {}
        self._access_times = {}
        
    @lru_cache(maxsize=256)
    def cached_device_analysis(self, device_name: str, config_hash: int) -> Dict[str, Any]:
        """缓存设备分析结果"""
        # 这里应该调用实际的分析逻辑
        # 为了演示，返回一个简化的结果
        return {
            'device_name': device_name,
            'config_hash': config_hash,
            'analysis_timestamp': time.time(),
            'cached': True
        }
    
    def is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._access_times:
            return False
        return time.time() - self._access_times[key] < self.cache_ttl
    
    def invalidate_cache(self, pattern: Optional[str] = None) -> None:
        """清理缓存"""
        if pattern:
            # 按模式清理
            keys_to_remove = [key for key in self._computation_cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._computation_cache.pop(key, None)
                self._access_times.pop(key, None)
        else:
            # 清理全部缓存
            self._computation_cache.clear()
            self._access_times.clear()
            self.cached_device_analysis.cache_clear()


class MemoryAgent1:
    """内存模式的Agent1 - 完全消除文件依赖"""
    
    def __init__(self, supported_platforms: Set[str]):
        self.supported_platforms = supported_platforms
        self.memory_manager = MemoryDataManager()
        self.stream_generator = StreamingDataGenerator(self.memory_manager)
        self.cache_manager = SmartCacheManager()
        self._concurrent_requests = 0
        
    def initialize_from_device_specs(self, raw_device_data: Dict[str, Any]) -> None:
        """从设备规格初始化内存数据"""
        start_time = time.time()
        self.memory_manager.load_raw_device_data(raw_device_data)
        processing_time = time.time() - start_time
        
        # 更新性能指标
        metrics = self.memory_manager.get_metrics()
        metrics.total_devices = len(raw_device_data)
        metrics.processing_time = processing_time
        
        print(f"✅ 内存Agent1初始化完成: {metrics.total_devices}个设备, 耗时{processing_time:.2f}秒")
    
    def get_existing_allocation_stream(self) -> Generator[Dict[str, Any], None, None]:
        """获取现有分配的数据流 - 替代文件读取"""
        metadata = {
            'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'source': 'memory_agent1',
            'total_devices': len(self.memory_manager.get_all_device_names()),
            'supported_platforms': list(self.supported_platforms),
            'version': 'v1.0-memory'
        }
        
        # 首先返回元数据
        yield {'metadata': metadata}
        
        # 然后流式返回设备配置
        for device_config in self.stream_generator.device_config_stream():
            # 转换为兼容的格式
            allocation_data = {
                'device_name': device_config['device_name'],
                'platforms': {},
                'io_summary': {
                    'total_ios': len(device_config['io_ports']),
                    'io_list': device_config['io_ports'],
                    'platform_count': len(device_config['platforms'])
                },
                'metadata': device_config['metadata']
            }
            
            # 构建平台配置
            for platform in device_config['platforms']:
                platform_config = device_config['config'].get(platform, {})
                allocation_data['platforms'][platform] = self._normalize_platform_config(platform_config)
            
            yield {'device': allocation_data}
    
    def _normalize_platform_config(self, platform_config: Any) -> Dict[str, Any]:
        """规范化平台配置"""
        if isinstance(platform_config, dict):
            return platform_config
        elif isinstance(platform_config, list):
            return {'io_list': platform_config}
        elif isinstance(platform_config, str):
            return {'single_io': platform_config}
        else:
            return {'raw_config': platform_config}
    
    async def get_existing_allocation_async(self) -> Dict[str, Any]:
        """异步获取现有分配数据"""
        self._concurrent_requests += 1
        try:
            loop = asyncio.get_event_loop()
            
            # 在线程池中执行同步操作
            result = await loop.run_in_executor(
                self.memory_manager._executor,
                self._build_allocation_dict
            )
            
            return result
        finally:
            self._concurrent_requests -= 1
    
    def _build_allocation_dict(self) -> Dict[str, Any]:
        """构建分配字典 - 在线程池中执行"""
        devices = {}
        metadata = None
        
        for stream_item in self.get_existing_allocation_stream():
            if 'metadata' in stream_item:
                metadata = stream_item['metadata']
            elif 'device' in stream_item:
                device_data = stream_item['device']
                devices[device_data['device_name']] = device_data
        
        return {
            'metadata': metadata,
            'devices': devices,
            'statistics': {
                'total_devices': len(devices),
                'memory_source': True,
                'cache_hits': self.memory_manager.get_metrics().cache_hits,
                'concurrent_requests': self._concurrent_requests
            }
        }
    
    def get_platform_analysis_stream(self, filter_platforms: Optional[Set[str]] = None) -> Generator[Dict[str, Any], None, None]:
        """获取平台分析数据流"""
        for platform_data in self.stream_generator.platform_mapping_stream(filter_platforms):
            # 增强平台分析信息
            enhanced_analysis = {
                'device_name': platform_data['device_name'],
                'platform_mappings': platform_data['platform_mappings'],
                'analysis': {
                    'supported_platforms': list(platform_data['platform_mappings'].keys()),
                    'total_platform_ios': sum(len(ios) for ios in platform_data['platform_mappings'].values()),
                    'cross_platform_ios': self._find_cross_platform_ios(platform_data['platform_mappings']),
                    'platform_complexity': len(platform_data['platform_mappings'])
                },
                'metadata': platform_data['metadata']
            }
            
            yield enhanced_analysis
    
    def _find_cross_platform_ios(self, platform_mappings: Dict[str, List[str]]) -> List[str]:
        """查找跨平台的IO口"""
        io_to_platforms = {}
        
        for platform, ios in platform_mappings.items():
            for io_name in ios:
                if io_name not in io_to_platforms:
                    io_to_platforms[io_name] = []
                io_to_platforms[io_name].append(platform)
        
        # 返回出现在多个平台的IO口
        cross_platform = []
        for io_name, platforms in io_to_platforms.items():
            if len(platforms) > 1:
                cross_platform.append(io_name)
        
        return cross_platform
    
    def get_io_analysis_summary(self) -> Dict[str, Any]:
        """获取IO分析汇总"""
        summary = {
            'total_devices': 0,
            'total_ios': 0,
            'io_type_distribution': {
                'p_series': 0,
                'l_series': 0,
                'single_char': 0,
                'complex': 0,
                'bitmask': 0
            },
            'platform_statistics': {},
            'complexity_distribution': {
                'simple': 0,      # 0-2分
                'moderate': 0,    # 2-5分
                'complex': 0,     # 5-8分
                'very_complex': 0 # 8-10分
            },
            'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for io_analysis in self.stream_generator.io_analysis_stream():
            summary['total_devices'] += 1
            summary['total_ios'] += io_analysis['total_ios']
            
            # 累加IO类型分布
            for io_type, count in io_analysis['io_types'].items():
                summary['io_type_distribution'][io_type] += count
            
            # 累加平台统计
            for platform, count in io_analysis['platform_distribution'].items():
                if platform not in summary['platform_statistics']:
                    summary['platform_statistics'][platform] = {'devices': 0, 'total_ios': 0}
                summary['platform_statistics'][platform]['devices'] += 1
                summary['platform_statistics'][platform]['total_ios'] += count
            
            # 复杂度分布
            complexity = io_analysis['complexity_score']
            if complexity <= 2:
                summary['complexity_distribution']['simple'] += 1
            elif complexity <= 5:
                summary['complexity_distribution']['moderate'] += 1
            elif complexity <= 8:
                summary['complexity_distribution']['complex'] += 1
            else:
                summary['complexity_distribution']['very_complex'] += 1
        
        return summary
    
    def clear_caches(self) -> None:
        """清理所有缓存"""
        self.cache_manager.invalidate_cache()
        self.memory_manager.get_device_config.cache_clear()
        print("✅ 所有缓存已清理")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        metrics = self.memory_manager.get_metrics()
        
        return {
            'memory_usage': {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024
            },
            'cache_performance': {
                'hits': metrics.cache_hits,
                'misses': metrics.cache_misses,
                'hit_rate': metrics.cache_hits / max(1, metrics.cache_hits + metrics.cache_misses)
            },
            'concurrency': {
                'active_requests': self._concurrent_requests,
                'max_workers': self.memory_manager._executor._max_workers
            },
            'data_statistics': {
                'total_devices': metrics.total_devices,
                'processing_time': metrics.processing_time,
                'last_update': self.memory_manager._last_update
            }
        }


# 工具函数
def create_memory_agent1(supported_platforms: Set[str], raw_device_data: Dict[str, Any]) -> MemoryAgent1:
    """创建并初始化内存模式的Agent1"""
    agent = MemoryAgent1(supported_platforms)
    agent.initialize_from_device_specs(raw_device_data)
    return agent


# 异步工具函数
async def get_allocation_data_async(agent: MemoryAgent1) -> Dict[str, Any]:
    """异步获取分配数据"""
    return await agent.get_existing_allocation_async()


# 性能测试函数
def benchmark_memory_agent1(raw_device_data: Dict[str, Any], iterations: int = 100) -> Dict[str, float]:
    """性能基准测试"""
    import time
    
    supported_platforms = {'switch', 'sensor', 'light', 'binary_sensor', 'climate'}
    
    # 初始化测试
    start_time = time.time()
    agent = create_memory_agent1(supported_platforms, raw_device_data)
    init_time = time.time() - start_time
    
    # 流式访问测试
    start_time = time.time()
    for _ in range(iterations):
        count = sum(1 for _ in agent.get_existing_allocation_stream())
    stream_time = time.time() - start_time
    
    # 分析测试
    start_time = time.time()
    summary = agent.get_io_analysis_summary()
    analysis_time = time.time() - start_time
    
    return {
        'initialization_time': init_time,
        'stream_access_time_per_100_iterations': stream_time,
        'analysis_time': analysis_time,
        'devices_processed': summary['total_devices'],
        'ios_processed': summary['total_ios']
    }