"""
DeviceStrategyFactory - 设备解析策略工厂

基于设备类型和配置特征选择合适的解析策略。
替代原始mapping_engine的硬编码if-elif逻辑，实现策略模式的动态分派。

支持的策略类型:
- DynamicDeviceStrategy: 动态分类设备 (priority=10)
- VersionedDeviceStrategy: 版本化设备 (priority=20)
- VirtualDeviceStrategy: 虚拟设备处理 (priority=30)
- StaticDeviceStrategy: 静态设备映射 (priority=90)

由 @MapleEve 创建，基于Phase 2.5关键重构任务
"""

import logging
from typing import Dict, Any, List, Optional

from .base_strategy import BaseDeviceStrategy
from .ha_constant_strategy import HAConstantStrategy
from .dynamic_device_strategy import DynamicDeviceStrategy
from .static_device_strategy import StaticDeviceStrategy
from .versioned_device_strategy import VersionedDeviceStrategy
from .virtual_device_strategy import VirtualDeviceStrategy


_LOGGER = logging.getLogger(__name__)


class DeviceStrategyFactory:
    """
    设备解析策略工厂

    根据设备类型和配置特征选择最合适的解析策略。
    替代mapping_engine的复杂判断逻辑，实现策略模式的清晰分派。
    """

    def __init__(self):
        """初始化策略工厂，创建所有策略实例"""
        # 创建HA常量转换工具策略
        self.ha_constant_strategy = HAConstantStrategy()

        # 创建所有策略实例
        self.strategies: List[BaseDeviceStrategy] = [
            DynamicDeviceStrategy(self.ha_constant_strategy),
            VersionedDeviceStrategy(self.ha_constant_strategy),
            VirtualDeviceStrategy(self.ha_constant_strategy),
            StaticDeviceStrategy(self.ha_constant_strategy),
        ]

        # 按优先级排序策略
        self.strategies.sort(key=lambda s: s.priority)

        _LOGGER.debug(
            "DeviceStrategyFactory initialized with %d strategies", len(self.strategies)
        )

    def get_strategy(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Optional[BaseDeviceStrategy]:
        """
        获取处理指定设备的最佳策略

        Args:
            device_type: 设备类型
            device: 设备数据字典
            raw_config: 原始设备配置

        Returns:
            BaseDeviceStrategy: 选中的策略或None
        """
        # 按优先级顺序尝试各个策略
        for strategy in self.strategies:
            try:
                if strategy.can_handle(device_type, device, raw_config):
                    _LOGGER.debug(
                        "Selected strategy %s for device %s (type: %s)",
                        strategy.get_strategy_name(),
                        device.get("me", "unknown"),
                        device_type,
                    )
                    return strategy
            except Exception as e:
                _LOGGER.warning(
                    "Strategy %s failed to evaluate device %s: %s",
                    strategy.get_strategy_name(),
                    device.get("me", "unknown"),
                    e,
                )
                continue

        _LOGGER.warning(
            "No suitable strategy found for device %s (type: %s)",
            device.get("me", "unknown"),
            device_type,
        )
        return None

    def resolve_device_mapping(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用最佳策略解析设备映射

        Args:
            device_type: 设备类型
            device: 设备数据字典
            raw_config: 原始设备配置

        Returns:
            Dict[str, Any]: 解析后的设备配置
        """
        strategy = self.get_strategy(device_type, device, raw_config)

        if not strategy:
            return {
                "_error": f"No suitable strategy found for device type: {device_type}",
                "_factory": "DeviceStrategyFactory",
            }

        try:
            return strategy.resolve_device_mapping(device, raw_config)
        except Exception as e:
            _LOGGER.exception(
                "Strategy %s failed to resolve device %s",
                strategy.get_strategy_name(),
                device.get("me", "unknown"),
            )
            return {
                "_error": f"Strategy {strategy.get_strategy_name()} failed: {str(e)}",
                "_factory": "DeviceStrategyFactory",
                "_strategy": strategy.get_strategy_name(),
            }

    def get_available_strategies(self) -> List[str]:
        """
        获取所有可用策略的名称列表

        Returns:
            List[str]: 策略名称列表
        """
        return [strategy.get_strategy_name() for strategy in self.strategies]

    def get_strategy_by_name(self, strategy_name: str) -> Optional[BaseDeviceStrategy]:
        """
        根据名称获取策略实例

        Args:
            strategy_name: 策略名称

        Returns:
            BaseDeviceStrategy: 策略实例或None
        """
        for strategy in self.strategies:
            if strategy.get_strategy_name() == strategy_name:
                return strategy
        return None

    def get_factory_stats(self) -> Dict[str, Any]:
        """
        获取工厂统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "total_strategies": len(self.strategies),
            "strategies": [
                {"name": strategy.get_strategy_name(), "priority": strategy.priority}
                for strategy in self.strategies
            ],
        }


# 全局工厂实例
_global_factory: Optional[DeviceStrategyFactory] = None


def get_device_strategy_factory() -> DeviceStrategyFactory:
    """
    获取全局策略工厂实例

    Returns:
        DeviceStrategyFactory: 全局工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = DeviceStrategyFactory()
    return _global_factory


def resolve_device_with_strategy(
    device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    便捷函数：使用策略工厂解析设备

    Args:
        device_type: 设备类型
        device: 设备数据字典
        raw_config: 原始设备配置

    Returns:
        Dict[str, Any]: 解析后的设备配置
    """
    factory = get_device_strategy_factory()
    return factory.resolve_device_mapping(device_type, device, raw_config)
