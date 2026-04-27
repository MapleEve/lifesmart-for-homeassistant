"""
StaticDeviceStrategy - 静态设备解析策略

处理静态配置的设备，提供基础的平台映射功能。
作为fallback策略，处理不需要特殊逻辑的标准设备。

从原始mapping_engine的静态设备处理逻辑提取，包括：
- 基础平台到IO口的映射
- HA常量转换应用
- 简单的配置验证

由 @MapleEve 创建，基于Phase 2.5关键重构任务
"""

from typing import Dict, Any

from .base_strategy import BaseDeviceStrategy
from .ha_constant_strategy import HAConstantStrategy


class StaticDeviceStrategy(BaseDeviceStrategy):
    """
    静态设备解析策略

    处理不需要特殊逻辑的标准设备，提供基础的平台映射功能。
    作为fallback策略，确保所有设备都能得到基本的配置支持。
    """

    def __init__(self, ha_constant_strategy: HAConstantStrategy):
        """
        初始化静态设备策略

        Args:
            ha_constant_strategy: HA常量转换策略实例
        """
        self.ha_constant_strategy = ha_constant_strategy

    def can_handle(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> bool:
        """
        静态策略作为fallback，处理所有其他策略无法处理的设备

        Args:
            device_type: 设备类型
            device: 设备数据
            raw_config: 原始配置

        Returns:
            bool: 始终返回True，作为fallback策略
        """
        # 静态策略作为最后的fallback，总是能处理
        return True

    def resolve_device_mapping(
        self, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析静态设备映射

        从原始mapping_engine._resolve_static_mapping方法提取

        Args:
            device: 设备数据字典
            raw_config: 原始设备配置

        Returns:
            解析后的设备配置
        """
        if not self.validate_raw_config(raw_config):
            return self.create_error_result(
                "Invalid raw configuration for static device"
            )

        # 应用HA常量转换
        device_config = self.ha_constant_strategy.convert_data_to_ha_mapping(raw_config)

        # 检查是否需要额外的静态映射处理
        device_data = self.get_device_data(device)

        # 提取平台映射
        result = self._extract_platform_mapping(device_config, device_data)

        return result

    def get_strategy_name(self) -> str:
        return "StaticDeviceStrategy"

    @property
    def priority(self) -> int:
        return 90  # 最低优先级，作为fallback策略

    def _extract_platform_mapping(
        self, device_config: Dict[str, Any], device_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从设备配置中提取平台映射

        Args:
            device_config: 已转换HA常量的设备配置
            device_data: 设备数据

        Returns:
            平台映射结果
        """
        result = {}

        for platform, ios in device_config.items():
            if platform == "name" or not isinstance(ios, dict):
                # 保留名称和非字典字段
                result[platform] = ios
                continue

            # 处理平台配置
            platform_ios = {}
            for io_port, io_config in ios.items():
                if isinstance(io_config, dict) and "description" in io_config:
                    # 只保留有效的IO配置
                    # 对于静态设备，简化处理逻辑
                    processed_config = io_config.copy()

                    # 添加静态设备特有标记
                    processed_config["_device_strategy"] = "static"
                    processed_config["_static_io"] = True

                    platform_ios[io_port] = processed_config

            if platform_ios:
                result[platform] = platform_ios

        return result
