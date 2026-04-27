"""
Device Resolution Strategies - Phase 2.5 Architecture Refactoring

Strategy模式实现，用于解决mapping_engine的1538行复杂性问题。
基于ZEN专家深度分析，将77个方法按职责拆分为专门的策略类。

Core Strategy Classes:
- BaseDeviceStrategy: 统一接口定义
- DynamicDeviceStrategy: 动态设备模式处理 (替代254行巨型方法)
- VirtualDeviceStrategy: 虚拟设备处理 (替代385行复杂逻辑)
- VersionedDeviceStrategy: 版本化设备处理
- StaticDeviceStrategy: 静态设备映射
- HAConstantStrategy: HA常量转换工具

由 @MapleEve 创建，基于Phase 2.5关键重构任务
"""

from .base_strategy import BaseDeviceStrategy
from .strategy_factory import DeviceStrategyFactory
from .dynamic_device_strategy import DynamicDeviceStrategy
from .virtual_device_strategy import VirtualDeviceStrategy
from .versioned_device_strategy import VersionedDeviceStrategy
from .static_device_strategy import StaticDeviceStrategy
from .ha_constant_strategy import HAConstantStrategy

__all__ = [
    "BaseDeviceStrategy",
    "DeviceStrategyFactory",
    "DynamicDeviceStrategy",
    "VirtualDeviceStrategy",
    "VersionedDeviceStrategy",
    "StaticDeviceStrategy",
    "HAConstantStrategy",
]
