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

from typing import Dict, Any

from .base_strategy import BaseDeviceStrategy
from .ha_constant_strategy import HAConstantStrategy


class VirtualDeviceStrategy(BaseDeviceStrategy):
    """
    虚拟设备解析策略

    处理需要生成虚拟子设备或多平台虚拟设备的复杂设备。
    注意：当前为简化实现，未完全集成所有虚拟设备逻辑。
    """

    def __init__(self, ha_constant_strategy: HAConstantStrategy):
        """
        初始化虚拟设备策略

        Args:
            ha_constant_strategy: HA常量转换策略实例
        """
        self.ha_constant_strategy = ha_constant_strategy

        # 尝试导入数据处理器
        try:
            from ..data.processors.data_processors import (
                is_alm_io_port,
                get_alm_subdevices,
            )

            self.is_alm_io_port = is_alm_io_port
            self.get_alm_subdevices = get_alm_subdevices
            self._data_processors_available = True
        except ImportError:
            self._data_processors_available = False

    def can_handle(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> bool:
        """
        判断是否需要虚拟设备处理

        Args:
            device_type: 设备类型
            device: 设备数据
            raw_config: 原始配置

        Returns:
            bool: 是否能处理此设备
        """
        # 检查是否有动态分类配置
        if "dynamic_classification" in raw_config:
            return True

        # 检查是否有ALM虚拟设备需求(简化版)
        if self._data_processors_available:
            device_data = device.get("data", {})
            for io_port in device_data.keys():
                if self.is_alm_io_port(io_port):
                    return True

        return False

    def resolve_device_mapping(
        self, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析虚拟设备映射

        从原始mapping_engine的虚拟设备处理逻辑简化提取

        Args:
            device: 设备数据字典
            raw_config: 原始设备配置

        Returns:
            解析后的设备配置
        """
        device_data = self.get_device_data(device)

        # 检查动态分类
        if "dynamic_classification" in raw_config:
            return self._resolve_dynamic_classification(raw_config, device_data)

        # 处理ALM虚拟设备(简化版)
        if self._data_processors_available:
            return self._handle_alm_virtual_devices(raw_config, device_data)

        return self.create_error_result("No virtual device processing available")

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

    def _handle_alm_virtual_devices(
        self, raw_config: Dict[str, Any], device_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理ALM虚拟设备(简化版)

        Args:
            raw_config: 原始配置
            device_data: 设备数据

        Returns:
            处理结果
        """
        if not self._data_processors_available:
            return self.create_error_result("ALM data processors not available")

        # 查找ALM IO口
        alm_ports = []
        for io_port in device_data.keys():
            if self.is_alm_io_port(io_port):
                alm_ports.append(io_port)

        if not alm_ports:
            return self.create_error_result("No ALM IO ports found")

        # 简化处理，返回ALM虚拟设备信息
        result = {
            "_virtual_device": True,
            "_device_type": "alm_virtual",
            "_alm_ports": alm_ports,
        }

        # 应用HA常量转换
        if raw_config:
            base_config = self.ha_constant_strategy.convert_data_to_ha_mapping(
                raw_config
            )
            result.update(base_config)

        return result
