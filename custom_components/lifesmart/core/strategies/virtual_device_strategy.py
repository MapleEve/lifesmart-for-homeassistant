"""
VirtualDeviceStrategy - 虚拟设备解析策略

处理虚拟设备和子设备生成，包括ALM虚拟设备和多平台虚拟设备。
从原始mapping_engine的虚拟设备处理逻辑提取。

从原始mapping_engine.py的977-1362行提取，包括：
- ALM虚拟子设备扩展
- 多平台虚拟设备生成
- 动态分类和位操作处理

由 @MapleEve 创建，基于Phase 2.5关键重构任务
"""

import logging
from typing import Dict, Any, List

from .base_strategy import BaseDeviceStrategy
from .ha_constant_strategy import HAConstantStrategy
from ..config.bitmask_platform_mapping_registry import (
    get_bitmask_platform_mapping_registry,
    VirtualDevice,
)

_LOGGER = logging.getLogger(__name__)


class VirtualDeviceStrategy(BaseDeviceStrategy):
    """
    增强的虚拟设备解析策略

    集成统一的BitmaskPlatformMappingRegistry，支持：
    - ALM虚拟子设备扩展
    - EVTLO多平台虚拟设备
    - config_bitmask通用处理
    - 动态分类设备处理
    - O(1)性能优化
    """

    def __init__(self, ha_constant_strategy: HAConstantStrategy):
        """
        初始化增强的虚拟设备策略

        Args:
            ha_constant_strategy: HA常量转换策略实例
        """
        self.ha_constant_strategy = ha_constant_strategy
        self.mapping_registry = get_bitmask_platform_mapping_registry()

        _LOGGER.debug("VirtualDeviceStrategy initialized with mapping registry")

    def can_handle(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> bool:
        """
        增强的虚拟设备检测

        Args:
            device_type: 设备类型
            device: 设备数据
            raw_config: 原始配置

        Returns:
            bool: 是否能处理此设备
        """
        # 检查动态分类配置
        if "dynamic_classification" in raw_config:
            _LOGGER.debug("Device %s has dynamic_classification", device_type)
            return True

        # O(1)检查是否包含bitmask IO口
        device_data = device.get("data", {})
        for io_port in device_data.keys():
            bitmask_type = self.mapping_registry.is_bitmask_io_port(io_port)
            if bitmask_type:
                _LOGGER.debug(
                    "Device %s has bitmask IO port %s (type: %s)",
                    device_type,
                    io_port,
                    bitmask_type,
                )
                return True

        # 检查config_bitmask类型的IO口
        for io_port, io_data in device_data.items():
            if isinstance(io_data, dict) and io_data.get("type") == "config_bitmask":
                _LOGGER.debug(
                    "Device %s has config_bitmask IO port %s", device_type, io_port
                )
                return True

        return False

    def resolve_device_mapping(
        self, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        增强的设备映射解析

        Args:
            device: 设备数据字典
            raw_config: 原始设备配置

        Returns:
            解析后的设备配置
        """
        device_data = self.get_device_data(device)

        # 处理动态分类
        if "dynamic_classification" in raw_config:
            return self._resolve_dynamic_classification(raw_config, device_data)

        # 处理bitmask虚拟设备
        return self._resolve_bitmask_virtual_devices(device, raw_config)

    def get_strategy_name(self) -> str:
        return "VirtualDeviceStrategy"

    @property
    def priority(self) -> int:
        return 30  # 中等优先级，处理虚拟设备

    def _resolve_dynamic_classification(
        self, raw_config: Dict[str, Any], device_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析动态分类设备

        从原始mapping_engine._resolve_dynamic_classification方法简化提取

        Args:
            raw_config: 原始配置
            device_data: 设备数据

        Returns:
            解析结果
        """
        dynamic_config = raw_config["dynamic_classification"]
        classification_type = dynamic_config.get("type")

        if classification_type == "conditional":
            return self._resolve_conditional_classification(dynamic_config, device_data)
        elif classification_type == "bitwise":
            return self._resolve_bitwise_classification(dynamic_config, device_data)

        return self.create_error_result(
            f"Unknown classification type: {classification_type}"
        )

    def _resolve_conditional_classification(
        self, dynamic_config: Dict[str, Any], device_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析条件分类设备(简化版)

        Args:
            dynamic_config: 动态配置
            device_data: 设备数据

        Returns:
            解析结果
        """
        condition_field = dynamic_config.get("condition_field")
        if not condition_field or condition_field not in device_data:
            return self.create_error_result("Condition field not found")

        # 简化处理，返回基础配置
        return {
            "_virtual_device": True,
            "_classification_type": "conditional",
            "_condition_field": condition_field,
        }

    def _resolve_bitwise_classification(
        self, dynamic_config: Dict[str, Any], device_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析位操作分类设备(简化版)

        Args:
            dynamic_config: 动态配置
            device_data: 设备数据

        Returns:
            解析结果
        """
        source_field = dynamic_config.get("source_field")
        if not source_field or source_field not in device_data:
            return self.create_error_result("Source field not found")

        # 简化处理，返回基础配置
        return {
            "_virtual_device": True,
            "_classification_type": "bitwise",
            "_source_field": source_field,
        }

    def _resolve_bitmask_virtual_devices(
        self, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析bitmask虚拟设备

        Args:
            device: 设备数据
            raw_config: 原始配置

        Returns:
            解析结果
        """
        device_data = self.get_device_data(device)
        result = {}

        _LOGGER.debug(
            "Resolving bitmask virtual devices for device %s",
            device.get("me", "unknown"),
        )

        # 遍历所有IO口，检测bitmask类型并生成虚拟设备
        virtual_device_count = 0
        for io_port, io_data in device_data.items():
            # O(1)检测bitmask类型
            bitmask_type = self.mapping_registry.is_bitmask_io_port(io_port)

            # 特殊处理config_bitmask
            if not bitmask_type and isinstance(io_data, dict):
                if io_data.get("type") == "config_bitmask":
                    bitmask_type = "config_bitmask"

            if bitmask_type:
                _LOGGER.debug("Processing %s IO port %s", bitmask_type, io_port)

                # 获取虚拟设备配置
                virtual_devices = self.mapping_registry.get_virtual_devices(
                    bitmask_type, io_port
                )

                # 按platform分组虚拟设备
                for virtual_device in virtual_devices:
                    platform = virtual_device.platform
                    if platform not in result:
                        result[platform] = {}

                    # 生成虚拟设备配置
                    virtual_config = self._create_virtual_device_config(
                        virtual_device, bitmask_type, io_port
                    )

                    result[platform][virtual_device.key] = virtual_config
                    virtual_device_count += 1

        _LOGGER.debug(
            "Generated %d virtual devices across %d platforms",
            virtual_device_count,
            len(result),
        )

        # 合并原始配置
        if raw_config:
            base_config = self.ha_constant_strategy.convert_data_to_ha_mapping(
                raw_config
            )
            result = self._merge_configs(result, base_config)

        # 添加元数据
        if result:
            result["_virtual_device_strategy"] = True
            result["_virtual_device_count"] = virtual_device_count

        return result

    def _create_virtual_device_config(
        self, virtual_device: VirtualDevice, bitmask_type: str, io_port: str
    ) -> Dict[str, Any]:
        """
        创建虚拟设备配置

        Args:
            virtual_device: 虚拟设备定义
            bitmask_type: bitmask类型
            io_port: 源IO口

        Returns:
            虚拟设备配置字典
        """
        config = {
            "description": virtual_device.description,
            "rw": "R",  # 虚拟设备默认只读
            "data_type": f"{bitmask_type.lower()}_{virtual_device.platform}",
            "conversion": virtual_device.extraction_params.get(
                "conversion", "val_direct"
            ),
            "detailed_description": virtual_device.description,
            "friendly_name": virtual_device.friendly_name,
            # HA特性
            "device_class": virtual_device.device_class,
            # 虚拟设备元数据
            "_is_virtual_device": True,
            "_bitmask_type": bitmask_type,
            "_source_io_port": io_port,
            "_virtual_key": virtual_device.key,
            "_extraction_params": virtual_device.extraction_params,
        }

        # 应用HA常量转换
        return self.ha_constant_strategy.convert_data_to_ha_mapping(config)

    def _merge_configs(
        self, virtual_config: Dict[str, Any], base_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        智能合并虚拟设备配置和基础配置

        Args:
            virtual_config: 虚拟设备配置
            base_config: 基础设备配置

        Returns:
            合并后的配置
        """
        result = virtual_config.copy()

        for platform, ios in base_config.items():
            if platform.startswith("_"):  # 跳过元数据字段
                continue

            if platform in result:
                # 合并到现有平台，基础配置优先
                if isinstance(ios, dict) and isinstance(result[platform], dict):
                    merged_ios = ios.copy()
                    merged_ios.update(result[platform])  # 虚拟设备覆盖同名IO
                    result[platform] = merged_ios
            else:
                # 新增平台
                result[platform] = ios

        return result

    def get_strategy_stats(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        return {
            "bitmask_types_supported": self.mapping_registry.get_all_bitmask_types(),
            "device_class_mappings": len(
                self.mapping_registry._device_class_platform_mapping
            ),
            "virtual_device_cache_size": len(
                self.mapping_registry._virtual_device_cache
            ),
        }
