"""
BitmaskPlatformMappingRegistry - 统一的bitmask→platform映射注册表
由 @MapleEve 创建，用于VirtualDeviceStrategy

核心功能:
- 提供O(1)性能的device_class→platform查找机制
- 支持多种bitmask类型的统一处理 (ALM、EVTLO、config_bitmask)
- 预构建虚拟设备缓存，避免运行时生成
- 配置驱动架构，新bitmask类型只需添加配置

架构特点:
- 单例模式：全局唯一注册表实例
- 预构建缓存：启动时构建所有查找表
- O(1)性能保证：哈希表和正则预编译
- 可扩展设计：动态注册新bitmask配置
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Pattern

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass

_LOGGER = logging.getLogger(__name__)


@dataclass
class VirtualDevice:
    """虚拟设备定义数据结构"""

    key: str
    name: str
    description: str
    platform: str
    device_class: Optional[Any]
    extraction_params: Dict[str, Any]
    friendly_name: str


@dataclass
class BitmaskConfig:
    """bitmask配置定义数据结构"""

    bitmask_type: str
    io_port_pattern: Pattern[str]
    platform_priority: List[str]
    detection_logic: str
    virtual_device_template: str
    bit_definitions: Dict[int, Dict[str, Any]]
    data_definitions: Dict[str, Dict[str, Any]]


class BitmaskPlatformMappingRegistry:
    """
    统一的bitmask→platform映射注册表

    提供O(1)性能的device_class→platform查找机制
    支持多种bitmask类型的统一处理
    """

    def __init__(self):
        """初始化注册表"""
        self._bitmask_configs: Dict[str, BitmaskConfig] = {}
        self._device_class_platform_mapping: Dict[Any, str] = {}
        self._io_port_patterns: List[tuple[Pattern[str], str]] = []
        self._virtual_device_cache: Dict[tuple[str, str], List[VirtualDevice]] = {}

        # 性能统计
        self._stats = {
            "lookup_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # 初始化配置
        self._load_default_configs()
        self._build_lookup_tables()

    def _load_default_configs(self):
        """加载默认的bitmask配置"""
        try:
            from .bitmask_platform_configs import (
                ALM_BITMASK_CONFIG,
                EVTLO_BITMASK_CONFIG,
                CONFIG_BITMASK_CONFIG,
                DEVICE_CLASS_PLATFORM_MAPPING,
            )

            # 注册ALM配置
            self._register_config_internal("ALM", ALM_BITMASK_CONFIG)

            # 注册EVTLO配置
            self._register_config_internal("EVTLO", EVTLO_BITMASK_CONFIG)

            # 注册config_bitmask配置
            self._register_config_internal("config_bitmask", CONFIG_BITMASK_CONFIG)

            # 加载device_class→platform映射
            self._device_class_platform_mapping = DEVICE_CLASS_PLATFORM_MAPPING.copy()

            _LOGGER.info(
                "BitmaskPlatformMappingRegistry loaded %d configurations",
                len(self._bitmask_configs),
            )

        except ImportError as e:
            _LOGGER.error("Failed to load bitmask configurations: %s", e)
            raise

    def _register_config_internal(self, bitmask_type: str, config_data: Dict[str, Any]):
        """内部配置注册方法"""
        try:
            config = BitmaskConfig(
                bitmask_type=bitmask_type,
                io_port_pattern=re.compile(config_data["io_port_pattern"]),
                platform_priority=config_data["platform_priority"],
                detection_logic=config_data.get("detection_logic", "pattern_match"),
                virtual_device_template=config_data["virtual_device_template"],
                bit_definitions=config_data.get("bit_definitions", {}),
                data_definitions=config_data.get("data_definitions", {}),
            )

            self._bitmask_configs[bitmask_type] = config
            _LOGGER.debug("Registered bitmask config: %s", bitmask_type)

        except Exception as e:
            _LOGGER.error("Failed to register config %s: %s", bitmask_type, e)
            raise

    def _build_lookup_tables(self):
        """构建O(1)查找表和缓存"""
        # 构建IO口模式查找表 - 按优先级排序
        self._io_port_patterns = []
        for bitmask_type, config in self._bitmask_configs.items():
            self._io_port_patterns.append((config.io_port_pattern, bitmask_type))

        # 特殊处理：ALM和EVTLO优先，config_bitmask最后
        self._io_port_patterns.sort(key=lambda x: 0 if x[1] in ["ALM", "EVTLO"] else 1)

        # 预构建虚拟设备缓存
        for bitmask_type, config in self._bitmask_configs.items():
            if bitmask_type == "ALM":
                self._prebuild_alm_virtual_devices(config)
            elif bitmask_type == "EVTLO":
                self._prebuild_evtlo_virtual_devices(config)
            elif bitmask_type == "config_bitmask":
                # config_bitmask需要动态检测，不预构建
                pass

        _LOGGER.debug(
            "Built lookup tables: %d patterns, %d cached devices",
            len(self._io_port_patterns),
            len(self._virtual_device_cache),
        )

    def _prebuild_alm_virtual_devices(self, config: BitmaskConfig):
        """预构建ALM虚拟设备"""
        virtual_devices = []

        for bit_position, bit_def in config.bit_definitions.items():
            virtual_key = config.virtual_device_template.format(
                io_port="ALM", bit_position=bit_position
            )

            virtual_device = VirtualDevice(
                key=virtual_key,
                name=bit_def["name"],
                description=bit_def["description"],
                platform=bit_def["platform"],
                device_class=bit_def["device_class"],
                extraction_params={
                    "conversion": "alm_bit_extraction",
                    "bit_position": bit_position,
                    "extraction_logic": bit_def["extraction_logic"],
                },
                friendly_name=bit_def.get("friendly_name", bit_def["name"]),
            )

            virtual_devices.append(virtual_device)

        # 缓存到查找表
        cache_key = ("ALM", "ALM")
        self._virtual_device_cache[cache_key] = virtual_devices
        _LOGGER.debug("Prebuilt %d ALM virtual devices", len(virtual_devices))

    def _prebuild_evtlo_virtual_devices(self, config: BitmaskConfig):
        """预构建EVTLO虚拟设备"""
        virtual_devices = []

        for data_key, data_def in config.data_definitions.items():
            virtual_key = config.virtual_device_template.format(
                io_port="EVTLO", data_key=data_key
            )

            virtual_device = VirtualDevice(
                key=virtual_key,
                name=data_def["name"],
                description=data_def.get("description", data_def["name"]),
                platform=data_def["platform"],
                device_class=data_def.get("device_class"),
                extraction_params={
                    "conversion": "evtlo_data_extraction",
                    "data_key": data_key,
                    "extraction_logic": data_def["extraction_logic"],
                    "extraction_params": data_def.get("extraction_params", {}),
                },
                friendly_name=data_def.get("friendly_name", data_def["name"]),
            )

            virtual_devices.append(virtual_device)

        # 缓存到查找表
        cache_key = ("EVTLO", "EVTLO")
        self._virtual_device_cache[cache_key] = virtual_devices
        _LOGGER.debug("Prebuilt %d EVTLO virtual devices", len(virtual_devices))

    def get_platform_for_device_class(self, device_class: Any) -> Optional[str]:
        """
        O(1)查找device_class对应的platform

        Args:
            device_class: HA设备类别常量

        Returns:
            platform名称或None
        """
        self._stats["lookup_count"] += 1
        return self._device_class_platform_mapping.get(device_class)

    def is_bitmask_io_port(self, io_port: str) -> Optional[str]:
        """
        O(k)检测IO口是否为bitmask类型，k为配置的bitmask类型数量

        Args:
            io_port: IO口名称

        Returns:
            bitmask类型或None
        """
        for pattern, bitmask_type in self._io_port_patterns:
            if pattern.match(io_port):
                return bitmask_type
        return None

    def get_virtual_devices(
        self, bitmask_type: str, io_port: str
    ) -> List[VirtualDevice]:
        """
        获取指定bitmask类型的虚拟设备配置

        Args:
            bitmask_type: bitmask类型
            io_port: IO口名称

        Returns:
            虚拟设备列表
        """
        cache_key = (bitmask_type, io_port)

        # 首先检查缓存
        if cache_key in self._virtual_device_cache:
            self._stats["cache_hits"] += 1
            return self._virtual_device_cache[cache_key]

        self._stats["cache_misses"] += 1

        # 动态生成(主要用于config_bitmask)
        if bitmask_type in self._bitmask_configs:
            config = self._bitmask_configs[bitmask_type]
            virtual_devices = self._generate_virtual_devices_dynamically(
                config, io_port
            )
            # 缓存结果
            self._virtual_device_cache[cache_key] = virtual_devices
            return virtual_devices

        return []

    def _generate_virtual_devices_dynamically(
        self, config: BitmaskConfig, io_port: str
    ) -> List[VirtualDevice]:
        """动态生成虚拟设备(用于config_bitmask等)"""
        virtual_devices = []

        if config.bitmask_type == "config_bitmask":
            # 为config_bitmask生成通用虚拟设备
            virtual_key = config.virtual_device_template.format(io_port=io_port)

            virtual_device = VirtualDevice(
                key=virtual_key,
                name=f"{io_port}配置",
                description=f"{io_port}的配置信息",
                platform="sensor",
                device_class=None,
                extraction_params={
                    "conversion": "val_direct",
                    "extraction_logic": "direct_value",
                },
                friendly_name=f"{io_port}配置",
            )

            virtual_devices.append(virtual_device)

        _LOGGER.debug(
            "Dynamically generated %d virtual devices for %s:%s",
            len(virtual_devices),
            config.bitmask_type,
            io_port,
        )

        return virtual_devices

    def get_bitmask_config(self, bitmask_type: str) -> Optional[BitmaskConfig]:
        """获取bitmask配置"""
        return self._bitmask_configs.get(bitmask_type)

    def get_all_bitmask_types(self) -> List[str]:
        """获取所有支持的bitmask类型"""
        return list(self._bitmask_configs.keys())

    def register_dynamic_config(self, bitmask_type: str, config_data: Dict[str, Any]):
        """
        动态注册新的bitmask配置

        Args:
            bitmask_type: bitmask类型名称
            config_data: 配置数据字典
        """
        self._register_config_internal(bitmask_type, config_data)
        self._build_lookup_tables()  # 重建查找表
        _LOGGER.info("Dynamically registered bitmask config: %s", bitmask_type)

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        cache_hit_rate = self._stats["cache_hits"] / max(
            1, self._stats["cache_hits"] + self._stats["cache_misses"]
        )

        return {
            "total_lookups": self._stats["lookup_count"],
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
            "bitmask_configs": len(self._bitmask_configs),
            "device_class_mappings": len(self._device_class_platform_mapping),
            "virtual_device_cache_size": len(self._virtual_device_cache),
            "io_port_patterns": len(self._io_port_patterns),
        }

    def clear_cache(self):
        """清理缓存(用于测试或重置)"""
        self._virtual_device_cache.clear()
        self._stats = {"lookup_count": 0, "cache_hits": 0, "cache_misses": 0}
        _LOGGER.info("Cache cleared")


# 全局注册表实例
_global_registry: Optional[BitmaskPlatformMappingRegistry] = None


def get_bitmask_platform_mapping_registry() -> BitmaskPlatformMappingRegistry:
    """
    获取全局bitmask映射注册表实例(单例模式)

    Returns:
        BitmaskPlatformMappingRegistry实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = BitmaskPlatformMappingRegistry()
        _LOGGER.info("BitmaskPlatformMappingRegistry global instance created")
    return _global_registry


def reset_global_registry():
    """重置全局注册表(用于测试)"""
    global _global_registry
    _global_registry = None
    _LOGGER.debug("Global registry reset")
